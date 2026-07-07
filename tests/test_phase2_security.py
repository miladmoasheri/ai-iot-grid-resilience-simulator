from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from attacks.backdoor_access import SimulatedBackdoorAccess
from devices.fleet_manager import FleetManager
from main import run_scenario
from reporting.metrics import MetricsCalculator
from security.firmware_security import FirmwarePackage
from security.recovery import RecoveryManager


def compromised_fleet():
    fleet_manager = FleetManager(PROJECT_ROOT / "config" / "fleet_config.yaml")
    target_devices = fleet_manager.get_all_devices()[:5]
    firmware_package = FirmwarePackage(
        firmware_id="fw-1.1.0",
        manufacturer_id="ThermoGrid-X",
        version="1.1.0",
        signature_valid=False,
        is_tampered=True,
        contains_simulated_backdoor=True,
        release_channel="lab",
    )
    fleet_manager.apply_firmware_update(firmware_package, target_devices)
    return fleet_manager, target_devices


def test_simulated_attacker_ip_affects_compromised_devices_only_through_backdoor_path():
    fleet_manager, target_devices = compromised_fleet()
    mixed_devices = target_devices + fleet_manager.get_all_devices()[5:7]
    access = SimulatedBackdoorAccess()

    result = access.attempt("203.0.113.50", mixed_devices, 19)

    assert result["success"] is True
    assert len(result["changed_devices"]) == 5
    assert len(result["blocked_devices"]) == 2
    assert result["eligible_backdoor_devices"] == 5
    assert result["backdoor_affected_devices"] == 5
    assert result["backdoor_blocked_devices"] == 2
    assert result["compromised_devices_targeted"] == 5
    assert result["trusted_devices_targeted"] == 2
    assert all(device.target_temperature == 19 for device in target_devices)


def test_quarantined_device_blocks_simulated_backdoor_access():
    _, target_devices = compromised_fleet()
    target_devices[0].quarantine("test quarantine")

    result = SimulatedBackdoorAccess().attempt("203.0.113.50", target_devices, 18)

    assert target_devices[0].device_id not in result["changed_devices"]
    assert len(result["changed_devices"]) == 4


def test_recovery_disables_backdoor_and_restores_recovered_state():
    fleet_manager, target_devices = compromised_fleet()
    recovery_manager = RecoveryManager()
    recovery_manager.quarantine_compromised_devices(fleet_manager.get_all_devices())
    recovered = recovery_manager.recover_devices_to_safe_firmware(fleet_manager.get_all_devices(), version="1.0.0")

    assert len(recovered) == 5
    assert all(not device.backdoor_enabled for device in target_devices)
    assert all(device.trust_status == "recovered" for device in target_devices)
    assert all(device.firmware_signature_valid for device in target_devices)


def test_tampered_firmware_sets_attack_detected_true():
    entries, _, _ = run_scenario("firmware_tampering_blocked")

    assert entries[0]["firmware_tampered"] is True
    assert entries[0]["attack_detected"] is True


def test_backdoor_payload_sets_attack_detected_true():
    entries, _, _ = run_scenario("firmware_tampering_weak_profile")

    assert entries[0]["firmware_contains_backdoor"] is True
    assert entries[0]["attack_detected"] is True


def test_unique_devices_compromised_counts_distinct_device_ids():
    metrics = MetricsCalculator().calculate(
        [
            {
                "policy_decision": "APPROVED",
                "reasons": [],
                "devices_changed": 5,
                "devices_compromised": 5,
                "compromised_device_ids": ["a", "b", "c", "d", "e"],
                "parsed_command": {"intent": "firmware_update"},
            },
            {
                "policy_decision": "APPROVED",
                "reasons": [],
                "devices_changed": 5,
                "devices_compromised": 2,
                "compromised_device_ids": ["d", "e", "f", "g"],
                "parsed_command": {"intent": "firmware_update"},
            },
        ]
    )

    assert metrics["newly_compromised_devices"] == 7
    assert metrics["unique_devices_compromised"] == 7
