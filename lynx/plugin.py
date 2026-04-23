"""Entry-point registration for the Lince Investor Suite plugin system.

Exposed via ``pyproject.toml`` under the ``lynx_investor_suite.agents``
entry-point group. See :mod:`lynx_investor_core.plugins` for the
discovery contract.

``lynx-fundamental`` is the generic / cross-sector agent. It participates
in the plugin registry so the dashboard treats it uniformly alongside the
sector-specialized agents.
"""

from __future__ import annotations

from lynx_investor_core.plugins import SectorAgent

from lynx import __version__


def register() -> SectorAgent:
    """Return this agent's descriptor for the plugin registry."""
    return SectorAgent(
        name="lynx-fundamental",
        short_name="fundamental",
        sector="General (any sector)",
        tagline="Value investing + moat analysis for any public company",
        prog_name="lynx-fundamental",
        version=__version__,
        package_module="lynx",
        entry_point_module="lynx.__main__",
        entry_point_function="main",
        icon="\U0001f4ca",  # bar chart
    )
