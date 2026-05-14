from fastapi import APIRouter, Depends
from app.database import get_db
from app.auth.utils import admin_required

router = APIRouter()

@router.get("/stats")
def get_stats(
    db=Depends(get_db),
    admin=Depends(admin_required)
):
    cur = db.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM books")
    total_books = cur.fetchone()["total"]

    cur.execute("SELECT COALESCE(SUM(available_stock), 0) AS total FROM books")
    available_books = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM users WHERE role='member'")
    total_members = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) AS total FROM loans WHERE status='approved'")
    active_loans = cur.fetchone()["total"]

    cur.execute("SELECT COALESCE(SUM(fine_amount), 0) AS total FROM loans")
    total_fines = cur.fetchone()["total"]

    return {
        "success": True,
        "stats": {
            "total_books": total_books,
            "available_books": available_books,
            "total_members": total_members,
            "active_loans": active_loans,
            "total_fines": total_fines
        }
    }

@router.get("/popular-books")
def popular_books(
    db=Depends(get_db),
    admin=Depends(admin_required)
):
    cur = db.cursor()

    cur.execute("""
        SELECT 
            books.id,
            books.title,
            books.author,
            COUNT(loans.id) AS total_borrowed
        FROM books
        LEFT JOIN loans ON books.id = loans.book_id
        GROUP BY books.id
        ORDER BY total_borrowed DESC
        LIMIT 10
    """)

    books = cur.fetchall()

    return {
        "success": True,
        "books": books
    }

@router.get("/active-loans")
def active_loans(
    db=Depends(get_db),
    admin=Depends(admin_required)
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
        WHERE loans.status='approved'
        ORDER BY loans.due_date ASC
    """)

    loans = cur.fetchall()

    return {
        "success": True,
        "loans": loans
    }

@router.get("/overdue")
def overdue_loans(
    db=Depends(get_db),
    admin=Depends(admin_required)
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
        WHERE loans.status='approved'
          AND loans.due_date < CURRENT_DATE
        ORDER BY loans.due_date ASC
    """)

    loans = cur.fetchall()

    return {
        "success": True,
        "loans": loans
    }