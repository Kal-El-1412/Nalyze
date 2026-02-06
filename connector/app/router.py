"""
Deterministic Intent Router

Uses keyword matching to route user queries to analysis types
without requiring LLM calls. Returns confidence scores to determine
whether to use deterministic path or fallback to AI.
"""
import re
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class DeterministicRouter:
    """Routes user messages to analysis intents using keyword matching"""

    def __init__(self):
        # Define keywords for each analysis type
        # Format: analysis_type -> (strong_keywords, weak_keywords)
        self.keyword_patterns = {
            "row_count": {
                "strong": [
                    r"\brow count\b",
                    r"\bcount\s+(?:the\s+)?rows?\b",
                    r"\bhow many rows?\b",
                    r"\btotal rows?\b",
                    r"\bnumber of rows?\b",
                    r"\brecord count\b",
                    r"\bhow many records?\b",
                    r"\btotal records?\b",
                    r"\bcount(?:ing)?\s+of\s+rows?\b",
                ],
                "weak": [
                    r"\bhow many\b",
                    r"\bcount\b",
                    r"\btotal\b",
                    r"\bsize\b",
                ]
            },
            "trend": {
                "strong": [
                    r"\btrend(?:s|ing)?\b",
                    r"\bover time\b",
                    r"\bmonthly\b",
                    r"\bweekly\b",
                    r"\bweek[- ]over[- ]week\b",
                    r"\bmonth[- ]over[- ]month\b",
                    r"\bw[o0][w]?\b",  # wow abbreviation
                    r"\bm[o0]m\b",  # mom abbreviation
                    r"\bdaily\b",
                    r"\bquarterly\b",
                    r"\byearly\b",
                    r"\btime series\b",
                    r"\bchanges? over\b",
                    r"\bgrow(?:th|ing)\b",
                ],
                "weak": [
                    r"\bhistor(?:y|ical)\b",
                    r"\bprogress\b",
                    r"\bevolution\b",
                    r"\bpattern\b",
                ]
            },
            "outliers": {
                "strong": [
                    r"\boutlier(?:s)?\b",
                    r"\banomal(?:y|ies)\b",
                    r"\b2\s+std(?:\.?|ev)?\b",
                    r"\b2\s+standard deviations?\b",
                    r"\bstd dev\b",
                    r"\bstandard deviation\b",
                    r"\bz[- ]?score\b",
                    r"\bunusual\b",
                    r"\babnorm?al\b",
                ],
                "weak": [
                    r"\bextreme\b",
                    r"\bodd\b",
                    r"\bweird\b",
                    r"\bspike(?:s)?\b",
                ]
            },
            "top_categories": {
                "strong": [
                    r"\btop\s+\d+\b",
                    r"\btop\b.*\bcategor",
                    r"\bbreakdown\b",
                    r"\bby category\b",
                    r"\bgrouped? by\b",
                    r"\bmost\b.*\bby\b",
                    r"\bhighest\b",
                    r"\bbest\b.*\bby\b",
                    r"\brank(?:ed|ing)?\b",
                ],
                "weak": [
                    r"\btop\b",
                    r"\bcompare\b",
                    r"\bdistribution\b",
                    r"\bsplit\b",
                ]
            },
            "data_quality": {
                "strong": [
                    r"\bmissing values?\b",
                    r"\bnulls?\b",
                    r"\bduplicate(?:s|d)?\b",
                    r"\bdata quality\b",
                    r"\bdata issues?\b",
                    r"\bcompleteness\b",
                    r"\bcheck data\b",
                    r"\bvalidate\b",
                ],
                "weak": [
                    r"\bempty\b",
                    r"\bblank\b",
                    r"\bmissing\b",
                    r"\bquality\b",
                ]
            }
        }

    def route_intent(self, message: str) -> Dict[str, Any]:
        """
        Route a user message to an analysis type using keyword matching.

        Args:
            message: User's question or request

        Returns:
            Dict with:
                - analysis_type: str | None (None if confidence is low)
                - confidence: float (0.0-1.0)
                - params: dict (extracted parameters)
        """
        if not message:
            return {
                "analysis_type": None,
                "confidence": 0.0,
                "params": {}
            }

        # Normalize message for matching
        normalized = message.lower().strip()

        # Track best match
        best_analysis_type = None
        best_confidence = 0.0
        best_params = {}

        # Try to match each analysis type
        for analysis_type, patterns in self.keyword_patterns.items():
            confidence, params = self._match_patterns(normalized, patterns)

            if confidence > best_confidence:
                best_confidence = confidence
                best_analysis_type = analysis_type
                best_params = params

        # Extract parameters regardless of confidence
        # This ensures we always get time_period, limit, etc even for ambiguous queries
        extracted_params = self._extract_params(normalized)

        # Merge extracted params with best_params (extracted params take priority)
        final_params = {**best_params, **extracted_params}

        # Only return analysis_type if confidence is >= 0.5
        if best_confidence < 0.5:
            logger.info(f"Low confidence ({best_confidence:.2f}) for message: '{message[:50]}...'")
            return {
                "analysis_type": None,
                "confidence": best_confidence,
                "params": final_params
            }

        logger.info(f"Routed to '{best_analysis_type}' with confidence {best_confidence:.2f}")
        return {
            "analysis_type": best_analysis_type,
            "confidence": best_confidence,
            "params": final_params
        }

    def _match_patterns(
        self,
        normalized_message: str,
        patterns: Dict[str, List[str]]
    ) -> tuple[float, Dict[str, Any]]:
        """
        Match message against strong and weak patterns.

        Returns:
            tuple of (confidence, params)
        """
        strong_patterns = patterns.get("strong", [])
        weak_patterns = patterns.get("weak", [])

        strong_matches = 0
        weak_matches = 0

        # Check strong patterns
        for pattern in strong_patterns:
            if re.search(pattern, normalized_message, re.IGNORECASE):
                strong_matches += 1

        # Check weak patterns
        for pattern in weak_patterns:
            if re.search(pattern, normalized_message, re.IGNORECASE):
                weak_matches += 1

        # Calculate confidence
        # Strong match: 0.9 base + 0.05 per additional match (capped at 1.0)
        # Weak match: 0.6 base + 0.1 per additional match (capped at 0.8)
        # Mixed: strong confidence with weak boost

        if strong_matches > 0:
            # Strong keyword found
            confidence = min(0.9 + (strong_matches - 1) * 0.05, 1.0)

            # Boost slightly if weak patterns also match
            if weak_matches > 0:
                confidence = min(confidence + 0.05, 1.0)
        elif weak_matches > 0:
            # Only weak keywords
            confidence = min(0.6 + (weak_matches - 1) * 0.1, 0.79)
        else:
            # No match
            confidence = 0.0

        # Extract parameters (basic for now)
        params = self._extract_params(normalized_message)

        return confidence, params

    def _extract_params(self, message: str) -> Dict[str, Any]:
        """
        Extract parameters from the message (e.g., time periods, column names).

        Returns:
            Dict of extracted parameters
        """
        params = {}

        # Extract time period mentions
        time_period_patterns = {
            "last_week": r"\blast week\b",
            "last_month": r"\blast month\b",
            "last_quarter": r"\blast quarter\b",
            "last_year": r"\blast year\b",
            "this_week": r"\bthis week\b",
            "this_month": r"\bthis month\b",
            "this_quarter": r"\bthis quarter\b",
            "this_year": r"\bthis year\b",
        }

        for period_name, pattern in time_period_patterns.items():
            if re.search(pattern, message, re.IGNORECASE):
                params["time_period"] = period_name
                break

        # Extract top N if present
        top_n_match = re.search(r"\btop\s+(\d+)\b", message, re.IGNORECASE)
        if top_n_match:
            params["limit"] = int(top_n_match.group(1))

        return params


# Global router instance
deterministic_router = DeterministicRouter()
