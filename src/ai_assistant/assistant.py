"""Deterministic simulated AI assistant for natural language commands."""

from __future__ import annotations

import re


class SimulatedAIAssistant:
    """Parses thermostat commands into structured intent.

    This class does not call a live model and does not execute commands. It is
    intentionally deterministic so Phase 1 scenarios are reproducible.
    """

    _temperature_pattern = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:degrees?|deg|c|celsius)?", re.IGNORECASE)
    _device_limit_pattern = re.compile(
        r"(?:first|top|limit(?:ed)?\s+to)\s+(\d+)\s+(?:building\s+[ab]\s+)?thermostats?",
        re.IGNORECASE,
    )

    def parse_command(self, command_text: str) -> dict:
        lowered = command_text.lower()
        target_device_limit = self._extract_device_limit(command_text)
        approval_granted = "approve" in lowered or "with approval" in lowered
        target_scope = "unknown"
        target_building = None

        if "all thermostats" in lowered or "entire fleet" in lowered:
            target_scope = "all"
        elif "building a" in lowered:
            target_scope = "building"
            target_building = "Building A"
        elif "building b" in lowered:
            target_scope = "building"
            target_building = "Building B"

        firmware_package = None
        if "firmware" in lowered and "install" in lowered:
            firmware_package = self._extract_firmware_package(command_text)
            intent = "firmware_update"
            requested_temperature = None
            if target_scope == "unknown":
                target_scope = "all"
        else:
            requested_temperature = self._extract_temperature(command_text)
            intent = "set_temperature" if "set" in lowered and requested_temperature is not None else "unknown"

        return {
            "intent": intent,
            "target_scope": target_scope,
            "target_building": target_building,
            "requested_temperature": requested_temperature,
            "target_device_limit": target_device_limit,
            "is_mass_command": target_scope == "all",
            "approval_granted": approval_granted,
            "firmware_package": firmware_package,
            "raw_text": command_text,
        }

    def _extract_temperature(self, command_text: str) -> float | None:
        matches = self._temperature_pattern.findall(command_text)
        if not matches:
            return None
        return float(matches[-1])

    def _extract_device_limit(self, command_text: str) -> int | None:
        match = self._device_limit_pattern.search(command_text)
        if not match:
            return None
        return int(match.group(1))

    def _extract_firmware_package(self, command_text: str) -> dict:
        lowered = command_text.lower()
        version_match = re.search(r"version\s+([0-9]+(?:\.[0-9]+){1,2})", command_text, re.IGNORECASE)
        version = version_match.group(1) if version_match else "unknown"
        is_tampered = "tampered" in lowered
        is_unsigned = "unsigned" in lowered
        contains_backdoor = "backdoor" in lowered
        signature_valid = not (is_unsigned or is_tampered)

        return {
            "firmware_id": f"fw-{version}",
            "manufacturer_id": "ThermoGrid-X",
            "version": version,
            "signature_valid": signature_valid,
            "is_tampered": is_tampered,
            "contains_simulated_backdoor": contains_backdoor,
            "release_channel": "lab" if is_tampered or is_unsigned else "stable",
        }
