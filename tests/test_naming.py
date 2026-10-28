from datetime import date
from pathlib import PurePosixPath

import pytest

from docmanager import config
from docmanager.models.document_types import DOCUMENT_TYPES
from docmanager.rules.naming import clean_part, free_path, relative_path

INVOICE = DOCUMENT_TYPES["invoice"]
LETTER = DOCUMENT_TYPES["letter"]
HOLLYBROOK = {"client_ref": "C-0042", "client_name": "Hollybrook Bakery Ltd"}


def invoice_path(**overrides):
    values = {
        **HOLLYBROOK,
        "doc_type": INVOICE,
        "fields": {"invoice_number": "INV-1043", "amount_pence": 12000},
        "document_date": date(2021, 3, 14),
        **overrides,
    }
    return relative_path(**values)


# --- N1: the default template ---


def test_n1_an_invoice_is_filed_under_client_type_and_date():
    assert invoice_path() == PurePosixPath(
        "C-0042 Hollybrook Bakery Ltd/Invoices/2021-03-14 Invoice INV-1043.pdf"
    )


def test_the_path_sits_under_the_archive_folder(tmp_path):
    archive = tmp_path / "archive"

    assert archive / invoice_path() == (
        tmp_path
        / "archive"
        / "C-0042 Hollybrook Bakery Ltd"
        / "Invoices"
        / "2021-03-14 Invoice INV-1043.pdf"
    )


def test_a_letter_uses_its_subject_as_the_key():
    path = relative_path(
        **HOLLYBROOK,
        doc_type=LETTER,
        fields={"subject": "Year end accounts reminder"},
        document_date=date(2022, 5, 10),
    )

    assert path == PurePosixPath(
        "C-0042 Hollybrook Bakery Ltd/Letters/2022-05-10 Letter Year end accounts reminder.pdf"
    )


def test_a_letter_with_no_subject_uses_the_word_letter():
    path = relative_path(
        **HOLLYBROOK,
        doc_type=LETTER,
        fields={"subject": None},
        document_date=date(2022, 5, 10),
    )

    assert path.name == "2022-05-10 Letter letter.pdf"


def test_an_invoice_with_no_number_uses_no_number():
    path = invoice_path(fields={"invoice_number": None})

    assert path.name == "2021-03-14 Invoice no number.pdf"


def test_the_template_is_read_from_config_when_none_is_given(monkeypatch):
    monkeypatch.setattr(
        config, "NAMING_TEMPLATE", "{client_ref}/{type_label} {key}.pdf"
    )

    assert invoice_path() == PurePosixPath("C-0042/Invoice INV-1043.pdf")


def test_a_template_can_be_passed_in():
    path = invoice_path(template="{type_plural}/{date} {key}.pdf")

    assert path == PurePosixPath("Invoices/2021-03-14 INV-1043.pdf")


# --- N2: no date ---


def test_n2_no_date_gives_undated():
    path = invoice_path(document_date=None)

    assert path == PurePosixPath(
        "C-0042 Hollybrook Bakery Ltd/Invoices/undated Invoice INV-1043.pdf"
    )


# --- N3: a name clash ---


def test_n3_a_free_name_is_left_alone():
    path = invoice_path()

    assert free_path(path, lambda p: False) == path


def test_n3_a_clash_adds_2_then_3_before_the_extension():
    path = invoice_path()
    folder = path.parent
    taken = {path}

    second = free_path(path, taken.__contains__)
    assert second == folder / "2021-03-14 Invoice INV-1043 (2).pdf"

    taken.add(second)
    third = free_path(path, taken.__contains__)
    assert third == folder / "2021-03-14 Invoice INV-1043 (3).pdf"
    assert third.name == "2021-03-14 Invoice INV-1043 (3).pdf"


def test_n3_a_gap_is_filled_first():
    path = invoice_path()
    taken = {path, path.with_name("2021-03-14 Invoice INV-1043 (3).pdf")}

    assert (
        free_path(path, taken.__contains__).name
        == "2021-03-14 Invoice INV-1043 (2).pdf"
    )


def test_n3_a_dot_inside_the_key_does_not_confuse_the_extension():
    path = invoice_path(fields={"invoice_number": "INV-1.5"})

    assert free_path(path, {path}.__contains__).name == (
        "2021-03-14 Invoice INV-1.5 (2).pdf"
    )


def test_n3_it_works_against_real_files(tmp_path):
    archive = tmp_path / "archive"
    path = invoice_path()
    (archive / path).parent.mkdir(parents=True)
    (archive / path).write_bytes(b"first")

    chosen = free_path(path, lambda p: (archive / p).exists())

    assert chosen.name == "2021-03-14 Invoice INV-1043 (2).pdf"


# --- N4: unsafe characters, and trailing dots and spaces ---


@pytest.mark.parametrize("char", list('/\\:*?"<>|'))
def test_n4_each_unsafe_character_becomes_a_dash(char):
    path = invoice_path(client_name=f"Smith{char}Jones")

    assert path.parts[0] == "C-0042 Smith-Jones"


def test_n4_all_the_unsafe_characters_at_once():
    path = invoice_path(client_name='A/B\\C:D*E?F"G<H>I|J')

    assert path.parts[0] == "C-0042 A-B-C-D-E-F-G-H-I-J"


def test_n4_a_slash_in_a_name_never_adds_a_folder_level():
    path = invoice_path(client_name="Smith/Jones/Sons")

    assert len(path.parts) == 3


def test_n4_trailing_dots_and_spaces_are_trimmed_from_a_name():
    path = invoice_path(client_name="Acme Ltd. . .  ")

    assert path.parts[0] == "C-0042 Acme Ltd"


def test_n4_trailing_dots_and_spaces_are_trimmed_from_the_key():
    path = invoice_path(fields={"invoice_number": "INV-9. "})

    assert path.name == "2021-03-14 Invoice INV-9.pdf"


def test_n4_the_folder_name_never_ends_in_a_dot_or_space():
    # Even when the client name is empty, so the folder would end in "C-0042 ".
    path = invoice_path(client_name="")

    assert path.parts[0] == "C-0042 -"
    for part in path.parts:
        assert part == part.rstrip(". ")


def test_n4_leading_dots_cannot_make_a_hidden_or_parent_folder():
    path = invoice_path(client_name="../..", fields={"invoice_number": "..hidden"})

    assert ".." not in path.parts
    assert all(not part.startswith(".") for part in path.parts)
    assert path.name == "2021-03-14 Invoice hidden.pdf"


@pytest.mark.parametrize(
    "text,cleaned",
    [
        ("", "-"),
        ("   ", "-"),
        ("...", "-"),
        (" . . ", "-"),
        ("\n\t", "-"),
        ("///", "---"),  # slashes become dashes, and dashes are fine
    ],
)
def test_a_value_with_nothing_usable_in_it_becomes_a_dash(text, cleaned):
    assert clean_part(text) == cleaned


def test_line_breaks_and_runs_of_spaces_become_a_single_space():
    path = relative_path(
        **HOLLYBROOK,
        doc_type=LETTER,
        fields={"subject": "Year end\n  accounts\treminder"},
        document_date=None,
    )

    assert path.name == "undated Letter Year end accounts reminder.pdf"


def test_control_characters_are_replaced():
    assert clean_part("a\x00b\x07c") == "a-b-c"


def test_control_characters_that_count_as_whitespace_become_a_space():
    assert clean_part("a\x1fb") == "a b"


def test_ordinary_unicode_letters_are_kept():
    assert clean_part("Café Müller & Søn") == "Café Müller & Søn"


def test_clean_part_leaves_an_ordinary_name_unchanged():
    assert clean_part("Hollybrook Bakery Ltd") == "Hollybrook Bakery Ltd"
