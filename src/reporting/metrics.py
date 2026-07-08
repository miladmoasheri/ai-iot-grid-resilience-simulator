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
        power_entries = [entry for entry in entries if entry.get("parsed_command", {}).get("intent") == "power_simulation"]
        power_by_scenario = {entry.get("scenario"): entry for entry in power_entries}
        baseline = power_by_scenario.get("power_baseline", {})
        dr_normal = power_by_scenario.get("demand_response_normal", {})
        dr_attack = power_by_scenario.get("demand_response_attack", {})
        backdoor_spike = power_by_scenario.get("backdoor_load_spike", {})
        comfort_attack = power_by_scenario.get("comfort_violation_attack", {})

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
            "phase3_power_scenarios_run": len(power_entries),
            "baseline_peak_load_kw": baseline.get("peak_load_kw", 0.0),
            "demand_response_normal_peak_load_kw": dr_normal.get("peak_load_kw", 0.0),
            "demand_response_attack_peak_load_kw": dr_attack.get("peak_load_kw", 0.0),
            "backdoor_load_spike_peak_load_kw": backdoor_spike.get("peak_load_kw", 0.0),
            "comfort_attack_peak_load_kw": comfort_attack.get("peak_load_kw", 0.0),
            "dr_normal_reduction_kw": dr_normal.get("demand_response_actual_reduction_kw", 0.0),
            "dr_attack_reduction_kw": dr_attack.get("demand_response_actual_reduction_kw", 0.0),
            "attack_vs_dr_load_increase_kw": round(
                dr_attack.get("event_average_load_kw", 0.0) - dr_normal.get("event_average_load_kw", 0.0),
                3,
            ),
            "backdoor_spike_vs_baseline_kw": round(
                backdoor_spike.get("load_spike_kw_from_compromised_devices", 0.0),
                3,
            ),
            "total_energy_consumed_kwh": round(
                sum(entry.get("total_energy_kwh", 0.0) for entry in power_entries),
                3,
            ),
            "comfort_loss_degree_minutes": round(
                sum(entry.get("comfort_loss_degree_minutes", 0.0) for entry in power_entries),
                3,
            ),
            "max_demand_response_failure_rate": max(
                (entry.get("demand_response_failure_rate", 0.0) for entry in power_entries),
                default=0.0,
            ),
            "compromised_load_kw": round(sum(entry.get("compromised_load_kw", 0.0) for entry in power_entries), 3),
            "protected_load_kw": round(sum(entry.get("protected_load_kw", 0.0) for entry in power_entries), 3),
            "demand_response_normal_failure_rate": dr_normal.get("demand_response_failure_rate", 0.0),
            "demand_response_attack_failure_rate": dr_attack.get("demand_response_failure_rate", 0.0),
            "backdoor_spike_compromised_devices_count": backdoor_spike.get("compromised_devices_count", 0),
            "backdoor_spike_compromised_load_kw": backdoor_spike.get("compromised_load_kw", 0.0),
            "backdoor_spike_protected_load_kw": backdoor_spike.get("protected_load_kw", 0.0),
            "backdoor_spike_total_load_kw": backdoor_spike.get("total_load_kw", 0.0),
            "load_spike_kw_from_compromised_devices": backdoor_spike.get(
                "load_spike_kw_from_compromised_devices",
                0.0,
            ),
            "comfort_attack_comfort_loss_degree_minutes": comfort_attack.get("comfort_loss_degree_minutes", 0.0),
        }
