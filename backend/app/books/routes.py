from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.database import get_db
from app.auth.utils import admin_required

router = APIRouter()

class BookRequest(BaseModel):
    title: str
    author: str
    isbn: str | None = None
    category_id: int | None = None
    publisher: str | None = None
    year: int | None = None
    description: str | None = None
    cover_url: str | None = None
    total_stock: int = 1
    available_stock: int = 1

@router.get("/books")
def get_books(
    page: int = 1,
    limit: int = 10,
    category_id: int | None = None,
    available: bool | None = None,
    db=Depends(get_db)
):
    offset = (page - 1) * limit
    cur = db.cursor()

    query = """
        SELECT books.*, categories.name AS category_name
        FROM books
        LEFT JOIN categories ON books.category_id = categories.id
        WHERE 1=1
    """
    params = []

    if category_id:
        query += " AND books.category_id=%s"
        params.append(category_id)

    if available is True:
        query += " AND books.available_stock > 0"
    elif available is False:
        query += " AND books.available_stock = 0"

    query += " ORDER BY books.id DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cur.execute(query, tuple(params))
    books = cur.fetchall()

    return {
        "success": True,
        "page": page,
        "limit": limit,
        "books": books
    }

@router.get("/books/search")
def search_books(
    q: str = Query(...),
    db=Depends(get_db)
):
    cur = db.cursor()

    keyword = f"%{q}%"
    cur.execute("""
        SELECT books.*, categories.name AS category_name
        FROM books
        LEFT JOIN categories ON books.category_id = categories.id
        WHERE books.title ILIKE %s
           OR books.author ILIKE %s
           OR categories.name ILIKE %s
        ORDER BY books.id DESC
    """, (keyword, keyword, keyword))

    books = cur.fetchall()

    return {
        "success": True,
        "query": q,
        "books": books
    }

@router.get("/books/{book_id}")
def get_book_detail(book_id: int, db=Depends(get_db)):
    cur = db.cursor()

    cur.execute("""
        SELECT books.*, categories.name AS category_name
        FROM books
        LEFT JOIN categories ON books.category_id = categories.id
        WHERE books.id=%s
    """, (book_id,))

    book = cur.fetchone()

    if not book:
        raise HTTPException(status_code=404, detail="Buku tidak ditemukan")

    return {
        "success": True,
        "book": book
    }

@router.get("/categories")
def get_categories(db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT * FROM categories ORDER BY name ASC")
    categories = cur.fetchall()

    return {
        "success": True,
        "categories": categories
    }

@router.post("/books")
def create_book(
    data: BookRequest,
    db=Depends(get_db),
    admin=Depends(admin_required)
):
    cur = db.cursor()

    cur.execute("""
        INSERT INTO books
        (title, author, isbn, category_id, publisher, year, description, cover_url, total_stock, available_stock)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING *
    """, (
        data.title,
        data.author,
        data.isbn,
        data.category_id,
        data.publisher,
        data.year,
        data.description,
        data.cover_url,
        data.total_stock,
        data.available_stock
    ))

    book = cur.fetchone()
    db.commit()

    return {
        "success": True,
        "message": "Buku berhasil ditambahkan",
        "book": book
    }

@router.put("/books/{book_id}")
def update_book(
    book_id: int,
    data: BookRequest,
    db=Depends(get_db),
    admin=Depends(admin_required)
):
    cur = db.cursor()

    cur.execute("""
        UPDATE books SET
            title=%s,
            author=%s,
            isbn=%s,
            category_id=%s,
            publisher=%s,
            year=%s,
            description=%s,
            cover_url=%s,
            total_stock=%s,
            available_stock=%s
        WHERE id=%s
        RETURNING *
    """, (
        data.title,
        data.author,
        data.isbn,
        data.category_id,
        data.publisher,
        data.year,
        data.description,
        data.cover_url,
        data.total_stock,
        data.available_stock,
        book_id
    ))

    book = cur.fetchone()

    if not book:
        raise HTTPException(status_code=404, detail="Buku tidak ditemukan")

    db.commit()

    return {
        "success": True,
        "message": "Buku berhasil diperbarui",
        "book": book
    }

@router.delete("/books/{book_id}")
def delete_book(
    book_id: int,
    db=Depends(get_db),
    admin=Depends(admin_required)
):
    cur = db.cursor()

    cur.execute("DELETE FROM books WHERE id=%s RETURNING id, title", (book_id,))
    book = cur.fetchone()

    if not book:
        raise HTTPException(status_code=404, detail="Buku tidak ditemukan")

    db.commit()

    return {
        "success": True,
        "message": "Buku berhasil dihapus",
        "book": book
    }