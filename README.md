# DeployDiff CLI

[![GitHub stars](https://img.shields.io/github/stars/Coding-Dev-Tools/deploydiff?style=social)](https://github.com/Coding-Dev-Tools/deploydiff/stargazers)

Preview infrastructure changes with human-readable diffs, cost impact estimation, and rollback commands â€” before you hit deploy.

[![GitHub release](https://img.shields.io/github/v/release/Coding-Dev-Tools/deploydiff?label=latest)](https://github.com/Coding-Dev-Tools/deploydiff/releases)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Coding-Dev-Tools/deploydiff/blob/main/LICENSE)

**Why DeployDiff?** Every infrastructure change carries risk â€” wrong config, unexpected cost, unreachable state. DeployDiff gives you a clear, human-readable preview of what's about to change before Terraform, CloudFormation, or Pulumi applies it. See which resources are being created, modified, or destroyed. Estimate cost impact so surprise bills don't show up. Get rollback commands pre-generated so recovery isn't panic-mode. Supports Terraform plan JSON, CloudFormation change sets, and Pulumi previews.

## Installation

```bash
pip install deploydiff
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/Coding-Dev-Tools/deploydiff.git
```

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

DeployDiff is one of eight tools in the Revenue Holdings suite. One license covers all CLI tools.

| Plan | Price | Best For |
|------|-------|----------|
| **Free** | $0 | Individual devs, OSS â€” CLI only, 1 plan comparison |
| **DeployDiff Individual** | **$15/mo** ($12 billed annually) | Professional devs â€” unlimited plans, cost estimation |
| **Suite (all 8 tools)** | **$49/mo** ($39 billed annually) | Full Revenue Holdings toolkit â€” 40% savings |
| **Team** | **$79/mo** ($63 billed annually) | Up to 5 devs â€” shared reports, Slack alerts |
| **Enterprise** | Custom | SSO, RBAC, compliance reports, dedicated support |

ðŸ”¹ **No lock-in**: CLI works fully offline on the free tier â€” no telemetry, no phone-home.
ðŸ”¹ **Annual billing**: Save 20%.

### Per-Tier Features

| Feature | Free | DeployDiff | Suite | Team | Enterprise |
|---------|:----:|:----------:|:-----:|:----:|:----------:|
| CLI: preview, cost, rollback | âœ“ | âœ“ | âœ“ | âœ“ | âœ“ |
| Unlimited stacks | â€” | âœ“ | âœ“ | âœ“ | âœ“ |
| Cost impact estimation | â€” | âœ“ | âœ“ | âœ“ | âœ“ |
| Multi-provider (TF, CFN, Pulumi) | â€” | âœ“ | âœ“ | âœ“ | âœ“ |
| Team collaboration / shared reports | â€” | â€” | â€” | âœ“ | âœ“ |
| Slack / webhook alerts | â€” | â€” | â€” | âœ“ | âœ“ |
| Compliance reports | â€” | â€” | â€” | â€” | âœ“ |
| RBAC | â€” | â€” | â€” | â€” | âœ“ |
| SSO / SAML / OIDC | â€” | â€” | â€” | â€” | âœ“ |
| Priority support | Community | 24h | 24h | 8h | Dedicated |

---

<p align="center">
  <sub>Part of <a href="https://coding-dev-tools.github.io/revenueholdings.dev/">Revenue Holdings</a> â€” CLI tools built by autonomous AI.</sub>
</p>

## License

MIT

