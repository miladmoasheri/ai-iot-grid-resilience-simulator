"""Safe simulated backdoor access path.

This module never opens sockets, scans networks, or contacts devices. It only
checks in-memory device state and applies simulated state changes.
"""

from __future__ import annotations


class SimulatedBackdoorAccess:
    """Attempts a direct simulated command against compromised devices."""

    def attempt(self, source_ip: str, target_devices: list, requested_temperature: float) -> dict:
        changed_devices: list[str] = []
        blocked_devices: list[str] = []
        eligible_devices: list[str] = []
        compromised_devices_targeted = 0
        trusted_devices_targeted = 0

        for device in target_devices:
            if device.trust_status == "compromised":
                compromised_devices_targeted += 1
            else:
                trusted_devices_targeted += 1

            eligible = (
                device.backdoor_enabled
                and device.trust_status == "compromised"
                and device.status != "quarantined"
            )
            if eligible:
                eligible_devices.append(device.device_id)
                device.update_target_temperature(requested_temperature)
                changed_devices.append(device.device_id)
            else:
                blocked_devices.append(device.device_id)

        return {
            "source_ip": source_ip,
            "attempted": True,
            "success": bool(changed_devices),
            "changed_devices": changed_devices,
            "blocked_devices": blocked_devices,
            "eligible_devices": eligible_devices,
            "eligible_backdoor_devices": len(eligible_devices),
            "backdoor_affected_devices": len(changed_devices),
            "backdoor_blocked_devices": len(blocked_devices),
            "compromised_devices_targeted": compromised_devices_targeted,
            "trusted_devices_targeted": trusted_devices_targeted,
            "requested_temperature": requested_temperature,
        }
