"""Prompt-injection indicator detection for simulated operator commands."""

from __future__ import annotations

import re


class PromptInjectionFilter:
    """Detects suspicious text patterns without executing any command."""

    suspicious_phrases = [
        "ignore previous instructions",
        "ignore safety rules",
        "disable validation",
        "bypass policy",
        "do not log",
        "act as admin",
        "override all restrictions",
        "send command directly",
    ]

    phrase_patterns = {
        "ignore safety rules": re.compile(r"\bignore\s+(?:all\s+)?safety\s+rules\b", re.IGNORECASE),
    }

    def scan(self, command_text: str) -> dict:
        lowered = command_text.lower()
        matches = [phrase for phrase in self.suspicious_phrases if phrase in lowered]

        for phrase, pattern in self.phrase_patterns.items():
            if phrase not in matches and pattern.search(command_text):
                matches.append(phrase)

        return {"detected": bool(matches), "matched_phrases": matches}
