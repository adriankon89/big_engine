from fastapi import APIRouter

from app.routers import auctions, auth, bids, health, users, wallets

router = APIRouter()
router.include_router(health.router, tags=["Health"])
router.include_router(auth.router, tags=["Auth"])
router.include_router(users.router, tags=["Users"])
router.include_router(wallets.router, tags=["Wallets"])
router.include_router(auctions.router, tags=["Auctions"])
router.include_router(bids.router, tags=["Bids"])
