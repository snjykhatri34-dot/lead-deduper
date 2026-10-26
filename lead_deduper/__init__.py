"""Lead deduper: merge duplicate contacts from multiple sources and score them."""
from .dedupe import MergedLead, dedupe, find_matches, score_lead

__all__ = ["MergedLead", "dedupe", "find_matches", "score_lead"]
