import os
import csv
import unittest

from lead_deduper.dedupe import dedupe, find_matches, merge_group, name_similarity, score_lead


def lead(id, name="", email="", phone="", company="", title="", source=""):
    return dict(id=id, name=name, email=email, phone=phone, company=company, title=title, source=source)


class MatchTest(unittest.TestCase):
    def test_same_email_different_case(self):
        leads = [lead("1", "A", "x@acme.example"), lead("2", "B", "X@ACME.EXAMPLE")]
        self.assertEqual([m.reason for m in find_matches(leads)], ["same email"])

    def test_same_phone_different_format(self):
        leads = [lead("1", phone="(512) 555-0142"), lead("2", phone="+1 512 555 0142")]
        self.assertEqual([m.reason for m in find_matches(leads)], ["same phone"])

    def test_similar_name_same_company(self):
        leads = [lead("1", "Marcus Bell", company="Harborview Hotels Inc."),
                 lead("2", "Marcus Bel", company="Harborview Hotels")]
        [m] = find_matches(leads)
        self.assertIn("similar name", m.reason)

    def test_similar_name_different_company_is_not_a_match(self):
        leads = [lead("1", "Marcus Bell", company="Harborview"), lead("2", "Marcus Bell", company="Lakeside")]
        self.assertEqual(find_matches(leads), [])

    def test_conflicting_contact_details_block_fuzzy_match(self):
        leads = [lead("1", "Raj Patel", "raj@patel.example", "6155550177", "Patel Motels"),
                 lead("2", "Rajesh Patel", "rajesh@patel.example", "6155550178", "Patel Motels")]
        self.assertEqual(find_matches(leads), [])

    def test_name_order_does_not_matter(self):
        self.assertEqual(name_similarity("Priya Shah", "Shah, Priya"), 1.0)


class MergeTest(unittest.TestCase):
    def test_fills_blanks_from_other_rows(self):
        merged = merge_group([
            lead("1", "Owen Brooks", "owen@coastal.example", "", "Coastal", "Owner", "Referral"),
            lead("2", "Owen Brooks", "", "843-555-0121", "Coastal", "", "Website form"),
        ])
        self.assertEqual(merged["phone"], "843-555-0121")
        self.assertEqual(merged["title"], "Owner")
        self.assertEqual(merged["source"], "Referral; Website form")

    def test_transitive_duplicates_become_one_lead(self):
        leads = [
            lead("1", "Priya Shah", "priya@sunset.example", company="Sunset Inn"),
            lead("2", "P. Shah", "priya@sunset.example", phone="5125550142"),
            lead("3", "Priya S", phone="512-555-0142"),
        ]
        [result] = dedupe(leads)
        self.assertEqual(result.source_ids, ["1", "2", "3"])


class ScoreTest(unittest.TestCase):
    def test_full_decision_maker(self):
        score, notes = score_lead(lead("1", "A", "a@acme.example", "5125550142", "Acme", "Founder & CEO"))
        self.assertEqual(score, 100)
        self.assertIn("decision maker", notes)

    def test_sparse_lead(self):
        score, _ = score_lead(lead("1", "A", "a@gmail.com"))
        self.assertEqual(score, 15)


class SampleDataTest(unittest.TestCase):
    def test_sample_file(self):
        path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_leads.csv")
        with open(path, newline="") as f:
            leads = list(csv.DictReader(f))
        results = dedupe(leads)
        self.assertEqual(len(leads), 16)
        self.assertEqual(len(results), 11)


if __name__ == "__main__":
    unittest.main()
