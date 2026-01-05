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
        ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Process each request
        """
        print(f"\n🔒 Auth Middleware: {request.method} {request.url.path}")
        
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            print(f"✅ OPTIONS request (CORS preflight), skipping auth")
            return await call_next(request)
        
        # Skip authentication for public routes
        if request.url.path in self.public_routes:
            print(f"✅ Public route, skipping auth")
            return await call_next(request)
        
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        
        print(f"📋 All Headers: {dict(request.headers)}")
        
        if not auth_header:
            print(f"❌ No Authorization header found")
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
            auth_url = f"{self.auth_service_url}/auth/validate"
            print(f"🔐 Validating token with: {auth_url}")
            print(f"🔑 Token (first 20 chars): {token[:20]}...")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    auth_url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0  # 5 second timeout
                )
                
                print(f"📡 NestJS Response Status: {response.status_code}")
                print(f"📡 NestJS Response Headers: {dict(response.headers)}")
                
                try:
                    response_body = response.json()
                    print(f"📡 NestJS Response Body: {response_body}")
                except:
                    response_text = response.text
                    print(f"📡 NestJS Response Text: {response_text}")
                
                if response.status_code != 200:
                    print(f"❌ Token validation failed: Status {response.status_code}")
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "detail": "Invalid or expired token",
                            "error": "unauthorized",
                            "nest_status": response.status_code,
                            "nest_response": response.text
                        }
                    )
                
                # Token is valid, attach user info to request state
                user_data = response.json()
                print(f"✅ Token valid! User: {user_data}")
                request.state.user = user_data
                
        except httpx.TimeoutException as e:
            print(f"⏱️ Timeout connecting to NestJS: {e}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": "Authentication service is not responding",
                    "error": "service_unavailable"
                }
            )
        except httpx.RequestError as e:
            print(f"🔌 Connection error to NestJS: {e}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": f"Could not connect to authentication service: {str(e)}",
                    "error": "service_unavailable"
                }
            )
        except Exception as e:
            print(f"💥 Unexpected error: {e}")
            import traceback
            traceback.print_exc()
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

