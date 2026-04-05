import re
from typing import Dict, Any
from ..base import BaseLogProcessor


class CustomBase(BaseLogProcessor):
    """
    Parent: Logic for unknown, internal, or non-standard logs.
    Focuses on Key-Value pair extraction and Bracketed metadata.
    """
    # Regex to find key=value or key:value patterns
    KV_PATTERN = re.compile(r'(\w+)=([\w\.\-\/]+)|(\w+):\s*([\w\.\-\/]+)')
    # Regex to find anything inside [BRACKETS] or (PARENTHESES)
    BRACKET_PATTERN = re.compile(r'[\[\(]([^\]\)]+)[\]\)]')

    def extract_generic_tags(self, message: str) -> Dict[str, Any]:
        """
        Utility: Scans for any identifiable metadata in a 'messy' string.
        """
        tags = {}
        # Find all KV pairs
        for match in self.KV_PATTERN.findall(message):
            # filter out empty matches from the OR group
            key = match[0] or match[2]
            val = match[1] or match[3]
            tags[key.lower()] = val

        # Find the first bracketed item (often a Module or Thread Name)
        bracket_match = self.BRACKET_PATTERN.search(message)
        if bracket_match:
            tags["context_tag"] = bracket_match.group(1)

        return tags