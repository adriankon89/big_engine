from fastapi import APIRouter

router = APIRouter(prefix="/moderation")


@router.get(
    "/auctions/manual-review",
)
def auction_manual_review() -> dict:
    return {"message": "This endpoint is under construction."}
