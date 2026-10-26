from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.auth.users import AuthStore
from app.config import Settings, get_settings
from app.discovery.compute import list_projects
from app.services.pipeline import run_pipeline
from app.services.scheduler import scheduler
from app.storage.store import Store

router = APIRouter(tags=["costpilot"])


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(default="", max_length=80)


class LoginBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class ConnectBody(BaseModel):
    cloud: str = Field(default="gcp", pattern="^(gcp)$")
    project_id: str = Field(..., min_length=3, max_length=128, pattern=r"^[a-z][a-z0-9\-]+$")


def _auth(settings: Settings = Depends(get_settings)) -> AuthStore:
    return AuthStore(settings)


def _token(authorization: str | None = Header(default=None)) -> str | None:
    if not authorization:
        return None
    if authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return authorization.strip()


def current_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> dict:
    user = _auth(settings).user_from_token(_token(authorization))
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    return user


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "discovery_mode": settings.discovery_mode,
        "storage_backend": settings.storage_backend,
        "ai_provider": settings.ai_provider,
        "gemini_configured": bool(settings.gemini_api_key),
        "refresh_interval_seconds": settings.refresh_interval_seconds,
        "read_only": True,
    }


@router.post("/auth/register")
def register(body: RegisterBody, settings: Settings = Depends(get_settings)) -> dict:
    try:
        user = _auth(settings).register(body.email, body.password, body.name)
        token, profile = _auth(settings).login(body.email, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"token": token, "user": profile}


@router.post("/auth/login")
def login(body: LoginBody, settings: Settings = Depends(get_settings)) -> dict:
    try:
        token, profile = _auth(settings).login(body.email, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {"token": token, "user": profile}


@router.post("/auth/logout")
def logout(authorization: str | None = Header(default=None), settings: Settings = Depends(get_settings)) -> dict:
    _auth(settings).logout(_token(authorization) or "")
    return {"ok": True}


@router.get("/auth/me")
def me(user: dict = Depends(current_user)) -> dict:
    return {"user": user}


@router.get("/clouds")
def clouds() -> dict:
    return {
        "clouds": [
            {"id": "gcp", "name": "Google Cloud", "enabled": True},
            {"id": "aws", "name": "Amazon Web Services", "enabled": False, "status": "coming_soon"},
            {"id": "azure", "name": "Microsoft Azure", "enabled": False, "status": "coming_soon"},
        ]
    }


@router.get("/projects")
def projects(user: dict = Depends(current_user), settings: Settings = Depends(get_settings)) -> dict:
    try:
        return {"projects": list_projects(settings)}
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not list GCP projects. Run ADC login locally or attach a runtime SA. ({exc})",
        ) from exc


@router.post("/connect")
def connect(
    body: ConnectBody,
    user: dict = Depends(current_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Save cloud project and immediately run discovery + analysis + Gemini recommendations."""
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY missing. Add your AI Studio key to backend .env and restart.",
        )
    auth = _auth(settings)
    profile = auth.update_cloud(user["id"], body.cloud, body.project_id)
    try:
        result = run_pipeline(settings, body.project_id)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Live discovery failed. Check ADC/service account and project id. ({exc})",
        ) from exc
    scheduler.set_project(body.project_id)
    return {"user": profile, "pipeline": result}


@router.get("/resources")
def resources(user: dict = Depends(current_user), settings: Settings = Depends(get_settings)) -> dict:
    data = Store(settings).get_resources()
    items = data.get("items", [])
    compute = [i for i in items if i.get("resource_type") == "compute_vm" or "instances" in str(i.get("resource_id", ""))]
    return {
        "project_id": data.get("project_id"),
        "sections": {"compute": {"vms": compute}},
        "count": len(items),
    }


@router.get("/analysis")
def analysis(user: dict = Depends(current_user), settings: Settings = Depends(get_settings)) -> dict:
    findings = Store(settings).get_findings()
    return {"findings": findings, "count": len(findings)}


@router.get("/recommendations")
def recommendations(user: dict = Depends(current_user), settings: Settings = Depends(get_settings)) -> dict:
    items = Store(settings).get_recommendations()
    return {"recommendations": items, "count": len(items)}


@router.post("/refresh")
def refresh(user: dict = Depends(current_user), settings: Settings = Depends(get_settings)) -> dict:
    project_id = user.get("gcp_project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="Connect a GCP project first")
    try:
        result = run_pipeline(settings, project_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return result