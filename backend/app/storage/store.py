"""Local JSON store by default (₹0). Optional BigQuery for real analytics demo."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from app.config import Settings


class Store:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.root = Path(settings.data_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.root / f"{name}.json"

    def _read(self, name: str) -> Any:
        path = self._path(name)
        if not path.exists():
            return [] if name != "meta" else {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _write(self, name: str, data: Any) -> None:
        """Atomic write to avoid partial JSON on crash."""
        path = self._path(name)
        fd, tmp_name = tempfile.mkstemp(dir=self.root, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_name, path)
        except Exception:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
            raise

    def save_resources(self, project_id: str, resources: list[dict[str, Any]]) -> None:
        self._write("resources", {"project_id": project_id, "items": resources})
        if self.settings.storage_backend == "bigquery":
            self._write_bigquery(resources)

    def get_resources(self) -> dict[str, Any]:
        data = self._read("resources")
        if isinstance(data, list):
            return {"project_id": "", "items": data}
        return data or {"project_id": "", "items": []}

    def save_findings(self, findings: list[dict[str, Any]]) -> None:
        self._write("findings", findings)

    def get_findings(self) -> list[dict[str, Any]]:
        data = self._read("findings")
        return data if isinstance(data, list) else []

    def save_recommendations(self, items: list[dict[str, Any]]) -> None:
        self._write("recommendations", items)

    def get_recommendations(self) -> list[dict[str, Any]]:
        data = self._read("recommendations")
        return data if isinstance(data, list) else []

    def _write_bigquery(self, resources: list[dict[str, Any]]) -> None:
        from google.cloud import bigquery

        client = bigquery.Client(project=self.settings.gcp_project_id or None)
        table_id = f"{client.project}.{self.settings.bigquery_dataset}.{self.settings.bigquery_table}"
        rows = [
            {
                "resource_id": r.get("resource_id"),
                "name": r.get("name"),
                "project_id": r.get("project_id"),
                "machine_type": r.get("machine_type"),
                "cpu_utilization_pct": r.get("cpu_utilization_pct"),
                "memory_utilization_pct": r.get("memory_utilization_pct"),
                "disk_utilization_pct": r.get("disk_utilization_pct"),
                "observed_at": r.get("observed_at"),
            }
            for r in resources
        ]
        if rows:
            errors = client.insert_rows_json(table_id, rows)
            if errors:
                raise RuntimeError(f"BigQuery insert errors: {errors}")