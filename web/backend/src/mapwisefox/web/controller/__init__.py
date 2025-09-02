from ._auth import router as auth_router
from ._evidence import router as evidence_router, EvidenceController
from ._home import router as main_router


__all__ = ["auth_router", "evidence_router", "EvidenceController", "main_router"]
