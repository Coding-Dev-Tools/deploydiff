# DeployDiff CLI

Preview infrastructure changes with cost impact estimates and rollback commands — **before** you apply anything.

[![PyPI](https://img.shields.io/pypi/v/deploydiff)](https://pypi.org/project/deploydiff/)
[![Python](https://img.shields.io/pypi/pyversions/deploydiff)](https://pypi.org/project/deploydiff/)
[![License](https://img.shields.io/pypi/l/deploydiff)](https://github.com/Coding-Dev-Tools/deploydiff/blob/main/LICENSE)

**Why DeployDiff?** Infrastructure teams need clarity before applying changes. DeployDiff decodes Terraform, CloudFormation, and Pulumi plans into a clear, human-readable preview — showing exactly what changes, what they'll cost, and how to roll back. Teams that preview before applying ship faster with fewer incidents. Works with Terraform, CloudFormation, and Pulumi out of the box.

## Install

```bash
pip install deploydiff
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

## Pricing

One license covers all Revenue Holdings CLI tools. Pricing is per-seat.

| Tier | Price | Best For |
|------|-------|----------|
| **Open Source** | $0 | Individual devs, OSS projects — CLI only, 1 stack |
| **Pro** | **$29/mo** ($23 billed annually) | Professional devs — unlimited stacks, cost estimation |
| **Team** | **$79/mo** ($63 billed annually) | Teams up to 5 — multi-stack orchestration, priority support |
| **Enterprise** | **$199/mo** (custom) | Organizations — SSO/SAML, RBAC, dedicated support, SLA |

🔹 **No lock-in**: CLI works fully offline on the free tier — no telemetry, no phone-home.  
🔹 **Annual billing**: Save 20%.  

### Per-Tier Features

| Feature | OSS | Pro | Team | Enterprise |
|---------|:---:|:---:|:----:|:----------:|
| Preview (Terraform, CloudFormation, Pulumi) | ✓ | ✓ | ✓ | ✓ |
| Unlimited stacks | — | ✓ | ✓ | ✓ |
| Cost impact estimation | — | ✓ | ✓ | ✓ |
| Rollback command generation | — | ✓ | ✓ | ✓ |
| Multi-stack orchestration | — | — | ✓ | ✓ |
| Priority support | Community | 24h | 8h | Dedicated |
| SSO / SAML / OIDC | — | — | — | ✓ |

---

<p align="center">
  <sub>Part of <a href="https://coding-dev-tools.github.io/revenueholdings.dev/">Revenue Holdings</a> — CLI tools built by autonomous AI.</sub>
</p>

## License

MIT
