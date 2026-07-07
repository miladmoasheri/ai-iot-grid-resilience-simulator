"""Defensive policy validation for simulated thermostat commands."""

from __future__ import annotations

from pathlib import Path

import yaml

from security.firmware_security import FirmwarePackage, FirmwareSecurityPolicy


class PolicyEngine:
    """Combines prompt, network, temperature, and fleet-size checks."""

    def __init__(
        self,
        policies_path: str | Path,
        firmware_security_policy: FirmwareSecurityPolicy | None = None,
        manufacturer_id: str = "ThermoGrid-X",
    ):
        self.policies_path = Path(policies_path)
        with self.policies_path.open("r", encoding="utf-8") as policies_file:
            self.policies = yaml.safe_load(policies_file)
        self.firmware_security_policy = firmware_security_policy
        self.manufacturer_id = manufacturer_id

    def evaluate(
        self,
        parsed_command: dict,
        prompt_result: dict,
        network_result: dict,
        target_devices: list,
    ) -> dict:
        reasons: list[str] = []

        intent = parsed_command.get("intent")
        if intent not in {"set_temperature", "firmware_update"}:
            reasons.append("Command intent is not recognized.")

        if self.policies["security"]["block_prompt_injection_if_detected"] and prompt_result.get("detected"):
            matches = ", ".join(prompt_result.get("matched_phrases", []))
            reasons.append(f"Prompt-injection indicators detected: {matches}.")

        if not network_result.get("allowed", False):
            reasons.append(network_result.get("reason", "Source IP is not allowed."))

        if intent == "set_temperature":
            requested_temperature = parsed_command.get("requested_temperature")
            if requested_temperature is None:
                reasons.append("No requested temperature was found.")
            else:
                minimum = self.policies["temperature"]["min"]
                maximum = self.policies["temperature"]["max"]
                if requested_temperature < minimum or requested_temperature > maximum:
                    reasons.append(
                        f"Requested temperature {requested_temperature:g} is outside allowed range {minimum}-{maximum}."
                    )

                max_change = self.policies["temperature"]["max_change_per_command"]
                if target_devices:
                    largest_change = max(abs(requested_temperature - device.target_temperature) for device in target_devices)
                    if largest_change > max_change:
                        reasons.append(
                            f"Requested change {largest_change:g} exceeds max change per command of {max_change}."
                        )

        if intent == "firmware_update":
            firmware_data = parsed_command.get("firmware_package")
            if not firmware_data:
                reasons.append("No firmware package metadata was found.")
            elif self.firmware_security_policy is None:
                reasons.append("No firmware security policy is configured.")
            else:
                firmware_package = FirmwarePackage(**firmware_data)
                firmware_decision = self.firmware_security_policy.evaluate(firmware_package, self.manufacturer_id)
                reasons.extend(firmware_decision["reasons"])

        if not target_devices:
            reasons.append("No target devices matched the command.")

        if self.policies["security"]["block_quarantined_devices"]:
            quarantined = [device.device_id for device in target_devices if device.status == "quarantined"]
            if quarantined:
                reasons.append(f"Command includes quarantined devices: {', '.join(quarantined[:5])}.")

        threshold = self.policies["commands"]["max_devices_without_approval"]
        approval_granted = bool(parsed_command.get("approval_granted", False))
        requires_approval = True
        if self.firmware_security_policy is not None:
            requires_approval = self.firmware_security_policy.requires_mass_approval()

        if len(target_devices) > threshold and requires_approval and not approval_granted:
            reasons.append(
                f"Command targets {len(target_devices)} devices, exceeding threshold of {threshold} without approval."
            )

        decision = "BLOCKED" if reasons else "APPROVED"
        return {"decision": decision, "reasons": reasons}
