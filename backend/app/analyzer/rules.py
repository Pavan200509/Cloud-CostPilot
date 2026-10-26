"""Simple rule-based findings for live inventory + optional utilization."""

from __future__ import annotations

from typing import Any

from app.config import Settings


def analyze_resources(resources: list[dict[str, Any]], settings: Settings) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    threshold = settings.cpu_underutilized_pct

    for r in resources:
        name = r.get("name", "unknown")
        cpu = r.get("cpu_utilization_pct")
        mem = r.get("memory_utilization_pct")
        cores = r.get("cpu_cores")
        machine = r.get("machine_type")

        if cpu is not None and cpu < threshold:
            findings.append(
                {
                    "resource_id": r.get("resource_id"),
                    "resource_name": name,
                    "finding_type": "underutilized_cpu",
                    "severity": "medium",
                    "summary": f"{name} CPU ~{cpu}% (below {threshold}% threshold).",
                    "metrics": {
                        "cpu_utilization_pct": cpu,
                        "memory_utilization_pct": mem,
                        "cpu_cores": cores,
                        "memory_gb": r.get("memory_gb"),
                    },
                    "machine_type": machine,
                }
            )
        elif mem is not None and mem < threshold:
            findings.append(
                {
                    "resource_id": r.get("resource_id"),
                    "resource_name": name,
                    "finding_type": "underutilized_memory",
                    "severity": "low",
                    "summary": f"{name} memory ~{mem}% (below {threshold}% threshold).",
                    "metrics": {"cpu_utilization_pct": cpu, "memory_utilization_pct": mem},
                    "machine_type": machine,
                }
            )
        else:
            # Live inventory without Monitoring metrics: still produce a review finding for Gemini.
            size_note = f"{cores} vCPU / {r.get('memory_gb')} GB" if cores else machine
            findings.append(
                {
                    "resource_id": r.get("resource_id"),
                    "resource_name": name,
                    "finding_type": "rightsizing_review",
                    "severity": "low",
                    "summary": (
                        f"{name} is {r.get('status')} in {r.get('zone')} on {machine} ({size_note}). "
                        "Review whether this size matches actual workload demand."
                    ),
                    "metrics": {
                        "cpu_cores": cores,
                        "memory_gb": r.get("memory_gb"),
                        "status": r.get("status"),
                        "zone": r.get("zone"),
                    },
                    "machine_type": machine,
                }
            )

        if r.get("status") and r.get("status") != "RUNNING":
            findings.append(
                {
                    "resource_id": r.get("resource_id"),
                    "resource_name": name,
                    "finding_type": "non_running_instance",
                    "severity": "info",
                    "summary": f"{name} status is {r.get('status')}. Confirm if this instance is still needed.",
                    "metrics": {"status": r.get("status")},
                    "machine_type": machine,
                }
            )

    return findings