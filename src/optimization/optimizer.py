"""Phase 5 optimization workflow."""

from __future__ import annotations

from pathlib import Path
import os

import pandas as pd
import yaml

from optimization.objective_functions import ObjectiveFunctionCalculator
from optimization.pareto_analysis import ParetoAnalyzer
from optimization.recommendation_engine import RecommendationEngine


class OptimizationRunner:
    """Runs objective scoring, grid-search ranking, Pareto analysis, and reports."""

    optimization_columns = [
        "weighted_objective_score",
        "security_risk_score",
        "power_impact_score",
        "comfort_impact_score",
        "demand_response_failure_score",
        "operational_friction_score",
        "availability_loss_score",
        "attack_success_rate",
        "demand_response_failure_rate",
        "availability_rate",
    ]

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.config_path = self.project_root / "config" / "optimization_config.yaml"
        self.phase4_results_path = self.project_root / "data" / "phase4_experiment_results.csv"
        self.data_dir = self.project_root / "data"
        self.report_dir = self.project_root / "reports"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()

    def run_optimization(self) -> pd.DataFrame:
        self._ensure_phase4_results()
        rows = []
        calculator = ObjectiveFunctionCalculator(self.phase4_results_path)
        for profile, weights in self.config["objective_weights"].items():
            scored = calculator.calculate_scores(weights, profile)
            grouped = scored.groupby("security_configuration")[self.optimization_columns].mean().reset_index()
            grouped["weighting_profile"] = profile
            grouped = grouped.rename(
                columns={
                    "weighted_objective_score": "mean_weighted_objective_score",
                    "security_risk_score": "mean_security_risk_score",
                    "power_impact_score": "mean_power_impact_score",
                    "comfort_impact_score": "mean_comfort_impact_score",
                    "demand_response_failure_score": "mean_demand_response_failure_score",
                    "operational_friction_score": "mean_operational_friction_score",
                    "availability_loss_score": "mean_availability_loss_score",
                    "attack_success_rate": "mean_attack_success_rate",
                    "demand_response_failure_rate": "mean_demand_response_failure_rate",
                    "availability_rate": "mean_availability_rate",
                }
            )
            grouped["rank"] = grouped["mean_weighted_objective_score"].rank(method="first").astype(int)
            rows.append(grouped)

        optimization = pd.concat(rows, ignore_index=True)
        column_order = [
            "weighting_profile",
            "security_configuration",
            "mean_weighted_objective_score",
            "mean_security_risk_score",
            "mean_power_impact_score",
            "mean_comfort_impact_score",
            "mean_demand_response_failure_score",
            "mean_operational_friction_score",
            "mean_availability_loss_score",
            "mean_attack_success_rate",
            "mean_demand_response_failure_rate",
            "mean_availability_rate",
            "rank",
        ]
        optimization = optimization[column_order].sort_values(["weighting_profile", "rank"])
        optimization.to_csv(self.data_dir / "phase5_optimization_results.csv", index=False)
        return optimization

    def run_pareto(self) -> pd.DataFrame:
        self._ensure_phase4_results()
        weights = self.config["objective_weights"]["balanced"]
        return ParetoAnalyzer(
            self.phase4_results_path,
            self.data_dir / "phase5_pareto_results.csv",
        ).analyze(weights)

    def run_recommendations(self) -> pd.DataFrame:
        optimization_path = self.data_dir / "phase5_optimization_results.csv"
        if not optimization_path.exists():
            self.run_optimization()
        return RecommendationEngine(
            optimization_path,
            self.config_path,
            self.data_dir,
            self.report_dir,
        ).generate()

    def run_all(self) -> dict:
        optimization = self.run_optimization()
        pareto = self.run_pareto()
        recommendations = self.run_recommendations()
        metrics = self._build_metrics(optimization, pareto, recommendations)
        self._write_report(optimization, pareto, recommendations)
        self._write_mathematical_model_files()
        self._create_charts(optimization, pareto, recommendations)
        return {
            "optimization": optimization,
            "pareto": pareto,
            "recommendations": recommendations,
            "metrics": metrics,
            "report_path": self.report_dir / "phase5_report.txt",
            "metrics_path": self.data_dir / "phase5_optimization_results.csv",
        }

    def _load_config(self) -> dict:
        with self.config_path.open("r", encoding="utf-8") as config_file:
            return yaml.safe_load(config_file)

    def _ensure_phase4_results(self) -> None:
        if self.phase4_results_path.exists():
            return
        from experiments.experiment_runner import Phase4ExperimentRunner

        Phase4ExperimentRunner(self.project_root).run_all()

    def _build_metrics(
        self,
        optimization: pd.DataFrame,
        pareto: pd.DataFrame,
        recommendations: pd.DataFrame,
    ) -> dict:
        return {
            "weighting_profiles": int(optimization["weighting_profile"].nunique()),
            "security_configurations_ranked": int(optimization["security_configuration"].nunique()),
            "pareto_efficient_points": int(pareto["is_pareto_efficient"].sum()),
            "recommendation_categories": int(recommendations["recommendation_category"].nunique()),
            "best_balanced_configuration": recommendations[
                recommendations["recommendation_category"] == "best_balanced_configuration"
            ]["security_configuration"].iloc[0],
        }

    def _write_report(
        self,
        optimization: pd.DataFrame,
        pareto: pd.DataFrame,
        recommendations: pd.DataFrame,
    ) -> None:
        lines = [
            "AI-Assisted Demand Response Cyber-Resilience Simulator",
            "Phase 5 Report",
            "",
            "Purpose:",
            "Phase 5 adds simulation-based decision support. It uses Phase 4 experiment results to identify cyber-resilience configurations that perform best under different objective weights.",
            "",
            "Safety Scope:",
            "This is a simulation-based decision-support model. All attack, firmware, backdoor, AI-assistant, and power-system behavior remains internal simulation state and generated metrics only.",
            "",
            "Optimization Method:",
            f"- Method: {self.config['optimization']['method']}",
            "- Source data: data/phase4_experiment_results.csv",
            "- Lower weighted objective scores are better.",
            "",
            "Formal Operations Research Model:",
        ]
        lines.extend(self._formal_model_lines())
        lines.extend(
            [
                "",
            "Objective Weights:",
            ]
        )
        for profile, weights in self.config["objective_weights"].items():
            weight_text = ", ".join(f"{key}={value}" for key, value in weights.items())
            lines.append(f"- {profile}: {weight_text}")

        lines.extend(["", "Best Configuration by Weighting Profile:"])
        best_rows = optimization.sort_values("rank").groupby("weighting_profile").first().reset_index()
        for _, row in best_rows.iterrows():
            lines.append(
                f"- {row['weighting_profile']}: {row['security_configuration']} "
                f"(mean score {row['mean_weighted_objective_score']:.4f})"
            )

        lines.extend(["", "Optimization Results:"])
        table = optimization[
            [
                "weighting_profile",
                "security_configuration",
                "mean_weighted_objective_score",
                "mean_attack_success_rate",
                "mean_demand_response_failure_rate",
                "mean_availability_rate",
                "rank",
            ]
        ].round(4)
        lines.extend(table.to_string(index=False).splitlines())

        lines.extend(
            [
                "",
                "Pareto Analysis Summary:",
                f"- Pareto-efficient experiment points: {int(pareto['is_pareto_efficient'].sum())}",
                "- Trade-off pairs evaluated: security risk vs operational friction, power impact vs comfort impact, and security risk vs availability loss.",
                "",
                "Recommendation Summary:",
            ]
        )
        for _, row in recommendations.iterrows():
            lines.append(
                f"- {row['recommendation_category']}: {row['security_configuration']} "
                f"(constraints met: {row['constraints_met']}; attack={row['mean_attack_success_rate']}, "
                f"DR failure={row['mean_demand_response_failure_rate']}, availability={row['mean_availability_rate']})"
            )
            lines.append(f"  Reason: {row['reason']}")

        lines.extend(
            [
                "",
                "Trade-off Interpretation:",
                "- Security-focused weights favor configurations that reduce attack success and demand-response disruption, even when operational friction increases.",
                "- Operations-focused weights favor lower approval burden, lower false positives, and higher availability, which may accept more residual security risk. A configuration can win under operations-focused weights while still failing feasibility constraints.",
                "- Balanced weights seek a compromise across cyber risk, power stability, comfort, demand-response reliability, friction, and availability.",
                "- The optimization is not only a dashboard or scoring tool; it is a simulation-driven binary decision model where the simulation provides parameter values and the model selects a configuration.",
                "- Future extension: The model can be extended into a time-indexed scheduling formulation where x_{c,t} selects a security configuration c for each time period t, allowing different profiles for business hours, weekends, maintenance windows, demand-response events, and active-attack conditions.",
                "",
                "Limitations:",
                "- The optimization results depend on chosen weights and simplified assumptions.",
                "- The results should not be interpreted as universal security truth.",
                "- A real deployment would require real device data, power-system validation, and operational stakeholder input.",
            ]
        )
        (self.report_dir / "phase5_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _formal_model_lines(self) -> list[str]:
        configurations = ", ".join(sorted(pd.read_csv(self.phase4_results_path)["security_configuration"].unique()))
        profiles = ", ".join(self.config["objective_weights"].keys())
        return [
            "",
            "Sets:",
            "- C = set of candidate security configurations.",
            f"- Example C = {{{configurations}}}.",
            "- K = set of weighting profiles.",
            f"- Example K = {{{profiles}}}.",
            "- M = set of evaluation metrics.",
            "",
            "Parameters:",
            "- AttackSuccess_c = mean attack success rate for configuration c.",
            "- DRFailure_c = mean demand-response failure rate for configuration c.",
            "- Availability_c = mean availability rate for configuration c.",
            "- SecurityRisk_c = normalized cybersecurity risk score for configuration c.",
            "- PowerImpact_c = normalized load/power impact score for configuration c.",
            "- ComfortImpact_c = normalized comfort-loss score for configuration c.",
            "- OperationalFriction_c = normalized operational friction score for configuration c.",
            "- AvailabilityLoss_c = normalized availability-loss score for configuration c.",
            "- SecurityCost_c = simulated security operation cost for configuration c.",
            "- w_m,k = weight of metric m under weighting profile k.",
            "",
            "Decision variables:",
            "- x_c = 1 if security configuration c is selected.",
            "- x_c = 0 otherwise.",
            "",
            "Objective function:",
            "For each weighting profile k, minimize Z_k:",
            "Z_k = sum over c in C of x_c [w_security,k * SecurityRisk_c + w_power,k * PowerImpact_c + w_comfort,k * ComfortImpact_c + w_dr,k * DRFailure_c + w_friction,k * OperationalFriction_c + w_availability,k * AvailabilityLoss_c].",
            "Lower Z_k is better.",
            "",
            "Constraints:",
            "- Select exactly one configuration: sum over c in C of x_c = 1.",
            "- Attack success threshold: sum over c in C of x_c * AttackSuccess_c <= 0.10.",
            "- Demand-response failure threshold: sum over c in C of x_c * DRFailure_c <= 0.10.",
            "- Availability threshold: sum over c in C of x_c * Availability_c >= 0.95.",
            "- Optional operational-friction constraint: sum over c in C of x_c * OperationalFriction_c <= F_max.",
            "- Optional security-cost constraint: sum over c in C of x_c * SecurityCost_c <= B.",
            "- Binary decision constraint: x_c in {0,1}.",
            "",
            "Interpretation:",
            "This is a binary configuration-selection optimization model. The simulation provides the parameter values, and the optimization chooses the best feasible security configuration under different decision-maker priorities.",
        ]

    def _write_mathematical_model_files(self) -> None:
        markdown_lines = [
            "# Phase 5 Mathematical Optimization Model",
            "",
            "This standalone formulation documents the Operations Research model used by Phase 5. It remains a safe academic simulation model only; all cyber and power-system behavior is represented through generated simulation metrics.",
        ]
        markdown_lines.extend(self._formal_model_lines())
        markdown_lines.extend(
            [
                "",
                "Link to simulation outputs:",
                "- `data/phase4_experiment_results.csv` provides simulation-derived parameter estimates.",
                "- `data/phase5_optimization_results.csv` reports objective values and ranks.",
                "- `data/phase5_recommendations.csv` reports profile winners and feasibility status.",
                "",
                "Limitations:",
                "- The selected configuration depends on simulated data, objective weights, and feasibility thresholds.",
                "- The model is not a universal cybersecurity truth or a real deployment policy.",
                "- Real use would require validated device data, power-system validation, and stakeholder review.",
                "",
                "Future extension: The model can be extended into a time-indexed scheduling formulation where x_{c,t} selects a security configuration c for each time period t, allowing different profiles for business hours, weekends, maintenance windows, demand-response events, and active-attack conditions.",
            ]
        )
        (self.report_dir / "phase5_mathematical_model.md").write_text(
            "\n".join(markdown_lines) + "\n",
            encoding="utf-8",
        )

        latex_lines = [
            "Phase 5 Mathematical Optimization Model - LaTeX-Friendly Formulation",
            "",
            "Sets:",
            "C = candidate security configurations",
            "K = weighting profiles",
            "M = evaluation metrics",
            "",
            "Decision variable:",
            "x_c \\in \\{0,1\\}",
            "",
            "Objective function for each weighting profile k \\in K:",
            "\\min Z_k = \\sum_{c \\in C} x_c \\left(",
            "w^{k}_{sec} R_c +",
            "w^{k}_{pow} P_c +",
            "w^{k}_{com} H_c +",
            "w^{k}_{dr} D_c +",
            "w^{k}_{op} O_c +",
            "w^{k}_{av} L_c",
            "\\right)",
            "",
            "Subject to:",
            "\\sum_{c \\in C} x_c = 1",
            "\\sum_{c \\in C} x_c A_c \\leq A^{max}",
            "\\sum_{c \\in C} x_c D_c \\leq D^{max}",
            "\\sum_{c \\in C} x_c V_c \\geq V^{min}",
            "\\sum_{c \\in C} x_c O_c \\leq F^{max} \\quad \\text{optional}",
            "\\sum_{c \\in C} x_c S_c \\leq B \\quad \\text{optional}",
            "x_c \\in \\{0,1\\} \\quad \\forall c \\in C",
            "",
            "Where:",
            "R_c = security risk score",
            "P_c = power impact score",
            "H_c = comfort impact score",
            "D_c = demand-response failure rate",
            "O_c = operational friction score",
            "L_c = availability loss score",
            "A_c = attack success rate",
            "V_c = availability rate",
            "S_c = simulated security operation cost",
            "",
            "Future extension: x_{c,t} can select configuration c for each time period t.",
        ]
        (self.report_dir / "phase5_mathematical_model_latex.txt").write_text(
            "\n".join(latex_lines) + "\n",
            encoding="utf-8",
        )

    def _create_charts(
        self,
        optimization: pd.DataFrame,
        pareto: pd.DataFrame,
        recommendations: pd.DataFrame,
    ) -> None:
        matplotlib_config_dir = self.project_root.parent.parent / "work" / "matplotlib_cache"
        matplotlib_config_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_config_dir))

        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        pivot = optimization.pivot(
            index="security_configuration",
            columns="weighting_profile",
            values="mean_weighted_objective_score",
        )
        pivot.plot(kind="bar", figsize=(10, 5))
        plt.title("Weighted Objective Score by Profile")
        plt.ylabel("Mean weighted objective score")
        plt.xticks(rotation=25, ha="right")
        plt.tight_layout()
        plt.savefig(self.report_dir / "phase5_weighted_objective_by_profile.png")
        plt.close()

        self._scatter_pareto(
            pareto,
            x_column="operational_friction_score",
            y_column="security_risk_score",
            title="Pareto Trade-off: Security Risk vs Operational Friction",
            output_name="phase5_pareto_security_vs_friction.png",
        )
        self._scatter_pareto(
            pareto,
            x_column="comfort_impact_score",
            y_column="power_impact_score",
            title="Pareto Trade-off: Power Impact vs Comfort Impact",
            output_name="phase5_pareto_power_vs_comfort.png",
        )

        best = optimization.sort_values("rank").groupby("weighting_profile").first().reset_index()
        plt.figure(figsize=(8, 5))
        plt.bar(best["weighting_profile"], best["mean_weighted_objective_score"], color="#54a24b")
        for index, row in best.iterrows():
            plt.text(index, row["mean_weighted_objective_score"], row["security_configuration"], ha="center", va="bottom")
        plt.title("Recommendation Summary by Weighting Profile")
        plt.ylabel("Best mean weighted score")
        plt.xticks(rotation=15, ha="right")
        plt.tight_layout()
        plt.savefig(self.report_dir / "phase5_recommendation_summary.png")
        plt.close()

    def _scatter_pareto(
        self,
        pareto: pd.DataFrame,
        x_column: str,
        y_column: str,
        title: str,
        output_name: str,
    ) -> None:
        import matplotlib.pyplot as plt

        plt.figure(figsize=(8, 5))
        for config, frame in pareto.groupby("security_configuration"):
            plt.scatter(frame[x_column], frame[y_column], s=18, alpha=0.45, label=config)
        efficient = pareto[pareto["is_pareto_efficient"]]
        plt.scatter(efficient[x_column], efficient[y_column], s=55, facecolors="none", edgecolors="black", label="Pareto")
        plt.title(title)
        plt.xlabel(x_column.replace("_", " "))
        plt.ylabel(y_column.replace("_", " "))
        plt.legend(fontsize=8)
        plt.tight_layout()
        plt.savefig(self.report_dir / output_name)
        plt.close()
