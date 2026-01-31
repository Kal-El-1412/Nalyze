import re
import hashlib
import logging
from typing import List, Dict, Any, Optional
from collections import Counter

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

PHONE_PATTERNS = [
    re.compile(r'^\+?1?\d{10,}$'),
    re.compile(r'^\(\d{3}\)\s*\d{3}[-\s]?\d{4}$'),
    re.compile(r'^\d{3}[-.\s]?\d{3}[-.\s]?\d{4}$'),
    re.compile(r'^\+\d{1,3}[-.\s]?\d{1,14}$'),
    re.compile(r'^04\d{8}$'),
]

NAME_PATTERN = re.compile(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)+$')

MIN_CONFIDENCE_THRESHOLD = 0.3
SAMPLE_SIZE = 1000


class PIIColumn:
    def __init__(self, name: str, pii_type: str, confidence: float):
        self.name = name
        self.type = pii_type
        self.confidence = round(confidence, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "confidence": self.confidence
        }


class PIIDetector:
    def detect_in_values(self, column_name: str, values: List[Any]) -> Optional[PIIColumn]:
        if not values:
            return None

        non_null_values = [v for v in values if v is not None and str(v).strip()]
        if not non_null_values:
            return None

        sample = non_null_values[:SAMPLE_SIZE]
        str_values = [str(v).strip() for v in sample]

        email_conf = self._check_emails(str_values)
        if email_conf > MIN_CONFIDENCE_THRESHOLD:
            return PIIColumn(column_name, "email", email_conf)

        phone_conf = self._check_phones(str_values)
        if phone_conf > MIN_CONFIDENCE_THRESHOLD:
            return PIIColumn(column_name, "phone", phone_conf)

        name_conf = self._check_names(str_values)
        if name_conf > MIN_CONFIDENCE_THRESHOLD:
            return PIIColumn(column_name, "name", name_conf)

        return None

    def _check_emails(self, values: List[str]) -> float:
        if not values:
            return 0.0

        matches = sum(1 for v in values if EMAIL_PATTERN.match(v))
        return matches / len(values)

    def _check_phones(self, values: List[str]) -> float:
        if not values:
            return 0.0

        matches = 0
        for v in values:
            cleaned = re.sub(r'[\s\-\(\)\.]+', '', v)
            if any(pattern.match(cleaned) for pattern in PHONE_PATTERNS):
                matches += 1

        return matches / len(values)

    def _check_names(self, values: List[str]) -> float:
        if not values:
            return 0.0

        matches = 0
        for v in values:
            if NAME_PATTERN.match(v):
                matches += 1
            elif self._is_likely_name(v):
                matches += 0.5

        return min(matches / len(values), 1.0)

    def _is_likely_name(self, value: str) -> bool:
        words = value.split()
        if len(words) < 2 or len(words) > 5:
            return False

        capitalized = sum(1 for w in words if w and w[0].isupper())
        if capitalized < 2:
            return False

        avg_length = sum(len(w) for w in words) / len(words)
        if avg_length < 2 or avg_length > 15:
            return False

        return True

    def scan_dataset(self, columns: List[Dict[str, Any]], data_sample: List[List[Any]]) -> List[PIIColumn]:
        pii_columns = []

        if not data_sample:
            logger.info("No data sample provided for PII detection")
            return pii_columns

        num_columns = len(columns)

        for col_idx, column in enumerate(columns):
            col_name = column.get("name")
            if not col_name:
                continue

            column_values = [row[col_idx] for row in data_sample if len(row) > col_idx]

            pii_result = self.detect_in_values(col_name, column_values)
            if pii_result:
                logger.info(
                    f"Detected PII in column '{col_name}': {pii_result.type} "
                    f"(confidence: {pii_result.confidence})"
                )
                pii_columns.append(pii_result)

        return pii_columns


class PIIMasker:
    @staticmethod
    def mask_email(email: str) -> str:
        if not email or '@' not in email:
            return email

        local, domain = email.split('@', 1)
        if len(local) <= 1:
            masked_local = '*'
        else:
            masked_local = local[0] + '***'

        return f"{masked_local}@{domain}"

    @staticmethod
    def mask_phone(phone: str) -> str:
        if not phone:
            return phone

        cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)

        if len(cleaned) < 4:
            return '*' * len(cleaned)

        if len(cleaned) >= 10:
            return cleaned[:2] + '*' * (len(cleaned) - 4) + cleaned[-2:]
        else:
            return cleaned[0] + '*' * (len(cleaned) - 2) + cleaned[-1]

    @staticmethod
    def mask_name(name: str) -> str:
        if not name:
            return name

        name_hash = hashlib.sha256(name.encode()).hexdigest()[:8]
        return f"Person_{name_hash}"

    @staticmethod
    def mask_value(value: Any, pii_type: str) -> str:
        if value is None:
            return None

        str_value = str(value)

        if pii_type == "email":
            return PIIMasker.mask_email(str_value)
        elif pii_type == "phone":
            return PIIMasker.mask_phone(str_value)
        elif pii_type == "name":
            return PIIMasker.mask_name(str_value)
        else:
            return str_value

    @staticmethod
    def mask_row(row: List[Any], pii_columns: List[PIIColumn], column_names: List[str]) -> List[Any]:
        name_to_pii = {pii.name: pii for pii in pii_columns}

        masked_row = []
        for idx, value in enumerate(row):
            col_name = column_names[idx] if idx < len(column_names) else None
            if col_name and col_name in name_to_pii:
                pii_info = name_to_pii[col_name]
                masked_value = PIIMasker.mask_value(value, pii_info.type)
                masked_row.append(masked_value)
            else:
                masked_row.append(value)

        return masked_row


pii_detector = PIIDetector()
pii_masker = PIIMasker()
