import os
import random
from datetime import datetime, timedelta, timezone

def demo_metrics():
    # Clearly labelled demo readings; these are not AWS measurements.
    return {
        "server": "cloudpulse-demo-server",
        "status": "Online",
        "cpu": round(random.uniform(18, 92), 1),
        "memory": round(random.uniform(35, 86), 1),
        "uptime": "Demo environment",
        "source": "Simulated demo metrics",
        "timestamp": datetime.now().astimezone().isoformat()
    }

def aws_metrics():
    import boto3

    instance_id = os.getenv("EC2_INSTANCE_ID")
    region = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
    if not instance_id:
        raise ValueError("Set EC2_INSTANCE_ID in your environment before using AWS mode.")

    cloudwatch = boto3.client("cloudwatch", region_name=region)
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=15)

    cpu_response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=start,
        EndTime=end,
        Period=300,
        Statistics=["Average"]
    )
    points = sorted(cpu_response.get("Datapoints", []), key=lambda x: x["Timestamp"])
    cpu = round(points[-1]["Average"], 1) if points else None

    status_response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="StatusCheckFailed",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=start,
        EndTime=end,
        Period=300,
        Statistics=["Maximum"]
    )
    status_points = sorted(status_response.get("Datapoints", []), key=lambda x: x["Timestamp"])
    failed = bool(status_points and status_points[-1]["Maximum"] >= 1)
    status_label = "Issue detected" if failed else ("Running (status check passed)" if status_points else "Status data unavailable")

    return {
        "server": instance_id,
        "status": status_label,
        "cpu": cpu,
        "memory": None,
        "uptime": "AWS EC2 instance",
        "source": f"AWS CloudWatch - {region}",
        "timestamp": datetime.now().astimezone().isoformat(),
        "note": "Memory is not available from default EC2 metrics. Install the CloudWatch Agent to publish memory metrics."
    }

def get_metrics(mode="demo"):
    if mode == "aws":
        return aws_metrics()
    return demo_metrics()
