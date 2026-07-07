"""Firmware trust policy for safe internal simulation."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel


class FirmwarePackage(BaseModel):
    """Metadata-only representation of a simulated firmware package."""

    firmware_id: str
    manufacturer_id: str
    version: str
    signature_valid: bool
    is_tampered: bool
    contains_simulated_backdoor: bool
    release_channel: str


class FirmwareSecurityPolicy:
    """Verifies simulated firmware metadata against a selected profile."""

    def __init__(self, profiles_path: str | Path, profile_name: str = "strict"):
        self.profiles_path = Path(profiles_path)
        with self.profiles_path.open("r", encoding="utf-8") as profiles_file:
            self.profiles = yaml.safe_load(profiles_file)

        if profile_name not in self.profiles:
            raise ValueError(f"Unknown security profile '{profile_name}'.")

        self.profile_name = profile_name
        self.profile = self.profiles[profile_name]

    def evaluate(self, firmware_package: FirmwarePackage, expected_manufacturer_id: str) -> dict:
        reasons: list[str] = []

        if firmware_package.manufacturer_id != expected_manufacturer_id:
            reasons.append(
                f"Firmware manufacturer {firmware_package.manufacturer_id} does not match {expected_manufacturer_id}."
            )

        if self.profile["require_firmware_signature"] and not firmware_package.signature_valid:
            reasons.append("Firmware signature is invalid and this profile requires valid signatures.")

        if not self.profile["allow_unsigned_firmware"] and not firmware_package.signature_valid:
            reasons.append("Unsigned or invalid-signature firmware is not allowed.")

        if firmware_package.is_tampered and not self.profile["allow_tampered_firmware"]:
            reasons.append("Tampered firmware is blocked by the selected security profile.")

        if firmware_package.contains_simulated_backdoor and self.profile["quarantine_on_backdoor_detection"]:
            reasons.append("Simulated backdoor marker detected and quarantine-on-detection is enabled.")

        return {"decision": "BLOCKED" if reasons else "APPROVED", "reasons": reasons}

    def requires_mass_approval(self) -> bool:
        return bool(self.profile.get("require_approval_for_mass_commands", True))
