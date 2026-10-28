"""Made-up OCR texts for the rules tests. Every name and number here is invented.

Each text has at least 20 words (decision 18), except where a name says otherwise.
"""

# SPEC C1: "INVOICE", "Invoice number INV-1043", "Amount due", "C-0042" and
# "Invoice date 14/03/2021". Scores Invoice 12, Letter 0.
INVOICE_C1 = """INVOICE
Brightwell Flour Mills
Invoice number INV-1043
Invoice date 14/03/2021
Client reference C-0042
Hollybrook Bakery Ltd, 12 Mill Lane, Daleford
Flour, 16kg sacks x 6    72.00
Yeast, 500g tubs x 4    28.00
Delivery    20.00
Amount due £120.00
Thank you for your custom.
"""

# An invoice with no label on its date: the first date in the text is used.
INVOICE_UNLABELLED_DATE = """INVOICE
Brightwell Flour Mills
Invoice number INV-2200
Issued 02 January 2021 for the goods delivered on 5 February 2021 to the bakery
at 12 Mill Lane, Daleford. Amount due 45.50
Please pay within thirty days.
"""

# An invoice that has no invoice number at all.
INVOICE_NO_NUMBER = """INVOICE
Brightwell Flour Mills
Invoice date 2021-03-14
Flour, 16kg sacks x 6 and yeast, 500g tubs x 4 delivered to the bakery.
Amount due 100.00
Please pay within thirty days of the date shown above.
"""

# An invoice whose date label is in the future (a misread), with an earlier date
# elsewhere in the text.
INVOICE_FUTURE_LABELLED_DATE = """INVOICE
Brightwell Flour Mills
Invoice number INV-3300
Order placed on 3 March 2021 and invoice date 14/03/2031 as printed on the paper.
Amount due 80.00
Thank you for your custom, and please pay within thirty days.
"""

LETTER = """Fernwood Accountancy Services
4 Orchard Court, Daleford

10 May 2022

Dear Mr Hartley,

Re: Year end accounts reminder

We are writing to tell you that your year end records are now ready for your
review. Please look over the enclosed figures and let us know if anything
looks wrong before the end of the month.

Yours sincerely,
A. Whitcombe
"""

# A letter with no "Re:" line and a long first sentence, for the "letter" key.
LETTER_NO_SUBJECT = """Fernwood Accountancy Services
4 Orchard Court, Daleford

10 May 2022

Dear Mr Hartley,

We are writing to tell you that your year end records are now ready for your
review and that nothing further is needed from you at this stage.

Yours sincerely,
A. Whitcombe
"""

# Scores Invoice 7 ("invoice" 4 + "amount due" 3) and Letter 5 ("dear" 3 + "re:" 2).
MIXED_INVOICE_7_LETTER_5 = """Dear Mr Hartley,
Our ref C-0042
Re: the paperwork for the bakery that we talked about on the telephone.
Please find below the invoice and the amount due for the work that was done
in the shop last week.
"""

# Every type scores 0.
NO_KEYWORDS = """The kettle in the back office needs descaling and the shelf above the
sink is loose. Bring tea bags and biscuits on Friday, and put the ladder back in
the shed when you have finished with it.
"""

# SPEC C4: no reference, but the names of two clients.
INVOICE_TWO_CLIENT_NAMES = """INVOICE
Invoice number INV-5000
Invoice date 14/03/2021
Work done for Smith Ltd at the shop, with a copy sent to J Smith & Co at
their head office, as agreed on the telephone last week.
Amount due 300.00
"""

# SPEC C5: a reference that isn't in the register.
INVOICE_UNKNOWN_REF = """INVOICE
Invoice number INV-6000
Invoice date 14/03/2021
Client reference C-0099
Work done for the shop as agreed on the telephone last week and delivered
to the address shown above.
Amount due 300.00
"""

# SPEC C6: a confident type and client, but no date anywhere.
INVOICE_NO_DATE = """INVOICE
Brightwell Flour Mills
Invoice number INV-7000
Client reference C-0042
Hollybrook Bakery Ltd, 12 Mill Lane, Daleford
Flour, 16kg sacks x 6 and yeast, 500g tubs x 4 delivered to the bakery.
Amount due 100.00
"""

# SPEC C11: a confident type and client, but only 11 words (the one text under 20).
INVOICE_ELEVEN_WORDS = (
    "INVOICE Invoice number INV-1043 Invoice date 14/03/2021 Amount due 120.00 C-0042"
)

# Names only, no reference, for the name-matching rules.
INVOICE_NAME_ONLY = """INVOICE
Invoice number INV-8000
Invoice date 14/03/2021
Work done for HOLLYBROOK BAKERY LTD at their shop in Daleford, as agreed on
the telephone last week and delivered to the address shown above.
Amount due 300.00
"""

# Two references.
INVOICE_TWO_REFS = """INVOICE
Invoice number INV-9000
Invoice date 14/03/2021
Client reference C-0043 with a copy for C-0042 at the head office, as agreed
on the telephone last week and delivered to the address shown above.
Amount due 300.00
"""

# A document that reads as both an invoice and a letter, with the fields of each, for
# the review tests. Invoice: INV-2222, 45.50, labelled date 14 Mar 2021. Letter: subject
# "Year end paperwork", first date 5 May 2022.
REVIEW_TEXT = """5 May 2022
INVOICE
Invoice number INV-2222
Invoice date 14/03/2021
Amount due 45.50
Dear Mr Hartley,
Re: Year end paperwork
Yours sincerely
"""
