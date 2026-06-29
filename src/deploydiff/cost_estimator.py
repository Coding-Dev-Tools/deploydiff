"""Cost impact estimation with local pricing data."""

from __future__ import annotations

import json
from pathlib import Path

from .models import ChangeAction, CostEstimate, DeployPlan, ResourceChange

# Local pricing data for common AWS resources (monthly estimates in USD)
# These are baseline estimates; real pricing varies by region, usage, etc.
DEFAULT_PRICING: dict[str, dict[str, float]] = {
    # EC2 instances (monthly per instance, on-demand)
    "aws_instance": {
        "t3.micro": 7.50,
        "t3.small": 15.00,
        "t3.medium": 30.00,
        "t3.large": 60.48,
        "t3.xlarge": 120.96,
        "t3.2xlarge": 241.92,
        "m5.large": 70.00,
        "m5.xlarge": 140.00,
        "m5.2xlarge": 280.00,
        "c5.large": 62.00,
        "c5.xlarge": 124.00,
        "default": 50.00,
    },
    # RDS instances (monthly per instance)
    "aws_db_instance": {
        "db.t3.micro": 12.50,
        "db.t3.small": 25.00,
        "db.t3.medium": 50.00,
        "db.t3.large": 100.00,
        "db.m5.large": 122.00,
        "db.m5.xlarge": 244.00,
        "default": 80.00,
    },
    # S3 (monthly estimate for typical usage)
    "aws_s3_bucket": {
        "default": 1.00,
    },
    # Lambda
    "aws_lambda_function": {
        "default": 0.50,
    },
    # DynamoDB
    "aws_dynamodb_table": {
        "default": 25.00,
    },
    # ECS/Fargate (monthly per task)
    "aws_ecs_service": {
        "default": 30.00,
    },
    # EKS
    "aws_eks_cluster": {
        "default": 73.00,
    },
    # CloudFront
    "aws_cloudfront_distribution": {
        "default": 10.00,
    },
    # ALB/NLB
    "aws_lb": {
        "default": 16.00,
    },
    # ElastiCache
    "aws_elasticache_cluster": {
        "cache.t3.micro": 12.00,
        "cache.t3.small": 24.00,
        "cache.t3.medium": 48.00,
        "cache.m5.large": 92.00,
        "default": 50.00,
    },
    # CloudWatch
    "aws_cloudwatch_log_group": {
        "default": 0.50,
    },
    # VPC/NAT Gateway
    "aws_nat_gateway": {
        "default": 32.00,
    },
    # EBS volumes
    "aws_ebs_volume": {
        "gp2": 0.80,
        "gp3": 0.60,
        "io1": 2.00,
        "default": 1.00,
    },
    # SNS
    "aws_sns_topic": {
        "default": 0.50,
    },
    # SQS
    "aws_sqs_queue": {
        "default": 0.40,
    },
    # KMS
    "aws_kms_key": {
        "default": 1.00,
    },
    # IAM
    "aws_iam_role": {
        "default": 0.00,
    },
    "aws_iam_policy": {
        "default": 0.00,
    },
    # Security groups
    "aws_security_group": {
        "default": 0.00,
    },
    # VPC
    "aws_vpc": {
        "default": 0.00,
    },
    "aws_subnet": {
        "default": 0.00,
    },
    # CloudFormation types
    "AWS::EC2::Instance": {
        "default": 50.00,
    },
    "AWS::RDS::DBInstance": {
        "default": 80.00,
    },
    "AWS::S3::Bucket": {
        "default": 1.00,
    },
    "AWS::Lambda::Function": {
        "default": 0.50,
    },
    "AWS::DynamoDB::Table": {
        "default": 25.00,
    },
    "AWS::ECS::Service": {
        "default": 30.00,
    },
    "AWS::EKS::Cluster": {
        "default": 73.00,
    },
    "AWS::CloudFront::Distribution": {
        "default": 10.00,
    },
    "AWS::ElasticLoadBalancingV2::LoadBalancer": {
        "default": 16.00,
    },
    "AWS::ElastiCache::CacheCluster": {
        "default": 50.00,
    },
    "AWS::EC2::NatGateway": {
        "default": 32.00,
    },
}


def estimate_costs(
    plan: DeployPlan, pricing_file: str | Path | None = None
) -> list[CostEstimate]:
    """Estimate monthly cost impact for each resource change in a plan.

    Args:
        plan: Parsed deployment plan.
        pricing_file: Optional path to custom pricing JSON file.

    Returns:
        List of CostEstimate objects, one per changed resource.
    """
    pricing = _load_pricing(pricing_file)
    estimates: list[CostEstimate] = []

    for change in plan.changes:
        before_cost = _estimate_resource_cost(change, pricing, before=True)
        after_cost = _estimate_resource_cost(change, pricing, before=False)

        estimate = CostEstimate(
            resource_address=change.address,
            monthly_cost_before=before_cost,
            monthly_cost_after=after_cost,
            description=_build_cost_description(change, before_cost, after_cost),
        )
        estimates.append(estimate)

    plan.cost_estimates = estimates
    return estimates


def _estimate_resource_cost(
    change: ResourceChange,
    pricing: dict[str, dict[str, float]],
    before: bool = False,
) -> float:
    """Estimate the monthly cost for a single resource.

    Args:
        change: The resource change.
        pricing: Pricing lookup table.
        before: If True, estimate the "before" cost; otherwise "after".
    """
    # If deleting, after cost is 0; if creating, before cost is 0
    if before and change.action == ChangeAction.CREATE:
        return 0.0
    if not before and change.action in (
        ChangeAction.DELETE,
        ChangeAction.DELETE_BEFORE_CREATE,
    ):
        return 0.0

    resource_type = change.resource_type
    type_pricing = pricing.get(resource_type, {"default": 5.00})

    # Try to find an instance type / size key in the resource config
    data = change.before if before else change.after
    if data and isinstance(data, dict):
        for field in (
            "instance_type",
            "InstanceType",
            "node_type",
            "NodeType",
            "volume_type",
            "engine",
        ):
            val = data.get(field, "")
            if val and str(val) in type_pricing:
                return type_pricing[str(val)]

    return type_pricing.get("default", 5.00)


def _build_cost_description(change: ResourceChange, before: float, after: float) -> str:
    """Build a human-readable cost description."""
    delta = after - before
    if delta > 0:
        return f"+${delta:.2f}/mo"
    elif delta < 0:
        return f"-${abs(delta):.2f}/mo"
    return "no change"


def _load_pricing(
    pricing_file: str | Path | None = None,
) -> dict[str, dict[str, float]]:
    """Load pricing data from a custom file, falling back to defaults."""
    if pricing_file is None:
        return DEFAULT_PRICING.copy()

    path = Path(pricing_file)
    if not path.exists():
        return DEFAULT_PRICING.copy()

    with open(path) as f:
        custom = json.load(f)

    # Merge with defaults (custom overrides)
    merged = DEFAULT_PRICING.copy()
    for resource_type, prices in custom.items():
        if resource_type in merged:
            merged[resource_type].update(prices)
        else:
            merged[resource_type] = prices

    return merged
