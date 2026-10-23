"""Scoped Hybrid BM25 + Character 3-Gram Cosine Evidence Retrieval (Proposal §5)."""
from .verification import char_ngrams_cosine, retrieve

__all__ = ["char_ngrams_cosine", "retrieve"]
