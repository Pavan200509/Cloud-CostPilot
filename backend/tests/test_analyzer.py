from app.analyzer.rules import analyze_resources
from app.config import Settings


def test_rightsizing_review_without_metrics():
    settings = Settings()
    resources = [
        {
            "resource_id": "r1",
            "name": "vm-a",
            "machine_type": "e2-standard-4",
            "status": "RUNNING",
            "zone": "us-central1-a",
            "cpu_cores": 4,
            "memory_gb": 16,
            "cpu_utilization_pct": None,
            "memory_utilization_pct": None,
        }
    ]
    findings = analyze_resources(resources, settings)
    assert any(f["finding_type"] == "rightsizing_review" for f in findings)


def test_underutilized_cpu():
    settings = Settings()
    resources = [
        {
            "resource_id": "r2",
            "name": "vm-low",
            "machine_type": "e2-standard-4",
            "status": "RUNNING",
            "cpu_utilization_pct": 10.0,
            "memory_utilization_pct": 40.0,
        }
    ]
    findings = analyze_resources(resources, settings)
    assert any(f["finding_type"] == "underutilized_cpu" for f in findings)