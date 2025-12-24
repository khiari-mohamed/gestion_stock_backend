from fastapi import APIRouter
from app.api.v1.endpoints import auth, articles, mouvements, dashboard, fournisseurs, previsions, rapports

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentification"])
api_router.include_router(articles.router, prefix="/articles", tags=["Articles"])
api_router.include_router(mouvements.router, prefix="/mouvements", tags=["Mouvements de Stock"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(fournisseurs.router, prefix="/fournisseurs", tags=["Fournisseurs"])
api_router.include_router(previsions.router, prefix="/previsions", tags=["Prévisions IA (Phase 2)"])
api_router.include_router(rapports.router, prefix="/rapports", tags=["Rapports (Phase 2)"])
