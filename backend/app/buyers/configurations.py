import re

from app.models import Product

from .agent import BaseBuyerAgent


def _tokenize(text: str) -> set:
    """Lower-case and strip punctuation before splitting into tokens."""
    return set(re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower()).split())


def _jaccard_similarity(s1: str, s2: str) -> float:
    """Token-level Jaccard similarity with punctuation normalization."""
    set1 = _tokenize(s1)
    set2 = _tokenize(s2)
    if not set1 or not set2:
        return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))

class StructuredBuyer(BaseBuyerAgent):
    """
    Structured-first buyer:
    Aggressively uses typed attributes and categories.
    Ranks primarily by exact category match and minimum price.
    """
    def discover_candidates(self) -> list[Product]:
        required = set(self.intent.hard_constraints.required_categories)
        candidates = []
        for p in self.products:
            if p.category in required:
                candidates.append(p)

        # Rank by lowest price first
        candidates.sort(key=lambda x: getattr(x, 'price_paise', float('inf')))
        return candidates

class SemanticBuyer(BaseBuyerAgent):
    """
    Semantic buyer:
    Uses natural-language matching against title/description heavily.
    Ignores strict category typed fields during discovery.
    """
    def discover_candidates(self) -> list[Product]:
        raw = self.intent.raw_intent

        scored_products = []
        for p in self.products:
            # Score based on how many words from the raw intent appear in title/desc
            text = f"{p.title} {p.description}"
            score = _jaccard_similarity(raw, text)
            if score > 0:
                scored_products.append((score, p))

        # Rank by highest semantic score
        scored_products.sort(key=lambda x: x[0], reverse=True)
        return [p for score, p in scored_products]

class HybridBuyer(BaseBuyerAgent):
    """
    Hybrid buyer:
    Combines semantic retrieval with typed validation.
    First does a semantic search, then re-ranks based on exact category matches.
    """
    def discover_candidates(self) -> list[Product]:
        raw = self.intent.raw_intent
        required = set(self.intent.hard_constraints.required_categories)

        scored_products = []
        for p in self.products:
            text = f"{p.title} {p.description}"
            semantic_score = _jaccard_similarity(raw, text)

            # Boost score heavily if typed category matches
            if p.category in required:
                semantic_score += 2.0

            if semantic_score > 0:
                scored_products.append((semantic_score, p))

        # Rank by highest hybrid score
        scored_products.sort(key=lambda x: x[0], reverse=True)
        return [p for score, p in scored_products]
