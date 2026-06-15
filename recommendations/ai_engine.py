"""
AI Engine for Size Recommendations.

Uses:
1. Sentence Transformers — encode reviews and compute semantic similarity to
   sizing anchors ("runs small", "true to size", "runs large") for new users.
2. Scikit-learn RandomForest — trained on purchase history for returning users.
3. Falls back to keyword-based rules if ML libraries are not installed.

All recommendations include confidence scores and explanations.
"""
from typing import Optional

# Try ML imports
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.ensemble import RandomForestClassifier
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


class SizeRecommendationEngine:
    """
    AI engine for size recommendations.

    Inputs:
    - Customer purchase history (sizes bought + kept/returned)
    - Customer body measurements (height, weight, body type)
    - Product reviews mentioning sizing
    - Brand-specific adjustments
    - Category fit patterns

    Output:
    - Recommended size
    - Confidence score (0-1)
    - Human-readable explanation
    """

    # Standard size ordering for comparison
    SIZE_ORDER = {
        "XS": 0, "S": 1, "M": 2, "L": 3, "XL": 4, "XXL": 5, "XXXL": 6,
        # Numeric sizes (pants/jeans)
        "26": 0, "28": 1, "30": 2, "32": 3, "34": 4, "36": 5, "38": 6, "40": 7, "42": 8,
        # Shoe sizes
        "6": 0, "7": 1, "8": 2, "9": 3, "10": 4, "11": 5, "12": 6,
    }

    # Body measurement to size mapping (unisex, Indian standard sizing)
    BODY_SIZE_MAP_TOPS = [
        # (max_height_cm, max_weight_kg, size)
        (160, 50, "XS"),
        (165, 58, "S"),
        (172, 68, "M"),
        (178, 80, "L"),
        (185, 92, "XL"),
        (195, 110, "XXL"),
        (999, 999, "XXXL"),
    ]

    BODY_SIZE_MAP_BOTTOMS = [
        # (max_height_cm, max_weight_kg, waist_size)
        (160, 50, "28"),
        (165, 58, "30"),
        (172, 68, "32"),
        (178, 78, "34"),
        (183, 88, "36"),
        (190, 100, "38"),
        (999, 999, "40"),
    ]

    def predict_size_from_body(
        self,
        height_cm: float,
        weight_kg: float,
        body_type: Optional[str] = None,
        available_sizes: list = None,
        product_category: str = "clothing",
    ) -> dict:
        """
        Predict clothing size from body measurements.

        Returns:
            dict with: recommended_size, confidence, explanation, method
        """
        if not height_cm or not weight_kg:
            return {
                "recommended_size": None,
                "confidence": 0,
                "explanation": "Height and weight required for body-based prediction.",
                "method": "body_measurements",
            }

        # Determine if tops or bottoms based on available sizes
        is_numeric = available_sizes and available_sizes[0].isdigit()
        size_map = self.BODY_SIZE_MAP_BOTTOMS if is_numeric else self.BODY_SIZE_MAP_TOPS

        # Find matching size
        predicted_size = size_map[-1][2]
        for max_h, max_w, size in size_map:
            if height_cm <= max_h and weight_kg <= max_w:
                predicted_size = size
                break

        # Body type adjustment
        if body_type == "slim":
            predicted_size = self._adjust_size(predicted_size, -1, available_sizes or [])
        elif body_type in ("plus", "athletic"):
            predicted_size = self._adjust_size(predicted_size, 1, available_sizes or [])

        # Ensure predicted size is available
        if available_sizes and predicted_size not in available_sizes:
            predicted_size = self._find_closest_available(predicted_size, available_sizes)

        confidence = 0.65 if body_type else 0.58

        explanation = (
            f"Based on your measurements (height: {height_cm}cm, weight: {weight_kg}kg"
            f"{', body type: ' + body_type if body_type else ''}), "
            f"we recommend size {predicted_size}. "
        )
        if body_type == "slim":
            explanation += "Adjusted down for slim build. "
        elif body_type == "athletic":
            explanation += "Adjusted up for athletic build (broader shoulders/chest). "
        elif body_type == "plus":
            explanation += "Adjusted up for plus size comfort. "
        explanation += "This prediction improves after your first purchase."

        return {
            "recommended_size": predicted_size,
            "confidence": round(confidence, 2),
            "explanation": explanation,
            "method": "body_measurements",
        }

    def _adjust_size(self, size: str, direction: int, available: list) -> str:
        """Adjust size up (+1) or down (-1) if available."""
        if not available:
            return size
        if size in available:
            idx = available.index(size) + direction
            if 0 <= idx < len(available):
                return available[idx]
        return size

    def _find_closest_available(self, target: str, available: list) -> str:
        """Find closest available size to target."""
        target_order = self.SIZE_ORDER.get(target.upper(), 3)
        best = available[0]
        best_dist = abs(self.SIZE_ORDER.get(available[0].upper(), 3) - target_order)
        for s in available[1:]:
            dist = abs(self.SIZE_ORDER.get(s.upper(), 3) - target_order)
            if dist < best_dist:
                best = s
                best_dist = dist
        return best

    def recommend_from_reviews_only(self, available_sizes: list, reviews: list) -> dict:
        """
        Recommend size based ONLY on product reviews using ML (Sentence Transformers).

        Method:
        1. Encode each review with sentence-transformers
        2. Compute cosine similarity to 3 anchor embeddings:
           - "runs small, tight, need to size up"
           - "true to size, fits perfectly, as expected"
           - "runs large, loose, need to size down"
        3. Classify each review into small/true/large bucket
        4. Majority vote determines recommendation

        Falls back to keyword matching if ML not available.
        """
        if not available_sizes:
            return None

        mid_idx = len(available_sizes) // 2

        if not reviews:
            return {
                "recommended_size": available_sizes[mid_idx],
                "confidence": 0.35,
                "explanation": (
                    f"No reviews available yet. Recommending {available_sizes[mid_idx]} "
                    f"as the standard mid-range size."
                ),
                "factors": {"default_mid_range": 1.0},
            }

        if ML_AVAILABLE:
            return self._ml_review_size_prediction(available_sizes, reviews, mid_idx)
        else:
            return self._keyword_review_size_prediction(available_sizes, reviews, mid_idx)

    def _ml_review_size_prediction(self, available_sizes: list, reviews: list, mid_idx: int) -> dict:
        """
        ML-powered review analysis using Sentence Transformers.
        Encodes reviews and computes similarity to sizing anchor sentences.
        """
        model = self._get_model()

        # Define semantic anchors for sizing
        small_anchors = [
            "This product runs small and tight, I needed to size up",
            "Too small for my usual size, very tight fit",
            "Runs smaller than expected, order one size bigger",
            "Narrow and snug, wish I ordered a larger size",
        ]
        true_anchors = [
            "True to size, fits perfectly as expected",
            "Perfect fit, exactly my usual size",
            "Fits just right, no issues with sizing",
            "Standard fit, matches the size chart well",
        ]
        large_anchors = [
            "Runs large and loose, I should have sized down",
            "Too big for my usual size, very oversized",
            "Runs bigger than expected, order one size smaller",
            "Baggy and loose fitting, need a smaller size",
        ]

        # Encode anchors (average each group)
        small_emb = np.mean(model.encode(small_anchors), axis=0, keepdims=True)
        true_emb = np.mean(model.encode(true_anchors), axis=0, keepdims=True)
        large_emb = np.mean(model.encode(large_anchors), axis=0, keepdims=True)

        # Encode reviews and classify each
        review_texts = [r.get("body", "") for r in reviews if len(r.get("body", "")) > 10]
        if not review_texts:
            return {
                "recommended_size": available_sizes[mid_idx],
                "confidence": 0.38,
                "explanation": f"Reviews too short for analysis. Recommending {available_sizes[mid_idx]}.",
                "factors": {"default_mid_range": 1.0},
            }

        review_embeddings = model.encode(review_texts)

        # Compute similarities
        sim_small = cosine_similarity(review_embeddings, small_emb).flatten()
        sim_true = cosine_similarity(review_embeddings, true_emb).flatten()
        sim_large = cosine_similarity(review_embeddings, large_emb).flatten()

        # Classify each review
        small_count = 0
        true_count = 0
        large_count = 0

        for i in range(len(review_texts)):
            scores = [sim_small[i], sim_true[i], sim_large[i]]
            max_idx = np.argmax(scores)
            max_score = scores[max_idx]

            # Only count if similarity is above threshold (meaningful sizing mention)
            if max_score > 0.25:
                if max_idx == 0:
                    small_count += 1
                elif max_idx == 1:
                    true_count += 1
                else:
                    large_count += 1

        total = small_count + true_count + large_count
        if total == 0:
            return {
                "recommended_size": available_sizes[mid_idx],
                "confidence": 0.42,
                "explanation": (
                    f"Analyzed {len(review_texts)} reviews with AI embeddings but found no strong "
                    f"sizing signal. Recommending {available_sizes[mid_idx]} as standard."
                ),
                "factors": {"review_analysis": 0.4, "no_clear_signal": 0.6, "reviews_analyzed": len(review_texts)},
            }

        # Confidence based on agreement strength
        max_count = max(small_count, true_count, large_count)
        confidence = min(0.82, 0.45 + (max_count / total) * 0.37)

        if small_count > large_count and small_count > true_count:
            rec_idx = min(mid_idx + 1, len(available_sizes) - 1)
            pct = round(small_count / total * 100)
            explanation = (
                f"AI analyzed {len(review_texts)} reviews using semantic similarity. "
                f"{pct}% of reviews indicate this product runs small/tight. "
                f"Recommending {available_sizes[rec_idx]} (one size up). "
                f"[ML method: Sentence embeddings + cosine similarity to sizing anchors]"
            )
            factors = {"runs_small": round(small_count / total, 2), "reviews_analyzed": len(review_texts)}

        elif large_count > small_count and large_count > true_count:
            rec_idx = max(mid_idx - 1, 0)
            pct = round(large_count / total * 100)
            explanation = (
                f"AI analyzed {len(review_texts)} reviews using semantic similarity. "
                f"{pct}% of reviews indicate this product runs large/loose. "
                f"Recommending {available_sizes[rec_idx]} (one size down). "
                f"[ML method: Sentence embeddings + cosine similarity to sizing anchors]"
            )
            factors = {"runs_large": round(large_count / total, 2), "reviews_analyzed": len(review_texts)}

        else:
            rec_idx = mid_idx
            pct = round(true_count / total * 100) if true_count else 0
            explanation = (
                f"AI analyzed {len(review_texts)} reviews using semantic similarity. "
                f"{pct}% confirm true-to-size fit. "
                f"Recommending {available_sizes[rec_idx]} as the standard size. "
                f"[ML method: Sentence embeddings + cosine similarity to sizing anchors]"
            )
            factors = {"true_to_size": round(true_count / max(total, 1), 2), "reviews_analyzed": len(review_texts)}
            confidence = min(0.78, confidence + 0.05)

        return {
            "recommended_size": available_sizes[rec_idx],
            "confidence": round(confidence, 2),
            "explanation": explanation,
            "factors": factors,
        }

    def _keyword_review_size_prediction(self, available_sizes: list, reviews: list, mid_idx: int) -> dict:
        """Fallback: keyword-based review analysis when ML libs not available."""
        small_keywords = ["small", "tight", "snug", "size up", "too small", "narrow", "runs small"]
        large_keywords = ["large", "big", "loose", "size down", "too big", "oversized", "runs large", "baggy"]
        true_keywords = ["true to size", "perfect fit", "fits well", "as expected", "just right", "fits perfectly"]

        small_count = 0
        large_count = 0
        true_count = 0

        for review in reviews:
            body = review.get("body", "").lower()
            if any(kw in body for kw in small_keywords):
                small_count += 1
            elif any(kw in body for kw in large_keywords):
                large_count += 1
            elif any(kw in body for kw in true_keywords):
                true_count += 1

        total = small_count + large_count + true_count
        if total == 0:
            return {
                "recommended_size": available_sizes[mid_idx],
                "confidence": 0.40,
                "explanation": f"No sizing info in {len(reviews)} reviews. Recommending {available_sizes[mid_idx]}.",
                "factors": {"default_mid_range": 1.0, "review_count": len(reviews)},
            }

        confidence = min(0.72, 0.40 + (total / len(reviews)) * 0.32)

        if small_count > large_count and small_count > true_count:
            rec_idx = min(mid_idx + 1, len(available_sizes) - 1)
            pct = round(small_count / total * 100)
            explanation = f"Based on {len(reviews)} reviews: {pct}% say runs small. Recommending {available_sizes[rec_idx]} (size up). [Keyword analysis mode]"
            factors = {"runs_small": round(small_count / total, 2), "review_count": len(reviews)}
        elif large_count > small_count and large_count > true_count:
            rec_idx = max(mid_idx - 1, 0)
            pct = round(large_count / total * 100)
            explanation = f"Based on {len(reviews)} reviews: {pct}% say runs large. Recommending {available_sizes[rec_idx]} (size down). [Keyword analysis mode]"
            factors = {"runs_large": round(large_count / total, 2), "review_count": len(reviews)}
        else:
            rec_idx = mid_idx
            pct = round(true_count / total * 100)
            explanation = f"Based on {len(reviews)} reviews: {pct}% say true to size. Recommending {available_sizes[rec_idx]}. [Keyword analysis mode]"
            factors = {"true_to_size": round(true_count / total, 2), "review_count": len(reviews)}

        return {
            "recommended_size": available_sizes[rec_idx],
            "confidence": round(confidence, 2),
            "explanation": explanation,
            "factors": factors,
        }

    @classmethod
    def _get_model(cls):
        """Get or load the sentence transformer model (cached)."""
        if not hasattr(cls, '_st_model') or cls._st_model is None:
            cls._st_model = SentenceTransformer("all-MiniLM-L6-v2")
        return cls._st_model

    def predict_size_ml(
        self,
        height_cm: float,
        weight_kg: float,
        body_type: Optional[str],
        available_sizes: list,
        training_data: list,
    ) -> dict:
        """
        Predict size using ML (RandomForest) trained on other users' body data.

        Training data comes from users who have height/weight AND kept purchase records.
        If not enough training data, falls back to lookup table.

        Args:
            height_cm: Customer's height
            weight_kg: Customer's weight
            body_type: slim/regular/athletic/plus
            available_sizes: Available sizes for this product
            training_data: List of {height, weight, body_type, size_kept}

        Returns:
            dict with recommended_size, confidence, explanation
        """
        if not ML_AVAILABLE:
            # Fallback to lookup table
            return self.predict_size_from_body(height_cm, weight_kg, body_type, available_sizes)

        # Need at least 5 training samples to use ML
        if len(training_data) < 5:
            result = self.predict_size_from_body(height_cm, weight_kg, body_type, available_sizes)
            result["explanation"] = (
                f"Not enough training data for ML model ({len(training_data)} samples, need 5+). "
                + result.get("explanation", "")
            )
            return result

        # Encode body types as numbers
        body_type_map = {"slim": 0, "regular": 1, "athletic": 2, "plus": 3}

        # Build training arrays
        X_train = []
        y_train = []
        size_set = set(available_sizes)

        for d in training_data:
            # Only use training data with sizes that match this product's available sizes
            if d["size_kept"] in size_set:
                bt = body_type_map.get(d.get("body_type", "regular"), 1)
                X_train.append([d["height"], d["weight"], bt])
                y_train.append(d["size_kept"])

        if len(X_train) < 3:
            # Not enough matching data, use lookup table
            result = self.predict_size_from_body(height_cm, weight_kg, body_type, available_sizes)
            result["explanation"] = (
                f"ML model: insufficient matching training data. " + result.get("explanation", "")
            )
            return result

        # Train RandomForest
        X_train = np.array(X_train)
        clf = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=5)
        clf.fit(X_train, y_train)

        # Predict for this user
        bt_encoded = body_type_map.get(body_type or "regular", 1)
        X_new = np.array([[height_cm, weight_kg, bt_encoded]])
        predicted_size = clf.predict(X_new)[0]

        # Get prediction probability for confidence
        proba = clf.predict_proba(X_new)[0]
        max_proba = float(np.max(proba))
        confidence = min(0.88, max_proba * 0.9)  # Scale down slightly

        # Ensure predicted size is in available sizes
        if predicted_size not in available_sizes:
            predicted_size = self._find_closest_available(predicted_size, available_sizes)

        explanation = (
            f"ML model (RandomForest) trained on {len(X_train)} purchase records from users "
            f"with similar body measurements. "
            f"Your input: height={height_cm}cm, weight={weight_kg}kg"
            f"{', body type=' + body_type if body_type else ''}. "
            f"Predicted size: {predicted_size} with {round(max_proba * 100)}% model probability."
        )

        return {
            "recommended_size": predicted_size,
            "confidence": round(confidence, 2),
            "explanation": explanation,
            "method": "ml_random_forest",
            "factors": {"ml_probability": round(max_proba, 2), "training_samples": len(X_train)},
        }

    def recommend_size(
        self,
        available_sizes: list,
        purchase_history: list,
        product_reviews: list,
        brand: Optional[str] = None,
        category: Optional[str] = None,
    ) -> dict:
        """
        Generate size recommendation.

        Args:
            available_sizes: List of available sizes for the product ["S", "M", "L", "XL"]
            purchase_history: List of dicts with keys: size, kept, return_reason, brand, category
            product_reviews: List of dicts with keys: body, size_purchased, rating
            brand: Product brand name
            category: Product category

        Returns:
            dict with: recommended_size, confidence, explanation, factors
        """
        if not available_sizes:
            return {
                "recommended_size": None,
                "confidence": 0,
                "explanation": "No sizes available for this product.",
                "factors": {},
            }

        # If no purchase history, use review-based recommendation
        if not purchase_history:
            return self._recommend_from_reviews(available_sizes, product_reviews, brand)

        # Calculate scores for each available size
        size_scores = {}
        factors_detail = {}

        for size in available_sizes:
            score, factors = self._score_size(
                size, available_sizes, purchase_history, product_reviews, brand, category
            )
            size_scores[size] = score
            factors_detail[size] = factors

        # Find best size
        best_size = max(size_scores, key=size_scores.get)
        best_score = size_scores[best_size]

        # Normalize confidence to 0-1
        confidence = min(1.0, max(0.1, best_score))

        # Generate explanation
        explanation = self._generate_explanation(
            best_size, confidence, purchase_history, product_reviews, brand, factors_detail[best_size]
        )

        return {
            "recommended_size": best_size,
            "confidence": round(confidence, 2),
            "explanation": explanation,
            "factors": factors_detail[best_size],
        }

    def _score_size(
        self,
        target_size: str,
        available_sizes: list,
        purchase_history: list,
        product_reviews: list,
        brand: Optional[str],
        category: Optional[str],
    ) -> tuple:
        """
        Score a specific size based on all available signals.

        Returns tuple of (score, factors_dict).
        """
        factors = {}
        total_score = 0.0

        # Factor 1: Purchase history (weight: 0.45)
        history_score = self._history_score(target_size, purchase_history, brand, category)
        factors["purchase_history"] = round(history_score, 3)
        total_score += history_score * 0.45

        # Factor 2: Return pattern analysis (weight: 0.25)
        return_score = self._return_pattern_score(target_size, purchase_history)
        factors["return_patterns"] = round(return_score, 3)
        total_score += return_score * 0.25

        # Factor 3: Review-based sizing (weight: 0.2)
        review_score = self._review_fit_score(target_size, available_sizes, product_reviews)
        factors["review_analysis"] = round(review_score, 3)
        total_score += review_score * 0.2

        # Factor 4: Brand consistency (weight: 0.1)
        brand_score = self._brand_consistency_score(target_size, purchase_history, brand)
        factors["brand_consistency"] = round(brand_score, 3)
        total_score += brand_score * 0.1

        return total_score, factors

    def _history_score(
        self, target_size: str, history: list, brand: Optional[str], category: Optional[str]
    ) -> float:
        """Score based on what sizes the customer kept."""
        if not history:
            return 0.5  # Neutral

        kept_sizes = [h["size"] for h in history if h.get("kept", True)]
        if not kept_sizes:
            return 0.5

        # Exact match with kept sizes
        exact_matches = kept_sizes.count(target_size)
        total_kept = len(kept_sizes)

        if exact_matches > 0:
            # Higher score for more consistent history
            consistency = exact_matches / total_kept
            # Bonus for same brand/category
            brand_matches = sum(
                1 for h in history
                if h.get("kept") and h["size"] == target_size and h.get("brand") == brand
            )
            brand_bonus = 0.1 if brand_matches > 0 else 0

            return min(1.0, 0.5 + (consistency * 0.4) + brand_bonus)

        # Check proximity to most common kept size
        most_common_kept = max(set(kept_sizes), key=kept_sizes.count)
        distance = self._size_distance(target_size, most_common_kept)

        if distance == 0:
            return 0.9
        elif distance == 1:
            return 0.4
        else:
            return 0.1

    def _return_pattern_score(self, target_size: str, history: list) -> float:
        """Score based on return patterns - avoid sizes that were returned."""
        if not history:
            return 0.5

        returned = [h for h in history if not h.get("kept", True)]
        if not returned:
            return 0.7  # No returns = good sign

        # Penalize if this exact size was returned
        returned_this_size = [h for h in returned if h["size"] == target_size]
        if returned_this_size:
            # Check reasons
            for h in returned_this_size:
                reason = h.get("return_reason", "")
                if reason == "too_small":
                    # They returned this size as too small, so don't recommend it
                    return 0.1
                elif reason == "too_large":
                    return 0.1
            return 0.2  # Generic return of this size

        # Check if returns suggest sizing up or down
        for h in returned:
            reason = h.get("return_reason", "")
            if reason == "too_small":
                # Customer returns smaller sizes, prefer larger
                returned_order = self.SIZE_ORDER.get(h["size"].upper(), -1)
                target_order = self.SIZE_ORDER.get(target_size.upper(), -1)
                if target_order > returned_order:
                    return 0.8  # Larger than what was returned as too small
            elif reason == "too_large":
                returned_order = self.SIZE_ORDER.get(h["size"].upper(), -1)
                target_order = self.SIZE_ORDER.get(target_size.upper(), -1)
                if target_order < returned_order:
                    return 0.8  # Smaller than what was returned as too large

        return 0.5

    def _review_fit_score(self, target_size: str, available_sizes: list, reviews: list) -> float:
        """Score based on review mentions of sizing (runs small/large)."""
        if not reviews:
            return 0.5

        small_indicators = ["small", "tight", "snug", "size up", "narrow"]
        large_indicators = ["large", "big", "loose", "size down", "oversized"]
        true_indicators = ["true to size", "perfect fit", "as expected", "just right"]

        small_count = 0
        large_count = 0
        true_count = 0

        for review in reviews:
            body = review.get("body", "").lower()
            if any(kw in body for kw in small_indicators):
                small_count += 1
            elif any(kw in body for kw in large_indicators):
                large_count += 1
            elif any(kw in body for kw in true_indicators):
                true_count += 1

        total = small_count + large_count + true_count
        if total == 0:
            return 0.5

        # If product runs small, recommend sizing up
        if small_count > large_count and small_count > true_count:
            # Product runs small - prefer larger sizes
            target_idx = available_sizes.index(target_size) if target_size in available_sizes else 0
            mid_idx = len(available_sizes) // 2
            if target_idx > mid_idx:
                return 0.8  # Larger size preferred
            elif target_idx == mid_idx:
                return 0.6
            else:
                return 0.3

        # If product runs large, recommend sizing down
        elif large_count > small_count and large_count > true_count:
            target_idx = available_sizes.index(target_size) if target_size in available_sizes else 0
            mid_idx = len(available_sizes) // 2
            if target_idx < mid_idx:
                return 0.8
            elif target_idx == mid_idx:
                return 0.6
            else:
                return 0.3

        # True to size - middle sizes score higher relative to history
        return 0.6

    def _brand_consistency_score(self, target_size: str, history: list, brand: Optional[str]) -> float:
        """Score based on brand-specific sizing consistency."""
        if not brand or not history:
            return 0.5

        brand_history = [h for h in history if h.get("brand", "").lower() == brand.lower()]
        if not brand_history:
            return 0.5

        # Same brand, same size kept = high confidence
        kept_same_brand = [h for h in brand_history if h.get("kept")]
        if not kept_same_brand:
            return 0.4

        sizes_kept = [h["size"] for h in kept_same_brand]
        if target_size in sizes_kept:
            return 0.9

        return 0.3

    def _size_distance(self, size_a: str, size_b: str) -> int:
        """Calculate distance between two sizes in the ordering."""
        order_a = self.SIZE_ORDER.get(size_a.upper(), -1)
        order_b = self.SIZE_ORDER.get(size_b.upper(), -1)

        if order_a == -1 or order_b == -1:
            return 0 if size_a.upper() == size_b.upper() else 1

        return abs(order_a - order_b)

    def _recommend_from_reviews(self, available_sizes: list, reviews: list, brand: Optional[str]) -> dict:
        """Recommend size based only on reviews (no purchase history)."""
        if not reviews:
            # Default to middle size
            mid_idx = len(available_sizes) // 2
            return {
                "recommended_size": available_sizes[mid_idx],
                "confidence": 0.3,
                "explanation": (
                    f"No purchase history available. Recommending {available_sizes[mid_idx]} "
                    f"as the mid-range size. Consider checking the size guide for this product."
                ),
                "factors": {"default_mid_range": 1.0},
            }

        # Analyze reviews for sizing insights
        small_count = 0
        large_count = 0

        for review in reviews:
            body = review.get("body", "").lower()
            if any(kw in body for kw in ["small", "tight", "size up"]):
                small_count += 1
            elif any(kw in body for kw in ["large", "loose", "size down"]):
                large_count += 1

        mid_idx = len(available_sizes) // 2

        if small_count > large_count:
            # Product runs small, recommend one size up from middle
            rec_idx = min(mid_idx + 1, len(available_sizes) - 1)
            explanation = (
                f"Based on {small_count} reviews indicating this product runs small, "
                f"we recommend {available_sizes[rec_idx]}. "
                f"Consider sizing up from your usual size."
            )
        elif large_count > small_count:
            rec_idx = max(mid_idx - 1, 0)
            explanation = (
                f"Based on {large_count} reviews indicating this product runs large, "
                f"we recommend {available_sizes[rec_idx]}. "
                f"Consider sizing down from your usual size."
            )
        else:
            rec_idx = mid_idx
            explanation = (
                f"Reviews suggest this product is true to size. "
                f"Recommending {available_sizes[rec_idx]} as the standard fit."
            )

        return {
            "recommended_size": available_sizes[rec_idx],
            "confidence": 0.45,
            "explanation": explanation,
            "factors": {"review_analysis": 1.0},
        }

    def _generate_explanation(
        self,
        recommended_size: str,
        confidence: float,
        history: list,
        reviews: list,
        brand: Optional[str],
        factors: dict,
    ) -> str:
        """Generate human-readable explanation for the recommendation."""
        parts = []

        # History-based explanation
        kept_sizes = [h["size"] for h in history if h.get("kept", True)]
        if kept_sizes:
            size_freq = {}
            for s in kept_sizes:
                size_freq[s] = size_freq.get(s, 0) + 1

            most_common = max(size_freq, key=size_freq.get)
            count = size_freq[most_common]

            if most_common == recommended_size:
                parts.append(
                    f"You purchased size {recommended_size} {count} time{'s' if count > 1 else ''} "
                    f"and kept {'all' if count > 1 else 'it'}."
                )
            else:
                parts.append(
                    f"Your most kept size is {most_common} ({count} purchases). "
                    f"Based on fit adjustments, {recommended_size} is recommended for this item."
                )

        # Return-based explanation
        returned = [h for h in history if not h.get("kept", True)]
        if returned:
            for h in returned:
                reason = h.get("return_reason", "")
                if reason == "too_small":
                    parts.append(f"You returned size {h['size']} as too small.")
                elif reason == "too_large":
                    parts.append(f"You returned size {h['size']} as too large.")

        # Review-based explanation
        if reviews:
            size_reviews = [r for r in reviews if "size" in r.get("body", "").lower() or "fit" in r.get("body", "").lower()]
            if size_reviews:
                small_mentions = sum(1 for r in size_reviews if any(kw in r["body"].lower() for kw in ["small", "tight"]))
                if small_mentions > len(size_reviews) / 2:
                    parts.append("Review analysis indicates this item runs slightly small.")
                large_mentions = sum(1 for r in size_reviews if any(kw in r["body"].lower() for kw in ["large", "loose"]))
                if large_mentions > len(size_reviews) / 2:
                    parts.append("Review analysis indicates this item runs slightly large.")

        # Brand explanation
        if brand:
            brand_history = [h for h in history if h.get("brand", "").lower() == brand.lower() and h.get("kept")]
            if brand_history:
                brand_sizes = [h["size"] for h in brand_history]
                if recommended_size in brand_sizes:
                    parts.append(f"You've previously kept size {recommended_size} from {brand}.")

        if not parts:
            parts.append(f"Size {recommended_size} recommended based on available data analysis.")

        return " ".join(parts)
