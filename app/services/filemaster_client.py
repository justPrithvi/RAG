"""
FileMaster Client
Fetches stored document files from the Java document service (Datavault-FileMaster).

Auth (service-to-service):
  X-Service-Key: INTERNAL_SERVICE_KEY   -> proves the caller is this Python service
  X-User-Id:     <id from Nest /auth/validate> -> FileMaster only returns the file if this user owns it

Never pass a user id that came from the client request body; only the one Nest returned.
"""
import os
import tempfile
from dataclasses import dataclass
from typing import Optional
from urllib.parse import unquote

import httpx

from app.config import settings


class FileMasterError(Exception):
    """Base error for FileMaster calls."""


class FileMasterNotConfigured(FileMasterError):
    """INTERNAL_SERVICE_KEY is missing."""


class FileMasterAuthError(FileMasterError):
    """FileMaster rejected the service key (401). The keys in the two services don't match."""


class DocumentNotFound(FileMasterError):
    """404: document doesn't exist, isn't owned by this user, or its file is missing."""


class FileTooLarge(FileMasterError):
    """File exceeds MAX_INGEST_FILE_BYTES."""


class FileMasterUnavailable(FileMasterError):
    """FileMaster unreachable, timed out, or returned an unexpected status."""


@dataclass
class FetchedFile:
    """A document file downloaded to a local temp path. Call cleanup() when done."""
    path: str
    file_name: str
    content_type: str
    size: int
    document_id: int

    @property
    def extension(self) -> str:
        return self.file_name.rsplit(".", 1)[-1].lower() if "." in self.file_name else ""

    def cleanup(self) -> None:
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass


class FileMasterClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        service_key: Optional[str] = None,
        timeout: Optional[float] = None,
        max_bytes: Optional[int] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.base_url = (base_url or settings.FILEMASTER_API_URL).rstrip("/")
        self.service_key = service_key if service_key is not None else settings.INTERNAL_SERVICE_KEY
        self.timeout = timeout or settings.FILEMASTER_TIMEOUT
        self.max_bytes = max_bytes or settings.MAX_INGEST_FILE_BYTES
        self._transport = transport  # injectable for tests

    @property
    def is_configured(self) -> bool:
        return bool(self.service_key)

    async def fetch_document_file(self, document_id: int, user_id: int) -> FetchedFile:
        """
        Stream GET /internal/documents/{id}/file to a temp file.
        Raises a FileMasterError subclass on any failure; the temp file is removed on failure.
        """
        if not self.is_configured:
            raise FileMasterNotConfigured("INTERNAL_SERVICE_KEY is not set")

        url = f"{self.base_url}/internal/documents/{document_id}/file"
        headers = {
            "X-Service-Key": self.service_key,
            "X-User-Id": str(user_id),
        }

        fd, temp_path = tempfile.mkstemp(prefix=f"ingest-{document_id}-")
        os.close(fd)

        try:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
                async with client.stream("GET", url, headers=headers) as response:
                    if response.status_code == 401:
                        raise FileMasterAuthError("FileMaster rejected the service key (401)")
                    if response.status_code == 404:
                        raise DocumentNotFound(
                            f"Document {document_id} not found for user {user_id}"
                        )
                    if response.status_code != 200:
                        raise FileMasterUnavailable(
                            f"FileMaster returned {response.status_code} for document {document_id}"
                        )

                    declared = response.headers.get("Content-Length")
                    if declared and declared.isdigit() and int(declared) > self.max_bytes:
                        raise FileTooLarge(
                            f"Document {document_id} is {declared} bytes; limit is {self.max_bytes}"
                        )

                    size = 0
                    with open(temp_path, "wb") as out:
                        async for chunk in response.aiter_bytes():
                            size += len(chunk)
                            if size > self.max_bytes:
                                raise FileTooLarge(
                                    f"Document {document_id} exceeds {self.max_bytes} bytes"
                                )
                            out.write(chunk)

                    file_name = unquote(response.headers.get("X-File-Name", "")) or f"document-{document_id}"
                    content_type = response.headers.get("Content-Type", "application/octet-stream")

            return FetchedFile(
                path=temp_path,
                file_name=file_name,
                content_type=content_type.split(";")[0].strip(),
                size=size,
                document_id=document_id,
            )

        except FileMasterError:
            _remove(temp_path)
            raise
        except httpx.TimeoutException as e:
            _remove(temp_path)
            raise FileMasterUnavailable(f"FileMaster timed out: {e}") from e
        except httpx.RequestError as e:
            _remove(temp_path)
            raise FileMasterUnavailable(f"Could not connect to FileMaster: {e}") from e
        except Exception:
            _remove(temp_path)
            raise


def _remove(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


filemaster_client = FileMasterClient()
