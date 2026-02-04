import logging
from typing import Dict, List, Tuple, Any
from app.models import Catalog, PIIColumnInfo

logger = logging.getLogger(__name__)


class PIIRedactor:
    """Handles redaction of PII column names and data from catalog and schema information"""

    def redact_catalog(self, catalog: Catalog, privacy_mode: bool = True) -> Tuple[Catalog, Dict[str, str]]:
        """
        Redact PII column names from catalog when privacy mode is enabled.

        Returns:
            - Redacted catalog (or original if privacy_mode is False)
            - Mapping of redacted names to original names
        """
        if not privacy_mode:
            logger.debug("Privacy mode OFF - returning original catalog")
            return catalog, {}

        if not catalog.piiColumns or len(catalog.piiColumns) == 0:
            logger.debug("No PII columns detected - returning original catalog")
            return catalog, {}

        logger.info(f"Privacy mode ON - redacting {len(catalog.piiColumns)} PII columns")

        pii_map = self._build_pii_mapping(catalog.piiColumns)

        redacted_catalog_dict = catalog.dict()

        redacted_catalog_dict["columns"] = [
            self._redact_column_info(col, pii_map)
            for col in redacted_catalog_dict["columns"]
        ]

        if "basicStats" in redacted_catalog_dict and redacted_catalog_dict["basicStats"]:
            redacted_catalog_dict["basicStats"] = {
                pii_map.get(col_name, col_name): stats
                for col_name, stats in redacted_catalog_dict["basicStats"].items()
            }

        if "detectedDateColumns" in redacted_catalog_dict and redacted_catalog_dict["detectedDateColumns"]:
            redacted_catalog_dict["detectedDateColumns"] = [
                pii_map.get(col_name, col_name)
                for col_name in redacted_catalog_dict["detectedDateColumns"]
            ]

        if "detectedNumericColumns" in redacted_catalog_dict and redacted_catalog_dict["detectedNumericColumns"]:
            redacted_catalog_dict["detectedNumericColumns"] = [
                pii_map.get(col_name, col_name)
                for col_name in redacted_catalog_dict["detectedNumericColumns"]
            ]

        redacted_catalog_dict["piiColumns"] = []

        redacted_catalog = Catalog(**redacted_catalog_dict)

        reverse_map = {v: k for k, v in pii_map.items()}

        logger.info(f"Redacted {len(pii_map)} PII columns: {pii_map}")

        return redacted_catalog, reverse_map

    def _build_pii_mapping(self, pii_columns: List[PIIColumnInfo]) -> Dict[str, str]:
        """
        Build mapping from original PII column names to redacted placeholders.

        Examples:
            customer_email -> PII_EMAIL_1
            contact_phone -> PII_PHONE_1
            user_name -> PII_NAME_1
        """
        type_counters = {}
        pii_map = {}

        for pii_col in pii_columns:
            col_name = pii_col.name
            pii_type = pii_col.type.upper()

            if pii_type not in type_counters:
                type_counters[pii_type] = 0

            type_counters[pii_type] += 1
            count = type_counters[pii_type]

            placeholder = f"PII_{pii_type}_{count}"
            pii_map[col_name] = placeholder

        return pii_map

    def _redact_column_info(self, col_info: Dict[str, Any], pii_map: Dict[str, str]) -> Dict[str, Any]:
        """Redact a single column's information"""
        col_name = col_info.get("name")
        if col_name in pii_map:
            redacted = col_info.copy()
            redacted["name"] = pii_map[col_name]
            return redacted
        return col_info

    def should_exclude_from_stats(self, col_name: str, pii_columns: List[PIIColumnInfo]) -> bool:
        """
        Check if a column should be excluded from statistics because it contains PII.
        """
        pii_names = {pii.name for pii in pii_columns}
        return col_name in pii_names


pii_redactor = PIIRedactor()
