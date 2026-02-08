"""
Results-Driven Summarizer

Generates summaries from actual query results, never from templates.
All summaries must reference real numbers extracted from result tables.
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ResultsSummarizer:
    """Generates summaries from query results without canned templates"""

    def summarize_results(
        self,
        analysis_type: str,
        tables: List[Dict[str, Any]],
        audit: Dict[str, Any],
        flags: Dict[str, bool]
    ) -> str:
        """
        Generate summary markdown from actual query results.

        Args:
            analysis_type: Type of analysis (row_count, trend, outliers, etc.)
            tables: List of result tables with {name, columns, rows, rowCount}
            audit: Audit metadata including executedQueries
            flags: Feature flags {aiAssist, safeMode, privacyMode}

        Returns:
            Summary markdown string based on real data
        """
        if not tables or len(tables) == 0:
            return self._error_no_results()

        # Try analysis-type-specific summarizer first
        summarizer_method = getattr(self, f"_summarize_{analysis_type}", None)
        if summarizer_method and callable(summarizer_method):
            try:
                summary = summarizer_method(tables, audit, flags)
                if summary:
                    return summary
            except Exception as e:
                logger.warning(f"Analysis-specific summarizer failed for {analysis_type}: {e}")
                # Fall through to generic summarizer

        # Fallback to generic summarizer
        return self._summarize_generic(tables, audit, flags)

    def _error_no_results(self) -> str:
        """Error when no results were produced"""
        return "**Error:** No results were produced. Query execution did not run successfully."

    # ============================================================
    # Analysis-Type-Specific Summarizers
    # ============================================================

    def _summarize_row_count(
        self,
        tables: List[Dict[str, Any]],
        audit: Dict[str, Any],
        flags: Dict[str, bool]
    ) -> str:
        """Summarize row count analysis with actual count from results"""
        if not tables or len(tables) == 0:
            return self._error_no_results()

        table = tables[0]
        rows = table.get("rows", [])
        columns = table.get("columns", [])

        if not rows or len(rows) == 0:
            return "**Row count:** Unable to determine (no data returned)"

        # Try to find row_count column by name (case-insensitive)
        count = None
        cols_lower = [c.lower() for c in columns] if columns else []

        if "row_count" in cols_lower:
            idx = cols_lower.index("row_count")
            count = rows[0][idx] if len(rows[0]) > idx else None
        elif cols_lower and len(rows[0]) > 0:
            # Fallback: use first column
            count = rows[0][0]

        if count is None:
            return "**Row count:** Unable to determine (no data in result)"

        # Format the summary
        if count == 0:
            return "## Row count\n\nThis dataset is empty (0 rows)."
        else:
            return f"## Row count\n\nThis dataset has **{count:,}** rows."

    def _summarize_trend(
        self,
        tables: List[Dict[str, Any]],
        audit: Dict[str, Any],
        flags: Dict[str, bool]
    ) -> str:
        """Summarize trend analysis with real period data"""
        if not tables or len(tables) == 0:
            return self._error_no_results()

        table = tables[0]
        rows = table.get("rows", [])
        columns = table.get("columns", [])

        if not rows or len(rows) == 0:
            return "**Trend Analysis:** No data points found"

        period_count = len(rows)
        parts = [f"**Trend Analysis:** {period_count} time periods analyzed"]

        # Try to find the most recent period (assuming sorted by date)
        # Columns typically: [date/month, count, total_X, avg_X]
        if len(rows) > 0 and len(rows[-1]) >= 2:
            latest_row = rows[-1]
            latest_period = latest_row[0]
            latest_count = latest_row[1] if len(latest_row) > 1 else None

            if latest_period and latest_count is not None:
                parts.append(f"- Most recent period ({latest_period}): {latest_count:,} records")

            # If there's a total/sum column (typically index 2)
            if len(latest_row) > 2 and latest_row[2] is not None:
                col_name = columns[2] if len(columns) > 2 else "total"
                parts.append(f"- {col_name}: {latest_row[2]:,.2f}")

        # Calculate period-over-period change if we have at least 2 periods
        if len(rows) >= 2 and len(rows[-1]) >= 2 and len(rows[-2]) >= 2:
            prev_count = rows[-2][1]
            curr_count = rows[-1][1]

            if prev_count and curr_count and prev_count > 0:
                change_pct = ((curr_count - prev_count) / prev_count) * 100
                direction = "increase" if change_pct > 0 else "decrease"
                parts.append(f"- Period-over-period: {abs(change_pct):.1f}% {direction}")

        return "\n".join(parts)

    def _summarize_top_categories(
        self,
        tables: List[Dict[str, Any]],
        audit: Dict[str, Any],
        flags: Dict[str, bool]
    ) -> str:
        """Summarize top categories with real counts and percentages"""
        if not tables or len(tables) == 0:
            return self._error_no_results()

        table = tables[0]
        rows = table.get("rows", [])

        if not rows or len(rows) == 0:
            return "**Top Categories:** No categories found"

        category_count = len(rows)
        parts = [f"**Top Categories:** {category_count} categories found"]

        # Calculate total count for percentage calculations
        total_count = sum(row[1] for row in rows if len(row) > 1 and row[1] is not None)

        # Show top 3 categories
        top_n = min(3, len(rows))
        for i in range(top_n):
            row = rows[i]
            if len(row) >= 2:
                category = row[0]
                count = row[1]
                if count is not None and total_count > 0:
                    percentage = (count / total_count) * 100
                    parts.append(f"- **{category}**: {count:,} ({percentage:.1f}%)")
                elif count is not None:
                    parts.append(f"- **{category}**: {count:,}")

        if len(rows) > 3:
            parts.append(f"- ...and {len(rows) - 3} more categories")

        return "\n".join(parts)

    def _summarize_outliers(
        self,
        tables: List[Dict[str, Any]],
        audit: Dict[str, Any],
        flags: Dict[str, bool]
    ) -> str:
        """Summarize outliers with real detection counts"""
        if not tables or len(tables) == 0:
            return self._error_no_results()

        table = tables[0]
        rows = table.get("rows", [])
        table_name = table.get("name", "")

        if not rows or len(rows) == 0:
            return "**Outliers:** No outliers detected (all values within 2 standard deviations)"

        # Safe mode: aggregated counts
        if "summary" in table_name.lower() or "outlier_count" in str(table.get("columns", [])):
            total_outliers = 0
            columns_with_outliers = 0
            max_z_score = 0

            for row in rows:
                if len(row) > 1 and row[1] is not None:
                    outlier_count = row[1]
                    if outlier_count > 0:
                        total_outliers += outlier_count
                        columns_with_outliers += 1

            if total_outliers == 0:
                return "**Outliers:** No outliers detected across all columns"

            parts = [
                f"**Outliers Detected:** {total_outliers:,} values exceed 2 standard deviations",
                f"- Columns with outliers: {columns_with_outliers}",
                f"- Detection threshold: >2 standard deviations from mean"
            ]

            return "\n".join(parts)

        # Regular mode: individual outlier rows
        else:
            outlier_count = len(rows)

            # Try to find unique columns
            unique_columns = set()
            max_z_score = 0

            for row in rows:
                if len(row) > 0:
                    column_name = row[0]
                    unique_columns.add(column_name)

                # Try to find z_score column (typically last column)
                if len(row) >= 5:
                    z_score = abs(row[4]) if row[4] is not None else 0
                    max_z_score = max(max_z_score, z_score)

            parts = [
                f"**Outliers Detected:** {outlier_count:,} outlier values found",
                f"- Columns analyzed: {len(unique_columns)}"
            ]

            if max_z_score > 0:
                parts.append(f"- Maximum z-score: {max_z_score:.2f}")

            parts.append(f"- Detection threshold: >2 standard deviations")

            return "\n".join(parts)

    def _summarize_data_quality(
        self,
        tables: List[Dict[str, Any]],
        audit: Dict[str, Any],
        flags: Dict[str, bool]
    ) -> str:
        """Summarize data quality checks with real counts"""
        if not tables or len(tables) == 0:
            return self._error_no_results()

        parts = ["**Data Quality Check:**"]

        # Process each table
        for table in tables:
            name = table.get("name", "").lower()
            rows = table.get("rows", [])
            columns = table.get("columns", [])

            if not rows or len(rows) == 0:
                continue

            row = rows[0]

            # Null counts table
            if "null" in name:
                total_rows = row[0] if len(row) > 0 else 0
                parts.append(f"- Total rows: {total_rows:,}")

                # Count columns with nulls
                null_columns = 0
                total_nulls = 0
                for i in range(1, len(row)):
                    if row[i] and row[i] > 0:
                        null_columns += 1
                        total_nulls += row[i]

                if null_columns > 0:
                    parts.append(f"- Columns with null values: {null_columns}")
                    parts.append(f"- Total null values: {total_nulls:,}")
                else:
                    parts.append(f"- No null values detected")

            # Duplicate check table
            elif "duplicate" in name:
                total = row[0] if len(row) > 0 else 0
                unique = row[1] if len(row) > 1 else 0
                duplicates = total - unique if total > unique else 0

                if duplicates > 0:
                    parts.append(f"- Duplicate rows: {duplicates:,}")
                else:
                    parts.append(f"- No duplicate rows detected")

        return "\n".join(parts) if len(parts) > 1 else "**Data Quality Check:** No quality issues detected"

    # ============================================================
    # Generic Fallback Summarizer
    # ============================================================

    def _summarize_generic(
        self,
        tables: List[Dict[str, Any]],
        audit: Dict[str, Any],
        flags: Dict[str, bool]
    ) -> str:
        """
        Generic summarizer for unknown/ad-hoc analyses.
        Only references actual data from tables, never invents interpretations.
        """
        if not tables or len(tables) == 0:
            return self._error_no_results()

        table_count = len(tables)
        parts = []

        if table_count == 1:
            parts.append("**Analysis Results:**")
        else:
            parts.append(f"**Analysis Results:** {table_count} result tables produced")

        # Summarize each table
        for i, table in enumerate(tables):
            name = table.get("name", f"Table {i+1}")
            rows = table.get("rows", [])
            columns = table.get("columns", [])
            row_count = table.get("rowCount", len(rows))

            parts.append(f"\n**{name}:**")
            parts.append(f"- Rows: {row_count:,}")
            parts.append(f"- Columns: {', '.join(columns)}")

            # Show numeric highlights from first row if available
            if rows and len(rows) > 0:
                first_row = rows[0]
                numeric_highlights = []

                for j, value in enumerate(first_row):
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        col_name = columns[j] if j < len(columns) else f"col_{j}"
                        numeric_highlights.append(f"{col_name}: {value:,.2f}" if isinstance(value, float) else f"{col_name}: {value:,}")

                if numeric_highlights and len(numeric_highlights) <= 3:
                    parts.append(f"- Values: {', '.join(numeric_highlights)}")

        return "\n".join(parts)


# Global summarizer instance
results_summarizer = ResultsSummarizer()
