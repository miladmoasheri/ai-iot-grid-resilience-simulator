"""Experiment configuration loading for Phase 4."""

from __future__ import annotations

from pathlib import Path

import yaml


class ExperimentConfig:
    """Loads and validates Phase 4 experiment settings."""

    required_sections = {
        "monte_carlo",
        "fleet",
        "attack",
        "security_configurations",
        "power",
        "objective_weights",
    }

    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        with self.config_path.open("r", encoding="utf-8") as config_file:
            self.data = yaml.safe_load(config_file)
        self.validate()

    def validate(self) -> None:
        missing = self.required_sections - set(self.data)
        if missing:
            raise ValueError(f"Missing experiment config sections: {', '.join(sorted(missing))}")

        if int(self.data["monte_carlo"]["runs_per_configuration"]) <= 0:
            raise ValueError("monte_carlo.runs_per_configuration must be positive.")

        if not self.data["security_configurations"]:
            raise ValueError("At least one security configuration is required.")

    @property
    def runs(self) -> int:
        return self.runs_per_configuration * len(self.security_configuration_names)

    @property
    def runs_per_configuration(self) -> int:
        return int(self.data["monte_carlo"]["runs_per_configuration"])

    @property
    def random_seed(self) -> int:
        return int(self.data["monte_carlo"]["random_seed"])

    @property
    def security_configuration_names(self) -> list[str]:
        return list(self.data["security_configurations"].keys())
