"""Monte Carlo experiment engine for Phase 4."""

from __future__ import annotations

import random
from pathlib import Path

import pandas as pd


class MonteCarloRunner:
    """Runs repeated simplified cyber-physical simulation experiments."""

    def __init__(self, experiment_config, output_dir: str | Path):
        self.config = experiment_config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        runs: int | None = None,
        random_seed: int | None = None,
        runs_per_configuration: int | None = None,
    ) -> pd.DataFrame:
        per_config = runs_per_configuration if runs_per_configuration is not None else runs
        per_config = per_config if per_config is not None else self.config.runs_per_configuration
        seed = random_seed if random_seed is not None else self.config.random_seed
        rng = random.Random(seed)
        rows = []
        run_id = 1
        for security_name in self.config.security_configuration_names:
            for configuration_run_id in range(1, per_config + 1):
                rows.append(self._run_single(run_id, configuration_run_id, security_name, rng))
                run_id += 1
        results = pd.DataFrame(rows)
        results.to_csv(self.output_dir / "phase4_experiment_results.csv", index=False)
        return results

    def _run_single(
        self,
        run_id: int,
        configuration_run_id: int,
        security_name: str,
        rng: random.Random,
    ) -> dict:
        data = self.config.data
        security = data["security_configurations"][security_name]

        fleet_size = int(rng.choice(data["fleet"]["fleet_sizes"]))
        compromised_pct = float(rng.choice(data["attack"]["compromised_device_percentages"]))
        attack_temperature = float(rng.choice(data["attack"]["attack_temperatures"]))
        attack_start_step = int(rng.choice(data["attack"]["attack_start_steps"]))
        hvac_power_kw = float(rng.choice(data["power"]["hvac_power_kw_values"]))
        ambient_temperature = float(rng.choice(data["power"]["ambient_temperatures"]))
        temperature_change_rate = float(rng.choice(data["power"]["temperature_change_rates"]))

        compromised_devices = max(1, round(fleet_size * compromised_pct / 100.0))
        firmware_signature_required = bool(security["firmware_signature_required"])
        prompt_filter_strictness = float(security["prompt_filter_strictness"])
        human_approval_threshold = int(security["human_approval_threshold"])
        quarantine_enabled = bool(security["quarantine_enabled"])
        recovery_enabled = bool(security["recovery_enabled"])
        weights = data["objective_weights"]

        attack_intensity = self._attack_intensity(attack_temperature)
        approval_factor = 0.85 if human_approval_threshold <= compromised_devices else 1.0
        firmware_factor = 0.35 if firmware_signature_required else 1.0
        prompt_factor = 1.0 - (0.55 * prompt_filter_strictness)
        quarantine_factor = 0.55 if quarantine_enabled else 1.0
        recovery_factor = 0.75 if recovery_enabled else 1.0

        attack_success_rate = min(
            1.0,
            max(
                0.0,
                (compromised_pct / 50.0)
                * attack_intensity
                * approval_factor
                * firmware_factor
                * prompt_factor
                * quarantine_factor
                * recovery_factor
                + rng.uniform(-0.03, 0.03),
            ),
        )

        effective_compromised = round(compromised_devices * attack_success_rate)
        baseline_peak_load_kw = fleet_size * hvac_power_kw * self._ambient_load_factor(ambient_temperature)
        compromised_load_capacity = effective_compromised * hvac_power_kw
        load_spike_kw = compromised_load_capacity * attack_intensity * (1.0 + (ambient_temperature - 30.0) / 20.0)
        peak_load_kw = baseline_peak_load_kw + max(0.0, load_spike_kw)

        total_energy_kwh = (
            baseline_peak_load_kw * 6.0
            + max(0.0, load_spike_kw) * max(1, 24 - attack_start_step) * 0.25
        )
        comfort_loss_degree_minutes = self._comfort_loss(
            attack_temperature,
            effective_compromised,
            temperature_change_rate,
            recovery_enabled,
        )
        demand_response_failure_rate = min(
            1.0,
            max(
                0.0,
                attack_success_rate * (compromised_pct / 50.0) * attack_intensity + rng.uniform(-0.02, 0.02),
            ),
        )

        devices_quarantined = effective_compromised if quarantine_enabled else 0
        devices_recovered = devices_quarantined if recovery_enabled else 0
        time_to_recovery = 0
        if recovery_enabled and devices_recovered:
            time_to_recovery = max(1, 8 - round(prompt_filter_strictness * 4))

        legitimate_command_rejection_rate = min(
            1.0,
            max(0.0, 0.02 + prompt_filter_strictness * 0.08 + (0.03 if human_approval_threshold < fleet_size else 0.0)),
        )

        approval_pressure = min(1.0, fleet_size / max(1, human_approval_threshold))
        human_approval_requests = round(approval_pressure * 4 + compromised_devices * 0.04)
        human_approval_delay_minutes = human_approval_requests * (1.5 + prompt_filter_strictness * 3.0)
        average_command_latency_ms = 80 + prompt_filter_strictness * 180
        if firmware_signature_required:
            average_command_latency_ms += 35
        if quarantine_enabled:
            average_command_latency_ms += 25

        false_positive_rate = min(1.0, 0.01 + prompt_filter_strictness ** 1.35 * 0.13)
        firmware_update_delay_minutes = (12 if firmware_signature_required else 2) + (4 if recovery_enabled else 0)
        quarantine_availability_loss = (devices_quarantined / fleet_size) * (0.65 if recovery_enabled else 1.0)
        devices_unavailable_due_to_quarantine = round(fleet_size * quarantine_availability_loss)
        availability_rate = max(0.0, 1.0 - quarantine_availability_loss)
        operator_workload_score = min(1.0, human_approval_requests / 12.0 + prompt_filter_strictness * 0.15)
        security_operation_cost = (
            prompt_filter_strictness * 12
            + (8 if firmware_signature_required else 1)
            + (6 if quarantine_enabled else 0)
            + (7 if recovery_enabled else 0)
            + human_approval_requests * 0.8
        )
        monitoring_overhead_score = min(
            1.0,
            prompt_filter_strictness * 0.55
            + (0.15 if firmware_signature_required else 0)
            + (0.12 if quarantine_enabled else 0)
            + (0.10 if recovery_enabled else 0),
        )
        total_operational_friction_score = min(
            1.0,
            false_positive_rate * 1.2
            + legitimate_command_rejection_rate
            + min(1.0, human_approval_delay_minutes / 45.0) * 0.35
            + monitoring_overhead_score * 0.35
            + min(1.0, security_operation_cost / 40.0) * 0.25,
        )

        security_risk_score = min(
            1.0,
            attack_success_rate * 0.55
            + demand_response_failure_rate * 0.25
            + (effective_compromised / max(1, fleet_size)) * 0.20,
        )
        power_impact_score = min(1.0, load_spike_kw / max(1.0, baseline_peak_load_kw * 0.35))
        comfort_impact_score = min(1.0, comfort_loss_degree_minutes / max(1.0, fleet_size * 240.0))
        operational_friction_score = total_operational_friction_score
        availability_loss_score = min(1.0, quarantine_availability_loss)
        balanced_objective_score = (
            weights["security_risk"] * security_risk_score
            + weights["power_impact"] * power_impact_score
            + weights["comfort_impact"] * comfort_impact_score
            + weights["demand_response_failure"] * demand_response_failure_rate
            + weights["operational_friction"] * operational_friction_score
            + weights["availability_loss"] * availability_loss_score
        )
        overall_resilience_score = max(0.0, 1.0 - balanced_objective_score)

        return {
            "run_id": run_id,
            "configuration_run_id": configuration_run_id,
            "security_configuration": security_name,
            "fleet_size": fleet_size,
            "compromised_device_percentage": compromised_pct,
            "compromised_devices": compromised_devices,
            "attack_temperature": attack_temperature,
            "hvac_power_kw": hvac_power_kw,
            "ambient_temperature": ambient_temperature,
            "temperature_change_rate": temperature_change_rate,
            "attack_start_step": attack_start_step,
            "attack_success_rate": round(attack_success_rate, 4),
            "peak_load_kw": round(peak_load_kw, 4),
            "baseline_peak_load_kw": round(baseline_peak_load_kw, 4),
            "load_spike_kw": round(max(0.0, load_spike_kw), 4),
            "total_energy_kwh": round(total_energy_kwh, 4),
            "comfort_loss_degree_minutes": round(comfort_loss_degree_minutes, 4),
            "demand_response_failure_rate": round(demand_response_failure_rate, 4),
            "time_to_recovery": time_to_recovery,
            "devices_quarantined": devices_quarantined,
            "devices_recovered": devices_recovered,
            "human_approval_requests": human_approval_requests,
            "human_approval_delay_minutes": round(human_approval_delay_minutes, 4),
            "average_command_latency_ms": round(average_command_latency_ms, 4),
            "false_positive_rate": round(false_positive_rate, 4),
            "legitimate_command_rejection_rate": round(legitimate_command_rejection_rate, 4),
            "firmware_update_delay_minutes": round(firmware_update_delay_minutes, 4),
            "quarantine_availability_loss": round(quarantine_availability_loss, 4),
            "devices_unavailable_due_to_quarantine": devices_unavailable_due_to_quarantine,
            "availability_rate": round(availability_rate, 4),
            "operator_workload_score": round(operator_workload_score, 4),
            "security_operation_cost": round(security_operation_cost, 4),
            "monitoring_overhead_score": round(monitoring_overhead_score, 4),
            "total_operational_friction_score": round(total_operational_friction_score, 4),
            "security_risk_score": round(security_risk_score, 4),
            "power_impact_score": round(power_impact_score, 4),
            "comfort_impact_score": round(comfort_impact_score, 4),
            "operational_friction_score": round(operational_friction_score, 4),
            "availability_loss_score": round(availability_loss_score, 4),
            "overall_resilience_score": round(overall_resilience_score, 4),
            "balanced_objective_score": round(balanced_objective_score, 4),
            "recovery_enabled": recovery_enabled,
            "quarantine_enabled": quarantine_enabled,
            "firmware_signature_required": firmware_signature_required,
            "prompt_filter_strictness": prompt_filter_strictness,
            "human_approval_threshold": human_approval_threshold,
        }

    def _attack_intensity(self, attack_temperature: float) -> float:
        if attack_temperature <= 16:
            return 1.0
        if attack_temperature <= 18:
            return 0.65
        return 0.45

    def _ambient_load_factor(self, ambient_temperature: float) -> float:
        return 0.75 + max(0.0, ambient_temperature - 28.0) * 0.04

    def _comfort_loss(
        self,
        attack_temperature: float,
        effective_compromised: int,
        temperature_change_rate: float,
        recovery_enabled: bool,
    ) -> float:
        if 20 <= attack_temperature <= 25:
            deviation = 0.0
        elif attack_temperature < 20:
            deviation = 20 - attack_temperature
        else:
            deviation = attack_temperature - 25

        recovery_factor = 0.45 if recovery_enabled else 1.0
        dynamics_factor = 0.25 / max(0.05, temperature_change_rate)
        return deviation * effective_compromised * 60.0 * recovery_factor * dynamics_factor
