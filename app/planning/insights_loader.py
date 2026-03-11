"""
Insights Loader - Bridges Mode 2 intelligence into Mode 3 planning
Loads, filters and ranks Mode 2 insights for use in portfolio decisions
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional


# Urgency rank for sorting (lower = more urgent)
_URGENCY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class InsightsLoader:
    """
    Loads Mode 2 insights and makes them available to Mode 3 planning sessions
    """

    INSIGHTS_FILE = "insights_log.json"

    def load(self, max_days: int = 30, max_insights: int = 20) -> List[Dict]:
        """
        Load and rank recent Mode 2 insights.

        Args:
            max_days:     Only include insights generated within this many days
            max_insights: Maximum number of insights to return

        Returns:
            List of insight dicts sorted by urgency then recency
        """
        if not os.path.exists(self.INSIGHTS_FILE):
            return []

        try:
            with open(self.INSIGHTS_FILE, "r") as f:
                all_insights = json.load(f)
        except Exception:
            return []

        cutoff = datetime.now() - timedelta(days=max_days)

        filtered = []
        seen_titles = set()

        for insight in all_insights:
            # Deduplicate by title
            title = insight.get("title", "")
            if title in seen_titles:
                continue
            seen_titles.add(title)

            # Recency filter
            generated_at = insight.get("generated_at", "")
            try:
                insight_time = datetime.fromisoformat(generated_at)
                if insight_time < cutoff:
                    continue
            except Exception:
                continue

            filtered.append(insight)

        # Sort: critical first, then high, medium, low; then newest first within each tier
        filtered.sort(key=lambda i: (
            _URGENCY_RANK.get(i.get("urgency", "low"), 3),
            -(datetime.fromisoformat(i["generated_at"]).timestamp())
        ))

        return filtered[:max_insights]

    def format_for_context(self, insights: List[Dict]) -> str:
        """
        Format insights as a concise context block for AIPI prompts.
        """
        if not insights:
            return "No recent Mode 2 intelligence available."

        lines = [f"MODE 2 INTELLIGENCE ({len(insights)} insights):"]

        for i, ins in enumerate(insights, 1):
            urgency = ins.get("urgency", "unknown").upper()
            category = ins.get("category", "")
            title = ins.get("title", "")
            observation = ins.get("observation", "")[:300]
            recommendation = ins.get("recommendation", "")[:200]
            generated_at = ins.get("generated_at", "")[:10]

            lines.append(
                f"\n[{i}] [{urgency}] [{category}] {title} ({generated_at})\n"
                f"    Observation: {observation}\n"
                f"    Recommendation: {recommendation}"
            )

        return "\n".join(lines)

    def get_summary(self, insights: List[Dict]) -> Dict:
        """
        Return a structured summary of loaded insights for session storage.
        """
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        categories = {}

        for ins in insights:
            urgency = ins.get("urgency", "low")
            counts[urgency] = counts.get(urgency, 0) + 1
            cat = ins.get("category", "Unknown")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total": len(insights),
            "by_urgency": counts,
            "by_category": categories,
            "insights": insights
        }
