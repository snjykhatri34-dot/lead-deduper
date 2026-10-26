import unittest

from lead_deduper.normalize import (
    is_business_email, normalize_company, normalize_email, normalize_name, normalize_phone,
)


class NormalizeTest(unittest.TestCase):
    def test_email_gmail_aliases(self):
        self.assertEqual(normalize_email(" Tom.Nguyen+leads@GMAIL.com "), "tomnguyen@gmail.com")

    def test_email_plus_tag_on_other_domains(self):
        self.assertEqual(normalize_email("ana+crm@acme.example"), "ana@acme.example")

    def test_email_invalid(self):
        self.assertEqual(normalize_email("not an email"), "")

    def test_business_email(self):
        self.assertTrue(is_business_email("ana@acme.example"))
        self.assertFalse(is_business_email("ana@gmail.com"))
        self.assertFalse(is_business_email(""))

    def test_phone_formats_match(self):
        formats = ["(512) 555-0142", "+1 512-555-0142", "512.555.0142", "15125550142"]
        self.assertEqual({normalize_phone(p) for p in formats}, {"5125550142"})

    def test_phone_too_short(self):
        self.assertEqual(normalize_phone("123"), "")

    def test_name_last_first(self):
        self.assertEqual(normalize_name("Shah, Priya"), "priya shah")

    def test_company_suffixes(self):
        self.assertEqual(normalize_company("The Coastal Stays Co."), "coastal stays")
        self.assertEqual(normalize_company("Harborview Hotels, Inc."), "harborview hotels")
        self.assertEqual(normalize_company("Smith & Sons LLC"), "smith and sons")


if __name__ == "__main__":
    unittest.main()
