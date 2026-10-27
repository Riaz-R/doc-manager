"""Importing this package registers every table with `Base`, so `create_all` sees them."""

from docmanager.models import records  # noqa: F401
