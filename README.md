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

## Planned Phase 4 Additions

- Anomaly detection over thermostat events.
- Statistical experiments across repeated simulations.
- Repeated experiments and sensitivity analysis for thermal and power assumptions.
- Optimization for comfort, safety, and demand-response goals.
