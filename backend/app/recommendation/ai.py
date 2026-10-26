"""Gemini recommendations (free-tier AI Studio key). Requires GEMINI_API_KEY."""

from __future__ import annotations

from typing import Any

from app.config import Settings


def _gemini_recommendation(finding: dict[str, Any], settings: Settings) -> dict[str, Any]:
    import google.generativeai as genai

    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)
    prompt = (
        "You are a cloud FinOps advisor for Cloud CostPilot. "
        "Give ONE short recommendation (max 3 sentences). "
        "Do not claim the app will change cloud resources. Advise the human only. "
        f"Finding type: {finding.get('finding_type')}. "
        f"Summary: {finding.get('summary')}. "
        f"Machine type: {finding.get('machine_type')}. "
        f"Metrics: {finding.get('metrics')}."
    )
    response = model.generate_content(
        prompt,
        generation_config={"max_output_tokens": 140, "temperature": 0.2},
    )
    text = (getattr(response, "text", None) or "").strip()
    if not text:
        text = finding.get("summary") or "Review this resource for cost optimization."
    return {
        "resource_id": finding.get("resource_id"),
        "resource_name": finding.get("resource_name"),
        "finding_type": finding.get("finding_type"),
        "severity": finding.get("severity"),
        "recommendation": text,
        "provider": "gemini",
        "model": settings.gemini_model,
        "actionable_by_platform": False,
    }


def generate_recommendations(findings: list[dict[str, Any]], settings: Settings) -> list[dict[str, Any]]:
    results = []
    for finding in findings:
        try:
            results.append(_gemini_recommendation(finding, settings))
        except Exception as exc:
            results.append(
                {
                    "resource_id": finding.get("resource_id"),
                    "resource_name": finding.get("resource_name"),
                    "finding_type": finding.get("finding_type"),
                    "severity": finding.get("severity"),
                    "recommendation": finding.get("summary")
                    or "Recommendation unavailable. Check GEMINI_API_KEY and free-tier quota.",
                    "provider": "gemini_error",
                    "error": str(exc),
                    "actionable_by_platform": False,
                }
            )
    return results