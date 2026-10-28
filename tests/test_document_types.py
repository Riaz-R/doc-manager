from datetime import date

import pytest
import texts

from docmanager import config
from docmanager.demo.photos import INVOICE, LETTER, UNCLEAR
from docmanager.models.document import Document
from docmanager.models.document_types import (
    DOCUMENT_TYPES,
    DocumentType,
    InvoiceType,
    LetterType,
)

TODAY = date(2026, 10, 27)
INVOICE_TYPE = DOCUMENT_TYPES["invoice"]
LETTER_TYPE = DOCUMENT_TYPES["letter"]


# --- The registry and the classes ---


def test_the_registry_holds_one_of_each_type_by_key():
    assert list(DOCUMENT_TYPES) == ["invoice", "letter"]
    assert isinstance(DOCUMENT_TYPES["invoice"], InvoiceType)
    assert isinstance(DOCUMENT_TYPES["letter"], LetterType)
    assert all(isinstance(t, DocumentType) for t in DOCUMENT_TYPES.values())


def test_each_type_has_its_key_labels_and_retention_years():
    assert (INVOICE_TYPE.key, INVOICE_TYPE.label, INVOICE_TYPE.plural_label) == (
        "invoice",
        "Invoice",
        "Invoices",
    )
    assert (LETTER_TYPE.key, LETTER_TYPE.label, LETTER_TYPE.plural_label) == (
        "letter",
        "Letter",
        "Letters",
    )
    assert INVOICE_TYPE.retention_years == 6
    assert LETTER_TYPE.retention_years == 3


def test_document_type_returns_the_registry_object_for_its_key():
    assert Document(doc_type="invoice").type is INVOICE_TYPE
    assert Document(doc_type="letter").type is LETTER_TYPE


def test_a_document_with_no_type_or_an_unknown_key_has_type_none():
    assert Document(doc_type=None).type is None
    assert Document(doc_type="payslip").type is None


# --- keyword_score ---


WEIGHTS = {"alpha": 4, "two words": 3, "re:": 2}


class TestKeywordScore:
    def score(self, text):
        return DocumentType.keyword_score(text, WEIGHTS)

    def test_each_keyword_counts_once_however_often_it_appears(self):
        assert self.score("alpha alpha alpha") == 4

    def test_weights_add_up(self):
        assert self.score("alpha and two words") == 7

    def test_case_is_ignored(self):
        assert self.score("ALPHA Two Words") == 7

    def test_only_whole_words_count(self):
        assert self.score("alphabet alphas malpha") == 0

    def test_a_phrase_matches_across_spaces_and_line_breaks(self):
        assert self.score("two\n  words") == 3

    def test_a_phrase_needs_all_its_words(self):
        assert self.score("two or words") == 0

    def test_a_keyword_with_a_colon_matches_at_the_start_of_a_word_only(self):
        assert self.score("Re: something") == 2
        assert self.score("more: something") == 0

    def test_a_colon_keyword_matches_even_with_no_space_after_it(self):
        assert self.score("Re:Subject") == 2

    def test_punctuation_next_to_a_keyword_is_fine(self):
        assert self.score("(alpha), two words.") == 7

    def test_no_keywords_scores_zero(self):
        assert self.score("") == 0


# --- score() on the fixtures (AT-11 parts) ---


@pytest.mark.parametrize(
    "text,invoice,letter",
    [
        (texts.INVOICE_C1, 12, 0),
        (texts.INVOICE_UNLABELLED_DATE, 10, 0),
        (texts.INVOICE_NO_NUMBER, 9, 0),
        (texts.LETTER, 0, 9),
        (texts.LETTER_NO_SUBJECT, 0, 6),
        (texts.MIXED_INVOICE_7_LETTER_5, 7, 5),
        (texts.NO_KEYWORDS, 0, 0),
    ],
)
def test_each_type_scores_the_fixtures(text, invoice, letter):
    assert INVOICE_TYPE.score(text) == invoice
    assert LETTER_TYPE.score(text) == letter


def test_the_demo_documents_score_as_intended():
    # The demo box must give a confident invoice, a confident letter, and a
    # document that scores 0 for both (so it lands in Needs checking).
    assert INVOICE_TYPE.score(INVOICE.text) == 12
    assert LETTER_TYPE.score(INVOICE.text) == 0
    assert LETTER_TYPE.score(LETTER.text) == 9
    assert INVOICE_TYPE.score(LETTER.text) == 0
    assert INVOICE_TYPE.score(UNCLEAR.text) == LETTER_TYPE.score(UNCLEAR.text) == 0


def test_the_demo_scores_clear_the_thresholds():
    assert INVOICE_TYPE.score(INVOICE.text) >= config.MIN_TYPE_SCORE
    assert LETTER_TYPE.score(LETTER.text) >= config.MIN_TYPE_SCORE


# --- Invoice fields ---


def test_the_invoice_fields_are_read_from_the_c1_text():
    fields = INVOICE_TYPE.extract(texts.INVOICE_C1, TODAY)

    assert fields == {
        "invoice_number": "INV-1043",
        "amount_pence": 12000,
        "document_date": date(2021, 3, 14),
    }


@pytest.mark.parametrize(
    "line,pence",
    [
        ("Amount due £120.00", 12000),
        ("Amount due 120.00", 12000),  # the pound sign is optional
        ("Amount due: £120", 12000),
        ("AMOUNT DUE £ 1,234.56", 123456),
        ("Amount due 0.99", 99),
        ("Amount due £120.5", 12050),
        ("amount due - £7.05", 705),
    ],
)
def test_the_amount_is_read_in_pence(line, pence):
    assert INVOICE_TYPE.extract(line, TODAY)["amount_pence"] == pence


def test_no_amount_due_line_means_no_amount():
    assert INVOICE_TYPE.extract("Invoice number INV-1", TODAY)["amount_pence"] is None


@pytest.mark.parametrize(
    "line,number",
    [
        ("Invoice number INV-1043", "INV-1043"),
        ("Invoice number: INV-1043", "INV-1043"),
        ("Invoice no. 1043", "1043"),
        ("INVOICE NO 77/2021", "77/2021"),
        ("Invoice # 55", "55"),
        ("invoice number   A-9", "A-9"),
    ],
)
def test_the_invoice_number_is_read(line, number):
    assert INVOICE_TYPE.extract(line, TODAY)["invoice_number"] == number


def test_a_word_after_the_label_is_not_an_invoice_number():
    text = "Invoice number is shown below. Invoice number INV-9"

    assert INVOICE_TYPE.extract(text, TODAY)["invoice_number"] == "INV-9"


def test_no_invoice_number_gives_none():
    fields = INVOICE_TYPE.extract(texts.INVOICE_NO_NUMBER, TODAY)

    assert fields["invoice_number"] is None


# --- Invoice date: a labelled date first, otherwise the first date ---


def test_the_labelled_invoice_date_wins_over_an_earlier_date():
    text = "Order placed 1 February 2021\nInvoice date 14/03/2021\nPaid 2021-05-01"

    assert INVOICE_TYPE.extract(text, TODAY)["document_date"] == date(2021, 3, 14)


def test_a_label_and_date_on_separate_lines_still_pair_up():
    text = "Delivered 1 February 2021\nInvoice date:\n14 March 2021"

    assert INVOICE_TYPE.extract(text, TODAY)["document_date"] == date(2021, 3, 14)


def test_date_of_invoice_is_also_a_label():
    text = "Delivered 1 February 2021 Date of invoice 14/03/2021"

    assert INVOICE_TYPE.extract(text, TODAY)["document_date"] == date(2021, 3, 14)


def test_without_a_label_the_first_date_is_used():
    fields = INVOICE_TYPE.extract(texts.INVOICE_UNLABELLED_DATE, TODAY)

    assert fields["document_date"] == date(2021, 1, 2)


def test_a_future_labelled_date_is_ignored_and_the_first_other_date_is_used():
    fields = INVOICE_TYPE.extract(texts.INVOICE_FUTURE_LABELLED_DATE, TODAY)

    assert fields["document_date"] == date(2021, 3, 3)


def test_no_date_at_all_gives_none():
    fields = INVOICE_TYPE.extract("Invoice number INV-1 Amount due 5.00", TODAY)

    assert fields["document_date"] is None


def test_an_unlabelled_date_further_on_is_not_taken_as_the_labelled_one():
    # "Invoice date" has no date straight after it, so it falls back to the first date.
    text = "Invoice date to follow. Delivered 1 February 2021."

    assert INVOICE_TYPE.extract(text, TODAY)["document_date"] == date(2021, 2, 1)


def test_every_invoice_field_is_always_present():
    assert set(INVOICE_TYPE.extract("nothing useful", TODAY)) == {
        "invoice_number",
        "amount_pence",
        "document_date",
    }


# --- Letter fields ---


def test_the_letter_subject_and_date_are_read():
    fields = LETTER_TYPE.extract(texts.LETTER, TODAY)

    assert fields == {
        "subject": "Year end accounts reminder",
        "document_date": date(2022, 5, 10),
    }


@pytest.mark.parametrize(
    "line,subject",
    [
        ("Re: Your enquiry", "Your enquiry"),
        ("RE: Your enquiry  ", "Your enquiry"),
        ("  re:   Your enquiry", "Your enquiry"),
        ("Dear Sir\nRe: Your enquiry\nMore text", "Your enquiry"),
    ],
)
def test_the_subject_comes_from_the_re_line(line, subject):
    assert LETTER_TYPE.extract(line, TODAY)["subject"] == subject


def test_a_letter_without_a_re_line_has_no_subject():
    fields = LETTER_TYPE.extract(texts.LETTER_NO_SUBJECT, TODAY)

    assert fields["subject"] is None
    assert fields["document_date"] == date(2022, 5, 10)


def test_the_letter_date_is_the_first_date_and_a_future_one_is_ignored():
    text = "Dear Sir\n14/03/2031\n3 March 2021\nRe: Hello"

    assert LETTER_TYPE.extract(text, TODAY)["document_date"] == date(2021, 3, 3)


def test_a_letter_with_no_date_has_none():
    assert LETTER_TYPE.extract("Dear Sir\nRe: Hello", TODAY)["document_date"] is None


def test_every_letter_field_is_always_present():
    assert set(LETTER_TYPE.extract("nothing useful", TODAY)) == {
        "subject",
        "document_date",
    }


def test_the_unclear_demo_document_has_no_fields_worth_reading():
    assert INVOICE_TYPE.extract(UNCLEAR.text, TODAY)["invoice_number"] is None
    assert LETTER_TYPE.extract(UNCLEAR.text, TODAY)["subject"] is None


# --- Filename keys ---


def test_the_invoice_key_is_the_number_or_no_number():
    assert INVOICE_TYPE.filename_key({"invoice_number": "INV-1043"}) == "INV-1043"
    assert INVOICE_TYPE.filename_key({"invoice_number": None}) == "no number"
    assert INVOICE_TYPE.filename_key({}) == "no number"
    assert INVOICE_TYPE.filename_key({"invoice_number": ""}) == "no number"


def test_the_letter_key_is_the_first_40_characters_of_the_subject_or_letter():
    assert LETTER_TYPE.filename_key({"subject": "Year end accounts"}) == (
        "Year end accounts"
    )
    long = "A" * 39 + " " + "B" * 20
    assert (
        LETTER_TYPE.filename_key({"subject": long}) == "A" * 39
    )  # the space is trimmed
    assert len(LETTER_TYPE.filename_key({"subject": "x" * 100})) == 40
    assert LETTER_TYPE.filename_key({"subject": None}) == "letter"
    assert LETTER_TYPE.filename_key({}) == "letter"
    assert LETTER_TYPE.filename_key({"subject": "   "}) == "letter"
