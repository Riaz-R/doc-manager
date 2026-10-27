import re
from pathlib import Path

import docmanager

WEB = Path(docmanager.__file__).parent / "web"
URL = re.compile(r"https?://", re.IGNORECASE)


def test_no_template_or_static_file_references_an_http_url():
    # AT-22: nothing is fetched from the network, so no page may point at a URL.
    files = [p for folder in ("templates", "static") for p in (WEB / folder).rglob("*")]
    files = [p for p in files if p.is_file()]
    assert files, "expected templates and a stylesheet to scan"

    offenders = [str(p.relative_to(WEB)) for p in files if URL.search(p.read_text())]

    assert offenders == []
