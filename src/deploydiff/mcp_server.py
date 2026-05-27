"""
MCP server entry point for deploydiff.

Starts an MCP stdio server that exposes all CLI commands as AI-callable tools.

Usage:
    deploydiff mcp                           # integrated subcommand
    deploydiff-mcp                           # standalone entry point
"""

from __future__ import annotations

import click_to_mcp


def run_mcp() -> None:
    """Start the MCP stdio server (entry point for console_scripts)."""
    from deploydiff.cli import main

    click_to_mcp.run(main, prefix="dd")


def run_for_app(app: object) -> None:
    """Start the MCP server for a given Click app (injected by cli.py)."""
    click_to_mcp.run(app, prefix="dd")
