"""Demand-response controls for the simulated thermostat fleet."""

from __future__ import annotations


class DemandResponseController:
    """Applies simple thermostat setpoint changes for demand response."""

    def apply_demand_response_event(
        self,
        devices: list,
        target_temperature: float,
        event_start_step: int,
        event_end_step: int,
        current_step: int | None = None,
    ) -> int:
        if current_step is not None and not (event_start_step <= current_step < event_end_step):
            return 0

        for device in devices:
            if device.status == "active":
                device.update_target_temperature(target_temperature)
        return len([device for device in devices if device.status == "active"])

    def calculate_baseline_load(self, devices: list, load_model) -> float:
        return load_model.calculate_fleet_load(devices)

    def calculate_actual_load_reduction(self, baseline_load_kw: float, actual_load_kw: float) -> float:
        return max(0.0, baseline_load_kw - actual_load_kw)

    def calculate_demand_response_failure_rate(self, target_kw: float, actual_kw: float) -> float:
        if target_kw <= 0:
            return 0.0
        shortfall = max(0.0, target_kw - actual_kw)
        return shortfall / target_kw
