from pathlib import Path
import sys

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
WORK_ROOT = PROJECT_ROOT.parents[1] / "work" / "phase5_test_outputs"

from experiments.experiment_config import ExperimentConfig
from experiments.monte_carlo import MonteCarloRunner
from optimization.objective_functions import ObjectiveFunctionCalculator
from optimization.optimizer import OptimizationRunner
from optimization.pareto_analysis import ParetoAnalyzer
from optimization.recommendation_engine import RecommendationEngine


def phase5_test_output_dir(name: str) -> Path:
    path = WORK_ROOT / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_phase4_results(output_dir: Path, runs_per_configuration: int = 8) -> Path:
    config = ExperimentConfig(PROJECT_ROOT / "config" / "experiment_config.yaml")
    MonteCarloRunner(config, output_dir).run(runs_per_configuration=runs_per_configuration, random_seed=21)
    return output_dir / "phase4_experiment_results.csv"


def create_optimization_results(output_dir: Path, weak_attack: float = 0.2762, weak_dr: float = 0.1558) -> Path:
    rows = [
        {
            "weighting_profile": "operations_focused",
            "security_configuration": "weak_baseline",
            "mean_weighted_objective_score": 0.10,
            "mean_security_risk_score": 0.20,
            "mean_power_impact_score": 0.10,
            "mean_comfort_impact_score": 0.10,
            "mean_demand_response_failure_score": weak_dr,
            "mean_operational_friction_score": 0.05,
            "mean_availability_loss_score": 0.0,
            "mean_attack_success_rate": weak_attack,
            "mean_demand_response_failure_rate": weak_dr,
            "mean_availability_rate": 1.0,
            "rank": 1,
        },
        {
            "weighting_profile": "operations_focused",
            "security_configuration": "firmware_focused",
            "mean_weighted_objective_score": 0.20,
            "mean_security_risk_score": 0.05,
            "mean_power_impact_score": 0.08,
            "mean_comfort_impact_score": 0.02,
            "mean_demand_response_failure_score": 0.02,
            "mean_operational_friction_score": 0.40,
            "mean_availability_loss_score": 0.01,
            "mean_attack_success_rate": 0.03,
            "mean_demand_response_failure_rate": 0.02,
            "mean_availability_rate": 0.99,
            "rank": 2,
        },
        {
            "weighting_profile": "balanced",
            "security_configuration": "weak_baseline",
            "mean_weighted_objective_score": 0.09,
            "mean_security_risk_score": 0.20,
            "mean_power_impact_score": 0.10,
            "mean_comfort_impact_score": 0.10,
            "mean_demand_response_failure_score": weak_dr,
            "mean_operational_friction_score": 0.05,
            "mean_availability_loss_score": 0.0,
            "mean_attack_success_rate": weak_attack,
            "mean_demand_response_failure_rate": weak_dr,
            "mean_availability_rate": 1.0,
            "rank": 1,
        },
        {
            "weighting_profile": "balanced",
            "security_configuration": "firmware_focused",
            "mean_weighted_objective_score": 0.11,
            "mean_security_risk_score": 0.05,
            "mean_power_impact_score": 0.08,
            "mean_comfort_impact_score": 0.02,
            "mean_demand_response_failure_score": 0.02,
            "mean_operational_friction_score": 0.40,
            "mean_availability_loss_score": 0.01,
            "mean_attack_success_rate": 0.03,
            "mean_demand_response_failure_rate": 0.02,
            "mean_availability_rate": 0.99,
            "rank": 2,
        },
        {
            "weighting_profile": "security_focused",
            "security_configuration": "firmware_focused",
            "mean_weighted_objective_score": 0.08,
            "mean_security_risk_score": 0.05,
            "mean_power_impact_score": 0.08,
            "mean_comfort_impact_score": 0.02,
            "mean_demand_response_failure_score": 0.02,
            "mean_operational_friction_score": 0.40,
            "mean_availability_loss_score": 0.01,
            "mean_attack_success_rate": 0.03,
            "mean_demand_response_failure_rate": 0.02,
            "mean_availability_rate": 0.99,
            "rank": 1,
        },
    ]
    path = output_dir / "phase5_optimization_results.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def generate_test_recommendations(output_dir: Path, weak_attack: float, weak_dr: float) -> pd.DataFrame:
    optimization_path = create_optimization_results(output_dir, weak_attack=weak_attack, weak_dr=weak_dr)
    return RecommendationEngine(
        optimization_path,
        PROJECT_ROOT / "config" / "optimization_config.yaml",
        output_dir,
        output_dir,
    ).generate()


def test_optimization_config_loads_correctly():
    with (PROJECT_ROOT / "config" / "optimization_config.yaml").open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    assert "security_focused" in config["objective_weights"]
    assert config["optimization"]["method"] == "grid_search"
    assert "security_risk_score" in config["optimization"]["pareto_objectives"]


def test_objective_scores_are_created():
    output_dir = phase5_test_output_dir("objective_scores")
    results_path = create_phase4_results(output_dir)
    weights = {
        "security_risk": 0.30,
        "power_impact": 0.20,
        "comfort_impact": 0.15,
        "demand_response_failure": 0.15,
        "operational_friction": 0.10,
        "availability_loss": 0.10,
    }

    scored = ObjectiveFunctionCalculator(results_path).calculate_scores(weights, "balanced")

    assert "weighted_objective_score" in scored.columns
    assert scored["weighted_objective_score"].between(0, 1).all()
    assert "demand_response_failure_score" in scored.columns


def test_weighted_objective_score_changes_when_weights_change():
    output_dir = phase5_test_output_dir("weight_changes")
    results_path = create_phase4_results(output_dir)
    calculator = ObjectiveFunctionCalculator(results_path)
    security_weights = {
        "security_risk": 0.80,
        "power_impact": 0.05,
        "comfort_impact": 0.05,
        "demand_response_failure": 0.05,
        "operational_friction": 0.03,
        "availability_loss": 0.02,
    }
    operations_weights = {
        "security_risk": 0.05,
        "power_impact": 0.05,
        "comfort_impact": 0.05,
        "demand_response_failure": 0.05,
        "operational_friction": 0.55,
        "availability_loss": 0.25,
    }

    security_scored = calculator.calculate_scores(security_weights, "security")
    operations_scored = calculator.calculate_scores(operations_weights, "operations")

    assert not security_scored["weighted_objective_score"].equals(operations_scored["weighted_objective_score"])


def test_optimizer_produces_results_for_all_weighting_profiles():
    runner = OptimizationRunner(PROJECT_ROOT)
    optimization = runner.run_optimization()

    assert set(optimization["weighting_profile"]) == {"security_focused", "operations_focused", "balanced"}
    assert optimization.groupby("weighting_profile")["rank"].min().eq(1).all()
    assert (PROJECT_ROOT / "data" / "phase5_optimization_results.csv").exists()


def test_each_weighting_profile_ranks_configurations():
    optimization = OptimizationRunner(PROJECT_ROOT).run_optimization()
    expected_config_count = optimization["security_configuration"].nunique()

    assert optimization.groupby("weighting_profile").size().eq(expected_config_count).all()
    assert optimization.groupby("weighting_profile")["rank"].max().eq(expected_config_count).all()


def test_pareto_analyzer_marks_at_least_one_point_efficient():
    output_dir = phase5_test_output_dir("pareto")
    results_path = create_phase4_results(output_dir, runs_per_configuration=10)
    pareto = ParetoAnalyzer(results_path, output_dir / "phase5_pareto_results.csv").analyze()

    assert pareto["is_pareto_efficient"].any()
    assert (output_dir / "phase5_pareto_results.csv").exists()


def test_recommendation_engine_produces_required_categories():
    runner = OptimizationRunner(PROJECT_ROOT)
    runner.run_optimization()
    recommendations = runner.run_recommendations()

    assert {
        "best_security_focused_configuration",
        "best_operations_focused_configuration",
        "best_balanced_configuration",
        "best_feasible_configuration",
    }.issubset(set(recommendations["recommendation_category"]))


def test_weak_baseline_fails_constraints_when_attack_success_is_too_high():
    output_dir = phase5_test_output_dir("weak_attack_constraint")
    recommendations = generate_test_recommendations(output_dir, weak_attack=0.2762, weak_dr=0.05)
    operations = recommendations[
        recommendations["recommendation_category"] == "best_operations_focused_configuration"
    ].iloc[0]

    assert operations["security_configuration"] == "weak_baseline"
    assert operations["constraints_met"] is False or operations["constraints_met"] == False
    assert "attack success" in operations["reason"]


def test_weak_baseline_fails_constraints_when_dr_failure_is_too_high():
    output_dir = phase5_test_output_dir("weak_dr_constraint")
    recommendations = generate_test_recommendations(output_dir, weak_attack=0.05, weak_dr=0.1558)
    operations = recommendations[
        recommendations["recommendation_category"] == "best_operations_focused_configuration"
    ].iloc[0]

    assert operations["security_configuration"] == "weak_baseline"
    assert operations["constraints_met"] is False or operations["constraints_met"] == False
    assert "DR failure" in operations["reason"]


def test_best_feasible_configuration_excludes_infeasible_configurations():
    output_dir = phase5_test_output_dir("feasible_excludes_weak")
    recommendations = generate_test_recommendations(output_dir, weak_attack=0.2762, weak_dr=0.1558)
    feasible = recommendations[recommendations["recommendation_category"] == "best_feasible_configuration"].iloc[0]

    assert feasible["security_configuration"] == "firmware_focused"
    assert feasible["constraints_met"] is True or feasible["constraints_met"] == True


def test_phase5_output_files_are_created():
    OptimizationRunner(PROJECT_ROOT).run_all()

    expected_files = [
        PROJECT_ROOT / "reports" / "phase5_report.txt",
        PROJECT_ROOT / "reports" / "phase5_recommendations.txt",
        PROJECT_ROOT / "reports" / "phase5_mathematical_model.md",
        PROJECT_ROOT / "reports" / "phase5_mathematical_model_latex.txt",
        PROJECT_ROOT / "reports" / "phase5_weighted_objective_by_profile.png",
        PROJECT_ROOT / "reports" / "phase5_pareto_security_vs_friction.png",
        PROJECT_ROOT / "reports" / "phase5_pareto_power_vs_comfort.png",
        PROJECT_ROOT / "reports" / "phase5_recommendation_summary.png",
        PROJECT_ROOT / "data" / "phase5_optimization_results.csv",
        PROJECT_ROOT / "data" / "phase5_pareto_results.csv",
        PROJECT_ROOT / "data" / "phase5_recommendations.csv",
    ]

    assert all(path.exists() for path in expected_files)


def test_dashboard_files_exist():
    assert (PROJECT_ROOT / "dashboard" / "app.py").exists()
    assert (PROJECT_ROOT / "dashboard" / "dashboard_utils.py").exists()


def test_dashboard_helper_functions_import_and_expected_files_exist():
    sys.path.insert(0, str(PROJECT_ROOT / "dashboard"))
    from dashboard_utils import file_inventory, load_csv, round_numeric

    OptimizationRunner(PROJECT_ROOT).run_all()
    dashboard_files = [
        "data/phase4_experiment_results.csv",
        "data/phase4_statistical_summary.csv",
        "data/phase4_sensitivity_results.csv",
        "data/phase5_optimization_results.csv",
        "data/phase5_pareto_results.csv",
        "data/phase5_recommendations.csv",
        "reports/phase5_mathematical_model.md",
        "reports/phase5_mathematical_model_latex.txt",
    ]

    inventory = file_inventory(dashboard_files)
    optimization = load_csv("data/phase5_optimization_results.csv")

    assert inventory["exists"].all()
    assert not optimization.empty
    assert "mean_weighted_objective_score" in round_numeric(optimization).columns


def test_phase5_mathematical_model_artifacts_and_docs_are_present():
    OptimizationRunner(PROJECT_ROOT).run_all()

    report_text = (PROJECT_ROOT / "reports" / "phase5_report.txt").read_text(encoding="utf-8")
    model_text = (PROJECT_ROOT / "reports" / "phase5_mathematical_model.md").read_text(encoding="utf-8")
    latex_text = (PROJECT_ROOT / "reports" / "phase5_mathematical_model_latex.txt").read_text(encoding="utf-8")
    readme_text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "Formal Operations Research Model" in report_text
    assert "Decision variables" in model_text
    assert "\\min Z_k" in latex_text
    assert "Decision variables" in readme_text
    assert "Objective function" in readme_text
    assert "Constraints" in readme_text
