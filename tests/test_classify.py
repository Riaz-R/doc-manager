from datetime import date, datetime

import pytest
import texts

from docmanager import config
from docmanager.demo.photos import INVOICE, LETTER, UNCLEAR
from docmanager.rules.classify import (
    LOW_TEXT_REASON,
    Classification,
    classify,
    count_words,
)

TODAY = date(2026, 10, 27)

LOW_TEXT = (
    "Very little text was read. Check the photos are clear before shredding the paper."
)


class StandInClient:
    """Just the two things the rules read from a client."""

    def __init__(self, ref, name):
        self.ref, self.name = ref, name


HOLLYBROOK = StandInClient("C-0042", "Hollybrook Bakery Ltd")
SMITH_LTD = StandInClient("C-0017", "Smith Ltd")
J_SMITH = StandInClient("C-0018", "J Smith & Co")
CLIENTS = [HOLLYBROOK, SMITH_LTD, J_SMITH]


def run(text, clients=CLIENTS, today=TODAY):
    return classify(text, clients, today)


# --- count_words ---


@pytest.mark.parametrize(
    "text,count",
    [
        ("", 0),
        ("   \n\t ", 0),
        ("one two three", 3),
        ("one\ntwo\n\nthree", 3),
        ("INV-1043 14/03/2021 120.00", 3),
        ("--- | ... £ &", 0),  # no letter or digit in any piece
        ("a - b", 2),
        ("café naïve", 2),  # letters outside ASCII count
        ("7", 1),
    ],
)
def test_a_word_is_a_whitespace_separated_piece_with_a_letter_or_digit(text, count):
    assert count_words(text) == count


def test_the_fixtures_have_at_least_20_words_except_the_c11_text():
    for name in dir(texts):
        value = getattr(texts, name)
        if name.isupper() and isinstance(value, str):
            if name == "INVOICE_ELEVEN_WORDS":
                assert count_words(value) == 11
            else:
                assert count_words(value) >= config.MIN_OCR_WORDS, name


def test_the_demo_documents_have_at_least_20_words_too():
    for document in (INVOICE, LETTER, UNCLEAR):
        assert count_words(document.text) >= config.MIN_OCR_WORDS, document.name


# --- C1: confident ---


def test_c1_a_confident_invoice_passes_every_check():
    result = run(texts.INVOICE_C1)

    assert isinstance(result, Classification)
    assert result.reasons == []
    assert result.passed
    assert result.doc_type == "invoice"
    assert (result.type_score, result.runner_up_score) == (12, 0)
    assert result.client is HOLLYBROOK
    assert result.document_date == date(2021, 3, 14)
    assert result.fields == {"invoice_number": "INV-1043", "amount_pence": 12000}


def test_the_fields_never_hold_the_date_because_json_cannot_store_one():
    assert "document_date" not in run(texts.INVOICE_C1).fields


def test_a_confident_letter_passes_with_a_client_found_by_ref():
    text = texts.LETTER + "\nOur ref: C-0042\n"

    result = run(text)

    assert result.reasons == []
    assert result.doc_type == "letter"
    assert result.fields == {"subject": "Year end accounts reminder"}
    assert result.document_date == date(2022, 5, 10)


def test_a_date_after_today_is_not_used():
    text = texts.INVOICE_C1.replace("14/03/2021", "14/03/2031")

    result = run(text)

    assert result.passed
    assert result.document_date is None


def test_the_demo_invoice_and_letter_pass_and_the_notes_do_not():
    invoice = run(INVOICE.text)
    letter = run(LETTER.text)
    notes = run(UNCLEAR.text)

    assert (invoice.passed, invoice.doc_type, invoice.client) == (
        True,
        "invoice",
        HOLLYBROOK,
    )
    assert invoice.document_date == date(2026, 3, 14)
    assert invoice.fields["invoice_number"] == "INV-1043"
    assert (letter.passed, letter.doc_type, letter.client) == (
        True,
        "letter",
        HOLLYBROOK,
    )
    assert not notes.passed
    assert notes.doc_type is None


# --- C2 and C3: the type check ---


def test_c2_an_unclear_type_is_flagged_with_both_candidates():
    result = run(texts.MIXED_INVOICE_7_LETTER_5)

    assert result.reasons == ["Not sure what type this is (Invoice or Letter?)"]
    assert result.doc_type is None
    assert (result.type_score, result.runner_up_score) == (7, 5)
    assert result.fields == {}
    assert result.document_date is None


def test_c3_text_that_scores_zero_for_every_type_is_flagged():
    text = texts.NO_KEYWORDS + "\nClient reference C-0042\n"

    result = run(text)

    assert result.reasons == ["Couldn't tell what type this is"]
    assert result.doc_type is None
    assert (result.type_score, result.runner_up_score) == (0, 0)


def test_a_single_weak_candidate_is_named_on_its_own():
    text = (
        texts.NO_KEYWORDS + "\nClient reference C-0042\nTotal\ninvoice\n"
    )  # Invoice 5

    result = run(text)

    assert result.reasons == ["Not sure what type this is (Invoice?)"]
    assert result.type_score == 5
    assert result.runner_up_score == 0


def test_a_score_just_under_the_minimum_is_not_enough():
    assert config.MIN_TYPE_SCORE == 6
    text = (
        texts.NO_KEYWORDS + "\nClient reference C-0042\ninvoice amount due\n"
    )  # 4 + 3 = 7
    assert run(text).doc_type == "invoice"

    text = texts.NO_KEYWORDS + "\nClient reference C-0042\ninvoice vat\n"  # 4 + 1 = 5
    assert run(text).doc_type is None


def test_the_margin_must_be_at_least_3_and_exactly_3_is_enough():
    assert config.MIN_TYPE_MARGIN == 3
    base = texts.NO_KEYWORDS + "\nClient reference C-0042\n"
    # Invoice 7 ("invoice" + "amount due"), Letter 4 ("dear" 3 + "enclosed" 1).
    assert run(base + "invoice amount due dear enclosed").doc_type == "invoice"
    # Invoice 7, Letter 5 ("dear" + "re:") is a margin of 2.
    assert run(base + "invoice amount due dear re:").doc_type is None


def test_a_tie_names_the_types_in_registry_order():
    text = (
        texts.NO_KEYWORDS
        + "\nClient reference C-0042\ninvoice amount due dear re: enclosed\n"
    )
    # Invoice 7, Letter 6.
    assert run(text).reasons == ["Not sure what type this is (Invoice or Letter?)"]


def test_thresholds_come_from_config(monkeypatch):
    monkeypatch.setattr(config, "MIN_TYPE_SCORE", 13)

    assert run(texts.INVOICE_C1).reasons == ["Not sure what type this is (Invoice?)"]


# --- C4, C5 and the client rules ---


def test_c4_two_client_names_and_no_reference_is_flagged_in_order_of_appearance():
    result = run(texts.INVOICE_TWO_CLIENT_NAMES)

    assert result.reasons == ["More than one client matched: Smith Ltd, J Smith & Co"]
    assert result.client is None
    assert result.doc_type == "invoice"  # the type check still passed


def test_c5_an_unknown_reference_is_flagged():
    result = run(texts.INVOICE_UNKNOWN_REF)

    assert result.reasons == ["Client C-0099 isn't in your client list"]
    assert result.client is None


def test_an_unknown_reference_is_not_rescued_by_a_name_in_the_text():
    text = texts.INVOICE_UNKNOWN_REF + "\nHollybrook Bakery Ltd\n"

    assert run(text).reasons == ["Client C-0099 isn't in your client list"]


def test_two_references_are_flagged_even_if_both_are_known():
    result = run(texts.INVOICE_TWO_REFS)

    assert result.reasons == ["More than one client reference found: C-0043, C-0042"]
    assert result.client is None


def test_the_same_reference_written_twice_is_one_reference():
    text = texts.INVOICE_C1 + "\nClient reference C-0042 again\n"

    assert run(text).reasons == []


def test_a_reference_is_found_whatever_its_case():
    text = texts.INVOICE_C1.replace("C-0042", "c-0042")

    assert run(text).client is HOLLYBROOK


def test_with_no_reference_a_single_name_matches_whole_phrase_ignoring_case():
    result = run(texts.INVOICE_NAME_ONLY)

    assert result.reasons == []
    assert result.client is HOLLYBROOK


@pytest.mark.parametrize(
    "name_in_text",
    [
        "Hollybrook Bakery Limited",
        "Hollybrook Bakery",
        "xHollybrook Bakery Ltd",
        "Hollybrook Bakery Ltdx",
    ],
)
def test_a_name_must_match_as_a_whole_phrase(name_in_text):
    text = texts.INVOICE_NAME_ONLY.replace("HOLLYBROOK BAKERY LTD", name_in_text)

    assert run(text).reasons == ["Couldn't tell which client this is for"]


def test_a_name_may_be_split_across_lines():
    text = texts.INVOICE_NAME_ONLY.replace(
        "HOLLYBROOK BAKERY LTD", "Hollybrook\nBakery  Ltd"
    )

    assert run(text).client is HOLLYBROOK


def test_no_reference_and_no_name_is_flagged():
    text = texts.INVOICE_NAME_ONLY.replace("HOLLYBROOK BAKERY LTD", "the shop")

    assert run(text).reasons == ["Couldn't tell which client this is for"]


def test_with_an_empty_register_nothing_matches():
    assert run(texts.INVOICE_NAME_ONLY, clients=[]).reasons == [
        "Couldn't tell which client this is for"
    ]
    assert run(texts.INVOICE_C1, clients=[]).reasons == [
        "Client C-0042 isn't in your client list"
    ]


def test_real_client_objects_work_too():
    from docmanager.models.client import Client

    client = Client(
        ref="C-0042", name="Hollybrook Bakery Ltd", created_at=datetime(2026, 1, 1)
    )

    assert run(texts.INVOICE_C1, clients=[client]).client is client


# --- C6: no date does not block filing ---


def test_c6_no_date_still_passes_with_an_empty_date():
    result = run(texts.INVOICE_NO_DATE)

    assert result.reasons == []
    assert result.passed
    assert result.document_date is None
    assert result.fields["invoice_number"] == "INV-7000"


# --- C11: the low-text check ---


def test_c11_a_confident_11_word_text_is_flagged_with_the_low_text_reason():
    result = run(texts.INVOICE_ELEVEN_WORDS)

    assert result.reasons == [LOW_TEXT]
    assert LOW_TEXT_REASON == LOW_TEXT
    # The type and client checks still ran and passed.
    assert result.doc_type == "invoice"
    assert result.client is HOLLYBROOK
    assert result.document_date == date(2021, 3, 14)
    assert not result.passed


def test_exactly_20_words_is_enough_and_19_is_not():
    assert config.MIN_OCR_WORDS == 20
    padding = " ".join(["word"] * 9)  # INVOICE_ELEVEN_WORDS has 11, so 9 more is 20
    assert run(texts.INVOICE_ELEVEN_WORDS + " " + padding).reasons == []
    assert run(texts.INVOICE_ELEVEN_WORDS + " " + " ".join(["word"] * 8)).reasons == [
        LOW_TEXT
    ]


def test_the_minimum_word_count_comes_from_config(monkeypatch):
    monkeypatch.setattr(config, "MIN_OCR_WORDS", 11)

    assert run(texts.INVOICE_ELEVEN_WORDS).reasons == []


def test_empty_text_fails_all_three_checks_and_every_reason_is_recorded_in_order():
    result = run("")

    assert result.reasons == [
        LOW_TEXT,
        "Couldn't tell what type this is",
        "Couldn't tell which client this is for",
    ]
    assert result.doc_type is None
    assert result.client is None


def test_the_text_reason_comes_first_and_the_others_still_follow():
    text = "Dear Sir Re: hello"  # 4 words, Letter 5 only, and no client

    assert run(text).reasons == [
        LOW_TEXT,
        "Not sure what type this is (Letter?)",
        "Couldn't tell which client this is for",
    ]
