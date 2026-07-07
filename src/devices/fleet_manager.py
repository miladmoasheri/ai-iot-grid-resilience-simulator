"""Fleet creation and simulated thermostat updates."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import yaml

from devices.thermostat import Thermostat


class FleetManager:
    """Manages an in-memory fleet of simulated thermostats."""

    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.devices = self._create_devices()

    def _load_config(self) -> dict:
        with self.config_path.open("r", encoding="utf-8") as config_file:
            return yaml.safe_load(config_file)

    def _create_devices(self) -> list[Thermostat]:
        devices: list[Thermostat] = []
        manufacturer_id = self.config["manufacturer_id"]
        defaults = self.config["defaults"]

        for building in self.config["buildings"]:
            building_id = building["building_id"]
            building_slug = building_id.replace(" ", "-").upper()
            for number in range(1, building["thermostat_count"] + 1):
                devices.append(
                    Thermostat(
                        device_id=f"{building_slug}-{number:03d}",
                        building_id=building_id,
                        manufacturer_id=manufacturer_id,
                        ip_address=f"{building['ip_prefix']}.{number}",
                        current_temperature=defaults["current_temperature"],
                        target_temperature=defaults["target_temperature"],
                        firmware_version=str(defaults["firmware_version"]),
                    )
                )
        return devices

    def get_devices_by_building(self, building_id: str) -> list[Thermostat]:
        return [device for device in self.devices if device.building_id.lower() == building_id.lower()]

    def get_all_devices(self) -> list[Thermostat]:
        return list(self.devices)

    def get_target_devices(self, parsed_command: dict) -> list[Thermostat]:
        if parsed_command.get("target_scope") == "all":
            devices = self.get_all_devices()
            return self._apply_target_limit(devices, parsed_command)

        building_id = parsed_command.get("target_building")
        if building_id:
            devices = self.get_devices_by_building(building_id)
            return self._apply_target_limit(devices, parsed_command)

        return []

    def _apply_target_limit(self, devices: list[Thermostat], parsed_command: dict) -> list[Thermostat]:
        limit = parsed_command.get("target_device_limit")
        if limit is None:
            return devices
        return devices[: max(0, int(limit))]

    def apply_temperature_command(self, parsed_command: dict, target_devices: Iterable[Thermostat] | None = None) -> int:
        devices = list(target_devices) if target_devices is not None else self.get_target_devices(parsed_command)
        requested_temperature = parsed_command.get("requested_temperature")

        if requested_temperature is None:
            return 0

        changed = 0
        for device in devices:
            if device.status == "active":
                device.update_target_temperature(float(requested_temperature))
                changed += 1
        return changed

    def apply_firmware_update(self, firmware_package, target_devices: Iterable[Thermostat]) -> dict:
        devices = list(target_devices)
        compromised_before = {device.device_id for device in devices if device.is_compromised()}

        for device in devices:
            if device.status == "active":
                device.install_firmware(firmware_package)

        compromised_after = {device.device_id for device in devices if device.is_compromised()}
        newly_compromised = sorted(compromised_after - compromised_before)
        return {
            "devices_updated": len([device for device in devices if device.status == "active"]),
            "devices_compromised": len(newly_compromised),
            "compromised_device_ids": newly_compromised,
            "backdoor_enabled": any(device.backdoor_enabled for device in devices),
        }

    def get_fleet_status(self) -> list[dict]:
        return [device.to_dict() for device in self.devices]
