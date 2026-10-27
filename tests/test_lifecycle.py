"""The lifecycle engine, tested with a lamp that exists only in this file."""

from enum import StrEnum

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from docmanager.db import Base
from docmanager.errors import UserFacingError
from docmanager.lifecycle import InvalidTransition, Lifecycle, Stateful
from docmanager.models.records import StateChange


class LampState(StrEnum):
    OFF = "off"
    ON = "on"

    @property
    def label(self) -> str:
        return {"off": "Off", "on": "On"}[self.value]


LAMP_LIFECYCLE = Lifecycle(
    noun="lamp",
    state_type=LampState,
    transitions={
        (None, "install"): LampState.OFF,
        (LampState.OFF, "switch_on"): LampState.ON,
        (LampState.ON, "switch_off"): LampState.OFF,
        (LampState.OFF, "scrap"): None,
    },
    phrases={"switch_off": "switched off", "switch_on": "switched on"},
)


class Lamp(Stateful, Base):
    __tablename__ = "test_lamps"
    kind = "lamp"
    lifecycle = LAMP_LIFECYCLE

    id: Mapped[int] = mapped_column(primary_key=True)
    has_bulb: Mapped[bool] = mapped_column(default=True)

    def guard_switch_on(self, now):
        if not self.has_bulb:
            return "The bulb is missing"
        return None


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def lamp(session, now):
    """A lamp that has been installed, so it is Off."""
    lamp = Lamp()
    session.add(lamp)
    lamp.apply("install", now=now)
    session.commit()
    return lamp


def changes(session):
    return session.scalars(select(StateChange).order_by(StateChange.id)).all()


def test_allowed_move_changes_state_and_writes_one_state_change(session, lamp, now):
    lamp.apply("switch_on", now=now, note="Evening")

    assert lamp.state == LampState.ON
    on_change = changes(session)[-1]
    assert len(changes(session)) == 2  # install, then switch_on
    assert on_change.object_kind == "lamp"
    assert on_change.object_id == lamp.id
    assert on_change.action == "switch_on"
    assert on_change.from_state == "off"
    assert on_change.to_state == "on"
    assert on_change.at == now
    assert on_change.note == "Evening"


def test_a_new_object_gets_its_id_before_its_history_row_is_written(session, now):
    lamp = Lamp()
    session.add(lamp)
    assert lamp.id is None
    assert lamp.state is None  # "(new)"

    lamp.apply("install", now=now)

    assert lamp.id is not None
    [change] = changes(session)
    assert change.object_id == lamp.id
    assert change.from_state is None
    assert change.to_state == "off"


def test_unknown_pair_raises_in_plain_words_and_changes_nothing(session, lamp, now):
    with pytest.raises(InvalidTransition) as problem:
        lamp.apply("switch_off", now=now)

    assert str(problem.value) == 'This lamp can\'t be switched off while it is "Off"'
    assert lamp.state == LampState.OFF
    assert len(changes(session)) == 1  # only the install


def test_a_new_object_can_only_make_its_first_move(session, now):
    lamp = Lamp()
    session.add(lamp)

    with pytest.raises(InvalidTransition) as problem:
        lamp.apply("switch_on", now=now)

    assert str(problem.value) == 'This lamp can\'t be switched on while it is "New"'


def test_unknown_action_name_still_gives_a_plain_message(lamp, now):
    with pytest.raises(InvalidTransition) as problem:
        lamp.apply("explode", now=now)

    assert (
        str(problem.value)
        == 'This lamp can\'t have "explode" applied while it is "Off"'
    )


def test_guard_reason_is_raised_and_changes_nothing(session, lamp, now):
    lamp.has_bulb = False

    with pytest.raises(InvalidTransition) as problem:
        lamp.apply("switch_on", now=now)

    assert str(problem.value) == "The bulb is missing"
    assert lamp.state == LampState.OFF
    assert len(changes(session)) == 1


def test_a_guard_that_returns_nothing_lets_the_move_through(lamp, now):
    lamp.apply("switch_on", now=now)
    assert lamp.state == LampState.ON


def test_state_has_no_setter(lamp):
    with pytest.raises(AttributeError):
        lamp.state = LampState.ON


def test_allowed_actions_follow_the_table_and_ignore_guards(lamp, now):
    lamp.has_bulb = False
    assert lamp.allowed_actions() == ["switch_on", "scrap"]

    lamp.has_bulb = True
    lamp.apply("switch_on", now=now)
    assert lamp.allowed_actions() == ["switch_off"]


def test_a_move_to_row_deleted_is_recorded_and_leaves_the_state_alone(
    session, lamp, now
):
    lamp.apply("scrap", now=now)

    scrap = changes(session)[-1]
    assert scrap.action == "scrap"
    assert scrap.from_state == "off"
    assert scrap.to_state is None
    # The service deletes the row next; until then the object still says Off.
    assert lamp.state == LampState.OFF


def test_apply_needs_the_object_to_be_in_a_session(now):
    with pytest.raises(RuntimeError, match="session"):
        Lamp().apply("install", now=now)


def test_lifecycle_target_and_actions_from_work_without_a_database():
    assert LAMP_LIFECYCLE.target(None, "install") == LampState.OFF
    assert LAMP_LIFECYCLE.target(LampState.OFF, "scrap") is None
    assert LAMP_LIFECYCLE.actions_from(None) == ["install"]
    assert LAMP_LIFECYCLE.actions_from(LampState.ON) == ["switch_off"]


def test_invalid_transition_is_a_plain_words_error_the_app_can_flash():
    assert issubclass(InvalidTransition, UserFacingError)
