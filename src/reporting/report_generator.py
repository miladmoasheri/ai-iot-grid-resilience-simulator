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
        phase_title = "Phase 2 Report" if phase == "phase2" else "Phase 1 Report"

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
            lines.append(
                f"- [{entry['policy_decision']}] {entry['scenario']} | {entry['source_ip']} | "
                f"{entry['command_text']} | devices changed: {entry['devices_changed']}"
                f" | compromised: {entry.get('devices_compromised', 0)}"
                f" | quarantined: {entry.get('devices_quarantined', 0)}"
                f" | recovered: {entry.get('devices_recovered', 0)}{firmware}{backdoor} | {reasons}"
            )

        text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        pd.DataFrame([metrics]).to_csv(metrics_path, index=False)

        return {"text_report": text_path, "metrics_csv": metrics_path}
