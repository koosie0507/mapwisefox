from fastapi import APIRouter

from ._collection import router as collection_router
from ._detail import router as detail_router

router = APIRouter(prefix="/api/v1", tags=["workbooks"])
router.include_router(collection_router)
router.include_router(detail_router)


__all__ = ["router", "collection_router", "detail_router"]
