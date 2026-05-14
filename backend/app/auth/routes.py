from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.auth.utils import hash_password, verify_password, create_access_token, get_current_user, admin_required

router = APIRouter()

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str | None = None
    address: str | None = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None

@router.post("/register")
def register(data: RegisterRequest, db=Depends(get_db)):
    cur = db.cursor()

    cur.execute("SELECT id FROM users WHERE email=%s", (data.email,))
    existing = cur.fetchone()

    if existing:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")

    password_hash = hash_password(data.password)

    cur.execute("""
        INSERT INTO users (name, email, password_hash, phone, address, role)
        VALUES (%s, %s, %s, %s, %s, 'member')
        RETURNING id, name, email, phone, address, role
    """, (data.name, data.email, password_hash, data.phone, data.address))

    user = cur.fetchone()
    db.commit()

    return {
        "success": True,
        "message": "Registrasi berhasil",
        "user": user
    }

@router.post("/login")
def login(data: LoginRequest, db=Depends(get_db)):
    cur = db.cursor()

    cur.execute("SELECT * FROM users WHERE email=%s", (data.email,))
    user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Email atau password salah")

    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email atau password salah")

    token = create_access_token({
        "id": user["id"],
        "email": user["email"],
        "role": user["role"]
    })

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }

@router.get("/profile")
def get_profile(current_user=Depends(get_current_user)):
    return {
        "success": True,
        "user": current_user
    }

@router.put("/profile")
def update_profile(
    data: ProfileUpdateRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    cur = db.cursor()

    new_name = data.name or current_user["name"]
    new_phone = data.phone or current_user["phone"]
    new_address = data.address or current_user["address"]

    cur.execute("""
        UPDATE users 
        SET name=%s, phone=%s, address=%s
        WHERE id=%s
        RETURNING id, name, email, phone, address, role
    """, (new_name, new_phone, new_address, current_user["id"]))

    user = cur.fetchone()
    db.commit()

    return {
        "success": True,
        "message": "Profil berhasil diperbarui",
        "user": user
    }

@router.get("/admin/users")
def get_all_users(
    db=Depends(get_db),
    admin=Depends(admin_required)
):
    cur = db.cursor()
    cur.execute("SELECT id, name, email, phone, address, role, is_active, created_at FROM users ORDER BY id DESC")
    users = cur.fetchall()

    return {
        "success": True,
        "users": users
    }

@router.put("/admin/users/{user_id}")
def update_user_status(
    user_id: int,
    is_active: bool,
    db=Depends(get_db),
    admin=Depends(admin_required)
):
    cur = db.cursor()
    cur.execute("""
        UPDATE users 
        SET is_active=%s 
        WHERE id=%s
        RETURNING id, name, email, is_active
    """, (is_active, user_id))

    user = cur.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    db.commit()

    return {
        "success": True,
        "message": "Status user berhasil diperbarui",
        "user": user
    }