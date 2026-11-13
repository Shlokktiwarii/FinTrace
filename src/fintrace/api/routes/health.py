from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def health(request: Request):
    services = getattr(request.app.state, "services", None)

    return {
        "status": "healthy" if services else "starting",
        "service": "FinTrace API",
    }