# DeployDiff CLI

[![GitHub stars](https://img.shields.io/github/stars/Coding-Dev-Tools/deploydiff?style=social)](https://github.com/Coding-Dev-Tools/deploydiff/stargazers)

Preview infrastructure changes with human-readable diffs, cost impact estimation, and rollback commands — before you hit deploy.

> ⭐ **Star this repo** if you manage infrastructure — it helps other devs find DeployDiff!

[![GitHub release](https://img.shields.io/github/v/release/Coding-Dev-Tools/deploydiff?label=latest)](https://github.com/Coding-Dev-Tools/deploydiff/releases)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Coding-Dev-Tools/deploydiff/blob/main/LICENSE)
[![Open Source Alternative](https://img.shields.io/badge/Open_Source_Alternative-%E2%87%92-blue?logo=opensourceinitiative)](https://www.opensourcealternative.to/project/deploydiff)
|[![LibHunt](https://img.shields.io/badge/LibHunt-%E2%87%92-blue?logo=codeigniter)](https://www.libhunt.com/r/Coding-Dev-Tools/deploydiff)
|[![PyPI](https://img.shields.io/pypi/v/deploydiff)](https://pypi.org/project/deploydiff/)

## Installation

```bash
pip install deploydiff
```

Or install the latest version directly from GitHub:
```bash
pip install git+https://github.com/Coding-Dev-Tools/deploydiff.git
```

Or install via Homebrew (macOS/Linux):
```bash
brew tap Coding-Dev-Tools/tap
brew install deploydiff
```

Or install via Scoop (Windows):
```bash
scoop bucket add Coding-Dev-Tools https://github.com/Coding-Dev-Tools/scoop-bucket
scoop install deploydiff
```

## Usage

```bash
# Preview infrastructure changes
deploydiff preview --tf plan.json
deploydiff preview --cfn changeset.json
deploydiff preview --pulumi preview.json
deploydiff preview --tf plan.json -v  # verbose: before/after details

# Estimate cost impact
deploydiff cost --tf plan.json
deploydiff cost --cfn changeset.json
deploydiff cost --tf plan.json --pricing custom-pricing.json

# Generate rollback commands
deploydiff rollback --tf plan.json
deploydiff rollback --cfn changeset.json

# Run as MCP server (for AI agent integration)
deploydiff mcp
```

### What You Get With `preview`

- **Resource summary**: count of creates, updates, deletes, and replaces
- **Property-level diffs**: what changed, from what to what
- **Destructive action highlighting**: replaces and deletions called out
- **Multi-provider**: Terraform, CloudFormation, Pulumi from a single CLI

### What You Get With `cost`

- **Cost impact estimate**: before vs. after per resource
- **Provider-native pricing**: reads Terraform/CFN cost metadata
- **Summary row**: total monthly change

### What You Get With `rollback`

- **Generated rollback commands**: reverse the last plan
- **Provider-specific**: correct syntax for Terraform, CloudFormation
- **No manual command construction**: eliminates panic-mode mistakes

## MCP Server Mode

DeployDiff can run as an MCP (Model Context Protocol) server, letting AI coding agents like Claude Code and Cursor interact with your infrastructure diffs directly:

```bash
# Start MCP server (requires click-to-mcp)
deploydiff mcp
```

## CI/CD Integration

```bash
# Preview changes in CI pipeline
deploydiff preview --tf plan.json

# Check cost impact before deploy
deploydiff cost --tf plan.json

# Generate rollback commands for rapid recovery
deploydiff rollback --tf plan.json
```

Combine with shell scripting for pipeline gating:

```bash
# Gate on destructive changes (check preview output for destroy actions)
deploydiff preview --tf plan.json | grep -q "destroy" && echo "WARNING: Contains destructive changes!"

# Check cost impact (use --pricing for custom pricing data)
deploydiff cost --tf plan.json --pricing custom-pricing.json
```

## Pricing

DeployDiff is one of 11 tools in the Revenue Holdings suite. One license covers all CLI tools.

| Plan | Price | Best For |
|------|-------|----------|
| **Free** | $0 | Individual devs, OSS — CLI only, 1 plan comparison |
| **DeployDiff Individual** | **$15/mo** ($12 billed annually) | Professional devs — unlimited plans, cost estimation |
| **Suite (all 11 tools)** | **$49/mo** ($39 billed annually) | Full Revenue Holdings toolkit — 40% savings |
| **Team** | **$79/mo** ($63 billed annually) | Up to 5 devs — shared reports, Slack alerts |
| **Enterprise** | Custom | SSO, RBAC, compliance reports, dedicated support |

🔹 **No lock-in**: CLI works fully offline on the free tier — no telemetry, no phone-home.
🔹 **Annual billing**: Save 20%.

### Per-Tier Features

| Feature | Free | DeployDiff | Suite | Team | Enterprise |
|---------|:----:|:----------:|:-----:|:----:|:----------:|
| CLI: preview, cost, rollback | ✓ | ✓ | ✓ | ✓ | ✓ |
| Unlimited stacks | — | ✓ | ✓ | ✓ | ✓ |
| Cost impact estimation | — | ✓ | ✓ | ✓ | ✓ |
| Multi-provider (TF, CFN, Pulumi) | — | ✓ | ✓ | ✓ | ✓ |
| Team collaboration / shared reports | — | — | — | ✓ | ✓ |
| Slack / webhook alerts | — | — | — | ✓ | ✓ |
| Compliance reports | — | — | — | — | ✓ |
| RBAC | — | — | — | — | ✓ |
| SSO / SAML / OIDC | — | — | — | — | ✓ |
| Priority support | Community | 24h | 24h | 8h | Dedicated |

---

<p align="center">
  <sub>Part of <a href="https://coding-dev-tools.github.io/devforge/">Revenue Holdings</a> — CLI tools built by autonomous AI.</sub>
</p>

## License

MIT

## Install

```bash
npm install
```

## Test

```bash
npm test  # runs: node --test tests/
```
