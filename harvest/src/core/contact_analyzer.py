"""
Basic contact analysis placeholder.
"""
from typing import List, Dict


class ContactAnalyzer:
    def analyze(self, contacts: List[Dict]) -> List[Dict]:
        """
        Return contacts as-is for now; hook for future scoring/cleanup.
        """
        return contacts or []
