from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from security.network_policy import NetworkPolicy


def test_unauthorized_ip_blocking():
    policy = NetworkPolicy(PROJECT_ROOT / "config" / "network_rules.yaml")
    result = policy.check_source_ip("203.0.113.50")

    assert result["allowed"] is False
    assert "blocked" in result["reason"]
