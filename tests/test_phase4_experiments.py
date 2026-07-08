from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
WORK_ROOT = PROJECT_ROOT.parents[1] / "work" / "phase4_test_outputs"

from experiments.experiment_config import ExperimentConfig
from experiments.experiment_runner import Phase4ExperimentRunner
from experiments.monte_carlo import MonteCarloRunner
from experiments.sensitivity_analysis import SensitivityAnalyzer
from experiments.statistical_analysis import StatisticalAnalyzer


def phase4_test_output_dir(name: str) -> Path:
    path = WORK_ROOT / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_experiment_config_loads_correctly():
    config = ExperimentConfig(PROJECT_ROOT / "config" / "experiment_config.yaml")

    assert config.runs_per_configuration == 250
    assert config.runs == 1000
    assert config.random_seed == 42
    assert "adaptive_resilience" in config.security_configuration_names


def test_monte_carlo_uses_balanced_sampling_per_configuration():
    config = ExperimentConfig(PROJECT_ROOT / "config" / "experiment_config.yaml")
    output_dir = phase4_test_output_dir("row_count")
    results = MonteCarloRunner(config, output_dir).run(runs_per_configuration=12, random_seed=7)

    assert len(results) == 12 * len(config.security_configuration_names)
    assert results.groupby("security_configuration").size().eq(12).all()
    assert (output_dir / "phase4_experiment_results.csv").exists()
    assert "load_spike_kw" in results.columns


def test_random_seed_makes_results_reproducible():
    config = ExperimentConfig(PROJECT_ROOT / "config" / "experiment_config.yaml")
    output_dir = phase4_test_output_dir("reproducible")
    first = MonteCarloRunner(config, output_dir / "first").run(runs_per_configuration=10, random_seed=99)
    second = MonteCarloRunner(config, output_dir / "second").run(runs_per_configuration=10, random_seed=99)

    pd.testing.assert_frame_equal(first, second)


def test_statistical_summary_contains_required_metrics():
    config = ExperimentConfig(PROJECT_ROOT / "config" / "experiment_config.yaml")
    output_dir = phase4_test_output_dir("stats")
    results = MonteCarloRunner(config, output_dir).run(runs_per_configuration=20, random_seed=5)
    results_path = output_dir / "phase4_experiment_results.csv"
    summary = StatisticalAnalyzer().analyze(results_path, output_dir / "phase4_statistical_summary.csv")

    assert "attack_success_rate" in set(summary["metric"])
    assert "total_operational_friction_score" in set(summary["metric"])
    assert "95_percent_confidence_interval_lower" in summary.columns
    assert "95_percent_confidence_interval_upper" in summary.columns


def test_confidence_interval_calculation_works():
    output_dir = phase4_test_output_dir("confidence_interval")
    rows = []
    for value in [0.1, 0.2, 0.3, 0.4]:
        rows.append(
            {
                "security_configuration": "weak_baseline",
                "attack_success_rate": value,
                "load_spike_kw": value * 10,
                "comfort_loss_degree_minutes": value * 100,
                "demand_response_failure_rate": value,
                "total_energy_kwh": value * 1000,
                "compromised_devices": value * 10,
                "devices_recovered": value,
                "human_approval_requests": value,
                "human_approval_delay_minutes": value,
                "average_command_latency_ms": value,
                "false_positive_rate": value,
                "legitimate_command_rejection_rate": value,
                "firmware_update_delay_minutes": value,
                "quarantine_availability_loss": value,
                "availability_rate": 1 - value,
                "operator_workload_score": value,
                "security_operation_cost": value,
                "total_operational_friction_score": value,
                "security_risk_score": value,
                "operational_friction_score": value,
                "availability_loss_score": value,
                "balanced_objective_score": value,
                "overall_resilience_score": 1 - value,
            }
        )
    results_path = output_dir / "results.csv"
    pd.DataFrame(rows).to_csv(results_path, index=False)

    summary = StatisticalAnalyzer().analyze(results_path, output_dir / "summary.csv")
    attack_summary = summary[summary["metric"] == "attack_success_rate"].iloc[0]

    assert attack_summary["95_percent_confidence_interval_lower"] < attack_summary["mean"]
    assert attack_summary["95_percent_confidence_interval_upper"] > attack_summary["mean"]


def test_sensitivity_analysis_ranks_variables():
    config = ExperimentConfig(PROJECT_ROOT / "config" / "experiment_config.yaml")
    output_dir = phase4_test_output_dir("sensitivity")
    MonteCarloRunner(config, output_dir).run(runs_per_configuration=30, random_seed=11)

    sensitivity = SensitivityAnalyzer().analyze(
        output_dir / "phase4_experiment_results.csv",
        output_dir / "phase4_sensitivity_results.csv",
    )

    assert "rank" in sensitivity.columns
    assert sensitivity.groupby("output_metric")["rank"].min().eq(1).all()
    assert "compromised_device_percentage" in set(sensitivity["input_parameter"])
    assert "balanced_objective_score" in set(sensitivity["output_metric"])
    assert sensitivity["interpretation_note"].str.contains("not causal proof").any()


def test_stricter_prompt_filter_can_increase_false_positive_rate():
    config = ExperimentConfig(PROJECT_ROOT / "config" / "experiment_config.yaml")
    output_dir = phase4_test_output_dir("false_positive")
    results = MonteCarloRunner(config, output_dir).run(runs_per_configuration=10, random_seed=13)
    means = results.groupby("security_configuration")["false_positive_rate"].mean()

    assert means["adaptive_resilience"] > means["weak_baseline"]


def test_lower_approval_threshold_increases_approval_delay():
    config = ExperimentConfig(PROJECT_ROOT / "config" / "experiment_config.yaml")
    output_dir = phase4_test_output_dir("approval_delay")
    results = MonteCarloRunner(config, output_dir).run(runs_per_configuration=10, random_seed=14)
    means = results.groupby("security_configuration")["human_approval_delay_minutes"].mean()

    assert means["adaptive_resilience"] > means["weak_baseline"]


def test_quarantine_can_reduce_availability_temporarily():
    config = ExperimentConfig(PROJECT_ROOT / "config" / "experiment_config.yaml")
    output_dir = phase4_test_output_dir("availability")
    results = MonteCarloRunner(config, output_dir).run(runs_per_configuration=10, random_seed=15)
    means = results.groupby("quarantine_enabled")["availability_rate"].mean()

    assert means[True] < means[False]


def test_balanced_objective_includes_security_and_operational_drawbacks():
    config = ExperimentConfig(PROJECT_ROOT / "config" / "experiment_config.yaml")
    output_dir = phase4_test_output_dir("balanced_objective")
    results = MonteCarloRunner(config, output_dir).run(runs_per_configuration=5, random_seed=16)

    assert (results["balanced_objective_score"] >= results["security_risk_score"] * 0.30).all()
    assert (results["balanced_objective_score"] >= results["operational_friction_score"] * 0.10).all()


def test_phase4_all_output_files_are_created():
    Phase4ExperimentRunner(PROJECT_ROOT).run_all()

    expected_files = [
        PROJECT_ROOT / "reports" / "phase4_report.txt",
        PROJECT_ROOT / "reports" / "phase4_metrics.csv",
        PROJECT_ROOT / "data" / "phase4_experiment_results.csv",
        PROJECT_ROOT / "data" / "phase4_statistical_summary.csv",
        PROJECT_ROOT / "data" / "phase4_sensitivity_results.csv",
        PROJECT_ROOT / "reports" / "phase4_attack_success_distribution.png",
        PROJECT_ROOT / "reports" / "phase4_sensitivity_tornado.png",
        PROJECT_ROOT / "reports" / "phase4_config_comparison.png",
        PROJECT_ROOT / "reports" / "phase4_dr_failure_boxplot.png",
        PROJECT_ROOT / "reports" / "phase4_security_vs_operational_friction.png",
        PROJECT_ROOT / "reports" / "phase4_balanced_objective_by_config.png",
        PROJECT_ROOT / "reports" / "phase4_false_positive_by_config.png",
        PROJECT_ROOT / "reports" / "phase4_approval_delay_by_config.png",
    ]

    assert all(path.exists() for path in expected_files)
