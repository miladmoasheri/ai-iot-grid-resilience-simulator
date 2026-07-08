"""Pareto trade-off analysis for Phase 5."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from optimization.objective_functions import ObjectiveFunctionCalculator


class ParetoAnalyzer:
    """Identifies Pareto-efficient experiment points across trade-off pairs."""

    objective_pairs = [
        ("security_risk_score", "operational_friction_score"),
        ("power_impact_score", "comfort_impact_score"),
        ("security_risk_score", "availability_loss_score"),
    ]

    def __init__(self, phase4_results_path: str | Path, output_path: str | Path):
        self.phase4_results_path = Path(phase4_results_path)
        self.output_path = Path(output_path)

    def analyze(self, weights: dict[str, float] | None = None) -> pd.DataFrame:
        weights = weights or {
            "security_risk": 0.30,
            "power_impact": 0.20,
            "comfort_impact": 0.15,
            "demand_response_failure": 0.15,
            "operational_friction": 0.10,
            "availability_loss": 0.10,
        }
        scored = ObjectiveFunctionCalculator(self.phase4_results_path).calculate_scores(weights, "pareto")
        pareto = scored[
            [
                "run_id",
                "security_configuration",
                "security_risk_score",
                "operational_friction_score",
                "power_impact_score",
                "comfort_impact_score",
                "availability_loss_score",
            ]
        ].copy()

        pair_flags = []
        for first, second in self.objective_pairs:
            flag_name = f"pareto_{first}_vs_{second}"
            pareto[flag_name] = self._is_efficient(pareto[[first, second]])
            pair_flags.append(flag_name)
        pareto["is_pareto_efficient"] = pareto[pair_flags].any(axis=1)

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        pareto.to_csv(self.output_path, index=False)
        return pareto

    def _is_efficient(self, objectives: pd.DataFrame) -> pd.Series:
        values = objectives.to_numpy()
        efficient = []
        for index, candidate in enumerate(values):
            others = values
            dominated = ((others <= candidate).all(axis=1) & (others < candidate).any(axis=1)).any()
            efficient.append(not dominated)
        return pd.Series(efficient, index=objectives.index)
