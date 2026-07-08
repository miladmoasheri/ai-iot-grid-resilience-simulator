"""Recommendation generation for Phase 5."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml


class RecommendationEngine:
    """Selects recommended configurations from optimization results."""

    def __init__(
        self,
        optimization_results_path: str | Path,
        config_path: str | Path,
        data_dir: str | Path,
        report_dir: str | Path,
    ):
        self.optimization_results_path = Path(optimization_results_path)
        self.config_path = Path(config_path)
        self.data_dir = Path(data_dir)
        self.report_dir = Path(report_dir)

    def generate(self) -> pd.DataFrame:
        optimization = pd.read_csv(self.optimization_results_path)
        config = self._load_config()
        constraints = config["recommendation"]
        rows = []

        profile_labels = {
            "security_focused": "best_security_focused_configuration",
            "operations_focused": "best_operations_focused_configuration",
            "balanced": "best_balanced_configuration",
        }
        for profile, category in profile_labels.items():
            best = optimization[optimization["weighting_profile"] == profile].sort_values("rank").iloc[0]
            constraints_met, violations = self._check_constraints(best, constraints)
            reason = "Lowest weighted objective score for this profile."
            if not constraints_met:
                reason += f" Does not satisfy feasibility constraints: {', '.join(violations)}."
            rows.append(self._row(category, best, constraints_met, reason))

        balanced_pool = optimization[optimization["weighting_profile"] == "balanced"].copy()
        balanced_pool["constraints_met"] = balanced_pool.apply(
            lambda row: self._check_constraints(row, constraints)[0],
            axis=1,
        )
        feasible_pool = balanced_pool[balanced_pool["constraints_met"]].sort_values("mean_weighted_objective_score")

        if feasible_pool.empty:
            fallback = optimization[optimization["weighting_profile"] == "balanced"].sort_values("rank").iloc[0]
            rows.append(
                self._row(
                    "best_feasible_configuration",
                    fallback,
                    False,
                    "No configuration satisfied all feasibility constraints; showing the best balanced fallback.",
                )
            )
        else:
            rows.append(
                self._row(
                    "best_feasible_configuration",
                    feasible_pool.iloc[0],
                    True,
                    "Lowest balanced score among configurations satisfying availability, attack, and DR constraints.",
                )
            )

        recommendations = pd.DataFrame(rows)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        recommendations.to_csv(self.data_dir / "phase5_recommendations.csv", index=False)
        self._write_report(recommendations, constraints)
        return recommendations

    def _load_config(self) -> dict:
        with self.config_path.open("r", encoding="utf-8") as config_file:
            return yaml.safe_load(config_file)

    def _row(self, category: str, result: pd.Series, constraints_met: bool, reason: str) -> dict:
        return {
            "recommendation_category": category,
            "weighting_profile": result["weighting_profile"],
            "security_configuration": result["security_configuration"],
            "mean_weighted_objective_score": round(float(result["mean_weighted_objective_score"]), 6),
            "mean_attack_success_rate": round(float(result["mean_attack_success_rate"]), 6),
            "mean_demand_response_failure_rate": round(float(result["mean_demand_response_failure_rate"]), 6),
            "mean_availability_rate": round(float(result["mean_availability_rate"]), 6),
            "constraints_met": constraints_met,
            "reason": reason,
        }

    def _check_constraints(self, result: pd.Series, constraints: dict) -> tuple[bool, list[str]]:
        violations = []
        availability_threshold = float(constraints["require_availability_above"])
        attack_threshold = float(constraints["require_attack_success_below"])
        dr_threshold = float(constraints["require_demand_response_failure_below"])

        availability_rate = float(result["mean_availability_rate"])
        attack_success_rate = float(result["mean_attack_success_rate"])
        dr_failure_rate = float(result["mean_demand_response_failure_rate"])

        if availability_rate < availability_threshold:
            violations.append(f"availability {availability_rate:.4f} < {availability_threshold:.4f}")
        if attack_success_rate > attack_threshold:
            violations.append(f"attack success {attack_success_rate:.4f} > {attack_threshold:.4f}")
        if dr_failure_rate > dr_threshold:
            violations.append(f"DR failure {dr_failure_rate:.4f} > {dr_threshold:.4f}")
        return len(violations) == 0, violations

    def _write_report(self, recommendations: pd.DataFrame, constraints: dict) -> None:
        lines = [
            "Phase 5 Recommendations",
            "",
            "Feasibility constraints:",
            f"- Availability rate >= {constraints['require_availability_above']}",
            f"- Attack success rate <= {constraints['require_attack_success_below']}",
            f"- Demand-response failure rate <= {constraints['require_demand_response_failure_below']}",
            "",
        ]
        for _, row in recommendations.iterrows():
            lines.extend(
                [
                    f"{row['recommendation_category']}:",
                    f"- Configuration: {row['security_configuration']}",
                    f"- Weighting profile: {row['weighting_profile']}",
                    f"- Mean weighted objective score: {row['mean_weighted_objective_score']}",
                    f"- Mean attack success rate: {row['mean_attack_success_rate']}",
                    f"- Mean demand-response failure rate: {row['mean_demand_response_failure_rate']}",
                    f"- Mean availability rate: {row['mean_availability_rate']}",
                    f"- Constraints met: {row['constraints_met']}",
                    f"- Reason: {row['reason']}",
                    "",
                ]
            )
        lines.extend(
            [
                "Interpretation:",
                "These recommendations are simulation-based decision support. They depend on the chosen weights, constraints, and simplified model assumptions.",
            ]
        )
        (self.report_dir / "phase5_recommendations.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
