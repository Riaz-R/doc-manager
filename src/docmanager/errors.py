class UserFacingError(Exception):
    """A refusal whose message is written in plain words for the user.

    The app shows the message in a banner instead of an error page. The
    domain errors (InvalidTransition, UploadRefused, GroupingError) build on it.
    """
