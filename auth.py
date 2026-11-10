from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import RegisterIn, LoginIn, UserOut
from ..security import hash_password, verify_password, create_access_token
from ..dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = str(data.email).lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "دا ایمیل مخکې ثبت شوی دی")
    user = User(full_name=data.full_name.strip(), email=email,
                password_hash=hash_password(data.password), role=data.role,
                department=data.department, student_or_staff_id=data.student_or_staff_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(user.id, user.role),
            "token_type": "bearer", "user": UserOut.model_validate(user)}

@router.post("/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(data.email).lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "ایمیل یا پاسورډ ناسم دی")
    if not user.is_active:
        raise HTTPException(403, "ستاسو حساب غیرفعال دی")
    return {"access_token": create_access_token(user.id, user.role),
            "token_type": "bearer", "user": UserOut.model_validate(user)}

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
