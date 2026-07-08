"""Phase 4 experiment orchestration, reporting, and charts."""

from __future__ import annotations

from pathlib import Path
import os

import pandas as pd

from experiments.experiment_config import ExperimentConfig
from experiments.monte_carlo import MonteCarloRunner
from experiments.sensitivity_analysis import SensitivityAnalyzer
from experiments.statistical_analysis import StatisticalAnalyzer


class Phase4ExperimentRunner:
    """Runs Monte Carlo, statistical, and sensitivity analysis workflows."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "data"
        self.report_dir = self.project_root / "reports"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.config = ExperimentConfig(self.project_root / "config" / "experiment_config.yaml")

    def run_monte_carlo(self, runs: int | None = None, random_seed: int | None = None) -> pd.DataFrame:
        return MonteCarloRunner(self.config, self.data_dir).run(runs=runs, random_seed=random_seed)

    def run_statistical_analysis(self) -> pd.DataFrame:
        return StatisticalAnalyzer().analyze(
            self.data_dir / "phase4_experiment_results.csv",
            self.data_dir / "phase4_statistical_summary.csv",
        )

    def run_sensitivity_analysis(self) -> pd.DataFrame:
        return SensitivityAnalyzer().analyze(
            self.data_dir / "phase4_experiment_results.csv",
            self.data_dir / "phase4_sensitivity_results.csv",
        )

    def run_all(self) -> dict:
        results = self.run_monte_carlo()
        stats = self.run_statistical_analysis()
        sensitivity = self.run_sensitivity_analysis()
        metrics = self._build_metrics(results, stats, sensitivity)
        self._write_metrics(metrics)
        self._write_report(results, stats, sensitivity, metrics)
        self._create_charts(results, stats, sensitivity)
        return {
            "results": results,
            "statistics": stats,
            "sensitivity": sensitivity,
            "metrics": metrics,
            "report_path": self.report_dir / "phase4_report.txt",
            "metrics_path": self.report_dir / "phase4_metrics.csv",
        }

    def _build_metrics(self, results: pd.DataFrame, stats: pd.DataFrame, sensitivity: pd.DataFrame) -> dict:
        grouped = results.groupby("security_configuration").mean(numeric_only=True)
        best_security = grouped["attack_success_rate"].idxmin()
        best_load_spike = grouped["load_spike_kw"].idxmin()
        best_comfort = grouped["comfort_loss_degree_minutes"].idxmin()
        best_dr = grouped["demand_response_failure_rate"].idxmin()
        lowest_friction = grouped["total_operational_friction_score"].idxmin()
        lowest_false_positive = grouped["false_positive_rate"].idxmin()
        lowest_approval_delay = grouped["human_approval_delay_minutes"].idxmin()
        highest_availability = grouped["availability_rate"].idxmax()
        lowest_cost = grouped["security_operation_cost"].idxmin()
        best_balanced = grouped["balanced_objective_score"].idxmin()
        best_resilience = grouped["overall_resilience_score"].idxmax()
        top_load_spike = sensitivity[sensitivity["output_metric"] == "load_spike_kw"].sort_values("rank").iloc[0]

        return {
            "monte_carlo_runs": int(len(results)),
            "runs_per_configuration": self.config.runs_per_configuration,
            "random_seed": self.config.random_seed,
            "security_configurations_compared": int(results["security_configuration"].nunique()),
            "best_configuration_for_security": best_security,
            "best_configuration_for_load_spike_reduction": best_load_spike,
            "best_configuration_for_comfort": best_comfort,
            "best_configuration_for_demand_response_reliability": best_dr,
            "configuration_with_lowest_operational_friction": lowest_friction,
            "configuration_with_lowest_false_positives": lowest_false_positive,
            "configuration_with_lowest_approval_delay": lowest_approval_delay,
            "configuration_with_highest_availability": highest_availability,
            "configuration_with_lowest_security_operation_cost": lowest_cost,
            "best_balanced_configuration": best_balanced,
            "best_overall_resilience_configuration": best_resilience,
            "mean_attack_success_rate": round(float(results["attack_success_rate"].mean()), 4),
            "mean_load_spike_kw": round(float(results["load_spike_kw"].mean()), 4),
            "mean_comfort_loss_degree_minutes": round(float(results["comfort_loss_degree_minutes"].mean()), 4),
            "mean_demand_response_failure_rate": round(float(results["demand_response_failure_rate"].mean()), 4),
            "mean_total_operational_friction_score": round(
                float(results["total_operational_friction_score"].mean()),
                4,
            ),
            "top_load_spike_sensitivity_parameter": top_load_spike["input_parameter"],
            "top_load_spike_sensitivity_score": float(top_load_spike["sensitivity_score"]),
        }

    def _write_metrics(self, metrics: dict) -> None:
        results = pd.read_csv(self.data_dir / "phase4_experiment_results.csv")
        metric_columns = {
            "attack_success_rate": "attack_success_rate_mean",
            "demand_response_failure_rate": "demand_response_failure_rate_mean",
            "load_spike_kw": "load_spike_kw_mean",
            "comfort_loss_degree_minutes": "comfort_loss_degree_minutes_mean",
            "false_positive_rate": "false_positive_rate_mean",
            "legitimate_command_rejection_rate": "legitimate_command_rejection_rate_mean",
            "human_approval_delay_minutes": "human_approval_delay_minutes_mean",
            "availability_rate": "availability_rate_mean",
            "total_operational_friction_score": "total_operational_friction_score_mean",
            "security_operation_cost": "security_operation_cost_mean",
            "balanced_objective_score": "balanced_objective_score_mean",
            "overall_resilience_score": "overall_resilience_score_mean",
        }
        config_metrics = (
            results.groupby("security_configuration")[list(metric_columns.keys())]
            .mean()
            .rename(columns=metric_columns)
            .round(4)
            .reset_index()
        )
        config_metrics.to_csv(self.report_dir / "phase4_metrics.csv", index=False)

    def _write_report(
        self,
        results: pd.DataFrame,
        stats: pd.DataFrame,
        sensitivity: pd.DataFrame,
        metrics: dict,
    ) -> None:
        lines = [
            "AI-Assisted Demand Response Cyber-Resilience Simulator",
            "Phase 4 Report",
            "",
            "Purpose:",
            "Phase 4 runs repeated safe internal simulations to compare security configurations and identify which cyber-physical parameters most affect attack success, demand-response failure, comfort loss, load spike, and recovery.",
            "",
            "Monte Carlo Setup:",
            f"- Runs per configuration: {metrics['runs_per_configuration']}",
            f"- Total runs: {metrics['monte_carlo_runs']}",
            f"- Random seed: {metrics['random_seed']}",
            f"Security configurations compared: {', '.join(sorted(results['security_configuration'].unique()))}",
            "",
            "Security Performance:",
            f"- Best configuration for attack reduction: {metrics['best_configuration_for_security']}",
            f"- Best configuration for demand-response reliability: {metrics['best_configuration_for_demand_response_reliability']}",
            f"- Best configuration for load spike reduction: {metrics['best_configuration_for_load_spike_reduction']}",
            f"- Best configuration for comfort protection: {metrics['best_configuration_for_comfort']}",
            "",
            "Operational Drawbacks:",
            f"- Lowest operational friction: {metrics['configuration_with_lowest_operational_friction']}",
            f"- Lowest false positives: {metrics['configuration_with_lowest_false_positives']}",
            f"- Lowest approval delay: {metrics['configuration_with_lowest_approval_delay']}",
            f"- Highest availability: {metrics['configuration_with_highest_availability']}",
            f"- Lowest security operation cost: {metrics['configuration_with_lowest_security_operation_cost']}",
            "",
            "Balanced Conclusion:",
            f"- Best security-focused configuration: {metrics['best_configuration_for_security']}",
            f"- Best operationally efficient configuration: {metrics['configuration_with_lowest_operational_friction']}",
            f"- Best balanced configuration: {metrics['best_balanced_configuration']}",
            "",
            "Mean Results by Configuration:",
        ]

        mean_table = (
            results.groupby("security_configuration")[
                [
                    "attack_success_rate",
                    "load_spike_kw",
                    "comfort_loss_degree_minutes",
                    "demand_response_failure_rate",
                    "devices_recovered",
                    "false_positive_rate",
                    "legitimate_command_rejection_rate",
                    "human_approval_delay_minutes",
                    "availability_rate",
                    "security_operation_cost",
                    "total_operational_friction_score",
                    "balanced_objective_score",
                    "overall_resilience_score",
                ]
            ]
            .mean()
            .round(4)
        )
        lines.extend(mean_table.to_string().splitlines())

        lines.extend(["", "Sensitivity Ranking for Load Spike:"])
        load_sensitivity = sensitivity[sensitivity["output_metric"] == "load_spike_kw"].sort_values("rank").head(5)
        for _, row in load_sensitivity.iterrows():
            lines.append(f"{int(row['rank'])}. {row['input_parameter']} ({row['sensitivity_score']})")

        lines.extend(["", "Sensitivity Ranking for Comfort Loss:"])
        comfort_sensitivity = sensitivity[
            sensitivity["output_metric"] == "comfort_loss_degree_minutes"
        ].sort_values("rank").head(5)
        for _, row in comfort_sensitivity.iterrows():
            lines.append(f"{int(row['rank'])}. {row['input_parameter']} ({row['sensitivity_score']})")

        lines.extend(["", "Sensitivity Ranking for Demand-Response Failure:"])
        dr_sensitivity = sensitivity[
            sensitivity["output_metric"] == "demand_response_failure_rate"
        ].sort_values("rank").head(5)
        for _, row in dr_sensitivity.iterrows():
            lines.append(f"{int(row['rank'])}. {row['input_parameter']} ({row['sensitivity_score']})")

        lines.extend(["", "Sensitivity Ranking for Operational Friction:"])
        friction_sensitivity = sensitivity[
            sensitivity["output_metric"] == "total_operational_friction_score"
        ].sort_values("rank").head(5)
        for _, row in friction_sensitivity.iterrows():
            lines.append(f"{int(row['rank'])}. {row['input_parameter']} ({row['sensitivity_score']})")

        lines.extend(["", "Sensitivity Interpretation Caution:"])
        lines.append(SensitivityAnalyzer.interpretation_note)

        lines.extend(
            [
                "",
                "Interpretation:",
                "- Lower attack success and load spike generally come from layered controls: firmware validation, quarantine, recovery, and stricter approval thresholds.",
                "- Stronger configurations can also increase approval burden, false positives, latency, firmware-update delay, monitoring overhead, and security operation cost.",
                "- The strongest cybersecurity profile is not automatically best overall; the balanced winner depends on the objective weights and operational constraints.",
                "- Results are generated by a simplified academic simulation, not real device control or grid power-flow analysis.",
                "",
                "Output datasets:",
                "- data/phase4_experiment_results.csv",
                "- data/phase4_statistical_summary.csv",
                "- data/phase4_sensitivity_results.csv",
            ]
        )

        (self.report_dir / "phase4_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _create_charts(self, results: pd.DataFrame, stats: pd.DataFrame, sensitivity: pd.DataFrame) -> None:
        matplotlib_config_dir = self.project_root.parent.parent / "work" / "matplotlib_cache"
        matplotlib_config_dir.mkdir(parents=True, exist_ok=True)
        os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_config_dir))

        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.figure(figsize=(8, 5))
        plt.hist(results["attack_success_rate"], bins=15, color="#4c78a8", edgecolor="white")
        plt.title("Attack Success Rate Distribution")
        plt.xlabel("Attack success rate")
        plt.ylabel("Run count")
        plt.tight_layout()
        plt.savefig(self.report_dir / "phase4_attack_success_distribution.png")
        plt.close()

        top_sensitivity = sensitivity[sensitivity["output_metric"] == "load_spike_kw"].sort_values("rank").head(8)
        plt.figure(figsize=(9, 5))
        plt.barh(top_sensitivity["input_parameter"], top_sensitivity["sensitivity_score"], color="#f58518")
        plt.gca().invert_yaxis()
        plt.title("Sensitivity Tornado: Load Spike")
        plt.xlabel("Sensitivity score")
        plt.tight_layout()
        plt.savefig(self.report_dir / "phase4_sensitivity_tornado.png")
        plt.close()

        comparison = results.groupby("security_configuration")[
            ["attack_success_rate", "demand_response_failure_rate", "total_operational_friction_score"]
        ].mean()
        comparison.plot(kind="bar", figsize=(9, 5))
        plt.title("Security Configuration Comparison")
        plt.ylabel("Mean rate")
        plt.xticks(rotation=25, ha="right")
        plt.tight_layout()
        plt.savefig(self.report_dir / "phase4_config_comparison.png")
        plt.close()

        configs = sorted(results["security_configuration"].unique())
        box_data = [
            results[results["security_configuration"] == config]["demand_response_failure_rate"]
            for config in configs
        ]
        plt.figure(figsize=(9, 5))
        plt.boxplot(box_data, tick_labels=configs)
        plt.title("Demand-Response Failure by Configuration")
        plt.ylabel("Failure rate")
        plt.xticks(rotation=25, ha="right")
        plt.tight_layout()
        plt.savefig(self.report_dir / "phase4_dr_failure_boxplot.png")
        plt.close()

        tradeoff = results.groupby("security_configuration")[
            ["operational_friction_score", "security_risk_score"]
        ].mean()
        plt.figure(figsize=(8, 5))
        plt.scatter(tradeoff["operational_friction_score"], tradeoff["security_risk_score"], color="#54a24b")
        for config, row in tradeoff.iterrows():
            plt.annotate(config, (row["operational_friction_score"], row["security_risk_score"]))
        plt.title("Security Risk vs Operational Friction")
        plt.xlabel("Mean operational friction score")
        plt.ylabel("Mean security risk score")
        plt.tight_layout()
        plt.savefig(self.report_dir / "phase4_security_vs_operational_friction.png")
        plt.close()

        balanced = results.groupby("security_configuration")["balanced_objective_score"].mean().sort_values()
        plt.figure(figsize=(9, 5))
        plt.bar(balanced.index, balanced.values, color="#b279a2")
        plt.title("Balanced Objective by Configuration")
        plt.ylabel("Mean balanced objective score")
        plt.xticks(rotation=25, ha="right")
        plt.tight_layout()
        plt.savefig(self.report_dir / "phase4_balanced_objective_by_config.png")
        plt.close()

        false_positive = results.groupby("security_configuration")["false_positive_rate"].mean().sort_values()
        plt.figure(figsize=(9, 5))
        plt.bar(false_positive.index, false_positive.values, color="#e45756")
        plt.title("False Positive Rate by Configuration")
        plt.ylabel("Mean false positive rate")
        plt.xticks(rotation=25, ha="right")
        plt.tight_layout()
        plt.savefig(self.report_dir / "phase4_false_positive_by_config.png")
        plt.close()

        approval_delay = results.groupby("security_configuration")["human_approval_delay_minutes"].mean().sort_values()
        plt.figure(figsize=(9, 5))
        plt.bar(approval_delay.index, approval_delay.values, color="#72b7b2")
        plt.title("Approval Delay by Configuration")
        plt.ylabel("Mean approval delay (minutes)")
        plt.xticks(rotation=25, ha="right")
        plt.tight_layout()
        plt.savefig(self.report_dir / "phase4_approval_delay_by_config.png")
        plt.close()
