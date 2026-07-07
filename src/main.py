"""Command line entry point for the simulator."""

from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console
from rich.table import Table

from ai_assistant.assistant import SimulatedAIAssistant
from ai_assistant.prompt_filter import PromptInjectionFilter
from attacks.backdoor_access import SimulatedBackdoorAccess
from attacks.scenario_runner import ScenarioRunner
from devices.fleet_manager import FleetManager
from reporting.logger import SimulationLogger
from reporting.metrics import MetricsCalculator
from reporting.report_generator import ReportGenerator
from security.firmware_security import FirmwarePackage, FirmwareSecurityPolicy
from security.network_policy import NetworkPolicy
from security.policy_engine import PolicyEngine
from security.recovery import RecoveryManager


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def count_trust_statuses(devices: list) -> dict:
    counts: dict[str, int] = {}
    for device in devices:
        counts[device.trust_status] = counts.get(device.trust_status, 0) + 1
    return counts


def run_scenario(scenario: str, profile: str = "strict") -> tuple[list[dict], dict, dict]:
    root = project_root()
    assistant = SimulatedAIAssistant()
    prompt_filter = PromptInjectionFilter()
    network_policy = NetworkPolicy(root / "config" / "network_rules.yaml")
    fleet_manager = FleetManager(root / "config" / "fleet_config.yaml")
    scenario_runner = ScenarioRunner()
    logger = SimulationLogger(root / "logs")
    backdoor_access = SimulatedBackdoorAccess()
    recovery_manager = RecoveryManager()

    for attempt in scenario_runner.get_attempts(scenario):
        action = attempt.get("action", "command")
        security_profile = attempt.get("security_profile", profile)
        firmware_policy = FirmwareSecurityPolicy(root / "config" / "security_profiles.yaml", security_profile)
        policy_engine = PolicyEngine(
            root / "config" / "policies.yaml",
            firmware_security_policy=firmware_policy,
            manufacturer_id=fleet_manager.config["manufacturer_id"],
        )

        if action == "simulated_backdoor_access":
            target_devices = fleet_manager.get_all_devices()[: int(attempt.get("target_device_limit", 10))]
            trust_before = count_trust_statuses(target_devices)
            result = backdoor_access.attempt(
                source_ip=attempt["source_ip"],
                target_devices=target_devices,
                requested_temperature=float(attempt["requested_temperature"]),
            )
            trust_after = count_trust_statuses(target_devices)
            logger.log(
                scenario=attempt["scenario"],
                source_ip=attempt["source_ip"],
                command_text=attempt["command_text"],
                parsed_command={
                    "intent": "simulated_backdoor_access",
                    "requested_temperature": attempt["requested_temperature"],
                    "target_scope": "limited",
                },
                policy_decision={
                    "decision": "APPROVED" if result["success"] else "BLOCKED",
                    "reasons": ["Simulated backdoor path affected compromised devices."]
                    if result["success"]
                    else ["No eligible compromised, non-quarantined devices accepted the simulated backdoor command."],
                },
                target_device_count=len(target_devices),
                devices_changed=len(result["changed_devices"]),
                attack_detected=True,
                security_profile=security_profile,
                trust_status_before=trust_before,
                trust_status_after=trust_after,
                simulated_backdoor_attempt=True,
                simulated_backdoor_success=result["success"],
                eligible_backdoor_devices=result["eligible_backdoor_devices"],
                backdoor_affected_devices=result["backdoor_affected_devices"],
                backdoor_blocked_devices=result["backdoor_blocked_devices"],
                compromised_devices_targeted=result["compromised_devices_targeted"],
                trusted_devices_targeted=result["trusted_devices_targeted"],
            )
            continue

        if action == "quarantine_recovery":
            all_devices = fleet_manager.get_all_devices()
            trust_before = count_trust_statuses(all_devices)
            quarantined = recovery_manager.quarantine_compromised_devices(all_devices)
            backdoor_result = backdoor_access.attempt(
                source_ip="203.0.113.50",
                target_devices=all_devices[:10],
                requested_temperature=18,
            )
            recovered = recovery_manager.recover_devices_to_safe_firmware(all_devices)
            trust_after = count_trust_statuses(all_devices)
            logger.log(
                scenario=attempt["scenario"],
                source_ip=attempt["source_ip"],
                command_text=attempt["command_text"],
                parsed_command={"intent": "quarantine_recovery", "target_scope": "all"},
                policy_decision={
                    "decision": "APPROVED",
                    "reasons": ["Compromised devices quarantined and recovered to safe firmware."],
                },
                target_device_count=len(all_devices),
                devices_changed=0,
                attack_detected=bool(quarantined),
                security_profile=security_profile,
                trust_status_before=trust_before,
                trust_status_after=trust_after,
                devices_quarantined=len(quarantined),
                devices_recovered=len(recovered),
                simulated_backdoor_attempt=True,
                simulated_backdoor_success=backdoor_result["success"],
                eligible_backdoor_devices=backdoor_result["eligible_backdoor_devices"],
                backdoor_affected_devices=backdoor_result["backdoor_affected_devices"],
                backdoor_blocked_devices=backdoor_result["backdoor_blocked_devices"],
                compromised_devices_targeted=backdoor_result["compromised_devices_targeted"],
                trusted_devices_targeted=backdoor_result["trusted_devices_targeted"],
            )
            continue

        parsed_command = assistant.parse_command(attempt["command_text"])
        parsed_command["approval_granted"] = bool(
            attempt.get("approval_granted", False) or parsed_command.get("approval_granted", False)
        )
        prompt_result = prompt_filter.scan(attempt["command_text"])
        network_result = network_policy.check_source_ip(attempt["source_ip"])
        target_devices = fleet_manager.get_target_devices(parsed_command)
        trust_before = count_trust_statuses(target_devices)
        policy_decision = policy_engine.evaluate(parsed_command, prompt_result, network_result, target_devices)

        devices_changed = 0
        devices_compromised = 0
        firmware_id = None
        firmware_version = None
        firmware_signature_valid = None
        firmware_tampered = None
        firmware_contains_backdoor = None
        backdoor_enabled = False
        compromised_device_ids: list[str] = []

        if policy_decision["decision"] == "APPROVED":
            if parsed_command["intent"] == "set_temperature":
                devices_changed = fleet_manager.apply_temperature_command(parsed_command, target_devices)
            elif parsed_command["intent"] == "firmware_update":
                firmware_package = FirmwarePackage(**parsed_command["firmware_package"])
                firmware_result = fleet_manager.apply_firmware_update(firmware_package, target_devices)
                devices_changed = firmware_result["devices_updated"]
                devices_compromised = firmware_result["devices_compromised"]
                compromised_device_ids = firmware_result["compromised_device_ids"]
                backdoor_enabled = firmware_result["backdoor_enabled"]

        firmware_package_data = parsed_command.get("firmware_package") or {}
        if firmware_package_data:
            firmware_id = firmware_package_data.get("firmware_id")
            firmware_version = firmware_package_data.get("version")
            firmware_signature_valid = firmware_package_data.get("signature_valid")
            firmware_tampered = firmware_package_data.get("is_tampered")
            firmware_contains_backdoor = firmware_package_data.get("contains_simulated_backdoor")

        trust_after = count_trust_statuses(target_devices)
        attack_detected = (
            prompt_result["detected"]
            or not network_result["allowed"]
            or bool(firmware_tampered)
            or bool(firmware_contains_backdoor)
        )

        logger.log(
            scenario=attempt["scenario"],
            source_ip=attempt["source_ip"],
            command_text=attempt["command_text"],
            parsed_command=parsed_command,
            policy_decision=policy_decision,
            target_device_count=len(target_devices),
            devices_changed=devices_changed,
            attack_detected=attack_detected,
            security_profile=security_profile,
            firmware_id=firmware_id,
            firmware_version=firmware_version,
            firmware_signature_valid=firmware_signature_valid,
            firmware_tampered=firmware_tampered,
            firmware_contains_backdoor=firmware_contains_backdoor,
            backdoor_enabled=backdoor_enabled,
            trust_status_before=trust_before,
            trust_status_after=trust_after,
            devices_compromised=devices_compromised,
            compromised_device_ids=compromised_device_ids,
        )

    logger.save()
    metrics = MetricsCalculator().calculate(logger.entries)
    phase = "phase2" if scenario.startswith("phase2") or any(
        entry["parsed_command"].get("intent") in {"firmware_update", "simulated_backdoor_access", "quarantine_recovery"}
        for entry in logger.entries
    ) else "phase1"
    report_paths = ReportGenerator(root / "reports").generate(logger.entries, metrics, phase=phase)
    return logger.entries, metrics, report_paths


def render_results(console: Console, scenario: str, entries: list[dict], metrics: dict, report_paths: dict) -> None:
    console.print("[bold]AI-Assisted Demand Response Cyber-Resilience Simulator[/bold]")
    console.print(f"Scenario: [cyan]{scenario}[/cyan]\n")

    table = Table(title="Policy Decisions")
    table.add_column("Decision")
    table.add_column("Scenario")
    table.add_column("Source IP")
    table.add_column("Target Count", justify="right")
    table.add_column("Changed", justify="right")
    table.add_column("Reasons")

    for entry in entries:
        decision_style = "green" if entry["policy_decision"] == "APPROVED" else "red"
        reasons = "\n".join(entry["reasons"]) if entry["reasons"] else "Approved by all policy checks."
        table.add_row(
            f"[{decision_style}]{entry['policy_decision']}[/{decision_style}]",
            entry["scenario"],
            entry["source_ip"],
            str(entry["target_device_count"]),
            str(entry["devices_changed"]),
            reasons,
        )

    console.print(table)
    console.print("\n[bold]Metrics[/bold]")
    for key, value in metrics.items():
        console.print(f"{key}: {value}")

    console.print(f"\nReport written to [cyan]{report_paths['text_report']}[/cyan]")
    console.print(f"Metrics written to [cyan]{report_paths['metrics_csv']}[/cyan]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run safe demand-response cyber-resilience simulation scenarios.")
    parser.add_argument(
        "--scenario",
        choices=[
            "normal",
            "prompt_injection",
            "unauthorized_ip",
            "mass_command",
            "all",
            "firmware_valid_update",
            "firmware_tampering_blocked",
            "firmware_tampering_weak_profile",
            "simulated_backdoor_access",
            "quarantine_recovery",
            "approved_mass_command",
            "phase2_all",
        ],
        default="normal",
        help="Scenario to run.",
    )
    parser.add_argument(
        "--profile",
        choices=["strict", "weak_baseline", "balanced"],
        default="strict",
        help="Default security profile for scenarios that do not specify one.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    console = Console()
    entries, metrics, report_paths = run_scenario(args.scenario, args.profile)
    render_results(console, args.scenario, entries, metrics, report_paths)


if __name__ == "__main__":
    main()
