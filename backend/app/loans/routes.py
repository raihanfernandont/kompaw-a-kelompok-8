from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import date, timedelta
from app.database import get_db
from app.auth.utils import get_current_user, admin_required

router = APIRouter()

class LoanRequest(BaseModel):
    book_id: int

@router.post("/loans")
def create_loan(
    data: LoanRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    cur = db.cursor()

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM loans
        WHERE user_id=%s AND status='approved'
    """, (current_user["id"],))

    active = cur.fetchone()["total"]

    if active >= 3:
        raise HTTPException(status_code=400, detail="Maksimal 3 buku dipinjam sekaligus")

    cur.execute("SELECT * FROM books WHERE id=%s", (data.book_id,))
    book = cur.fetchone()

    if not book:
        raise HTTPException(status_code=404, detail="Buku tidak ditemukan")

    if book["available_stock"] < 1:
        raise HTTPException(status_code=400, detail="Stok buku tidak tersedia")

    cur.execute("""
        INSERT INTO loans (user_id, book_id, status)
        VALUES (%s, %s, 'pending')
        RETURNING *
    """, (current_user["id"], data.book_id))

    loan = cur.fetchone()
    db.commit()

    return {
        "success": True,
        "message": "Peminjaman berhasil diajukan, menunggu konfirmasi admin",
        "loan": loan
    }

@router.get("/loans/my")
def get_my_loans(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    cur = db.cursor()

    cur.execute("""
        SELECT loans.*, books.title AS book_title, books.author AS book_author
        FROM loans
        JOIN books ON loans.book_id = books.id
        WHERE loans.user_id=%s
        ORDER BY loans.id DESC
    """, (current_user["id"],))

    loans = cur.fetchall()

    return {
        "success": True,
        "loans": loans
    }

@router.get("/loans")
def get_all_loans(
    db=Depends(get_db),
    admin=Depends(admin_required)
):
    cur = db.cursor()

    cur.execute("""
        SELECT 
            loans.*,
            users.name AS user_name,
            users.email AS user_email,
            books.title AS book_title
        FROM loans
        JOIN users ON loans.user_id = users.id
        JOIN books ON loans.book_id = books.id
        ORDER BY loans.id DESC
    """)

    loans = cur.fetchall()

    return {
        "success": True,
        "loans": loans
    }

@router.get("/loans/{loan_id}")
def get_loan_detail(
    loan_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    cur = db.cursor()

    cur.execute("""
        SELECT 
            loans.*,
            users.name AS user_name,
            books.title AS book_title
        FROM loans
        JOIN users ON loans.user_id = users.id
        JOIN books ON loans.book_id = books.id
        WHERE loans.id=%s
    """, (loan_id,))

    loan = cur.fetchone()

    if not loan:
        raise HTTPException(status_code=404, detail="Peminjaman tidak ditemukan")

    if current_user["role"] != "admin" and loan["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Tidak boleh melihat data ini")

    return {
        "success": True,
        "loan": loan
    }

@router.put("/loans/{loan_id}/approve")
def approve_loan(
    loan_id: int,
    db=Depends(get_db),
    admin=Depends(admin_required)
):
    cur = db.cursor()

    cur.execute("SELECT * FROM loans WHERE id=%s", (loan_id,))
    loan = cur.fetchone()

    if not loan:
        raise HTTPException(status_code=404, detail="Peminjaman tidak ditemukan")

    if loan["status"] != "pending":
        raise HTTPException(status_code=400, detail="Hanya peminjaman pending yang bisa disetujui")

    cur.execute("SELECT * FROM books WHERE id=%s", (loan["book_id"],))
    book = cur.fetchone()

    if book["available_stock"] < 1:
        raise HTTPException(status_code=400, detail="Stok buku tidak tersedia")

    today = date.today()
    due = today + timedelta(days=7)

    cur.execute("""
        UPDATE loans
        SET status='approved', loan_date=%s, due_date=%s
        WHERE id=%s
        RETURNING *
    """, (today, due, loan_id))

    updated_loan = cur.fetchone()

    cur.execute("""
        UPDATE books
        SET available_stock = available_stock - 1
        WHERE id=%s
    """, (loan["book_id"],))

    db.commit()

    return {
        "success": True,
        "message": "Peminjaman disetujui",
        "due_date": str(due),
        "loan": updated_loan
    }

@router.put("/loans/{loan_id}/return")
def return_loan(
    loan_id: int,
    db=Depends(get_db),
    admin=Depends(admin_required)
):
    cur = db.cursor()

    cur.execute("SELECT * FROM loans WHERE id=%s", (loan_id,))
    loan = cur.fetchone()

    if not loan:
        raise HTTPException(status_code=404, detail="Peminjaman tidak ditemukan")

    if loan["status"] != "approved":
        raise HTTPException(status_code=400, detail="Hanya buku yang sedang dipinjam yang bisa dikembalikan")

    today = date.today()
    fine = 0

    if loan["due_date"] and today > loan["due_date"]:
        late_days = (today - loan["due_date"]).days
        fine = late_days * 1000

    cur.execute("""
        UPDATE loans
        SET status='returned', return_date=%s, fine_amount=%s
        WHERE id=%s
        RETURNING *
    """, (today, fine, loan_id))

    updated_loan = cur.fetchone()

    cur.execute("""
        UPDATE books
        SET available_stock = available_stock + 1
        WHERE id=%s
    """, (loan["book_id"],))

    db.commit()

    return {
        "success": True,
        "message": "Buku berhasil dikembalikan",
        "fine_amount": fine,
        "loan": updated_loan
    }