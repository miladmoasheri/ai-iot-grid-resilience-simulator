"""Quarantine and recovery workflows for simulated compromised devices."""

from __future__ import annotations


class RecoveryManager:
    """Detects, quarantines, and recovers simulated device compromise state."""

    def __init__(self):
        self.recovery_log: list[dict] = []

    def detect_compromised_devices(self, devices: list) -> list:
        compromised = [device for device in devices if device.is_compromised()]
        self.recovery_log.append({"action": "detect", "device_count": len(compromised)})
        return compromised

    def quarantine_compromised_devices(self, devices: list, reason: str = "compromise detected") -> list:
        compromised = self.detect_compromised_devices(devices)
        for device in compromised:
            device.quarantine(reason)
        self.recovery_log.append({"action": "quarantine", "device_count": len(compromised), "reason": reason})
        return compromised

    def recover_devices_to_safe_firmware(self, devices: list, version: str = "1.0.0") -> list:
        recovered = []
        for device in devices:
            if device.trust_status in {"compromised", "quarantined"} or device.backdoor_enabled:
                device.recover_to_safe_firmware(version)
                recovered.append(device)
        self.recovery_log.append({"action": "recover", "device_count": len(recovered), "version": version})
        return recovered
