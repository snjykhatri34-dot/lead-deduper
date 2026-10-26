"""Normalise messy contact fields so the same person matches across sources."""
from __future__ import annotations

import re

FREE_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "live.com", "aol.com", "icloud.com", "me.com", "proton.me", "protonmail.com",
}

COMPANY_SUFFIXES = {
    "inc", "incorporated", "llc", "ltd", "limited", "corp", "corporation", "co",
    "company", "plc", "lp", "llp", "group", "holdings", "pvt",
}


def normalize_email(email: str) -> str:
    """Lowercase, trim, and collapse Gmail aliases (dots and +tags)."""
    email = email.strip().lower()
    if "@" not in email:
        return ""
    local, domain = email.rsplit("@", 1)
    if domain in ("gmail.com", "googlemail.com"):
        local = local.split("+", 1)[0].replace(".", "")
        domain = "gmail.com"
    else:
        local = local.split("+", 1)[0]
    return f"{local}@{domain}"


def email_domain(email: str) -> str:
    normalized = normalize_email(email)
    return normalized.split("@", 1)[1] if normalized else ""


def is_business_email(email: str) -> bool:
    domain = email_domain(email)
    return bool(domain) and domain not in FREE_EMAIL_DOMAINS


def normalize_phone(phone: str) -> str:
    """Digits only; drops a leading US/Canada country code."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits if len(digits) >= 7 else ""


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation, and handle "Last, First" ordering."""
    name = name.strip()
    if "," in name:
        last, first = name.split(",", 1)
        name = f"{first} {last}"
    return " ".join(re.sub(r"[^\w\s]", " ", name.lower()).split())


def normalize_company(company: str) -> str:
    """Lowercase, drop punctuation, "the", and legal suffixes like Inc or LLC."""
    words = re.sub(r"[^\w\s]", " ", company.lower().replace("&", " and ")).split()
    words = [w for w in words if w not in COMPANY_SUFFIXES]
    if words and words[0] == "the":
        words = words[1:]
    return " ".join(words)
