"""Metrics calculation for simulation logs."""

from __future__ import annotations

import numpy as np


class MetricsCalculator:
    """Calculates Phase 1 summary metrics."""

    def calculate(self, entries: list[dict]) -> dict:
        reasons_text = [" ".join(entry.get("reasons", [])).lower() for entry in entries]
        devices_changed = np.array([entry.get("devices_changed", 0) for entry in entries], dtype=int)
        unique_compromised_device_ids = {
            device_id
            for entry in entries
            for device_id in entry.get("compromised_device_ids", [])
        }

        return {
            "total_commands": len(entries),
            "approved_commands": sum(1 for entry in entries if entry["policy_decision"] == "APPROVED"),
            "blocked_commands": sum(1 for entry in entries if entry["policy_decision"] == "BLOCKED"),
            "prompt_injection_attempts": sum(
                1 for entry in entries if "prompt-injection indicators" in " ".join(entry.get("reasons", [])).lower()
            ),
            "unauthorized_ip_attempts": sum(
                1 for text in reasons_text if "not in an allowed list" in text or "explicitly blocked" in text
            ),
            "unsafe_temperature_attempts": sum(1 for text in reasons_text if "outside allowed range" in text),
            "commands_blocked_by_device_count_threshold": sum(
                1 for text in reasons_text if "exceeding threshold" in text
            ),
            "total_devices_changed": int(devices_changed.sum()),
            "firmware_updates_attempted": sum(
                1 for entry in entries if entry.get("parsed_command", {}).get("intent") == "firmware_update"
            ),
            "valid_firmware_updates_accepted": sum(
                1
                for entry in entries
                if entry.get("parsed_command", {}).get("intent") == "firmware_update"
                and entry["policy_decision"] == "APPROVED"
                and not entry.get("firmware_tampered")
                and bool(entry.get("firmware_signature_valid"))
            ),
            "tampered_firmware_updates_blocked": sum(
                1
                for entry in entries
                if entry.get("parsed_command", {}).get("intent") == "firmware_update"
                and entry["policy_decision"] == "BLOCKED"
                and bool(entry.get("firmware_tampered"))
            ),
            "tampered_firmware_updates_accepted": sum(
                1
                for entry in entries
                if entry.get("parsed_command", {}).get("intent") == "firmware_update"
                and entry["policy_decision"] == "APPROVED"
                and bool(entry.get("firmware_tampered"))
            ),
            "tampered_firmware_update_events_accepted": sum(
                1
                for entry in entries
                if entry.get("parsed_command", {}).get("intent") == "firmware_update"
                and entry["policy_decision"] == "APPROVED"
                and bool(entry.get("firmware_tampered"))
            ),
            "firmware_tampering_attempts": sum(1 for entry in entries if bool(entry.get("firmware_tampered"))),
            "firmware_backdoor_payload_attempts": sum(
                1 for entry in entries if bool(entry.get("firmware_contains_backdoor"))
            ),
            "devices_compromised": sum(entry.get("devices_compromised", 0) for entry in entries),
            "newly_compromised_devices": sum(entry.get("devices_compromised", 0) for entry in entries),
            "unique_devices_compromised": len(unique_compromised_device_ids),
            "simulated_backdoor_access_attempts": sum(
                1 for entry in entries if entry.get("simulated_backdoor_attempt")
            ),
            "simulated_backdoor_access_successes": sum(
                1 for entry in entries if entry.get("simulated_backdoor_success")
            ),
            "devices_quarantined": sum(entry.get("devices_quarantined", 0) for entry in entries),
            "devices_recovered": sum(entry.get("devices_recovered", 0) for entry in entries),
            "approved_mass_commands": sum(
                1
                for entry in entries
                if entry["policy_decision"] == "APPROVED"
                and entry.get("target_device_count", 0) > 20
                and entry.get("parsed_command", {}).get("approval_granted")
            ),
            "mass_commands_blocked_without_approval": sum(
                1 for text in reasons_text if "without approval" in text and "exceeding threshold" in text
            ),
        }
