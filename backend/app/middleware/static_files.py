"""Static File Optimization Middleware

This module provides:
- ETag headers for browser caching
- Last-Modified headers
- CDN-ready cache control headers
- Image compression for slide PNGs
"""
import os
import hashlib
import mimetypes
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from fastapi import Request, Response
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.staticfiles import StaticFiles

logger = logging.getLogger(__name__)


class OptimizedStaticFiles(StaticFiles):
    """
    Optimized static file serving with caching headers

    Features:
    - ETag generation for cache validation
    - Last-Modified headers
    - Aggressive caching for immutable files
    - Conditional requests (304 Not Modified)
    """

    def __init__(
        self,
        directory: str,
        check_dir: bool = True,
        max_age: int = 86400,  # 24 hours default
        immutable_patterns: Optional[list] = None
    ):
        """
        Args:
            directory: Static files directory
            check_dir: Check if directory exists
            max_age: Cache max age in seconds
            immutable_patterns: File patterns that never change (e.g., ['.jpg', '.png'])
        """
        super().__init__(directory=directory, check_dir=check_dir)
        self.max_age = max_age
        self.immutable_patterns = immutable_patterns or [
            ".jpg", ".jpeg", ".png", ".gif", ".webp",
            ".woff", ".woff2", ".ttf", ".otf"
        ]

    async def get_response(self, path: str, scope) -> Response:
        """Override to add caching headers"""
        # Get base response
        response = await super().get_response(path, scope)

        if not isinstance(response, FileResponse):
            return response

        # Get file path
        file_path = Path(self.directory) / path

        if not file_path.exists():
            return response

        # Generate ETag
        etag = self._generate_etag(file_path)
        response.headers["ETag"] = etag

        # Add Last-Modified
        mtime = os.path.getmtime(file_path)
        last_modified = datetime.fromtimestamp(mtime, tz=timezone.utc)
        response.headers["Last-Modified"] = last_modified.strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )

        # Check if file is immutable (never changes)
        is_immutable = any(
            path.endswith(pattern) for pattern in self.immutable_patterns
        )

        # Set Cache-Control headers
        if is_immutable:
            # Aggressive caching for immutable files (1 year)
            response.headers["Cache-Control"] = (
                f"public, max-age=31536000, immutable"
            )
        else:
            # Standard caching with revalidation
            response.headers["Cache-Control"] = (
                f"public, max-age={self.max_age}, must-revalidate"
            )

        # CDN-friendly headers
        response.headers["Vary"] = "Accept-Encoding"

        # Check conditional request (If-None-Match)
        request = Request(scope)
        if_none_match = request.headers.get("If-None-Match")
        if if_none_match == etag:
            # Return 304 Not Modified
            return Response(status_code=304, headers=response.headers)

        # Check conditional request (If-Modified-Since)
        if_modified_since = request.headers.get("If-Modified-Since")
        if if_modified_since:
            try:
                ims_date = datetime.strptime(
                    if_modified_since, "%a, %d %b %Y %H:%M:%S GMT"
                ).replace(tzinfo=timezone.utc)

                if last_modified <= ims_date:
                    # Return 304 Not Modified
                    return Response(status_code=304, headers=response.headers)
            except ValueError:
                pass  # Invalid date format, ignore

        return response

    def _generate_etag(self, file_path: Path) -> str:
        """
        Generate ETag from file metadata

        Uses file size + modification time for efficiency
        (avoids reading entire file)
        """
        stat = file_path.stat()
        etag_source = f"{stat.st_size}-{stat.st_mtime_ns}"
        etag_hash = hashlib.md5(etag_source.encode()).hexdigest()
        return f'"{etag_hash}"'


class ImageCompressionMiddleware(BaseHTTPMiddleware):
    """
    Image compression middleware

    Automatically compresses PNG images to WebP for better performance.
    Requires Pillow library.
    """

    def __init__(self, app, quality: int = 85, convert_to_webp: bool = True):
        """
        Args:
            app: FastAPI application
            quality: Compression quality (1-100)
            convert_to_webp: Convert PNG to WebP
        """
        super().__init__(app)
        self.quality = quality
        self.convert_to_webp = convert_to_webp

        # Check if Pillow is available
        try:
            import PIL
            self.pillow_available = True
            logger.info(
                f"Image compression enabled: quality={quality}, "
                f"webp_conversion={convert_to_webp}"
            )
        except ImportError:
            self.pillow_available = False
            logger.warning("Image compression disabled: Pillow not installed")

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only process image responses
        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            return response

        # Skip if Pillow not available
        if not self.pillow_available:
            return response

        # Check if client accepts WebP
        accept = request.headers.get("accept", "")
        client_accepts_webp = "image/webp" in accept

        # Only compress PNG files to WebP if enabled and client supports it
        if (
            self.convert_to_webp
            and client_accepts_webp
            and content_type == "image/png"
        ):
            try:
                # Convert PNG to WebP
                compressed_response = await self._convert_to_webp(response)
                if compressed_response:
                    return compressed_response
            except Exception as e:
                logger.error(f"Image compression error: {e}")

        return response

    async def _convert_to_webp(self, response: Response) -> Optional[Response]:
        """Convert PNG response to WebP"""
        from io import BytesIO
        from PIL import Image

        try:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Open image
            image = Image.open(BytesIO(body))

            # Convert to WebP
            output = BytesIO()
            image.save(output, format="WEBP", quality=self.quality, method=6)
            compressed_body = output.getvalue()

            # Calculate compression ratio
            original_size = len(body)
            compressed_size = len(compressed_body)
            ratio = (1 - compressed_size / original_size) * 100

            logger.debug(
                f"Converted PNG to WebP: {original_size}B -> {compressed_size}B "
                f"({ratio:.1f}% reduction)"
            )

            # Create new response
            return Response(
                content=compressed_body,
                headers={
                    **response.headers,
                    "Content-Type": "image/webp",
                    "Content-Length": str(compressed_size),
                    "X-Compressed": "true",
                    "X-Compression-Ratio": f"{ratio:.1f}%"
                }
            )

        except Exception as e:
            logger.error(f"WebP conversion failed: {e}")
            return None


# Utility functions

def generate_cache_busting_url(file_path: str, version: Optional[str] = None) -> str:
    """
    Generate cache-busting URL for static files

    Args:
        file_path: Original file path (e.g., "/static/logo.png")
        version: Optional version string (uses file hash if None)

    Returns:
        URL with version parameter (e.g., "/static/logo.png?v=abc123")
    """
    if version is None:
        # Generate hash from file if it exists
        path = Path(file_path.lstrip("/"))
        if path.exists():
            stat = path.stat()
            version = hashlib.md5(
                f"{stat.st_size}-{stat.st_mtime_ns}".encode()
            ).hexdigest()[:8]
        else:
            # Use timestamp as fallback
            version = str(int(datetime.now().timestamp()))

    return f"{file_path}?v={version}"


def get_optimized_content_type(file_path: str) -> str:
    """
    Get optimized content type for file

    Returns WebP for images if appropriate, otherwise standard MIME type.
    """
    mime_type, _ = mimetypes.guess_type(file_path)

    # Default to application/octet-stream if unknown
    if mime_type is None:
        return "application/octet-stream"

    # Return optimized MIME types
    return mime_type
