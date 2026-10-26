"""Find duplicate leads, merge them, and score what's left."""
from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Dict, List, Tuple

from .normalize import (
    is_business_email, normalize_company, normalize_email, normalize_name, normalize_phone,
)

FIELDS = ["id", "name", "email", "phone", "company", "title", "source"]
DECISION_MAKER_WORDS = ("owner", "founder", "ceo", "president", "director", "partner", "principal", "gm", "general manager")


@dataclass
class Match:
    a: int
    b: int
    reason: str


@dataclass
class MergedLead:
    record: Dict[str, str]
    source_ids: List[str]
    reasons: List[str] = field(default_factory=list)
    score: int = 0
    score_notes: List[str] = field(default_factory=list)


class _UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def union(self, a: int, b: int) -> None:
        self.parent[self.find(b)] = self.find(a)


def name_similarity(a: str, b: str) -> float:
    a, b = normalize_name(a), normalize_name(b)
    if not a or not b:
        return 0.0
    # Compare with tokens sorted too, so "Priya Shah" matches "Shah Priya".
    return max(
        SequenceMatcher(None, a, b).ratio(),
        SequenceMatcher(None, " ".join(sorted(a.split())), " ".join(sorted(b.split()))).ratio(),
    )


def _conflicting(a: Dict[str, str], b: Dict[str, str]) -> bool:
    """Different work emails or different phones mean two people, however alike the names."""
    phone_a, phone_b = normalize_phone(a.get("phone", "")), normalize_phone(b.get("phone", ""))
    if phone_a and phone_b and phone_a != phone_b:
        return True
    email_a, email_b = a.get("email", ""), b.get("email", "")
    return (is_business_email(email_a) and is_business_email(email_b)
            and normalize_email(email_a) != normalize_email(email_b))


def find_matches(leads: List[Dict[str, str]], name_threshold: float = 0.85) -> List[Match]:
    """Pairs of rows that look like the same person, with the reason."""
    matches = []
    by_email: Dict[str, int] = {}
    by_phone: Dict[str, int] = {}
    for i, lead in enumerate(leads):
        email = normalize_email(lead.get("email", ""))
        phone = normalize_phone(lead.get("phone", ""))
        if email and email in by_email:
            matches.append(Match(by_email[email], i, "same email"))
        elif email:
            by_email[email] = i
        if phone and phone in by_phone:
            matches.append(Match(by_phone[phone], i, "same phone"))
        elif phone:
            by_phone[phone] = i

    # Fuzzy pass: similar name at the same company. Grouping by company keeps it fast.
    by_company: Dict[str, List[int]] = {}
    for i, lead in enumerate(leads):
        company = normalize_company(lead.get("company", ""))
        if company:
            by_company.setdefault(company, []).append(i)
    for indexes in by_company.values():
        for x, i in enumerate(indexes):
            for j in indexes[x + 1:]:
                if _conflicting(leads[i], leads[j]):
                    continue
                similarity = name_similarity(leads[i].get("name", ""), leads[j].get("name", ""))
                if similarity >= name_threshold:
                    matches.append(Match(i, j, f"similar name at same company ({similarity:.0%})"))
    return matches


def _completeness(lead: Dict[str, str]) -> int:
    return sum(bool(lead.get(f, "").strip()) for f in FIELDS) + is_business_email(lead.get("email", ""))


def merge_group(leads: List[Dict[str, str]]) -> Dict[str, str]:
    """Start from the most complete row and fill its blanks from the others."""
    ordered = sorted(leads, key=_completeness, reverse=True)
    merged = dict(ordered[0])
    for other in ordered[1:]:
        for f in FIELDS:
            if not merged.get(f, "").strip() and other.get(f, "").strip():
                merged[f] = other[f]
    sources = []
    for lead in ordered:
        source = lead.get("source", "").strip()
        if source and source not in sources:
            sources.append(source)
    merged["source"] = "; ".join(sources)
    return merged


def score_lead(lead: Dict[str, str]) -> Tuple[int, List[str]]:
    """A simple 0-100 contactability score with the reasons behind it."""
    score, notes = 0, []
    if is_business_email(lead.get("email", "")):
        score, notes = score + 35, notes + ["business email"]
    elif normalize_email(lead.get("email", "")):
        score, notes = score + 15, notes + ["personal email"]
    if normalize_phone(lead.get("phone", "")):
        score, notes = score + 25, notes + ["phone"]
    if lead.get("company", "").strip():
        score, notes = score + 15, notes + ["company"]
    title = lead.get("title", "").lower()
    if any(word in title for word in DECISION_MAKER_WORDS):
        score, notes = score + 25, notes + ["decision maker"]
    elif title.strip():
        score, notes = score + 10, notes + ["title"]
    return min(score, 100), notes


def dedupe(leads: List[Dict[str, str]], name_threshold: float = 0.85) -> List[MergedLead]:
    """Cluster duplicate leads, merge each cluster, and score the result."""
    uf = _UnionFind(len(leads))
    matches = find_matches(leads, name_threshold)
    for m in matches:
        uf.union(m.a, m.b)

    groups: Dict[int, List[int]] = {}
    for i in range(len(leads)):
        groups.setdefault(uf.find(i), []).append(i)

    results = []
    for members in sorted(groups.values(), key=lambda g: g[0]):
        member_set = set(members)
        record = merge_group([leads[i] for i in members])
        score, notes = score_lead(record)
        results.append(MergedLead(
            record=record,
            source_ids=[leads[i].get("id", str(i)) for i in members],
            reasons=sorted({m.reason for m in matches if m.a in member_set}),
            score=score,
            score_notes=notes,
        ))
    return results
