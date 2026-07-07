"""Simulation logging to CSV and JSON files."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


class SimulationLogger:
    """Collects run entries and writes them to logs."""

    def __init__(self, log_dir: str | Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.entries: list[dict] = []

    def log(
        self,
        scenario: str,
        source_ip: str,
        command_text: str,
        parsed_command: dict,
        policy_decision: dict,
        target_device_count: int,
        devices_changed: int,
        attack_detected: bool,
        security_profile: str = "strict",
        firmware_id: str | None = None,
        firmware_version: str | None = None,
        firmware_signature_valid: bool | None = None,
        firmware_tampered: bool | None = None,
        firmware_contains_backdoor: bool | None = None,
        backdoor_enabled: bool = False,
        trust_status_before: dict | None = None,
        trust_status_after: dict | None = None,
        devices_compromised: int = 0,
        compromised_device_ids: list[str] | None = None,
        devices_quarantined: int = 0,
        devices_recovered: int = 0,
        simulated_backdoor_attempt: bool = False,
        simulated_backdoor_success: bool = False,
        eligible_backdoor_devices: int = 0,
        backdoor_affected_devices: int = 0,
        backdoor_blocked_devices: int = 0,
        compromised_devices_targeted: int = 0,
        trusted_devices_targeted: int = 0,
    ) -> dict:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "scenario": scenario,
            "source_ip": source_ip,
            "command_text": command_text,
            "parsed_command": parsed_command,
            "policy_decision": policy_decision["decision"],
            "reasons": policy_decision["reasons"],
            "target_device_count": target_device_count,
            "devices_changed": devices_changed,
            "attack_detected": attack_detected,
            "security_profile": security_profile,
            "firmware_id": firmware_id,
            "firmware_version": firmware_version,
            "firmware_signature_valid": firmware_signature_valid,
            "firmware_tampered": firmware_tampered,
            "firmware_contains_backdoor": firmware_contains_backdoor,
            "backdoor_enabled": backdoor_enabled,
            "trust_status_before": trust_status_before or {},
            "trust_status_after": trust_status_after or {},
            "devices_compromised": devices_compromised,
            "compromised_device_ids": compromised_device_ids or [],
            "devices_quarantined": devices_quarantined,
            "devices_recovered": devices_recovered,
            "simulated_backdoor_attempt": simulated_backdoor_attempt,
            "simulated_backdoor_success": simulated_backdoor_success,
            "eligible_backdoor_devices": eligible_backdoor_devices,
            "backdoor_affected_devices": backdoor_affected_devices,
            "backdoor_blocked_devices": backdoor_blocked_devices,
            "compromised_devices_targeted": compromised_devices_targeted,
            "trusted_devices_targeted": trusted_devices_targeted,
        }
        self.entries.append(entry)
        return entry

    def save(self) -> None:
        json_path = self.log_dir / "simulation_log.json"
        csv_path = self.log_dir / "simulation_log.csv"

        with json_path.open("w", encoding="utf-8") as json_file:
            json.dump(self.entries, json_file, indent=2)

        csv_entries = []
        for entry in self.entries:
            csv_entry = dict(entry)
            csv_entry["parsed_command"] = json.dumps(entry["parsed_command"])
            csv_entry["reasons"] = json.dumps(entry["reasons"])
            csv_entry["trust_status_before"] = json.dumps(entry["trust_status_before"])
            csv_entry["trust_status_after"] = json.dumps(entry["trust_status_after"])
            csv_entry["compromised_device_ids"] = json.dumps(entry["compromised_device_ids"])
            csv_entries.append(csv_entry)

        pd.DataFrame(csv_entries).to_csv(csv_path, index=False)
