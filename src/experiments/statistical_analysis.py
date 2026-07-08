"""Statistical analysis for Phase 4 experiment outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class StatisticalAnalyzer:
    """Builds research-style summary statistics by security configuration."""

    outcome_metrics = [
        # Cybersecurity
        "attack_success_rate",
        "compromised_devices",
        "devices_recovered",
        # Power and demand response
        "load_spike_kw",
        "demand_response_failure_rate",
        "total_energy_kwh",
        # Comfort
        "comfort_loss_degree_minutes",
        # Operational drawbacks
        "human_approval_requests",
        "human_approval_delay_minutes",
        "average_command_latency_ms",
        "false_positive_rate",
        "legitimate_command_rejection_rate",
        "firmware_update_delay_minutes",
        "quarantine_availability_loss",
        "availability_rate",
        "operator_workload_score",
        "security_operation_cost",
        "total_operational_friction_score",
        # Composite
        "security_risk_score",
        "operational_friction_score",
        "availability_loss_score",
        "balanced_objective_score",
        "overall_resilience_score",
    ]

    def analyze(self, results_path: str | Path, output_path: str | Path) -> pd.DataFrame:
        results = pd.read_csv(results_path)
        rows: list[dict] = []

        for configuration, group in results.groupby("security_configuration"):
            for metric in self.outcome_metrics:
                series = group[metric].astype(float)
                count = int(series.count())
                mean = float(series.mean())
                std = float(series.std(ddof=1)) if count > 1 else 0.0
                ci_margin = 1.96 * std / (count ** 0.5) if count > 1 else 0.0
                rows.append(
                    {
                        "security_configuration": configuration,
                        "metric": metric,
                        "count": count,
                        "mean": round(mean, 4),
                        "median": round(float(series.median()), 4),
                        "standard_deviation": round(std, 4),
                        "min": round(float(series.min()), 4),
                        "max": round(float(series.max()), 4),
                        "95_percent_confidence_interval_lower": round(mean - ci_margin, 4),
                        "95_percent_confidence_interval_upper": round(mean + ci_margin, 4),
                    }
                )

        summary = pd.DataFrame(rows)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(output_path, index=False)
        return summary
