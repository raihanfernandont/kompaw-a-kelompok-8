from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.books.routes import router as books_router
from app.loans.routes import router as loans_router
from app.reports.routes import router as reports_router

app = FastAPI(
    title="Perpustakaan Digital API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(books_router, prefix="/api", tags=["Books"])
app.include_router(loans_router, prefix="/api", tags=["Loans"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "Perpustakaan Digital"
    }