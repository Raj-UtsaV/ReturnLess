"""
AI Engine for Review Analysis.

Uses Sentence Transformers for embeddings and Scikit-learn for clustering/classification.
Falls back to mock implementation if ML dependencies are unavailable.

All AI decisions include explanations per architecture rules.
"""
import re
import math
from typing import Optional

# Try importing ML libraries, fall back to mock if unavailable
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


class ReviewAIEngine:
    """
    AI engine for analyzing product reviews.

    Capabilities:
    - Sentiment analysis (positive/negative/neutral with score)
    - Topic extraction (key aspects discussed)
    - Review summarization (aggregate insights)
    - Size fit analysis (for clothing products)

    Falls back to rule-based mock if ML libraries not installed.
    """

    _model = None  # Class-level model cache

    def __init__(self):
        """Initialize the AI engine."""
        self.ml_available = ML_AVAILABLE
        if self.ml_available and ReviewAIEngine._model is None:
            try:
                ReviewAIEngine._model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self.ml_available = False

    def analyze_sentiment(self, text: str) -> dict:
        """
        Analyze sentiment of a review text.

        Returns:
            dict with keys: score (-1 to 1), label (positive/negative/neutral), explanation
        """
        if self.ml_available:
            return self._ml_sentiment(text)
        return self._mock_sentiment(text)

    def extract_topics(self, text: str) -> list:
        """
        Extract key topics/aspects from review text.

        Returns:
            List of topic strings (e.g., ["battery life", "build quality"])
        """
        if self.ml_available:
            return self._ml_extract_topics(text)
        return self._mock_extract_topics(text)

    def generate_summary(self, reviews: list) -> dict:
        """
        Generate AI summary from a list of reviews.

        Args:
            reviews: List of review dicts with 'body', 'rating', 'title' keys

        Returns:
            dict with: summary_text, pros, cons, common_topics, sentiment_distribution,
                      confidence_score, explanation
        """
        if not reviews:
            return {
                "summary_text": "No reviews available yet.",
                "pros": [],
                "cons": [],
                "common_topics": [],
                "positive_pct": 0,
                "neutral_pct": 0,
                "negative_pct": 0,
                "confidence_score": 0,
                "explanation": "No reviews to analyze.",
            }

        if self.ml_available:
            return self._ml_generate_summary(reviews)
        return self._mock_generate_summary(reviews)

    def analyze_size_fit(self, reviews: list) -> dict:
        """
        Analyze size fit from reviews mentioning sizing.

        Returns:
            dict with: runs_small_pct, true_to_size_pct, runs_large_pct, explanation
        """
        if self.ml_available:
            return self._ml_analyze_size_fit(reviews)
        return self._mock_analyze_size_fit(reviews)

    # ─── ML-Powered Implementations ─────────────────────────────────────────────

    def _ml_sentiment(self, text: str) -> dict:
        """ML-based sentiment using embeddings + keyword features."""
        # Use embedding similarity to positive/negative anchors
        model = ReviewAIEngine._model
        text_embedding = model.encode([text])
        positive_anchor = model.encode(["excellent amazing great love perfect wonderful fantastic"])
        negative_anchor = model.encode(["terrible awful horrible hate worst broken disappointed"])

        pos_sim = cosine_similarity(text_embedding, positive_anchor)[0][0]
        neg_sim = cosine_similarity(text_embedding, negative_anchor)[0][0]

        # Normalize to -1 to 1 scale
        score = float(pos_sim - neg_sim)
        score = max(-1.0, min(1.0, score * 2))  # Scale up

        if score > 0.15:
            label = "positive"
        elif score < -0.15:
            label = "negative"
        else:
            label = "neutral"

        explanation = (
            f"Sentiment determined via semantic similarity analysis. "
            f"Positive similarity: {pos_sim:.3f}, Negative similarity: {neg_sim:.3f}. "
            f"Net score: {score:.3f} → classified as {label}."
        )

        return {"score": round(score, 3), "label": label, "explanation": explanation}

    def _ml_extract_topics(self, text: str) -> list:
        """ML-based topic extraction using noun phrase patterns + embeddings."""
        # Common product review aspects
        aspect_candidates = [
            "battery life", "build quality", "screen display", "camera quality",
            "performance speed", "value for money", "design looks", "comfort fit",
            "sound quality", "durability", "ease of use", "customer service",
            "size fit", "material quality", "weight", "packaging delivery",
            "color", "price", "features", "software", "connectivity",
            "water resistance", "charging", "noise cancellation",
        ]

        model = ReviewAIEngine._model
        text_embedding = model.encode([text.lower()])
        aspect_embeddings = model.encode(aspect_candidates)

        similarities = cosine_similarity(text_embedding, aspect_embeddings)[0]

        # Return aspects with similarity above threshold
        threshold = 0.3
        topics = []
        for i, sim in enumerate(similarities):
            if sim > threshold:
                topics.append(aspect_candidates[i])

        # Sort by relevance, return top 5
        topic_scores = [(aspect_candidates[i], similarities[i]) for i in range(len(similarities))]
        topic_scores.sort(key=lambda x: x[1], reverse=True)
        return [t[0] for t in topic_scores[:5] if t[1] > threshold]

    def _ml_generate_summary(self, reviews: list) -> dict:
        """ML-based summary generation using clustering and aggregation."""
        model = ReviewAIEngine._model

        # Analyze sentiment for each review
        sentiments = []
        all_topics = []
        for review in reviews:
            sent = self._ml_sentiment(review.get("body", ""))
            sentiments.append(sent)
            topics = self._ml_extract_topics(review.get("body", ""))
            all_topics.extend(topics)

        # Sentiment distribution
        pos_count = sum(1 for s in sentiments if s["label"] == "positive")
        neg_count = sum(1 for s in sentiments if s["label"] == "negative")
        neu_count = sum(1 for s in sentiments if s["label"] == "neutral")
        total = len(sentiments)

        positive_pct = round((pos_count / total) * 100, 1) if total > 0 else 0
        negative_pct = round((neg_count / total) * 100, 1) if total > 0 else 0
        neutral_pct = round((neu_count / total) * 100, 1) if total > 0 else 0

        # Topic frequency
        topic_freq = {}
        for t in all_topics:
            topic_freq[t] = topic_freq.get(t, 0) + 1
        common_topics = sorted(topic_freq.keys(), key=lambda x: topic_freq[x], reverse=True)[:6]

        # Extract pros and cons from positive/negative reviews
        pros = self._extract_key_phrases(
            [r["body"] for r, s in zip(reviews, sentiments) if s["label"] == "positive"],
            sentiment="positive"
        )
        cons = self._extract_key_phrases(
            [r["body"] for r, s in zip(reviews, sentiments) if s["label"] == "negative"],
            sentiment="negative"
        )

        # Generate summary text
        avg_rating = sum(r.get("rating", 3) for r in reviews) / len(reviews)
        summary_text = self._build_summary_text(avg_rating, positive_pct, common_topics, pros, cons, len(reviews))

        # Confidence based on review count
        confidence = min(1.0, len(reviews) / 20.0)

        explanation = (
            f"Summary generated from {len(reviews)} reviews using semantic analysis. "
            f"Sentiment classified via embedding similarity to positive/negative anchors. "
            f"Topics extracted by measuring semantic proximity to common product aspects. "
            f"Confidence score ({confidence:.2f}) based on review volume relative to 20-review threshold."
        )

        return {
            "summary_text": summary_text,
            "pros": pros[:5],
            "cons": cons[:5],
            "common_topics": common_topics,
            "positive_pct": positive_pct,
            "neutral_pct": neutral_pct,
            "negative_pct": negative_pct,
            "confidence_score": round(confidence, 2),
            "explanation": explanation,
        }

    def _ml_analyze_size_fit(self, reviews: list) -> dict:
        """Analyze size fit using semantic similarity to size descriptions."""
        model = ReviewAIEngine._model

        small_anchor = model.encode(["runs small tight too small need larger size up"])
        true_anchor = model.encode(["true to size perfect fit fits well as expected"])
        large_anchor = model.encode(["runs large loose too big need smaller size down"])

        small_count = 0
        true_count = 0
        large_count = 0

        for review in reviews:
            body = review.get("body", "").lower()
            if not any(kw in body for kw in ["size", "fit", "tight", "loose", "small", "large"]):
                continue

            embedding = model.encode([body])
            sim_small = cosine_similarity(embedding, small_anchor)[0][0]
            sim_true = cosine_similarity(embedding, true_anchor)[0][0]
            sim_large = cosine_similarity(embedding, large_anchor)[0][0]

            max_sim = max(sim_small, sim_true, sim_large)
            if max_sim == sim_small:
                small_count += 1
            elif max_sim == sim_large:
                large_count += 1
            else:
                true_count += 1

        total = small_count + true_count + large_count
        if total == 0:
            return {
                "runs_small_pct": 0,
                "true_to_size_pct": 100,
                "runs_large_pct": 0,
                "total_fit_reviews": 0,
                "explanation": "No size-related reviews found to analyze.",
            }

        result = {
            "runs_small_pct": round((small_count / total) * 100, 1),
            "true_to_size_pct": round((true_count / total) * 100, 1),
            "runs_large_pct": round((large_count / total) * 100, 1),
            "total_fit_reviews": total,
            "explanation": (
                f"Size fit analyzed from {total} reviews mentioning fit/sizing. "
                f"Each review compared to 'runs small', 'true to size', and 'runs large' "
                f"semantic anchors using cosine similarity of sentence embeddings."
            ),
        }
        return result

    def _extract_key_phrases(self, texts: list, sentiment: str) -> list:
        """Extract key phrases from a list of texts."""
        if not texts:
            return []

        # Simple extraction: find common phrases
        all_text = " ".join(texts).lower()

        # Positive aspects
        positive_indicators = [
            "great", "excellent", "love", "amazing", "perfect", "good",
            "comfortable", "fast", "quality", "recommend", "worth",
            "beautiful", "impressive", "reliable", "easy",
        ]
        # Negative aspects
        negative_indicators = [
            "bad", "poor", "disappointing", "slow", "broke", "cheap",
            "uncomfortable", "difficult", "overpriced", "fragile",
            "defective", "flimsy", "worst", "horrible",
        ]

        indicators = positive_indicators if sentiment == "positive" else negative_indicators
        phrases = []

        for indicator in indicators:
            if indicator in all_text:
                # Extract a short context around the keyword
                pattern = rf'\b\w+\s+{indicator}\b|\b{indicator}\s+\w+\b'
                matches = re.findall(pattern, all_text)
                if matches:
                    phrases.append(matches[0].strip().title())
                else:
                    phrases.append(indicator.title())

        return list(dict.fromkeys(phrases))[:5]  # Deduplicate, limit to 5

    def _build_summary_text(
        self, avg_rating: float, positive_pct: float,
        topics: list, pros: list, cons: list, review_count: int
    ) -> str:
        """Build human-readable summary text."""
        rating_desc = "highly rated" if avg_rating >= 4.0 else "well received" if avg_rating >= 3.0 else "mixed reviews"
        sentiment_desc = (
            "overwhelmingly positive" if positive_pct > 80
            else "mostly positive" if positive_pct > 60
            else "mixed" if positive_pct > 40
            else "mostly critical"
        )

        summary = f"Based on {review_count} reviews, this product is {rating_desc} with {sentiment_desc} sentiment."

        if topics:
            summary += f" Customers frequently discuss {', '.join(topics[:3])}."

        if pros:
            summary += f" Highlights include {pros[0].lower()}"
            if len(pros) > 1:
                summary += f" and {pros[1].lower()}"
            summary += "."

        if cons:
            summary += f" Some concerns around {cons[0].lower()}"
            if len(cons) > 1:
                summary += f" and {cons[1].lower()}"
            summary += "."

        return summary

    # ─── Mock Implementations (No ML Dependencies) ───────────────────────────────

    def _mock_sentiment(self, text: str) -> dict:
        """Rule-based sentiment analysis using keyword matching."""
        text_lower = text.lower()

        positive_words = {
            "great", "excellent", "amazing", "love", "perfect", "wonderful",
            "fantastic", "awesome", "brilliant", "outstanding", "superb",
            "happy", "satisfied", "recommend", "best", "quality", "comfortable",
            "impressive", "reliable", "worth", "beautiful", "fast",
        }
        negative_words = {
            "terrible", "awful", "horrible", "hate", "worst", "bad",
            "disappointing", "poor", "broken", "defective", "waste",
            "uncomfortable", "slow", "cheap", "flimsy", "overpriced",
            "frustrating", "useless", "regret", "return", "refund",
        }

        words = set(re.findall(r'\b\w+\b', text_lower))
        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)
        total = pos_count + neg_count

        if total == 0:
            score = 0.0
            label = "neutral"
        else:
            score = (pos_count - neg_count) / total
            if score > 0.2:
                label = "positive"
            elif score < -0.2:
                label = "negative"
            else:
                label = "neutral"

        explanation = (
            f"Sentiment determined via keyword analysis (mock mode - ML libraries not installed). "
            f"Found {pos_count} positive and {neg_count} negative indicator words. "
            f"Score: {score:.3f} → {label}."
        )

        return {"score": round(score, 3), "label": label, "explanation": explanation}

    def _mock_extract_topics(self, text: str) -> list:
        """Rule-based topic extraction using keyword patterns."""
        text_lower = text.lower()

        topic_keywords = {
            "battery life": ["battery", "charge", "charging", "lasts"],
            "build quality": ["build", "quality", "sturdy", "solid", "durable", "material"],
            "screen display": ["screen", "display", "brightness", "resolution"],
            "camera quality": ["camera", "photo", "picture", "lens"],
            "performance speed": ["fast", "slow", "performance", "speed", "lag", "smooth"],
            "value for money": ["price", "value", "worth", "expensive", "cheap", "money"],
            "design looks": ["design", "look", "beautiful", "aesthetic", "sleek", "style"],
            "comfort fit": ["comfortable", "comfort", "fit", "fits", "size", "wear"],
            "sound quality": ["sound", "audio", "bass", "speaker", "music", "volume"],
            "durability": ["durable", "lasted", "broke", "broken", "fragile", "sturdy"],
            "ease of use": ["easy", "simple", "intuitive", "user-friendly", "complicated"],
            "delivery packaging": ["delivery", "shipping", "package", "arrived", "box"],
        }

        found_topics = []
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                found_topics.append(topic)

        return found_topics[:5]

    def _mock_generate_summary(self, reviews: list) -> dict:
        """Rule-based summary generation."""
        sentiments = [self._mock_sentiment(r.get("body", "")) for r in reviews]
        all_topics = []
        for review in reviews:
            topics = self._mock_extract_topics(review.get("body", ""))
            all_topics.extend(topics)

        # Sentiment distribution
        total = len(sentiments)
        pos_count = sum(1 for s in sentiments if s["label"] == "positive")
        neg_count = sum(1 for s in sentiments if s["label"] == "negative")
        neu_count = sum(1 for s in sentiments if s["label"] == "neutral")

        positive_pct = round((pos_count / total) * 100, 1) if total > 0 else 0
        negative_pct = round((neg_count / total) * 100, 1) if total > 0 else 0
        neutral_pct = round((neu_count / total) * 100, 1) if total > 0 else 0

        # Topic frequency
        topic_freq = {}
        for t in all_topics:
            topic_freq[t] = topic_freq.get(t, 0) + 1
        common_topics = sorted(topic_freq.keys(), key=lambda x: topic_freq[x], reverse=True)[:6]

        # Pros/Cons from high/low rated reviews
        high_rated = [r for r in reviews if r.get("rating", 3) >= 4]
        low_rated = [r for r in reviews if r.get("rating", 3) <= 2]

        pros = self._extract_key_phrases([r.get("body", "") for r in high_rated], "positive")
        cons = self._extract_key_phrases([r.get("body", "") for r in low_rated], "negative")

        avg_rating = sum(r.get("rating", 3) for r in reviews) / len(reviews)
        summary_text = self._build_summary_text(avg_rating, positive_pct, common_topics, pros, cons, len(reviews))

        confidence = min(1.0, len(reviews) / 20.0)

        explanation = (
            f"Summary generated using rule-based analysis (mock mode - ML libraries not installed). "
            f"Sentiment classified via keyword matching against curated positive/negative word lists. "
            f"Topics identified by matching review text against predefined aspect keyword groups. "
            f"Confidence score ({confidence:.2f}) based on review volume."
        )

        return {
            "summary_text": summary_text,
            "pros": pros[:5],
            "cons": cons[:5],
            "common_topics": common_topics,
            "positive_pct": positive_pct,
            "neutral_pct": neutral_pct,
            "negative_pct": negative_pct,
            "confidence_score": round(confidence, 2),
            "explanation": explanation,
        }

    def _mock_analyze_size_fit(self, reviews: list) -> dict:
        """Rule-based size fit analysis."""
        small_keywords = ["small", "tight", "snug", "size up", "too small", "narrow"]
        large_keywords = ["large", "big", "loose", "size down", "too big", "oversized"]
        true_keywords = ["true to size", "perfect fit", "fits well", "as expected", "just right"]

        small_count = 0
        true_count = 0
        large_count = 0

        for review in reviews:
            body = review.get("body", "").lower()
            if not any(kw in body for kw in ["size", "fit", "tight", "loose", "small", "large"]):
                continue

            is_small = any(kw in body for kw in small_keywords)
            is_large = any(kw in body for kw in large_keywords)
            is_true = any(kw in body for kw in true_keywords)

            if is_small and not is_large:
                small_count += 1
            elif is_large and not is_small:
                large_count += 1
            elif is_true or (not is_small and not is_large):
                true_count += 1

        total = small_count + true_count + large_count
        if total == 0:
            return {
                "runs_small_pct": 0,
                "true_to_size_pct": 100,
                "runs_large_pct": 0,
                "total_fit_reviews": 0,
                "explanation": "No size-related reviews found. Using default (true to size).",
            }

        return {
            "runs_small_pct": round((small_count / total) * 100, 1),
            "true_to_size_pct": round((true_count / total) * 100, 1),
            "runs_large_pct": round((large_count / total) * 100, 1),
            "total_fit_reviews": total,
            "explanation": (
                f"Size fit analyzed from {total} reviews containing fit/size mentions "
                f"(mock mode - keyword matching). "
                f"Small indicators: {small_count}, True-to-size: {true_count}, Large indicators: {large_count}."
            ),
        }
