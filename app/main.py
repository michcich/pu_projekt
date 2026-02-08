from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database.database import init_db
from app.api import chat, reports, companies, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    await init_db()
    print("✓ Database initialized with company-based schema")
    print(f"✓ Upload folder: {settings.upload_folder}")
    yield
    # Shutdown: cleanup if needed
    print("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API chatbota do analizy raportów finansowych firm giełdowych",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(companies.router)
app.include_router(reports.router)
app.include_router(chat.router, prefix="/api/chat") # ADDED PREFIX HERE
app.include_router(analytics.router)


@app.get("/")
async def root():
    return {
        "message": "Financial Chatbot API - Company-based Analysis",
        "version": settings.app_version,
        "description": "Chatbot analizujący wszystkie raporty firm na podstawie bazy danych",
        "docs": "/docs",
        "features": [
            "Zarządzanie firmami",
            "Upload raportów dla firm",
            "Analiza wszystkich raportów firmy",
            "Chatbot z kontekstem wszystkich dokumentów",
            "Analiza trendów w czasie",
            "Wizualizacja danych na wykresach"
        ]
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "database": "connected"
    }


@app.get("/stats")
async def get_stats():
    """Statystyki systemu"""
    from app.database.database import async_session_maker, Company, Report, ChatSession
    from sqlalchemy import select, func
    
    async with async_session_maker() as db:
        # Liczba firm
        companies_count = await db.execute(select(func.count(Company.id)))
        companies = companies_count.scalar()
        
        # Liczba raportów
        reports_count = await db.execute(select(func.count(Report.id)))
        reports = reports_count.scalar()
        
        # Liczba sesji
        sessions_count = await db.execute(select(func.count(ChatSession.id)))
        sessions = sessions_count.scalar()
    
    return {
        "companies": companies,
        "reports": reports,
        "chat_sessions": sessions,
        "status": "operational"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )