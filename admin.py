from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from ..database import get_db
from ..models import User, Document, DocumentReport, DownloadLog
from ..dependencies import require_admin
from ..schemas import UserStatusIn, DocumentApprovalIn
from ..config import settings
from ..utils import remove_document_file

router = APIRouter(prefix="/api/admin", tags=["Administration"])

@router.get("/stats")
def stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return {
        "users": db.query(func.count(User.id)).scalar() or 0,
        "students": db.query(func.count(User.id)).filter(User.role == "student").scalar() or 0,
        "teachers": db.query(func.count(User.id)).filter(User.role == "teacher").scalar() or 0,
        "documents": db.query(func.count(Document.id)).scalar() or 0,
        "pending_documents": db.query(func.count(Document.id)).filter(Document.is_approved.is_(False)).scalar() or 0,
        "downloads": db.query(func.coalesce(func.sum(Document.downloads), 0)).scalar() or 0,
        "storage_bytes": db.query(func.coalesce(func.sum(Document.file_size), 0)).scalar() or 0,
        "open_reports": db.query(func.count(DocumentReport.id)).filter(DocumentReport.status == "open").scalar() or 0
    }

@router.get("/users")
def users(q: str = "", role: str = "", db: Session = Depends(get_db),
          admin: User = Depends(require_admin)):
    query = db.query(User)
    if q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(or_(User.full_name.ilike(term), User.email.ilike(term)))
    if role in ("student", "teacher", "admin"): query = query.filter(User.role == role)
    return [{"id": u.id, "full_name": u.full_name, "email": u.email, "role": u.role,
             "department": u.department, "student_or_staff_id": u.student_or_staff_id,
             "is_active": u.is_active, "created_at": u.created_at}
            for u in query.order_by(User.created_at.desc()).limit(1000).all()]

@router.patch("/users/{user_id}/status")
def update_user_status(user_id: int, data: UserStatusIn,
                       db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    target = db.get(User, user_id)
    if not target: raise HTTPException(404, "کارن ونه موندل شو")
    if target.id == admin.id: raise HTTPException(400, "خپل حساب له دې لارې نه شئ غیرفعالولی")
    target.is_active = data.is_active
    db.commit()
    return {"id": target.id, "is_active": target.is_active}

@router.get("/documents/pending")
def pending_documents(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    docs = db.query(Document).filter(Document.is_approved.is_(False)).order_by(Document.created_at.asc()).all()
    return [{"id": d.id, "title": d.title, "uploader": d.owner.full_name,
             "filename": d.original_filename, "created_at": d.created_at} for d in docs]

@router.patch("/documents/{document_id}/approval")
def approve_document(document_id: int, data: DocumentApprovalIn,
                     db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    doc = db.get(Document, document_id)
    if not doc: raise HTTPException(404, "فایل ونه موندل شو")
    doc.is_approved = data.is_approved
    db.commit()
    return {"id": doc.id, "is_approved": doc.is_approved}

@router.get("/reports")
def reports(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    rows = db.query(DocumentReport).order_by(DocumentReport.created_at.desc()).limit(500).all()
    return [{"id": r.id, "document_id": r.document_id, "reported_by": r.reported_by,
             "reason": r.reason, "status": r.status, "created_at": r.created_at} for r in rows]

@router.patch("/reports/{report_id}/resolve")
def resolve_report(report_id: int, db: Session = Depends(get_db),
                   admin: User = Depends(require_admin)):
    report = db.get(DocumentReport, report_id)
    if not report: raise HTTPException(404, "راپور ونه موندل شو")
    report.status = "resolved"; db.commit()
    return {"id": report.id, "status": report.status}

@router.get("/downloads/recent")
def recent_downloads(limit: int = Query(50, ge=1, le=200),
                    db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    rows = db.query(DownloadLog).order_by(DownloadLog.downloaded_at.desc()).limit(limit).all()
    return [{"user_id": r.user_id, "document_id": r.document_id,
             "downloaded_at": r.downloaded_at} for r in rows]
