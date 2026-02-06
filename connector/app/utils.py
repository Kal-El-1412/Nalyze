import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def sanitize_sql(sql: str) -> str:
    sql = sql.strip()

    dangerous_keywords = [
        r'\bDROP\b',
        r'\bDELETE\b',
        r'\bTRUNCATE\b',
        r'\bUPDATE\b',
        r'\bINSERT\b',
        r'\bALTER\b',
        r'\bCREATE\b',
        r'\bEXEC\b',
        r'\bEXECUTE\b'
    ]

    for keyword in dangerous_keywords:
        if re.search(keyword, sql, re.IGNORECASE):
            raise ValueError(f"SQL contains prohibited operation: {keyword}")

    return sql


def validate_column_name(column_name: str) -> bool:
    if not column_name:
        return False

    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column_name):
        return False

    return True


def format_file_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def detect_pii_patterns(text: str) -> List[str]:
    patterns = []

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.search(email_pattern, str(text)):
        patterns.append("email")

    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    if re.search(phone_pattern, str(text)):
        patterns.append("phone")

    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    if re.search(ssn_pattern, str(text)):
        patterns.append("ssn")

    credit_card_pattern = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    if re.search(credit_card_pattern, str(text)):
        patterns.append("credit_card")

    return patterns


def truncate_string(text: str, max_length: int = 100) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


