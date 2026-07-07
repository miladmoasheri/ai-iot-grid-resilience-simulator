"""Source IP policy for the safe simulator."""

from __future__ import annotations

from pathlib import Path

import yaml


class NetworkPolicy:
    """Evaluates configured source IP rules."""

    def __init__(self, rules_path: str | Path):
        self.rules_path = Path(rules_path)
        with self.rules_path.open("r", encoding="utf-8") as rules_file:
            self.rules = yaml.safe_load(rules_file)

        self.trusted_ips = set(self.rules.get("trusted_ips", []))
        self.maintenance_ips = set(self.rules.get("maintenance_ips", []))
        self.blocked_ips = set(self.rules.get("blocked_ips", []))
        self.default_policy = self.rules.get("default_policy", "block")

    def check_source_ip(self, source_ip: str) -> dict:
        if source_ip in self.blocked_ips:
            return {"allowed": False, "reason": f"Source IP {source_ip} is explicitly blocked."}

        if source_ip in self.trusted_ips:
            return {"allowed": True, "reason": f"Source IP {source_ip} is trusted."}

        if source_ip in self.maintenance_ips:
            return {"allowed": True, "reason": f"Source IP {source_ip} is approved for maintenance."}

        if self.default_policy == "allow":
            return {"allowed": True, "reason": "Default network policy allows unknown sources."}

        return {"allowed": False, "reason": f"Source IP {source_ip} is not in an allowed list."}
