"""Sensitivity analysis for Phase 4 experiment outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class SensitivityAnalyzer:
    """Ranks input variables using simple normalized correlation scores."""

    input_variables = [
        "compromised_device_percentage",
        "attack_temperature",
        "hvac_power_kw",
        "ambient_temperature",
        "temperature_change_rate",
        "prompt_filter_strictness",
        "human_approval_threshold",
        "firmware_signature_required",
        "quarantine_enabled",
        "recovery_enabled",
        "false_positive_rate",
        "human_approval_delay_minutes",
        "average_command_latency_ms",
        "availability_rate",
        "total_operational_friction_score",
    ]

    output_metrics = [
        "attack_success_rate",
        "load_spike_kw",
        "comfort_loss_degree_minutes",
        "demand_response_failure_rate",
        "total_operational_friction_score",
        "balanced_objective_score",
    ]

    interpretation_note = (
        "Sensitivity scores are approximate simulation-based rankings, not causal proof. "
        "Some variables are bundled by security configuration, so correlations may reflect configuration design. "
        "Full causal interpretation would require a factorial design or controlled one-factor-at-a-time experiment."
    )

    def analyze(self, results_path: str | Path, output_path: str | Path) -> pd.DataFrame:
        results = pd.read_csv(results_path)
        encoded = results.copy()
        for column in ["firmware_signature_required", "quarantine_enabled", "recovery_enabled"]:
            encoded[column] = encoded[column].astype(bool).astype(int)

        rows: list[dict] = []
        for output_metric in self.output_metrics:
            scores = []
            for input_variable in self.input_variables:
                if input_variable == output_metric:
                    continue
                if encoded[input_variable].nunique() <= 1 or encoded[output_metric].nunique() <= 1:
                    score = 0.0
                else:
                    score = abs(float(encoded[[input_variable, output_metric]].corr().iloc[0, 1]))
                    if pd.isna(score):
                        score = 0.0
                scores.append((input_variable, score))

            scores.sort(key=lambda item: item[1], reverse=True)
            for rank, (input_variable, score) in enumerate(scores, start=1):
                rows.append(
                    {
                        "output_metric": output_metric,
                        "input_parameter": input_variable,
                        "sensitivity_score": round(score, 4),
                        "rank": rank,
                        "interpretation_note": self.interpretation_note,
                    }
                )

        sensitivity = pd.DataFrame(rows)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sensitivity.to_csv(output_path, index=False)
        return sensitivity
