"""Auto discover → analyze → recommend pipeline."""

from __future__ import annotations

import logging
from typing import Any

from app.analyzer.rules import analyze_resources
from app.config import Settings
from app.discovery.compute import discover_vms
from app.recommendation.ai import generate_recommendations
from app.storage.store import Store

log = logging.getLogger("costpilot.pipeline")


def run_pipeline(settings: Settings, project_id: str) -> dict[str, Any]:
    log.info("Pipeline start project=%s", project_id)
    resources = discover_vms(settings, project_id)
    store = Store(settings)
    store.save_resources(project_id, resources)
    findings = analyze_resources(resources, settings)
    store.save_findings(findings)
    recs = generate_recommendations(findings, settings)
    store.save_recommendations(recs)
    result = {
        "project_id": project_id,
        "resource_count": len(resources),
        "finding_count": len(findings),
        "recommendation_count": len(recs),
        "read_only": True,
    }
    log.info("Pipeline done %s", result)
    return result