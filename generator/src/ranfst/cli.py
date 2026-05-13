# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Command-line interface for the ranfst synthetic data generator.

Usage:
    ranfst list-scenarios
    ranfst describe --scenario A
    ranfst generate --scenario A --seed 42 --output ./data/scenario_A.parquet
"""
from __future__ import annotations

import sys
from pathlib import Path

import click

from ranfst import __version__
from ranfst.scenarios import REGISTRY


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="ranfst")
def main() -> None:
    """RAN synthetic telemetry generator CLI."""


@main.command("list-scenarios")
def list_scenarios() -> None:
    """List all available scenarios."""
    click.echo(f"{'ID':<4} {'Name':<50} {'Triply':<7}")
    click.echo("-" * 65)
    for sid in sorted(REGISTRY):
        cls = REGISTRY[sid]
        triply = "yes" if getattr(cls, "TRIPLY_CITED", False) else "-"
        click.echo(f"{sid:<4} {cls.NAME:<50} {triply:<7}")


@main.command("describe")
@click.option("--scenario", "-s", required=True, help="Scenario ID (e.g. S, A, B, ...)")
def describe(scenario: str) -> None:
    """Print the description of a scenario."""
    if scenario not in REGISTRY:
        click.echo(f"Unknown scenario: {scenario}", err=True)
        click.echo(f"Available: {', '.join(sorted(REGISTRY))}", err=True)
        sys.exit(1)
    cls = REGISTRY[scenario]
    click.echo(f"Scenario {scenario}: {cls.NAME}")
    click.echo("=" * 70)
    click.echo(cls.__doc__ or "No description available.")


@main.command("generate")
@click.option("--scenario", "-s", required=True)
@click.option("--seed", type=int, required=True)
@click.option("--output", "-o", type=click.Path(path_type=Path), required=True)
@click.option("--n-cells", type=int, default=None)
@click.option("--duration-days", type=float, default=None)
@click.option("--granularity", type=click.Choice(["fast", "slow", "both"]), default="slow")
def generate(scenario: str, seed: int, output: Path, n_cells: int | None,
             duration_days: float | None, granularity: str) -> None:
    """Generate a synthetic dataset for a scenario."""
    if scenario not in REGISTRY:
        click.echo(f"Unknown scenario: {scenario}", err=True)
        sys.exit(1)
    cls = REGISTRY[scenario]
    instance = cls(seed=seed, n_cells=n_cells,
                   duration_days=duration_days, granularity=granularity)
    output.parent.mkdir(parents=True, exist_ok=True)
    instance.generate(output)
    click.echo(f"Wrote: {output}")


if __name__ == "__main__":
    main()
