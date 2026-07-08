"""Phase 3 power-demand metrics."""

from __future__ import annotations

import pandas as pd


class PowerMetricsCalculator:
    """Calculates load, energy, comfort, and DR impact metrics."""

    def calculate(
        self,
        timeseries: pd.DataFrame,
        time_step_minutes: int,
        baseline_timeseries: pd.DataFrame | None = None,
        demand_response_target_kw: float = 0.0,
        compromised_device_ids: set[str] | None = None,
        event_start_step: int | None = None,
        event_end_step: int | None = None,
    ) -> dict:
        load_by_step = timeseries.groupby("time_step")["power_demand_kw"].sum()
        baseline_by_step = (
            baseline_timeseries.groupby("time_step")["power_demand_kw"].sum()
            if baseline_timeseries is not None
            else load_by_step
        )

        baseline_peak = float(baseline_by_step.max()) if not baseline_by_step.empty else 0.0
        attack_peak = float(load_by_step.max()) if not load_by_step.empty else 0.0
        peak_increase = attack_peak - baseline_peak
        total_energy = float(load_by_step.sum() * (time_step_minutes / 60.0))

        comfort_loss_degree_minutes = float(
            (timeseries["comfort_deviation"] * time_step_minutes).sum()
        )
        average_deviation = float(timeseries["comfort_deviation"].mean())
        max_deviation = float(timeseries["comfort_deviation"].max())

        if event_start_step is not None and event_end_step is not None:
            event_steps = list(range(event_start_step, event_end_step))
            pre_event_steps = list(range(0, event_start_step))
        else:
            event_steps = list(load_by_step.index)
            pre_event_steps = []

        event_load = load_by_step[load_by_step.index.isin(event_steps)]
        baseline_event_load = baseline_by_step[baseline_by_step.index.isin(event_steps)]
        pre_event_load = load_by_step[load_by_step.index.isin(pre_event_steps)]

        pre_event_average = float(pre_event_load.mean()) if not pre_event_load.empty else 0.0
        event_average = float(event_load.mean()) if not event_load.empty else 0.0
        baseline_event_average = float(baseline_event_load.mean()) if not baseline_event_load.empty else event_average

        actual_reduction = max(0.0, baseline_event_average - event_average)
        target_reduction = demand_response_target_kw
        achievement_rate = 0.0
        failure_rate = 0.0
        if target_reduction > 0:
            achievement_rate = min(1.0, actual_reduction / target_reduction)
            failure_rate = max(0.0, 1.0 - (actual_reduction / target_reduction))

        recovery_steps = 0
        if attack_peak > baseline_peak and baseline_peak >= 0:
            recovery_threshold = baseline_peak * 1.05
            above = load_by_step[load_by_step > recovery_threshold]
            recovery_steps = int(above.index.max() + 1) if not above.empty else 0

        compromised_ids = compromised_device_ids or set()
        compromised_load_kw = 0.0
        protected_load_kw = attack_peak
        if compromised_ids:
            compromised_rows = timeseries[timeseries["device_id"].isin(compromised_ids)]
            protected_rows = timeseries[~timeseries["device_id"].isin(compromised_ids)]
            compromised_load_kw = float(compromised_rows.groupby("time_step")["power_demand_kw"].sum().max())
            protected_load_kw = float(protected_rows.groupby("time_step")["power_demand_kw"].sum().max())

        return {
            "baseline_peak_load_kw": round(baseline_peak, 3),
            "attack_peak_load_kw": round(attack_peak, 3),
            "peak_load_increase_kw": round(peak_increase, 3),
            "peak_load_increase_percent": round((peak_increase / baseline_peak * 100), 3)
            if baseline_peak > 0
            else 0.0,
            "total_energy_consumed_kwh": round(total_energy, 3),
            "comfort_loss_degree_minutes": round(comfort_loss_degree_minutes, 3),
            "average_temperature_deviation": round(average_deviation, 3),
            "max_temperature_deviation": round(max_deviation, 3),
            "demand_response_target_kw": round(demand_response_target_kw, 3),
            "demand_response_actual_kw": round(actual_reduction, 3),
            "pre_event_average_load_kw": round(pre_event_average, 3),
            "event_average_load_kw": round(event_average, 3),
            "baseline_event_average_load_kw": round(baseline_event_average, 3),
            "demand_response_target_reduction_kw": round(target_reduction, 3),
            "demand_response_actual_reduction_kw": round(actual_reduction, 3),
            "demand_response_achievement_rate": round(achievement_rate, 3),
            "demand_response_failure_rate": round(failure_rate, 3),
            "load_recovery_time_steps": recovery_steps,
            "compromised_load_kw": round(compromised_load_kw, 3),
            "protected_load_kw": round(protected_load_kw, 3),
            "total_load_kw": round(attack_peak, 3),
            "load_spike_kw_from_compromised_devices": round(compromised_load_kw, 3),
        }
