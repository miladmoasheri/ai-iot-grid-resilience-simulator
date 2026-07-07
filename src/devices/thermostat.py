"""Simulated thermostat device model."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Thermostat(BaseModel):
    """A simulated thermostat with no real device or network behavior."""

    device_id: str
    building_id: str
    manufacturer_id: str
    ip_address: str
    current_temperature: float
    target_temperature: float
    firmware_version: str
    status: str = Field(default="active")
    trust_status: str = Field(default="trusted")
    firmware_signature_valid: bool = Field(default=True)
    backdoor_enabled: bool = Field(default=False)
    last_firmware_update: str | None = Field(default=None)
    compromise_reason: str | None = Field(default=None)

    def update_target_temperature(self, new_temperature: float) -> None:
        """Update the simulated target temperature."""

        self.target_temperature = float(new_temperature)

    def install_firmware(self, firmware_package: Any) -> None:
        """Install simulated firmware metadata onto the device."""

        self.firmware_version = firmware_package.version
        self.firmware_signature_valid = firmware_package.signature_valid
        self.last_firmware_update = firmware_package.firmware_id

        if firmware_package.is_tampered or firmware_package.contains_simulated_backdoor:
            reason_parts = []
            if firmware_package.is_tampered:
                reason_parts.append("tampered firmware accepted by selected profile")
            if firmware_package.contains_simulated_backdoor:
                reason_parts.append("simulated backdoor marker present")
            self.enable_simulated_backdoor("; ".join(reason_parts))
        elif self.trust_status != "quarantined":
            self.trust_status = "trusted"
            self.backdoor_enabled = False
            self.compromise_reason = None

    def enable_simulated_backdoor(self, reason: str) -> None:
        """Mark a simulated compromise state without creating real access paths."""

        self.backdoor_enabled = True
        self.trust_status = "compromised"
        self.compromise_reason = reason

    def quarantine(self, reason: str) -> None:
        """Quarantine the simulated device and disable any simulated backdoor flag."""

        self.status = "quarantined"
        self.trust_status = "quarantined"
        self.backdoor_enabled = False
        if self.compromise_reason:
            self.compromise_reason = f"{self.compromise_reason}; quarantined: {reason}"
        else:
            self.compromise_reason = f"quarantined: {reason}"

    def recover_to_safe_firmware(self, version: str) -> None:
        """Recover the simulated device to a trusted firmware state."""

        self.status = "active"
        self.trust_status = "recovered"
        self.firmware_version = version
        self.firmware_signature_valid = True
        self.backdoor_enabled = False
        self.last_firmware_update = f"recovery-{version}"

    def is_compromised(self) -> bool:
        """Return whether the simulated device is currently compromised."""

        return self.trust_status == "compromised" or self.backdoor_enabled

    def to_dict(self) -> dict:
        """Return a serializable device snapshot."""

        return self.model_dump()
