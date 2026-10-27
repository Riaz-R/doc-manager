"""A small hand-written state machine, shared by Page and Document.

A lifecycle is a table of allowed moves. Every change to a Page or Document goes
through `apply()`, which checks the table, runs any guard, and writes one
StateChange row so the history is complete.
"""

from datetime import datetime
from enum import StrEnum
from typing import ClassVar

from sqlalchemy.orm import Mapped, mapped_column, object_session

from docmanager.errors import UserFacingError


class InvalidTransition(UserFacingError):
    """A move the lifecycle doesn't allow. The message is plain words for the user."""


class Lifecycle:
    """The table of allowed moves: {(from_state, action): to_state}.

    `None` as a from-state means "(new)", an object that doesn't exist yet.
    `None` as a to-state means "(row deleted)".
    """

    def __init__(
        self,
        *,
        noun: str,
        state_type: type[StrEnum],
        transitions: dict[tuple[StrEnum | None, str], StrEnum | None],
        phrases: dict[str, str] | None = None,
    ):
        self.noun = noun  # "document", used in refusal messages
        self.state_type = state_type  # the enum that the stored text turns back into
        self.transitions = transitions
        self.phrases = phrases or {}  # action -> "moved to the bin"

    def target(self, state: StrEnum | None, action: str) -> StrEnum | None:
        """The state `action` leads to from `state`, or a plain-words refusal."""
        if (state, action) not in self.transitions:
            if action in self.phrases:
                what = f"be {self.phrases[action]}"
            else:
                what = f'have "{action}" applied'
            label = state.label if state is not None else "New"
            raise InvalidTransition(
                f'This {self.noun} can\'t {what} while it is "{label}"'
            )
        return self.transitions[(state, action)]

    def actions_from(self, state: StrEnum | None) -> list[str]:
        """Every action the table lists for `state`, in table order."""
        return [
            action for (from_state, action) in self.transitions if from_state == state
        ]


class Stateful:
    """Mixin for a model that follows a Lifecycle.

    The subclass sets `kind` (for the history rows) and `lifecycle`, and needs an
    `id` column. The state is stored as text in a column named `state`.
    """

    kind: ClassVar[str]
    lifecycle: ClassVar[Lifecycle]

    _state: Mapped[str | None] = mapped_column("state", default=None)

    @property
    def state(self) -> StrEnum | None:
        """The current state. Read-only: change it only through `apply()`."""
        if self._state is None:
            return None  # "(new)"
        return self.lifecycle.state_type(self._state)

    def allowed_actions(self) -> list[str]:
        """Actions the table allows now. Guards aren't run, so a button can show and then refuse."""
        return self.lifecycle.actions_from(self.state)

    def apply(self, action: str, *, now: datetime, note: str | None = None) -> None:
        """Make one move: check the table, run the guard, set the state, record it."""
        from docmanager.models.records import StateChange

        session = object_session(self)
        if session is None:
            raise RuntimeError("Add this object to a session before applying an action")

        from_state = self.state
        to_state = self.lifecycle.target(from_state, action)

        guard = getattr(self, f"guard_{action}", None)
        if guard is not None:
            reason = guard(now)
            if reason:
                raise InvalidTransition(reason)

        # A move to "(row deleted)" leaves the state as it is: the service deletes
        # the row straight afterwards, in the same transaction.
        if to_state is not None:
            self._state = to_state.value
        if self.id is None:
            session.flush()  # the database gives the new row its id

        session.add(
            StateChange(
                object_kind=self.kind,
                object_id=self.id,
                action=action,
                from_state=from_state.value if from_state else None,
                to_state=to_state.value if to_state else None,
                at=now,
                note=note,
            )
        )
