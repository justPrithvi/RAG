"""
Authentication Middleware
Validates JWT tokens with the main NestJS backend
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import httpx


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate JWT tokens with NestJS backend
    
    Flow:
    1. Extract Bearer token from Authorization header
    2. Call NestJS validation endpoint
    3. If valid, proceed with request
    4. If invalid, return 401 Unauthorized
    """
    
    def __init__(self, app, auth_service_url: str):
        super().__init__(app)
        self.auth_service_url = auth_service_url
        
        # Public routes that don't need authentication
        self.public_routes = [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/health"
            # Remove /api/chat and /api/conversations to enable auth
        ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Process each request
        """
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Skip authentication for public routes
        if request.url.path in self.public_routes:
            return await call_next(request)
        
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Missing Authorization header",
                    "error": "unauthorized"
                }
            )
        
        # Check if it's a Bearer token
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Invalid Authorization header format. Expected: Bearer <token>",
                    "error": "unauthorized"
                }
            )
        
        # Extract token
        token = auth_header.replace("Bearer ", "")
        
        # Validate token with NestJS backend
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.auth_service_url}/auth/validate",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0  # 5 second timeout
                )
                
                if response.status_code != 200:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "detail": "Invalid or expired token",
                            "error": "unauthorized"
                        }
                    )
                
                # Token is valid, attach user info to request state
                user_data = response.json()
                request.state.user = user_data
                
        except httpx.TimeoutException:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": "Authentication service is not responding",
                    "error": "service_unavailable"
                }
            )
        except httpx.RequestError as e:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": f"Could not connect to authentication service: {str(e)}",
                    "error": "service_unavailable"
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": f"Authentication error: {str(e)}",
                    "error": "internal_error"
                }
            )
        
        # Proceed with the request
        response = await call_next(request)
        return response

