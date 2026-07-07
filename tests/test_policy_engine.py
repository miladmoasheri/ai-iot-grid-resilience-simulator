from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ai_assistant.assistant import SimulatedAIAssistant
from ai_assistant.prompt_filter import PromptInjectionFilter
from devices.fleet_manager import FleetManager
from security.firmware_security import FirmwarePackage, FirmwareSecurityPolicy
from security.network_policy import NetworkPolicy
from security.policy_engine import PolicyEngine


def build_pipeline(command_text: str, source_ip: str, approval_granted: bool = False):
    assistant = SimulatedAIAssistant()
    prompt_filter = PromptInjectionFilter()
    network_policy = NetworkPolicy(PROJECT_ROOT / "config" / "network_rules.yaml")
    policy_engine = PolicyEngine(PROJECT_ROOT / "config" / "policies.yaml")
    fleet_manager = FleetManager(PROJECT_ROOT / "config" / "fleet_config.yaml")

    parsed = assistant.parse_command(command_text)
    parsed["approval_granted"] = approval_granted or parsed.get("approval_granted", False)
    prompt_result = prompt_filter.scan(command_text)
    network_result = network_policy.check_source_ip(source_ip)
    target_devices = fleet_manager.get_target_devices(parsed)
    decision = policy_engine.evaluate(parsed, prompt_result, network_result, target_devices)
    return decision


def build_firmware_pipeline(command_text: str, profile: str):
    assistant = SimulatedAIAssistant()
    prompt_filter = PromptInjectionFilter()
    network_policy = NetworkPolicy(PROJECT_ROOT / "config" / "network_rules.yaml")
    firmware_policy = FirmwareSecurityPolicy(PROJECT_ROOT / "config" / "security_profiles.yaml", profile)
    policy_engine = PolicyEngine(
        PROJECT_ROOT / "config" / "policies.yaml",
        firmware_security_policy=firmware_policy,
    )
    fleet_manager = FleetManager(PROJECT_ROOT / "config" / "fleet_config.yaml")

    parsed = assistant.parse_command(command_text)
    prompt_result = prompt_filter.scan(command_text)
    network_result = network_policy.check_source_ip("10.0.0.20")
    target_devices = fleet_manager.get_target_devices(parsed)
    decision = policy_engine.evaluate(parsed, prompt_result, network_result, target_devices)
    return decision, parsed, target_devices, fleet_manager


def test_unsafe_temperature_blocking():
    decision = build_pipeline("Set Building A thermostats to 40 degrees", "10.0.0.10")

    assert decision["decision"] == "BLOCKED"
    assert any("outside allowed range" in reason for reason in decision["reasons"])


def test_normal_trusted_command_approval():
    decision = build_pipeline("Set first 10 Building A thermostats to 22 degrees", "10.0.0.10")

    assert decision["decision"] == "APPROVED"
    assert decision["reasons"] == []


def test_trusted_ip_50_devices_without_approval_blocked():
    decision = build_pipeline("Set Building A thermostats to 22 degrees", "10.0.0.10")

    assert decision["decision"] == "BLOCKED"
    assert any("exceeding threshold" in reason for reason in decision["reasons"])


def test_trusted_ip_50_devices_with_approval_approved():
    decision = build_pipeline("Set Building A thermostats to 22 degrees", "10.0.0.10", approval_granted=True)

    assert decision["decision"] == "APPROVED"
    assert decision["reasons"] == []


def test_mass_command_blocking():
    decision = build_pipeline("Set all thermostats to 21 degrees", "10.0.0.10")

    assert decision["decision"] == "BLOCKED"
    assert any("exceeding threshold" in reason for reason in decision["reasons"])


def test_mass_command_with_approval_accepted_if_safe():
    decision = build_pipeline("Set all thermostats to 21 degrees with approval", "10.0.0.10")

    assert decision["decision"] == "APPROVED"
    assert decision["reasons"] == []


def test_signed_firmware_accepted_under_strict_profile():
    decision, _, _, _ = build_firmware_pipeline("Install firmware version 1.1.0 on first 10 thermostats", "strict")

    assert decision["decision"] == "APPROVED"
    assert decision["reasons"] == []


def test_firmware_update_does_not_populate_requested_temperature():
    parsed = SimulatedAIAssistant().parse_command("Install firmware version 1.1.0 on first 10 thermostats")

    assert parsed["intent"] == "firmware_update"
    assert parsed["requested_temperature"] is None
    assert parsed["target_device_limit"] == 10


def test_tampered_firmware_blocked_under_strict_profile():
    decision, _, _, _ = build_firmware_pipeline(
        "Install tampered firmware version 1.1.0 on first 10 thermostats",
        "strict",
    )

    assert decision["decision"] == "BLOCKED"
    assert any("Tampered firmware" in reason for reason in decision["reasons"])


def test_tampered_firmware_accepted_under_weak_profile_and_enables_backdoor():
    decision, parsed, target_devices, fleet_manager = build_firmware_pipeline(
        "Install tampered unsigned firmware version 1.1.0 with backdoor on first 5 thermostats",
        "weak_baseline",
    )

    assert decision["decision"] == "APPROVED"
    firmware_package = FirmwarePackage(**parsed["firmware_package"])
    result = fleet_manager.apply_firmware_update(firmware_package, target_devices)
    assert result["devices_compromised"] == 5
    assert all(device.backdoor_enabled for device in target_devices)
