"""Exception handlers for FastAPI"""
import os
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError


def setup_exception_handlers(app: FastAPI):
    """Setup custom exception handlers"""
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle ValueError exceptions"""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)}
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors"""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()}
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions"""
        import traceback
        error_trace = traceback.format_exc()
        # Always log the full traceback for debugging
        print(f"[EXCEPTION] Unhandled exception: {str(exc)}")
        print(f"[EXCEPTION] Traceback: {error_trace}")
        # Return error details in development, generic message in production
        debug_mode = os.getenv("DEBUG", "true").lower() == "true"
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": str(exc) if debug_mode else "Internal server error",
                "error_type": type(exc).__name__,
                "traceback": error_trace if debug_mode else None
            }
        )
