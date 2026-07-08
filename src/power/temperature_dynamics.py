"""Time-step temperature and load simulation."""

from __future__ import annotations

import pandas as pd


class TemperatureDynamicsSimulator:
    """Runs simple thermostat temperature dynamics over discrete time steps."""

    def run_time_steps(
        self,
        devices: list,
        time_steps: int,
        time_step_minutes: int,
        scenario: str = "baseline",
        step_callback=None,
    ) -> pd.DataFrame:
        records: list[dict] = []

        for time_step in range(time_steps):
            if step_callback is not None:
                step_callback(time_step, devices)

            for device in devices:
                power_demand_kw = device.calculate_power_demand_kw()
                records.append(
                    {
                        "time_step": time_step,
                        "time_minutes": time_step * time_step_minutes,
                        "device_id": device.device_id,
                        "building_id": device.building_id,
                        "current_temperature": round(device.current_temperature, 3),
                        "target_temperature": round(device.target_temperature, 3),
                        "hvac_active": device.hvac_active,
                        "power_demand_kw": power_demand_kw,
                        "comfort_deviation": device.calculate_comfort_deviation(),
                        "trust_status": device.trust_status,
                        "scenario": scenario,
                    }
                )
                device.update_temperature_step()

        return pd.DataFrame(records)
