"""
Document access checks.

Ownership is read from the `documents` table in the shared data_vault database
(owned by Nest, written by FileMaster). Python only reads it.
Rule (same as FileMaster download): the owner or an admin may use a document.
"""
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser


def parse_document_id(document_id) -> int:
    """Documents have positive integer ids. Anything else is treated as not found."""
    try:
        value = int(str(document_id).strip())
    except (TypeError, ValueError):
        raise HTTPException(status_code=404, detail="Document not found")
    if value <= 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return value


def require_document_access(db: Session, document_id, user: CurrentUser) -> int:
    """
    Raise 404 unless the document exists and the user owns it (or is an admin).
    404 rather than 403, so the API doesn't reveal which document ids exist.
    Returns the parsed integer document id.
    """
    doc_id = parse_document_id(document_id)
    try:
        owner_id = db.execute(
            text("SELECT user_id FROM documents WHERE id = :id"), {"id": doc_id}
        ).scalar()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=503, detail="Could not verify document access")

    if owner_id is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc_id
