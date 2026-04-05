import re
from typing import Dict, Any
from ..base import BaseLogProcessor


class SecurityBase(BaseLogProcessor):
    """
    Parent: Logic for Auth, Identity, and SIEM logs.
    Focuses on User Attribution and Success/Failure states.
    """
    # Pattern to find email-like usernames or DOMAIN\user
    USER_PATTERN = re.compile(r'\b([\w\.-]+@[\w\.-]+\.\w{2,}|[a-zA-Z0-9._-]+\\[a-zA-Z0-9._-]+)\b')
    # Common security outcome keywords
    OUTCOME_PATTERN = re.compile(r'\b(SUCCESS|FAILED|DENIED|ALLOWED|CHALLENGE|LOCKED)\b', re.IGNORECASE)

    def extract_security_context(self, message: str) -> Dict[str, Any]:
        """
        Utility: Extracts the 'Who' and the 'Result'.
        """
        user_match = self.USER_PATTERN.search(message)
        outcome_match = self.OUTCOME_PATTERN.search(message)

        return {
            "user": user_match.group(1) if user_match else "anonymous",
            "outcome": outcome_match.group(1).upper() if outcome_match else "UNKNOWN",
            "is_failure": any(x in message.upper() for x in ["FAILED", "DENIED", "LOCKED", "UNAUTHORIZED"])
        }