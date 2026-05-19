# DeployDiff CLI

[![GitHub stars](https://img.shields.io/github/stars/Coding-Dev-Tools/deploydiff?style=social)](https://github.com/Coding-Dev-Tools/deploydiff/stargazers)
[![Awesome DevOps](https://img.shields.io/badge/Awesome_DevOps-Submitted-grey?logo=github)](https://github.com/wmariuss/awesome-devops)<!-- PR #433 -->

Preview infrastructure changes with human-readable diffs, cost impact estimation, and rollback commands — before you hit deploy.

[![GitHub release](https://img.shields.io/github/v/release/Coding-Dev-Tools/deploydiff?label=latest)](https://github.com/Coding-Dev-Tools/deploydiff/releases)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Coding-Dev-Tools/deploydiff/blob/main/LICENSE)
[![Open Source Alternative](https://img.shields.io/badge/Open_Source_Alternative-%E2%87%92-blue?logo=opensourceinitiative)](https://www.opensourcealternative.to/project/deploydiff)
[![LibHunt](https://img.shields.io/badge/LibHunt-%E2%87%92-blue?logo=codeigniter)](https://www.libhunt.com/r/Coding-Dev-Tools/deploydiff)
[![Awesome Python](https://img.shields.io/badge/Awesome_Python-%E2%87%92-blue?logo=python)](https://github.com/uhub/awesome-python)

**Why DeployDiff?** Every infrastructure change carries risk — wrong config, unexpected cost, unreachable state. DeployDiff gives you a clear, human-readable preview of what's about to change before Terraform, CloudFormation, or Pulumi applies it. See which resources are being created, modified, or destroyed. Estimate cost impact so surprise bills don't show up. Get rollback commands pre-generated so recovery isn't panic-mode. Supports Terraform plan JSON, CloudFormation change sets, and Pulumi previews.

## Installation

```bash
pip install deploydiff
```

Or install directly from GitHub:

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

**npm (Node.js wrapper):**
```bash
npm install -g deploydiff
```
Then run: `deploydiff --help`

## Usage

```bash
# Preview infrastructure changes
deploydiff preview --tf plan.json
deploydiff preview --cfn changeset.json
deploydiff preview --pulumi preview.json

# Estimate cost impact
deploydiff cost --tf plan.json
deploydiff cost --cfn changeset.json

# Generate rollback commands
deploydiff rollback --tf plan.json
deploydiff rollback --cfn changeset.json
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

## CI/CD Integration

```bash
# Preview changes in CI, gate on destructive actions
deploydiff preview --tf plan.json --exit-on-destroy || echo "Contains destructive changes!"

# Add cost check to your deployment pipeline
deploydiff cost --tf plan.json --threshold 500 || echo "Cost increase exceeds $500!"
```

## Pricing

DeployDiff is one of 11 tools in the DevForge suite. One license covers all CLI tools.

| Plan | Price | Best For |
|------|-------|----------|
| **Free** | $0 | Individual devs, OSS — CLI only, 1 plan comparison |
| **DeployDiff Individual** | **$15/mo** ($12 billed annually) | Professional devs — unlimited plans, cost estimation |
| **Suite (all 11 tools)** | **$49/mo** ($39 billed annually) | Full DevForge toolkit — 40% savings |
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
  <sub>Part of <a href="https://coding-dev-tools.github.io/devforge.dev/">DevForge</a> — CLI tools built by autonomous AI.</sub>
</p>

## License

MIT
