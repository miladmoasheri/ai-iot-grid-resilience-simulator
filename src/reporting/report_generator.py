"""Report generation for simulator runs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class ReportGenerator:
    """Writes text and CSV reports."""

    def __init__(self, report_dir: str | Path):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, entries: list[dict], metrics: dict, phase: str = "phase1") -> dict:
        text_path = self.report_dir / f"{phase}_report.txt"
        metrics_path = self.report_dir / f"{phase}_metrics.csv"
        phase_titles = {
            "phase1": "Phase 1 Report",
            "phase2": "Phase 2 Report",
            "phase3": "Phase 3 Report",
        }
        phase_title = phase_titles.get(phase, "Simulation Report")

        lines = [
            "AI-Assisted Demand Response Cyber-Resilience Simulator",
            phase_title,
            "",
            "Summary Metrics:",
        ]
        for key, value in metrics.items():
            lines.append(f"- {key}: {value}")

        if phase == "phase2":
            lines.extend(
                [
                    "",
                    "Phase 2 campaign note:",
                    "- phase2_all is a sequential campaign run. Some scenario steps intentionally reuse the same first 5 devices.",
                    "- Event metrics count accepted or attempted actions each time they occur.",
                    "- Unique device metrics count distinct device IDs across the full campaign.",
                ]
            )
        if phase == "phase3":
            lines.extend(
                [
                    "",
                    "Phase 3 model note:",
                    "- This is a simplified HVAC load and demand-response model, not a full grid power-flow simulation.",
                    "- Load values are generated from thermostat state, simple cooling logic, and fixed per-device HVAC kW.",
                    "- Passive ambient heat gain is included so indoor temperatures drift upward when cooling is inactive.",
                    "- Phase 4 is planned to add repeated experiments, statistical analysis, and sensitivity analysis.",
                    "",
                    "Phase 3 interpretation:",
                    f"- Baseline peak load: {metrics.get('baseline_peak_load_kw', 0)} kW.",
                    f"- Normal demand response event-window reduction: {metrics.get('dr_normal_reduction_kw', 0)} kW.",
                    f"- Demand-response attack event-window reduction: {metrics.get('dr_attack_reduction_kw', 0)} kW.",
                    f"- Attack versus normal DR event load increase: {metrics.get('attack_vs_dr_load_increase_kw', 0)} kW.",
                    f"- Backdoor load spike versus its neutral baseline: {metrics.get('backdoor_spike_vs_baseline_kw', 0)} kW.",
                    "- The comfort violation scenario can reduce HVAC load while increasing comfort loss, showing a safety-impact trade-off.",
                ]
            )

        lines.extend(["", "Command Decisions:"])
        for entry in entries:
            reasons = "; ".join(entry.get("reasons", [])) or "No blocking reasons."
            firmware = ""
            if entry.get("firmware_id"):
                firmware = f" | firmware: {entry['firmware_id']} {entry.get('firmware_version')}"
            backdoor = ""
            if entry.get("simulated_backdoor_attempt"):
                backdoor = (
                    f" | eligible_backdoor_devices: {entry.get('eligible_backdoor_devices', 0)}"
                    f" | backdoor_affected_devices: {entry.get('backdoor_affected_devices', 0)}"
                    f" | backdoor_blocked_devices: {entry.get('backdoor_blocked_devices', 0)}"
                    f" | compromised_devices_targeted: {entry.get('compromised_devices_targeted', 0)}"
                    f" | trusted_devices_targeted: {entry.get('trusted_devices_targeted', 0)}"
                )
            power = ""
            if entry.get("parsed_command", {}).get("intent") == "power_simulation":
                power = (
                    f" | peak_load_kw: {entry.get('peak_load_kw', 0)}"
                    f" | total_energy_kwh: {entry.get('total_energy_kwh', 0)}"
                    f" | comfort_loss_degree_minutes: {entry.get('comfort_loss_degree_minutes', 0)}"
                    f" | pre_event_average_load_kw: {entry.get('pre_event_average_load_kw', 0)}"
                    f" | event_average_load_kw: {entry.get('event_average_load_kw', 0)}"
                    f" | baseline_event_average_load_kw: {entry.get('baseline_event_average_load_kw', 0)}"
                    f" | demand_response_target_reduction_kw: {entry.get('demand_response_target_reduction_kw', 0)}"
                    f" | demand_response_actual_reduction_kw: {entry.get('demand_response_actual_reduction_kw', 0)}"
                    f" | demand_response_achievement_rate: {entry.get('demand_response_achievement_rate', 0)}"
                    f" | demand_response_failure_rate: {entry.get('demand_response_failure_rate', 0)}"
                    f" | compromised_devices_count: {entry.get('compromised_devices_count', 0)}"
                    f" | compromised_load_kw: {entry.get('compromised_load_kw', 0)}"
                    f" | protected_load_kw: {entry.get('protected_load_kw', 0)}"
                    f" | total_load_kw: {entry.get('total_load_kw', 0)}"
                    f" | load_spike_kw_from_compromised_devices: {entry.get('load_spike_kw_from_compromised_devices', 0)}"
                )
            lines.append(
                f"- [{entry['policy_decision']}] {entry['scenario']} | {entry['source_ip']} | "
                f"{entry['command_text']} | devices changed: {entry['devices_changed']}"
                f" | compromised: {entry.get('devices_compromised', 0)}"
                f" | quarantined: {entry.get('devices_quarantined', 0)}"
                f" | recovered: {entry.get('devices_recovered', 0)}{firmware}{backdoor}{power} | {reasons}"
            )

        text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        pd.DataFrame([metrics]).to_csv(metrics_path, index=False)

        return {"text_report": text_path, "metrics_csv": metrics_path}
