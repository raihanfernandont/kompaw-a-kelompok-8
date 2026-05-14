import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Header
from app.database import get_db

SECRET_KEY = os.getenv("SECRET_KEY", "secret_key_default")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    authorization: str = Header(None),
    db=Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token tidak ditemukan")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Format token salah")
    except ValueError:
        raise HTTPException(status_code=401, detail="Format authorization salah")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Token tidak valid")

        cur = db.cursor()
        cur.execute("SELECT id, name, email, phone, address, role, is_active FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="User tidak ditemukan")

        if not user["is_active"]:
            raise HTTPException(status_code=403, detail="Akun tidak aktif")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid")

def admin_required(current_user=Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Hanya admin yang boleh mengakses")
    return current_user