# Phase 5 Mathematical Optimization Model

This standalone formulation documents the Operations Research model used by Phase 5. It remains a safe academic simulation model only; all cyber and power-system behavior is represented through generated simulation metrics.

Sets:
- C = set of candidate security configurations.
- Example C = {adaptive_resilience, firmware_focused, network_focused, weak_baseline}.
- K = set of weighting profiles.
- Example K = {security_focused, operations_focused, balanced}.
- M = set of evaluation metrics.

Parameters:
- AttackSuccess_c = mean attack success rate for configuration c.
- DRFailure_c = mean demand-response failure rate for configuration c.
- Availability_c = mean availability rate for configuration c.
- SecurityRisk_c = normalized cybersecurity risk score for configuration c.
- PowerImpact_c = normalized load/power impact score for configuration c.
- ComfortImpact_c = normalized comfort-loss score for configuration c.
- OperationalFriction_c = normalized operational friction score for configuration c.
- AvailabilityLoss_c = normalized availability-loss score for configuration c.
- SecurityCost_c = simulated security operation cost for configuration c.
- w_m,k = weight of metric m under weighting profile k.

Decision variables:
- x_c = 1 if security configuration c is selected.
- x_c = 0 otherwise.

Objective function:
For each weighting profile k, minimize Z_k:
Z_k = sum over c in C of x_c [w_security,k * SecurityRisk_c + w_power,k * PowerImpact_c + w_comfort,k * ComfortImpact_c + w_dr,k * DRFailure_c + w_friction,k * OperationalFriction_c + w_availability,k * AvailabilityLoss_c].
Lower Z_k is better.

Constraints:
- Select exactly one configuration: sum over c in C of x_c = 1.
- Attack success threshold: sum over c in C of x_c * AttackSuccess_c <= 0.10.
- Demand-response failure threshold: sum over c in C of x_c * DRFailure_c <= 0.10.
- Availability threshold: sum over c in C of x_c * Availability_c >= 0.95.
- Optional operational-friction constraint: sum over c in C of x_c * OperationalFriction_c <= F_max.
- Optional security-cost constraint: sum over c in C of x_c * SecurityCost_c <= B.
- Binary decision constraint: x_c in {0,1}.

Interpretation:
This is a binary configuration-selection optimization model. The simulation provides the parameter values, and the optimization chooses the best feasible security configuration under different decision-maker priorities.

Link to simulation outputs:
- `data/phase4_experiment_results.csv` provides simulation-derived parameter estimates.
- `data/phase5_optimization_results.csv` reports objective values and ranks.
- `data/phase5_recommendations.csv` reports profile winners and feasibility status.

Limitations:
- The selected configuration depends on simulated data, objective weights, and feasibility thresholds.
- The model is not a universal cybersecurity truth or a real deployment policy.
- Real use would require validated device data, power-system validation, and stakeholder review.

Future extension: The model can be extended into a time-indexed scheduling formulation where x_{c,t} selects a security configuration c for each time period t, allowing different profiles for business hours, weekends, maintenance windows, demand-response events, and active-attack conditions.
