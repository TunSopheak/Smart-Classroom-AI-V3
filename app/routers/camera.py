from fastapi import APIRouter

router = APIRouter(prefix="/camera", tags=["camera"])


@router.get("/health")
def camera_health():
    return {"status": "ready", "source": "computer_webcam_or_pi_snapshot_later"}
