from pathlib import Path
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from .models import Document, Bookmark, User

def document_access_query(db: Session, user: User):
    query = db.query(Document).options(joinedload(Document.owner))
    if user.role != "admin":
        query = query.filter(
            Document.is_approved.is_(True),
            ((Document.visibility == "university") | (Document.uploaded_by == user.id))
        )
    return query

def serialize_document(doc: Document, user: User, db: Session):
    bookmarked = db.query(Bookmark.id).filter(
        Bookmark.user_id == user.id, Bookmark.document_id == doc.id
    ).first() is not None
    return {
        "id": doc.id, "title": doc.title, "description": doc.description,
        "category": doc.category, "department": doc.department, "subject": doc.subject,
        "visibility": doc.visibility, "original_filename": doc.original_filename,
        "file_size": doc.file_size, "downloads": doc.downloads,
        "is_approved": doc.is_approved, "uploader_name": doc.owner.full_name,
        "uploader_role": doc.owner.role, "created_at": doc.created_at,
        "is_owner": doc.uploaded_by == user.id, "is_bookmarked": bookmarked
    }

def remove_document_file(upload_dir: Path, stored_filename: str):
    path = (upload_dir / stored_filename).resolve()
    if path.parent == upload_dir.resolve() and path.exists():
        path.unlink()
