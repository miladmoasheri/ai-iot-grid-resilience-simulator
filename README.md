# AI-Assisted Demand Response Cyber-Resilience Simulator

Phase 1 is a safe academic Python simulation of an AI-assisted demand-response workflow for a smart thermostat fleet.

The simulator models an operator sending natural language commands to a simulated AI assistant. The assistant converts each request into structured intent, then a defensive validation pipeline checks prompt-injection indicators, source IP policy, temperature safety limits, and mass-command rules before any simulated thermostat state is changed.

## Safe and Defensive Scope

This project does not create malware, backdoors, network scanners, exploits, command-and-control logic, or unauthorized access tooling.

All cyber behavior is represented as internal Python simulation state, policy decisions, and logs. IP addresses are configuration values only. No real ports are opened, no packets are sent, and no real IoT devices are contacted.

## Architecture

- `src/ai_assistant/assistant.py` parses natural language thermostat requests.
- `src/ai_assistant/prompt_filter.py` detects prompt-injection phrases.
- `src/security/network_policy.py` evaluates source IP allow/block rules.
- `src/security/policy_engine.py` makes final APPROVED or BLOCKED decisions.
- `src/devices/fleet_manager.py` creates and updates a simulated thermostat fleet.
- `src/attacks/scenario_runner.py` provides safe internal scenarios.
- `src/reporting/logger.py` writes CSV and JSON decision logs.
- `src/reporting/metrics.py` summarizes simulation outcomes.
- `src/reporting/report_generator.py` writes Phase 1 reports.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS or Linux, use:

```bash
source .venv/bin/activate
```

## Run Scenarios

From the project root:

```bash
python src/main.py --scenario normal
python src/main.py --scenario prompt_injection
python src/main.py --scenario unauthorized_ip
python src/main.py --scenario mass_command
python src/main.py --scenario all
```

Phase 2 scenarios:

```bash
python src/main.py --scenario firmware_valid_update
python src/main.py --scenario firmware_tampering_blocked
python src/main.py --scenario firmware_tampering_weak_profile
python src/main.py --scenario simulated_backdoor_access
python src/main.py --scenario quarantine_recovery
python src/main.py --scenario approved_mass_command
python src/main.py --scenario phase2_all
python src/main.py --scenario phase2_all --profile strict
python src/main.py --scenario phase2_all --profile weak_baseline
python src/main.py --scenario phase2_all --profile balanced
```

Phase 3 power-demand scenarios:

```bash
python src/main.py --scenario power_baseline
python src/main.py --scenario demand_response_normal
python src/main.py --scenario demand_response_attack
python src/main.py --scenario backdoor_load_spike
python src/main.py --scenario comfort_violation_attack
python src/main.py --scenario phase3_all
```

Phase 4 experiment scenarios:

```bash
python src/main.py --scenario phase4_monte_carlo
python src/main.py --scenario phase4_sensitivity
python src/main.py --scenario phase4_all
```

Phase 5 optimization scenarios:

```bash
python src/main.py --scenario phase5_optimization
python src/main.py --scenario phase5_pareto
python src/main.py --scenario phase5_all
```

Launch the dashboard:

```bash
streamlit run dashboard/app.py
```

## Sample Output

```text
AI-Assisted Demand Response Cyber-Resilience Simulator
Scenario: normal

APPROVED | trusted operator adjusts the first 10 Building A thermostats to 22 degrees
Changed devices: 10

Report written to reports/phase1_report.txt
Metrics written to reports/phase1_metrics.csv
```

Blocked scenarios display the defensive reasons, such as prompt-injection phrases, blocked source IPs, unsafe temperature requests, or mass-command limits.

## Logs and Reports

Each run writes:

- `logs/simulation_log.csv`
- `logs/simulation_log.json`
- `reports/phase1_report.txt` and `reports/phase1_metrics.csv` for Phase 1 scenarios
- `reports/phase2_report.txt` and `reports/phase2_metrics.csv` for Phase 2 scenarios
- `reports/phase3_report.txt`, `reports/phase3_metrics.csv`, and `data/phase3_load_timeseries.csv` for Phase 3 scenarios
- `reports/phase4_report.txt`, `reports/phase4_metrics.csv`, and Phase 4 experiment datasets for Phase 4 scenarios
- `reports/phase5_report.txt`, `reports/phase5_recommendations.txt`, Phase 5 charts, and Phase 5 optimization datasets for Phase 5 scenarios

## Phase 2

Phase 2 adds firmware trust, simulated compromise state, approval-gated mass commands, quarantine, and recovery. It remains a defensive academic simulation only: firmware tampering and backdoor behavior are represented as Python object state and logs. The project does not create real backdoors, sockets, scanners, network listeners, exploits, or access paths.

### Firmware Trust Model

Firmware updates use metadata-only `FirmwarePackage` objects with manufacturer, version, signature validity, tampering, simulated-backdoor marker, and release-channel fields. The `FirmwareSecurityPolicy` evaluates packages against security profiles:

- `strict`: requires valid signatures, blocks tampered firmware, quarantines on simulated backdoor detection, and requires approval for mass commands.
- `balanced`: same protective defaults as strict for Phase 2.
- `weak_baseline`: allows unsigned and tampered firmware for comparative simulation experiments.

### Simulated Backdoor Model

The `SimulatedBackdoorAccess` class never opens ports or performs networking. It only applies an internal direct-command simulation to devices whose in-memory state has `backdoor_enabled=True`, `trust_status=compromised`, and `status` not quarantined.

### Human Approval Workflow

Commands that target more than `max_devices_without_approval` devices are blocked unless `approval_granted=True`. The parser recognizes approval language such as:

```text
Approve and set all thermostats to 21 degrees
Set all thermostats to 21 degrees with approval
```

### Quarantine and Recovery

The `RecoveryManager` detects compromised devices, quarantines them by disabling simulated backdoor state, and recovers devices to safe firmware such as `1.0.0`. Recovery sets firmware signatures valid again and marks devices as recovered.

### Phase 2 Sample Output

```text
APPROVED | firmware_valid_update | devices changed: 10
BLOCKED  | firmware_tampering_blocked | tampered firmware blocked by strict profile
APPROVED | simulated_backdoor_access | compromised devices changed through simulated path only
APPROVED | quarantine_recovery | compromised devices quarantined and recovered
```

## Testing

```bash
pytest
```

Tests cover prompt-injection detection, unauthorized IP blocking, unsafe temperature blocking, normal trusted command approval, and mass-command blocking.

## Phase 1 Limitations

- The AI assistant uses deterministic parsing rules rather than a live model.
- Device behavior is simplified to target temperature changes.
- The demand-response model does not yet estimate power load.
- Human approval is represented as a policy assumption rather than an interactive workflow.
- Attack scenarios are safe labels and internal inputs only.

## Phase 2 Limitations

- Firmware packages are metadata objects, not binary firmware images.
- Backdoor behavior is simulated as internal device state only.
- Approval is represented by parsed text or scenario flags, not a user-facing approval dashboard.
- Quarantine and recovery are immediate state transitions rather than time-based workflows.

## Phase 3

Phase 3 adds a simplified power-demand and demand-response impact model. Each thermostat now has HVAC power, active cooling state, thermal zone type, comfort bounds, a cooling rate, and passive ambient heat gain. The model produces load curves, total energy estimates, comfort-loss metrics, event-window demand-response target and actual reduction values, and compromised-versus-protected load summaries.

This is not a full grid power-flow simulation. It is a transparent academic load model driven by thermostat setpoints, gradual temperature movement, ambient heat gain, and fixed HVAC power values.

Phase 3 scenarios include:

- `power_baseline`: normal HVAC load and comfort tracking.
- `demand_response_normal`: a legitimate event raises setpoints to reduce cooling load.
- `demand_response_attack`: compromised devices resist the event by targeting a lower temperature.
- `backdoor_load_spike`: compromised devices are pushed to a low cooling setpoint.
- `comfort_violation_attack`: compromised devices are pushed above the comfort band.
- `phase3_all`: runs the full Phase 3 scenario set and writes one combined report.

## Phase 4

Phase 4 adds repeated experiments, statistical analysis, sensitivity analysis, and security-configuration comparison. It answers research questions such as which parameters most affect attack success, demand-response failure, comfort loss, load spikes, recovery performance, and operational friction.

The Monte Carlo engine uses balanced sampling by configuration. By default it runs 250 experiments for each security configuration, for 1,000 total runs. It varies fleet size, compromised-device percentage, attack temperature, prompt-filter strictness, firmware-signature requirements, approval thresholds, quarantine/recovery settings, HVAC power, ambient temperature, thermal rate, and attack start step.

Security configurations compared:

- `weak_baseline`: weak firmware validation and minimal quarantine/recovery.
- `network_focused`: stronger network/approval posture with moderate firmware and AI controls.
- `firmware_focused`: strict firmware validation with recovery enabled.
- `adaptive_resilience`: layered controls with approval, quarantine, and recovery.

Phase 4 outputs:

- `data/phase4_experiment_results.csv`
- `data/phase4_statistical_summary.csv`
- `data/phase4_sensitivity_results.csv`
- `reports/phase4_report.txt`
- `reports/phase4_metrics.csv`
- `reports/phase4_attack_success_distribution.png`
- `reports/phase4_sensitivity_tornado.png`
- `reports/phase4_config_comparison.png`
- `reports/phase4_dr_failure_boxplot.png`
- `reports/phase4_security_vs_operational_friction.png`
- `reports/phase4_balanced_objective_by_config.png`
- `reports/phase4_false_positive_by_config.png`
- `reports/phase4_approval_delay_by_config.png`

The statistical summary reports mean, median, standard deviation, min, max, and 95 percent confidence intervals for attack success, load spike, comfort loss, demand-response failure, total energy, compromised devices, recovered devices, false positives, command latency, approval delays, availability, security operation cost, operational friction, and composite resilience scores.

The sensitivity analysis uses approximate simulation-based normalized correlation rankings to identify which inputs most influence load spike, comfort loss, demand-response failure, attack success, operational friction, and balanced objective score. These rankings are not causal proof because some variables are bundled by security configuration.

## Phase 5

Phase 5 adds a decision-support optimization layer over the Phase 4 Monte Carlo results. It compares cyber-resilience configurations under different objective weights, identifies Pareto trade-offs, recommends configurations under feasibility constraints, and provides a Streamlit dashboard for exploring the results.

The objective function combines:

- `security_risk_score`
- `power_impact_score`
- `comfort_impact_score`
- `demand_response_failure_score`
- `operational_friction_score`
- `availability_loss_score`

Lower weighted objective scores are better. The default weighting profiles are:

- `security_focused`: emphasizes attack reduction and power/comfort protection.
- `operations_focused`: emphasizes availability and low operational friction.
- `balanced`: uses the Phase 4 balanced weights across security, power, comfort, demand-response reliability, friction, and availability.

Phase 5 outputs:

- `data/phase5_optimization_results.csv`
- `data/phase5_pareto_results.csv`
- `data/phase5_recommendations.csv`
- `reports/phase5_report.txt`
- `reports/phase5_recommendations.txt`
- `reports/phase5_mathematical_model.md`
- `reports/phase5_mathematical_model_latex.txt`
- `reports/phase5_weighted_objective_by_profile.png`
- `reports/phase5_pareto_security_vs_friction.png`
- `reports/phase5_pareto_power_vs_comfort.png`
- `reports/phase5_recommendation_summary.png`

The Pareto analysis evaluates trade-offs such as security risk versus operational friction, power impact versus comfort impact, and security risk versus availability loss. The recommendation engine reports the best security-focused, operations-focused, balanced, and feasible configurations.

### Formal Operations Research Model

Phase 5 is a simulation-driven binary configuration-selection optimization model. The simulation provides parameter values, and the optimization selects the best feasible security configuration under different decision-maker priorities.

Sets:

- `C`: candidate security configurations, such as `weak_baseline`, `network_focused`, `firmware_focused`, and `adaptive_resilience`.
- `K`: weighting profiles, such as `security_focused`, `operations_focused`, and `balanced`.
- `M`: evaluation metrics.

Parameters include `AttackSuccess_c`, `DRFailure_c`, `Availability_c`, `SecurityRisk_c`, `PowerImpact_c`, `ComfortImpact_c`, `OperationalFriction_c`, `AvailabilityLoss_c`, `SecurityCost_c`, and `w_m,k`, the weight of metric `m` under weighting profile `k`.

Decision variables:

- `x_c = 1` if security configuration `c` is selected.
- `x_c = 0` otherwise.

Objective function:

For each weighting profile `k`, minimize:

```text
Z_k = sum over c in C of x_c [
  w_security,k * SecurityRisk_c
  + w_power,k * PowerImpact_c
  + w_comfort,k * ComfortImpact_c
  + w_dr,k * DRFailure_c
  + w_friction,k * OperationalFriction_c
  + w_availability,k * AvailabilityLoss_c
]
```

Lower `Z_k` is better.

Constraints:

- Select exactly one configuration: `sum over c in C of x_c = 1`.
- Attack success threshold: `sum over c in C of x_c * AttackSuccess_c <= 0.10`.
- Demand-response failure threshold: `sum over c in C of x_c * DRFailure_c <= 0.10`.
- Availability threshold: `sum over c in C of x_c * Availability_c >= 0.95`.
- Optional operational-friction constraint: `sum over c in C of x_c * OperationalFriction_c <= F_max`.
- Optional security-cost constraint: `sum over c in C of x_c * SecurityCost_c <= B`.
- Binary decision constraint: `x_c in {0,1}`.

Future extension: The model can be extended into a time-indexed scheduling formulation where `x_{c,t}` selects a security configuration `c` for each time period `t`, allowing different profiles for business hours, weekends, maintenance windows, demand-response events, and active-attack conditions.

The dashboard loads Phase 4 and Phase 5 outputs and provides sections for project overview, configuration comparison, sensitivity ranking, optimization, Pareto trade-offs, and recommendation summary.

Important interpretation note: Phase 5 is a simulation-based decision-support model. The optimization results depend on chosen weights and simplified assumptions. They should not be interpreted as universal security truth. A real deployment would require real device data, power-system validation, and operational stakeholder input.
