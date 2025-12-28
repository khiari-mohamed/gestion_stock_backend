"""
Rate Limiting Service - Production Grade
Features: Per-IP, Per-User, Per-Endpoint, DDoS protection
Uses Redis for distributed rate limiting
"""

from typing import Optional, Dict
from datetime import datetime, timedelta
from app.core.database import redis_client
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitType(str, Enum):
    GLOBAL = "global"  # Overall API limit
    IP = "ip"  # Per IP address limit
    USER = "user"  # Per authenticated user limit
    ENDPOINT = "endpoint"  # Per endpoint limit
    LOGIN = "login"  # Login attempt limiting
    EXPORT = "export"  # Heavy operation limiting


class RateLimitConfig:
    """Rate limiting configuration"""
    
    # Global limits (requests per minute)
    GLOBAL_LIMIT = 10000  # 10k requests per minute globally
    
    # Per-IP limits
    IP_LIMIT_GENERAL = 600  # 10 requests per second per IP
    IP_LIMIT_AUTH = 10  # 10 login attempts per minute per IP
    IP_LIMIT_EXPORT = 20  # 20 exports per hour per IP
    
    # Per-user limits
    USER_LIMIT_GENERAL = 300  # 5 requests per second per user
    USER_LIMIT_EXPORT = 10  # 10 exports per hour per user
    
    # Per-endpoint limits
    ENDPOINT_LIMITS = {
        "POST /auth/login": 10,  # 10 per minute
        "POST /articles": 100,  # 100 per minute
        "GET /articles": 200,  # 200 per minute
        "POST /exports": 20,  # 20 per hour
    }
    
    # DDoS thresholds
    DDOS_THRESHOLD_REQUESTS = 1000  # Requests per minute to trigger DDoS protection
    DDOS_THRESHOLD_UNIQUE_IPS = 100  # Unique IPs per minute
    DDOS_BLOCK_DURATION = 3600  # Block for 1 hour


class RateLimiter:
    """Production-grade rate limiter using Redis"""
    
    @staticmethod
    async def check_rate_limit(
        identifier: str,
        limit_type: RateLimitType,
        limit: int,
        window_seconds: int = 60
    ) -> Dict:
        """
        Check if request is within rate limit
        
        Returns:
        {
            "allowed": bool,
            "remaining": int,
            "reset_at": datetime,
            "retry_after": int  # seconds
        }
        """
        try:
            if not redis_client:
                logger.warning("Redis not available, allowing all requests")
                return {
                    "allowed": True,
                    "remaining": limit,
                    "reset_at": datetime.now() + timedelta(seconds=window_seconds)
                }
            
            key = f"ratelimit:{limit_type.value}:{identifier}"
            
            # Get current count
            current = await redis_client.get(key)
            current_count = int(current) if current else 0
            
            # Check if limit exceeded
            if current_count >= limit:
                ttl = await redis_client.ttl(key)
                reset_at = datetime.now() + timedelta(seconds=max(1, ttl))
                
                logger.warning(
                    f"Rate limit exceeded: {limit_type} {identifier} "
                    f"({current_count}/{limit})"
                )
                
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_at": reset_at,
                    "retry_after": max(1, ttl)
                }
            
            # Increment counter
            new_count = current_count + 1
            
            # Set expiration on first request
            if current_count == 0:
                await redis_client.setex(key, window_seconds, str(new_count))
            else:
                await redis_client.incr(key)
            
            ttl = await redis_client.ttl(key)
            reset_at = datetime.now() + timedelta(seconds=ttl)
            
            return {
                "allowed": True,
                "remaining": limit - new_count,
                "reset_at": reset_at,
                "retry_after": None
            }
        
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Fail open - allow request if Redis fails
            return {
                "allowed": True,
                "remaining": limit,
                "reset_at": datetime.now() + timedelta(seconds=window_seconds)
            }
    
    @staticmethod
    async def check_ip_limit(
        ip_address: str,
        endpoint: str = None
    ) -> Dict:
        """Check per-IP rate limit"""
        
        # Determine limit based on endpoint
        if endpoint and "login" in endpoint.lower():
            limit = RateLimitConfig.IP_LIMIT_AUTH
            window = 60
        elif endpoint and "export" in endpoint.lower():
            limit = RateLimitConfig.IP_LIMIT_EXPORT
            window = 3600
        else:
            limit = RateLimitConfig.IP_LIMIT_GENERAL
            window = 60
        
        return await RateLimiter.check_rate_limit(
            f"ip:{ip_address}",
            RateLimitType.IP,
            limit,
            window
        )
    
    @staticmethod
    async def check_user_limit(
        user_id: str,
        endpoint: str = None
    ) -> Dict:
        """Check per-user rate limit"""
        
        if endpoint and "export" in endpoint.lower():
            limit = RateLimitConfig.USER_LIMIT_EXPORT
            window = 3600
        else:
            limit = RateLimitConfig.USER_LIMIT_GENERAL
            window = 60
        
        return await RateLimiter.check_rate_limit(
            f"user:{user_id}",
            RateLimitType.USER,
            limit,
            window
        )
    
    @staticmethod
    async def check_endpoint_limit(endpoint: str) -> Dict:
        """Check per-endpoint rate limit"""
        limit = RateLimitConfig.ENDPOINT_LIMITS.get(endpoint, 100)
        
        return await RateLimiter.check_rate_limit(
            f"endpoint:{endpoint}",
            RateLimitType.ENDPOINT,
            limit,
            60
        )
    
    @staticmethod
    async def check_global_limit() -> Dict:
        """Check global API rate limit"""
        return await RateLimiter.check_rate_limit(
            "global",
            RateLimitType.GLOBAL,
            RateLimitConfig.GLOBAL_LIMIT,
            60
        )
    
    @staticmethod
    async def is_ip_blocked(ip_address: str) -> bool:
        """Check if IP is DDoS blocked"""
        try:
            if not redis_client:
                return False
            
            blocked_key = f"ddos_block:{ip_address}"
            result = await redis_client.exists(blocked_key)
            
            return result > 0
        
        except Exception as e:
            logger.error(f"Error checking IP block: {e}")
            return False
    
    @staticmethod
    async def block_ip(ip_address: str, duration: int = None) -> None:
        """Block an IP address"""
        try:
            if not redis_client:
                return
            
            if not duration:
                duration = RateLimitConfig.DDOS_BLOCK_DURATION
            
            block_key = f"ddos_block:{ip_address}"
            await redis_client.setex(block_key, duration, "1")
            
            logger.warning(f"IP blocked: {ip_address} for {duration} seconds")
        
        except Exception as e:
            logger.error(f"Error blocking IP: {e}")
    
    @staticmethod
    async def check_ddos_patterns(ip_address: str) -> Dict:
        """
        Detect potential DDoS patterns
        Returns detection results
        """
        try:
            if not redis_client:
                return {"ddos_detected": False}
            
            # Check if IP exceeded global threshold
            ip_key = f"ratelimit:ip:{ip_address}"
            current_requests = await redis_client.get(ip_key)
            
            if current_requests and int(current_requests) > RateLimitConfig.DDOS_THRESHOLD_REQUESTS:
                logger.warning(
                    f"Potential DDoS detected from {ip_address}: "
                    f"{current_requests} requests in 60 seconds"
                )
                
                # Block the IP
                await RateLimiter.block_ip(ip_address)
                
                return {
                    "ddos_detected": True,
                    "reason": "excessive_requests",
                    "requests_count": int(current_requests),
                    "action": "IP_BLOCKED"
                }
            
            # Check for distributed attack (many unique IPs)
            ddos_ips_key = "ddos_unique_ips"
            unique_ips = await redis_client.scard(ddos_ips_key)
            
            if unique_ips and unique_ips > RateLimitConfig.DDOS_THRESHOLD_UNIQUE_IPS:
                logger.warning(
                    f"Potential distributed DDoS detected: "
                    f"{unique_ips} unique IPs in 60 seconds"
                )
                
                return {
                    "ddos_detected": True,
                    "reason": "distributed_attack",
                    "unique_ips": unique_ips,
                    "action": "ELEVATED_MONITORING"
                }
            
            return {"ddos_detected": False}
        
        except Exception as e:
            logger.error(f"Error checking DDoS patterns: {e}")
            return {"ddos_detected": False}
    
    @staticmethod
    async def record_request_attempt(
        ip_address: str,
        user_id: Optional[str] = None,
        endpoint: str = None,
        method: str = None
    ) -> None:
        """Record a request attempt for analytics"""
        try:
            if not redis_client:
                return
            
            # Record unique IPs for DDoS detection
            await redis_client.sadd("ddos_unique_ips", ip_address)
            await redis_client.expire("ddos_unique_ips", 60)
            
            # Record endpoint hits
            if endpoint and method:
                endpoint_key = f"endpoint_hits:{method} {endpoint}"
                await redis_client.incr(endpoint_key)
                await redis_client.expire(endpoint_key, 60)
            
            # Record user activity
            if user_id:
                user_key = f"user_activity:{user_id}"
                await redis_client.incr(user_key)
                await redis_client.expire(user_key, 3600)
        
        except Exception as e:
            logger.error(f"Error recording request: {e}")
    
    @staticmethod
    async def get_rate_limit_status(identifier: str, limit_type: RateLimitType) -> Dict:
        """Get current rate limit status"""
        try:
            if not redis_client:
                return {"status": "redis_unavailable"}
            
            key = f"ratelimit:{limit_type.value}:{identifier}"
            current = await redis_client.get(key)
            ttl = await redis_client.ttl(key)
            
            return {
                "identifier": identifier,
                "type": limit_type.value,
                "current_count": int(current) if current else 0,
                "time_remaining": max(0, ttl),
                "reset_at": (datetime.now() + timedelta(seconds=max(0, ttl))).isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")
            return {"error": str(e)}
    
    @staticmethod
    async def reset_user_limits(user_id: str) -> None:
        """Reset all limits for a user (admin override)"""
        try:
            if not redis_client:
                return
            
            keys_to_delete = [
                f"ratelimit:user:{user_id}",
                f"ratelimit:ip:*",  # Can't pattern match, would need scan
                f"user_activity:{user_id}"
            ]
            
            for key in keys_to_delete:
                if "*" not in key:
                    await redis_client.delete(key)
            
            logger.info(f"Rate limits reset for user {user_id}")
        
        except Exception as e:
            logger.error(f"Error resetting limits: {e}")
    
    @staticmethod
    async def get_api_stats() -> Dict:
        """Get API usage statistics"""
        try:
            if not redis_client:
                return {"status": "redis_unavailable"}
            
            # Get global counter
            global_count = await redis_client.get("ratelimit:global:global")
            
            # Count unique IPs
            unique_ips = await redis_client.scard("ddos_unique_ips") or 0
            
            return {
                "global_requests_minute": int(global_count) if global_count else 0,
                "unique_ips_minute": unique_ips,
                "limit_global": RateLimitConfig.GLOBAL_LIMIT,
                "ddos_threshold": RateLimitConfig.DDOS_THRESHOLD_REQUESTS,
                "health": "healthy" if int(global_count or 0) < RateLimitConfig.GLOBAL_LIMIT else "elevated"
            }
        
        except Exception as e:
            logger.error(f"Error getting API stats: {e}")
            return {"error": str(e)}
    
    async def cleanup_old_entries(self):
        """Nettoyer les entrées expirées toutes les 5 minutes"""
        while True:
            await asyncio.sleep(300)  # 5 minutes
            cutoff = datetime.now() - timedelta(minutes=5)
            
            for client_id in list(self.requests.keys()):
                self.requests[client_id] = [
                    req_time for req_time in self.requests[client_id]
                    if req_time > cutoff
                ]
                
                if not self.requests[client_id]:
                    del self.requests[client_id]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware de rate limiting"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute)
    
    async def dispatch(self, request: Request, call_next):
        # Exclure les endpoints de santé
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Identifier le client (IP ou user_id si authentifié)
        client_id = request.client.host
        
        # Vérifier si autorisé
        if not await self.limiter.is_allowed(client_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Trop de requêtes. Veuillez réessayer dans 1 minute."
            )
        
        response = await call_next(request)
        return response
