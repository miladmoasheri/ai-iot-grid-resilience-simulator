"""HVAC load calculations for simulated thermostat fleets."""

from __future__ import annotations


class HVACLoadModel:
    """Calculates device and fleet HVAC load."""

    def calculate_device_load(self, device) -> float:
        return float(device.calculate_power_demand_kw())

    def calculate_fleet_load(self, devices: list) -> float:
        return float(sum(self.calculate_device_load(device) for device in devices))

    def calculate_active_hvac_count(self, devices: list) -> int:
        return sum(1 for device in devices if device.calculate_hvac_state())
