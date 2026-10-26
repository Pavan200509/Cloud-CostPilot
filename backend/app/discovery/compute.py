"""Read-only Compute Engine discovery using ADC / runtime service account."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.config import Settings

_MACHINE_HINTS = {
    "e2-micro": (2, 1),
    "e2-small": (2, 2),
    "e2-medium": (2, 4),
    "e2-standard-2": (2, 8),
    "e2-standard-4": (4, 16),
    "e2-standard-8": (8, 32),
    "e2-highmem-2": (2, 16),
    "e2-highmem-4": (4, 32),
    "e2-highmem-8": (8, 64),
    "n1-standard-1": (1, 3.75),
    "n1-standard-2": (2, 7.5),
    "n1-standard-4": (4, 15),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _machine_specs(machine_type: str) -> tuple[int | None, float | None]:
    if machine_type in _MACHINE_HINTS:
        return _MACHINE_HINTS[machine_type]
    m = re.match(r".*-standard-(\d+)$", machine_type)
    if m:
        cores = int(m.group(1))
        return cores, float(cores * 4)
    m = re.match(r".*-highmem-(\d+)$", machine_type)
    if m:
        cores = int(m.group(1))
        return cores, float(cores * 8)
    return None, None


def list_projects(settings: Settings) -> list[dict[str, str]]:
    from google.cloud import resourcemanager_v3

    client = resourcemanager_v3.ProjectsClient()
    projects = []
    for p in client.search_projects():
        if p.state.name == "ACTIVE":
            projects.append({"project_id": p.project_id, "name": p.display_name or p.project_id})
    if settings.gcp_project_id and not any(x["project_id"] == settings.gcp_project_id for x in projects):
        projects.insert(0, {"project_id": settings.gcp_project_id, "name": settings.gcp_project_id})
    return projects


def discover_vms(settings: Settings, project_id: str) -> list[dict[str, Any]]:
    from google.cloud import compute_v1

    client = compute_v1.InstancesClient()
    agg = client.aggregated_list(project=project_id)
    vms: list[dict[str, Any]] = []
    for zone_path, response in agg:
        if not response.instances:
            continue
        zone = zone_path.split("/")[-1]
        for inst in response.instances:
            mt = inst.machine_type.split("/")[-1] if inst.machine_type else "unknown"
            cores, mem = _machine_specs(mt)
            vms.append(
                {
                    "resource_id": f"{project_id}/zones/{zone}/instances/{inst.name}",
                    "name": inst.name,
                    "project_id": project_id,
                    "zone": zone,
                    "machine_type": mt,
                    "status": inst.status,
                    "cpu_cores": cores,
                    "memory_gb": mem,
                    "cpu_utilization_pct": None,
                    "memory_utilization_pct": None,
                    "disk_utilization_pct": None,
                    "observed_at": _now(),
                    "provider": "gcp",
                    "resource_type": "compute_vm",
                }
            )
    return vms