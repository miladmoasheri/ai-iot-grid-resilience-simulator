"""Objective scoring functions for Phase 5 optimization."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class ObjectiveFunctionCalculator:
    """Loads Phase 4 results and creates normalized optimization objectives."""

    score_columns = [
        "security_risk_score",
        "power_impact_score",
        "comfort_impact_score",
        "demand_response_failure_score",
        "operational_friction_score",
        "availability_loss_score",
    ]

    def __init__(self, phase4_results_path: str | Path):
        self.phase4_results_path = Path(phase4_results_path)

    def load_results(self) -> pd.DataFrame:
        if not self.phase4_results_path.exists():
            raise FileNotFoundError(f"Missing Phase 4 results: {self.phase4_results_path}")
        return pd.read_csv(self.phase4_results_path)

    def calculate_scores(self, weights: dict[str, float], weighting_profile: str = "custom") -> pd.DataFrame:
        results = self.load_results().copy()
        scored = self.add_objective_scores(results, weights)
        scored["weighting_profile"] = weighting_profile
        return scored

    def add_objective_scores(self, results: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
        scored = results.copy()
        scored["security_risk_score"] = self._weighted_average(
            [
                self._bounded_metric(scored, "attack_success_rate"),
                self._normalize_metric(scored, "compromised_devices"),
                self._bounded_metric(scored, "demand_response_failure_rate"),
            ],
            [0.55, 0.20, 0.25],
        )
        scored["power_impact_score"] = self._weighted_average(
            [
                self._normalize_metric(scored, "load_spike_kw"),
                self._normalize_metric(scored, "total_energy_kwh"),
                self._normalize_metric(scored, "peak_load_kw"),
            ],
            [0.55, 0.25, 0.20],
        )
        scored["comfort_impact_score"] = self._normalize_metric(scored, "comfort_loss_degree_minutes")
        scored["demand_response_failure_score"] = self._bounded_metric(scored, "demand_response_failure_rate")
        scored["operational_friction_score"] = self._weighted_average(
            [
                self._bounded_metric(scored, "total_operational_friction_score"),
                self._normalize_metric(scored, "security_operation_cost"),
                self._bounded_metric(scored, "false_positive_rate"),
                self._normalize_metric(scored, "human_approval_delay_minutes"),
            ],
            [0.45, 0.25, 0.15, 0.15],
        )
        scored["availability_loss_score"] = (1.0 - self._bounded_metric(scored, "availability_rate")).clip(0.0, 1.0)

        scored["weighted_objective_score"] = (
            float(weights["security_risk"]) * scored["security_risk_score"]
            + float(weights["power_impact"]) * scored["power_impact_score"]
            + float(weights["comfort_impact"]) * scored["comfort_impact_score"]
            + float(weights["demand_response_failure"]) * scored["demand_response_failure_score"]
            + float(weights["operational_friction"]) * scored["operational_friction_score"]
            + float(weights["availability_loss"]) * scored["availability_loss_score"]
        ).round(6)
        return scored

    def _bounded_metric(self, results: pd.DataFrame, column: str) -> pd.Series:
        if column not in results:
            return pd.Series([0.0] * len(results), index=results.index)
        return pd.to_numeric(results[column], errors="coerce").fillna(0.0).clip(0.0, 1.0)

    def _normalize_metric(self, results: pd.DataFrame, column: str) -> pd.Series:
        if column not in results:
            return pd.Series([0.0] * len(results), index=results.index)
        values = pd.to_numeric(results[column], errors="coerce").fillna(0.0)
        minimum = float(values.min())
        maximum = float(values.max())
        if maximum == minimum:
            return pd.Series([0.0] * len(values), index=results.index)
        return ((values - minimum) / (maximum - minimum)).clip(0.0, 1.0)

    def _weighted_average(self, series_list: list[pd.Series], weights: list[float]) -> pd.Series:
        total_weight = sum(weights)
        combined = sum(weight * series for series, weight in zip(series_list, weights))
        return (combined / total_weight).clip(0.0, 1.0)
