# DeployDiff CLI

Preview infrastructure changes with human-readable diffs, cost impact estimation, and rollback commands.

Supports: Terraform plan JSON, CloudFormation change sets, Pulumi previews.

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

## Pricing Tiers

- **Free**: 1 stack
- **Pro** ($25/mo): Unlimited stacks
- **Team** ($79/mo): Multi-stack, team collaboration

## License

MIT
