"""
MCP server entry point for deploydiff.

Starts an MCP stdio server that exposes all CLI commands as AI-callable tools.

Usage:
    deploydiff mcp                           # integrated subcommand
    deploydiff-mcp                           # standalone entry point
"""

from __future__ import annotations


def run_mcp() -> None:
    """Start the MCP stdio server (entry point for console_scripts)."""
    try:
        import click_to_mcp
    except ImportError:
        import sys

        print(
            "Error: click-to-mcp is not installed. "
            "Install it with: pip install click-to-mcp",
            file=sys.stderr,
        )
        sys.exit(1)

    from deploydiff.cli import main

    click_to_mcp.run(main, prefix="dd")


def run_for_app(app: object) -> None:
    """Start the MCP server for a given Click app (injected by cli.py)."""
    try:
        import click_to_mcp
    except ImportError:
        import sys

        print(
            "Error: click-to-mcp is not installed. "
            "Install it with: pip install click-to-mcp",
            file=sys.stderr,
        )
        sys.exit(1)

    click_to_mcp.run(app, prefix="dd")
