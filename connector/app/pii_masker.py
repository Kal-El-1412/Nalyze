import re
import logging
from typing import Any, List, Dict, Tuple
from app.models import Catalog, PIIColumnInfo

logger = logging.getLogger(__name__)


class PIIMasker:
    """Handles masking of PII values in query results"""

    def mask_value(self, value: Any, pii_type: str) -> str:
        """
        Mask a single PII value based on its type.

        Args:
            value: The value to mask
            pii_type: The type of PII (email, phone, name, etc.)

        Returns:
            Masked string value
        """
        if value is None:
            return None

        value_str = str(value)

        if not value_str or value_str.strip() == "":
            return value_str

        pii_type_lower = pii_type.lower()

        if pii_type_lower == "email":
            return self._mask_email(value_str)
        elif pii_type_lower == "phone":
            return self._mask_phone(value_str)
        elif pii_type_lower == "name":
            return self._mask_name(value_str)
        else:
            return self._mask_generic(value_str)

    def _mask_email(self, email: str) -> str:
        """
        Mask email: test@example.com -> t***@example.com
        """
        if '@' not in email:
            return self._mask_generic(email)

        local, domain = email.split('@', 1)

        if len(local) == 0:
            masked_local = "***"
        elif len(local) == 1:
            masked_local = local[0] + "***"
        else:
            masked_local = local[0] + "***"

        return f"{masked_local}@{domain}"

    def _mask_phone(self, phone: str) -> str:
        """
        Mask phone: 555-123-4567 -> ****4567 (last 4 digits)
        """
        digits = re.sub(r'\D', '', phone)

        if len(digits) < 4:
            return "****"

        last_four = digits[-4:]
        return f"****{last_four}"

    def _mask_name(self, name: str) -> str:
        """
        Mask name: John Doe -> J***
        """
        name = name.strip()

        if len(name) == 0:
            return "***"
        elif len(name) == 1:
            return name[0] + "***"
        else:
            return name[0] + "***"

    def _mask_generic(self, value: str) -> str:
        """
        Generic masking: show first char + ***
        """
        value = value.strip()

        if len(value) == 0:
            return "***"
        elif len(value) == 1:
            return value[0] + "***"
        else:
            return value[0] + "***"

    def mask_result_rows(
        self,
        columns: List[str],
        rows: List[Tuple],
        catalog: Catalog,
        privacy_mode: bool = True
    ) -> List[Tuple]:
        """
        Mask PII values in query result rows.

        Args:
            columns: List of column names in the result
            rows: List of row tuples
            catalog: Dataset catalog containing PII column info
            privacy_mode: Whether to apply masking

        Returns:
            List of rows with PII values masked (or original if privacy_mode=False)
        """
        if not privacy_mode:
            logger.debug("Privacy mode OFF - returning unmasked results")
            return rows

        if not catalog or not catalog.piiColumns or len(catalog.piiColumns) == 0:
            logger.debug("No PII columns detected - returning unmasked results")
            return rows

        pii_column_map = {pii.name: pii.type for pii in catalog.piiColumns}

        pii_indices = []
        for idx, col_name in enumerate(columns):
            if col_name in pii_column_map:
                pii_type = pii_column_map[col_name]
                pii_indices.append((idx, pii_type))

        if not pii_indices:
            logger.debug("No PII columns in result set - returning unmasked results")
            return rows

        logger.info(f"Privacy mode ON - masking {len(pii_indices)} PII columns in {len(rows)} rows")

        masked_rows = []
        for row in rows:
            row_list = list(row)

            for idx, pii_type in pii_indices:
                if idx < len(row_list):
                    original_value = row_list[idx]
                    masked_value = self.mask_value(original_value, pii_type)
                    row_list[idx] = masked_value

            masked_rows.append(tuple(row_list))

        logger.info(f"Masked {len(masked_rows)} rows successfully")
        return masked_rows


pii_masker = PIIMasker()
