"""Streamlit dashboard for the cyber-resilience simulator."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard_utils import data_path, file_inventory, load_csv, read_text, round_numeric


st.set_page_config(page_title="AI-IoT Cyber-Resilience Simulator", layout="wide")


def show_missing_warning(files: list[str] | None = None) -> None:
    if files:
        st.warning("Missing generated output files: " + ", ".join(files))
    else:
        st.warning("Some outputs are missing. Run `python src/main.py --scenario phase5_all` from the project root.")


def show_image(relative_path: str, caption: str) -> None:
    path = data_path(relative_path)
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=True)
    else:
        st.info(f"Chart not found: `{relative_path}`")


def mean_by_config(results: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "attack_success_rate",
        "demand_response_failure_rate",
        "total_operational_friction_score",
        "availability_rate",
    ]
    return (
        results.groupby("security_configuration")[columns]
        .mean()
        .reset_index()
        .rename(
            columns={
                "attack_success_rate": "mean_attack_success_rate",
                "demand_response_failure_rate": "mean_demand_response_failure_rate",
                "total_operational_friction_score": "mean_operational_friction",
                "availability_rate": "mean_availability_rate",
            }
        )
    )


phase4_results = load_csv("data/phase4_experiment_results.csv")
phase4_stats = load_csv("data/phase4_statistical_summary.csv")
phase4_sensitivity = load_csv("data/phase4_sensitivity_results.csv")
phase5_optimization = load_csv("data/phase5_optimization_results.csv")
phase5_pareto = load_csv("data/phase5_pareto_results.csv")
phase5_recommendations = load_csv("data/phase5_recommendations.csv")

st.title("AI-IoT Demand Response Cyber-Resilience Simulator")
st.caption("Safe academic simulation dashboard for Phases 1-5.")

section = st.sidebar.radio(
    "Dashboard Section",
    [
        "Project Overview",
        "Phase 4 Statistical Results",
        "Phase 4 Sensitivity Analysis",
        "Phase 5 Optimization Results",
        "Pareto Trade-offs",
        "Recommendations",
        "Mathematical OR Model",
        "Reports and Outputs",
    ],
)

if section == "Project Overview":
    st.header("Project Overview")
    left, right = st.columns([2, 1])
    with left:
        st.subheader("AI-IoT Demand Response Cyber-Resilience Simulator")
        st.write(
            "A safe academic simulator for studying AI-assisted thermostat control, firmware trust, "
            "demand-response performance, cyber-resilience experiments, and Operations Research optimization."
        )
    with right:
        st.info("Safety scope: all attacks, backdoors, firmware tampering, IoT control, and power-system effects are simulated only.")

    phase_summary = pd.DataFrame(
        [
            {"phase": "Phase 1", "summary": "IoT thermostat AI assistant simulator"},
            {"phase": "Phase 2", "summary": "Firmware tampering and simulated backdoor"},
            {"phase": "Phase 3", "summary": "Power-demand and demand-response model"},
            {"phase": "Phase 4", "summary": "Monte Carlo, statistics, sensitivity analysis"},
            {"phase": "Phase 5", "summary": "Optimization, Pareto analysis, dashboard"},
        ]
    )
    st.subheader("Phase Summary")
    st.dataframe(phase_summary, use_container_width=True, hide_index=True)
    st.caption("The dashboard presents generated simulation outputs; it does not control real devices or networks.")

elif section == "Phase 4 Statistical Results":
    st.header("Phase 4 Statistical Results")
    if phase4_results.empty:
        show_missing_warning(["data/phase4_experiment_results.csv"])
    else:
        runs = len(phase4_results)
        configs = phase4_results["security_configuration"].nunique()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Monte Carlo runs", f"{runs:,}")
        col2.metric("Configurations", configs)
        col3.metric("Mean attack success", f"{phase4_results['attack_success_rate'].mean():.4f}")
        col4.metric("Mean availability", f"{phase4_results['availability_rate'].mean():.4f}")

        configuration_options = sorted(phase4_results["security_configuration"].unique())
        selected_config = st.selectbox("Select security configuration", configuration_options)
        filtered = phase4_results[phase4_results["security_configuration"] == selected_config]

        st.subheader("Configuration Means")
        comparison = round_numeric(mean_by_config(phase4_results))
        st.dataframe(comparison, use_container_width=True, hide_index=True)

        st.subheader(f"Selected Configuration: {selected_config}")
        selected_summary = round_numeric(
            filtered[
                [
                    "attack_success_rate",
                    "demand_response_failure_rate",
                    "total_operational_friction_score",
                    "availability_rate",
                    "load_spike_kw",
                    "comfort_loss_degree_minutes",
                ]
            ].mean()
            .to_frame("mean_value")
            .reset_index()
            .rename(columns={"index": "metric"})
        )
        st.dataframe(selected_summary, use_container_width=True, hide_index=True)

        if not phase4_stats.empty:
            st.subheader("Statistical Summary")
            st.dataframe(round_numeric(phase4_stats), use_container_width=True, hide_index=True)

        st.caption("These values summarize repeated safe internal simulations across sampled operating and security conditions.")

elif section == "Phase 4 Sensitivity Analysis":
    st.header("Phase 4 Sensitivity Analysis")
    if phase4_sensitivity.empty:
        show_missing_warning(["data/phase4_sensitivity_results.csv"])
    else:
        st.warning("Sensitivity scores are approximate simulation-based rankings, not causal proof.")
        target_metrics = [
            "attack_success_rate",
            "load_spike_kw",
            "comfort_loss_degree_minutes",
            "demand_response_failure_rate",
            "total_operational_friction_score",
            "balanced_objective_score",
        ]
        selected_metric = st.selectbox("Outcome metric", target_metrics)
        ranking = phase4_sensitivity[phase4_sensitivity["output_metric"] == selected_metric].sort_values("rank")
        st.subheader(f"Top Drivers: {selected_metric}")
        st.dataframe(round_numeric(ranking.head(5)), use_container_width=True, hide_index=True)

        with st.expander("Full sensitivity ranking table", expanded=False):
            st.dataframe(round_numeric(phase4_sensitivity), use_container_width=True, hide_index=True)

        show_image("reports/phase4_sensitivity_tornado.png", "Phase 4 sensitivity tornado chart")
        st.caption("Higher sensitivity scores indicate stronger approximate association in the generated experiment data.")

elif section == "Phase 5 Optimization Results":
    st.header("Phase 5 Optimization Results")
    if phase5_optimization.empty:
        show_missing_warning(["data/phase5_optimization_results.csv"])
    else:
        profiles = sorted(phase5_optimization["weighting_profile"].unique())
        selected_profile = st.selectbox("Weighting profile", profiles)
        profile_rows = phase5_optimization[phase5_optimization["weighting_profile"] == selected_profile].sort_values("rank")
        best = profile_rows.iloc[0]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Best configuration", best["security_configuration"])
        col2.metric("Objective score", f"{best['mean_weighted_objective_score']:.4f}")
        col3.metric("Attack success", f"{best['mean_attack_success_rate']:.4f}")
        col4.metric("Availability", f"{best['mean_availability_rate']:.4f}")

        display_columns = [
            "weighting_profile",
            "security_configuration",
            "mean_weighted_objective_score",
            "mean_attack_success_rate",
            "mean_demand_response_failure_rate",
            "mean_availability_rate",
            "rank",
        ]
        st.subheader("Ranked Configurations")
        st.dataframe(round_numeric(profile_rows[display_columns]), use_container_width=True, hide_index=True)

        with st.expander("All weighting profiles", expanded=False):
            st.dataframe(round_numeric(phase5_optimization[display_columns]), use_container_width=True, hide_index=True)

        show_image("reports/phase5_weighted_objective_by_profile.png", "Weighted objective score by configuration and profile")
        st.caption("Lower weighted objective scores are better. Feasibility constraints are evaluated separately in the recommendations section.")

elif section == "Pareto Trade-offs":
    st.header("Pareto Trade-offs")
    if phase5_pareto.empty:
        show_missing_warning(["data/phase5_pareto_results.csv"])
    else:
        efficient = phase5_pareto[phase5_pareto["is_pareto_efficient"] == True]
        st.metric("Pareto-efficient points", len(efficient))
        st.write(
            "Pareto-efficient points represent trade-off solutions where one objective cannot be improved "
            "without worsening another."
        )
        st.subheader("Pareto-Efficient Rows")
        st.dataframe(round_numeric(efficient), use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        with col1:
            show_image("reports/phase5_pareto_security_vs_friction.png", "Security risk vs operational friction")
        with col2:
            show_image("reports/phase5_pareto_power_vs_comfort.png", "Power impact vs comfort impact")

elif section == "Recommendations":
    st.header("Recommendations")
    if phase5_recommendations.empty:
        show_missing_warning(["data/phase5_recommendations.csv"])
    else:
        renamed = phase5_recommendations.rename(
            columns={
                "recommendation_category": "recommendation_type",
                "security_configuration": "configuration",
            }
        )
        display_columns = [
            "recommendation_type",
            "configuration",
            "weighting_profile",
            "mean_weighted_objective_score",
            "mean_attack_success_rate",
            "mean_demand_response_failure_rate",
            "mean_availability_rate",
            "constraints_met",
            "reason",
        ]
        st.dataframe(round_numeric(renamed[display_columns]), use_container_width=True, hide_index=True)

        st.subheader("Recommendation Highlights")
        for _, row in renamed.iterrows():
            label = row["recommendation_type"].replace("_", " ").title()
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.metric(label, row["configuration"])
                col2.metric("Objective score", f"{row['mean_weighted_objective_score']:.4f}")
                col3.metric("Constraints met", str(row["constraints_met"]))
                st.caption(row["reason"])
                if not bool(row["constraints_met"]):
                    st.warning(
                        f"{row['configuration']} wins under {row['weighting_profile']} weights but does not satisfy feasibility constraints. {row['reason']}"
                    )

        show_image("reports/phase5_recommendation_summary.png", "Best configuration score by weighting profile")
        st.caption("The operations-focused winner can be operationally attractive while still failing attack or demand-response feasibility thresholds.")

elif section == "Mathematical OR Model":
    st.header("Mathematical OR Model")
    model_path = data_path("reports/phase5_mathematical_model.md")
    latex_path = data_path("reports/phase5_mathematical_model_latex.txt")
    if not model_path.exists() or not latex_path.exists():
        show_missing_warning(["reports/phase5_mathematical_model.md", "reports/phase5_mathematical_model_latex.txt"])
    else:
        st.write(
            "Phase 5 is a simulation-driven binary configuration-selection optimization model. "
            "The simulation provides parameter values; the OR model chooses a feasible configuration under a weighting profile."
        )
        st.subheader("Decision Variable")
        st.latex(r"x_c \in \{0,1\}")

        st.subheader("Objective Function")
        st.latex(
            r"""
            \min Z_k = \sum_{c \in C} x_c \left(
            w^{k}_{sec} R_c +
            w^{k}_{pow} P_c +
            w^{k}_{com} H_c +
            w^{k}_{dr} D_c +
            w^{k}_{op} O_c +
            w^{k}_{av} L_c
            \right)
            """
        )

        st.subheader("Core Constraints")
        st.latex(r"\sum_{c \in C} x_c = 1")
        st.latex(r"\sum_{c \in C} x_c A_c \leq A^{max}")
        st.latex(r"\sum_{c \in C} x_c D_c \leq D^{max}")
        st.latex(r"\sum_{c \in C} x_c V_c \geq V^{min}")

        with st.expander("Full standalone model", expanded=True):
            st.markdown(read_text("reports/phase5_mathematical_model.md"))

        with st.expander("LaTeX-friendly text", expanded=False):
            st.code(read_text("reports/phase5_mathematical_model_latex.txt"), language="latex")

elif section == "Reports and Outputs":
    st.header("Reports and Outputs")
    expected_files = [
        "reports/phase5_report.txt",
        "reports/phase5_recommendations.txt",
        "reports/phase5_mathematical_model.md",
        "reports/phase5_mathematical_model_latex.txt",
        "data/phase5_optimization_results.csv",
        "data/phase5_pareto_results.csv",
        "data/phase5_recommendations.csv",
        "data/phase4_experiment_results.csv",
        "data/phase4_statistical_summary.csv",
        "data/phase4_sensitivity_results.csv",
    ]
    inventory = file_inventory(expected_files)
    st.dataframe(inventory, use_container_width=True, hide_index=True)
    st.caption("All paths are local project outputs generated by simulation commands. No external network calls are used.")
