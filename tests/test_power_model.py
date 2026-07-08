from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from devices.thermostat import Thermostat
from main import load_yaml, project_root, run_single_power_scenario
from power.demand_response import DemandResponseController
from power.hvac_load_model import HVACLoadModel
from power.power_metrics import PowerMetricsCalculator
from power.temperature_dynamics import TemperatureDynamicsSimulator


def make_device(device_id: str, current: float = 24, target: float = 22, power_kw: float = 2.5) -> Thermostat:
    return Thermostat(
        device_id=device_id,
        building_id="Building A",
        manufacturer_id="ThermoGrid-X",
        ip_address=f"10.0.1.{device_id[-1]}",
        current_temperature=current,
        target_temperature=target,
        firmware_version="1.0.0",
        hvac_power_kw=power_kw,
        temperature_change_rate=0.25,
    )


def test_device_hvac_load_calculation():
    device = make_device("A-001", current=24, target=22, power_kw=2.0)

    assert device.calculate_hvac_state() is True
    assert device.calculate_power_demand_kw() == 2.0


def test_fleet_load_aggregation():
    devices = [
        make_device("A-001", current=24, target=22, power_kw=2.0),
        make_device("A-002", current=22, target=22, power_kw=2.0),
        make_device("A-003", current=26, target=24, power_kw=5.0),
    ]

    assert HVACLoadModel().calculate_fleet_load(devices) == 7.0
    assert HVACLoadModel().calculate_active_hvac_count(devices) == 2


def test_temperature_changes_gradually_over_time():
    device = make_device("A-001", current=24, target=22)

    TemperatureDynamicsSimulator().run_time_steps([device], time_steps=2, time_step_minutes=15)

    assert device.current_temperature == 23.5


def test_demand_response_event_changes_target_temperature():
    devices = [make_device("A-001", current=24, target=22), make_device("A-002", current=24, target=22)]

    changed = DemandResponseController().apply_demand_response_event(devices, 24, 8, 16, current_step=8)

    assert changed == 2
    assert all(device.target_temperature == 24 for device in devices)


def test_attack_target_temperature_creates_higher_load_than_baseline():
    baseline_devices = [make_device("A-001", current=24, target=24), make_device("A-002", current=24, target=24)]
    attack_devices = [make_device("A-001", current=24, target=16), make_device("A-002", current=24, target=24)]
    load_model = HVACLoadModel()

    assert load_model.calculate_fleet_load(attack_devices) > load_model.calculate_fleet_load(baseline_devices)


def test_comfort_attack_increases_comfort_loss():
    baseline = [make_device("A-001", current=24, target=24)]
    attack = [make_device("A-001", current=24, target=28)]
    simulator = TemperatureDynamicsSimulator()
    baseline_ts = simulator.run_time_steps(baseline, time_steps=12, time_step_minutes=15)
    attack_ts = simulator.run_time_steps(attack, time_steps=12, time_step_minutes=15)
    metrics = PowerMetricsCalculator()

    baseline_loss = metrics.calculate(baseline_ts, 15)["comfort_loss_degree_minutes"]
    attack_loss = metrics.calculate(attack_ts, 15)["comfort_loss_degree_minutes"]

    assert attack_loss > baseline_loss


def test_power_metrics_calculate_peak_load_correctly():
    devices = [
        make_device("A-001", current=24, target=22, power_kw=2.0),
        make_device("A-002", current=24, target=22, power_kw=5.0),
    ]
    ts = TemperatureDynamicsSimulator().run_time_steps(devices, time_steps=1, time_step_minutes=15)

    metrics = PowerMetricsCalculator().calculate(ts, time_step_minutes=15)

    assert metrics["baseline_peak_load_kw"] == 7.0
    assert metrics["attack_peak_load_kw"] == 7.0


def test_ambient_heat_gain_prevents_load_staying_zero_forever():
    device = make_device("A-001", current=22, target=22, power_kw=2.0)
    device.ambient_temperature = 30
    device.passive_heat_gain_rate = 0.5

    ts = TemperatureDynamicsSimulator().run_time_steps([device], time_steps=8, time_step_minutes=15)

    assert ts["power_demand_kw"].iloc[0] == 0
    assert ts["power_demand_kw"].sum() > 0


def test_demand_response_normal_reduces_event_window_load():
    root = project_root()
    power_config = load_yaml(root / "config" / "power_config.yaml")

    metrics, _ = run_single_power_scenario(root, "demand_response_normal", power_config)

    assert metrics["baseline_event_average_load_kw"] > metrics["event_average_load_kw"]
    assert metrics["demand_response_actual_reduction_kw"] > 0


def test_demand_response_attack_performs_worse_than_normal():
    root = project_root()
    power_config = load_yaml(root / "config" / "power_config.yaml")

    normal_metrics, _ = run_single_power_scenario(root, "demand_response_normal", power_config)
    attack_metrics, _ = run_single_power_scenario(root, "demand_response_attack", power_config)

    assert attack_metrics["event_average_load_kw"] > normal_metrics["event_average_load_kw"]
    assert attack_metrics["demand_response_actual_reduction_kw"] < normal_metrics["demand_response_actual_reduction_kw"]


def test_demand_response_failure_rate_lower_for_normal_than_attack():
    root = project_root()
    power_config = load_yaml(root / "config" / "power_config.yaml")

    normal_metrics, _ = run_single_power_scenario(root, "demand_response_normal", power_config)
    attack_metrics, _ = run_single_power_scenario(root, "demand_response_attack", power_config)

    assert normal_metrics["demand_response_failure_rate"] < attack_metrics["demand_response_failure_rate"]


def test_scenario_specific_metrics_are_reported_clearly():
    from main import run_scenario

    _, metrics, _ = run_scenario("phase3_all")

    assert "demand_response_normal_peak_load_kw" in metrics
    assert "demand_response_attack_peak_load_kw" in metrics
    assert "dr_normal_reduction_kw" in metrics
    assert "dr_attack_reduction_kw" in metrics
    assert "backdoor_spike_vs_baseline_kw" in metrics
    assert metrics["dr_normal_reduction_kw"] > metrics["dr_attack_reduction_kw"]
    assert metrics["backdoor_spike_vs_baseline_kw"] > 0
