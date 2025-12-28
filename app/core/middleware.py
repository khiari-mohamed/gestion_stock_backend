from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import json
from datetime import datetime
from app.core.database import prisma

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses with timing information"""
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log request details
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(process_time * 1000, 2),
                "client_ip": request.client.host if request.client else "unknown"
            }
            
            # Add user info if authenticated
            if hasattr(request, "state") and hasattr(request.state, "user"):
                log_data["user_id"] = request.state.user.get("id")
                log_data["entreprise_id"] = request.state.user.get("entreprise_id")
            
            logger.info(json.dumps(log_data))
            
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(f"Request failed: {request.method} {request.url.path} - {str(e)}")
            raise


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Handle and log unhandled errors"""
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(
                f"Unhandled error: {str(e)}",
                exc_info=True,
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else "unknown"
                }
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Erreur interne du serveur",
                    "error_code": "INTERNAL_SERVER_ERROR"
                }
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Log important actions for audit trail"""
    
    # Endpoints that should be audited
    AUDIT_ENDPOINTS = {
        "POST": ["/articles", "/mouvements", "/bons-commande", "/fournisseurs"],
        "PUT": ["/articles", "/magasins", "/fournisseurs"],
        "DELETE": ["/articles", "/magasins", "/fournisseurs"],
        "PATCH": ["/bons-commande", "/transferts"]
    }
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Check if this endpoint should be audited
        should_audit = self._should_audit(request)
        
        if should_audit and response.status_code < 400:
            try:
                # Extract user info from request state
                user_id = None
                user_email = None
                entreprise_id = None
                
                if hasattr(request, "state") and hasattr(request.state, "user"):
                    user_id = request.state.user.get("id")
                    user_email = request.state.user.get("email")
                    entreprise_id = request.state.user.get("entreprise_id")
                
                # Log to audit trail
                await prisma.auditlog.create(
                    data={
                        "user_id": user_id,
                        "user_email": user_email,
                        "action": f"{request.method} {request.url.path}",
                        "entity_type": self._extract_entity_type(request.url.path),
                        "ip_address": request.client.host if request.client else None,
                        "user_agent": request.headers.get("user-agent"),
                        "entreprise_id": entreprise_id
                    }
                )
            except Exception as e:
                logger.error(f"Error writing audit log: {str(e)}")
        
        return response
    
    def _should_audit(self, request: Request) -> bool:
        """Check if endpoint should be audited"""
        for method, endpoints in self.AUDIT_ENDPOINTS.items():
            if request.method == method:
                for endpoint in endpoints:
                    if endpoint in request.url.path:
                        return True
        return False
    
    def _extract_entity_type(self, path: str) -> str:
        """Extract entity type from request path"""
        if "/articles" in path:
            return "Article"
        elif "/mouvements" in path:
            return "MouvementStock"
        elif "/bons-commande" in path:
            return "BonCommande"
        elif "/fournisseurs" in path:
            return "Fournisseur"
        elif "/magasins" in path:
            return "Magasin"
        elif "/transferts" in path:
            return "TransfertStock"
        return "Unknown"

