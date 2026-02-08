from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON, ForeignKey
from datetime import datetime
from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=True,
    future=True
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


class Company(Base):
    """Tabela firm - główna jednostka organizacyjna"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    ticker = Column(String, nullable=True, index=True)
    description = Column(Text, nullable=True)
    industry = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    reports = relationship("Report", back_populates="company", cascade="all, delete-orphan")


class Report(Base):
    """Tabela raportów - pliki PDF przypisane do firm"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    report_type = Column(String, nullable=True)
    report_period = Column(String, nullable=True)
    report_year = Column(Integer, nullable=True, index=True)
    report_quarter = Column(Integer, nullable=True)
    
    upload_date = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    
    extracted_text = Column(Text, nullable=True)
    key_metrics = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    status = Column(String, default="uploaded")
    
    # Relacje
    company = relationship("Company", back_populates="reports")


class ChatSession(Base):
    """Tabela sesji chatbota - przypisana do firmy"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")
    messages = relationship("ChatHistory", back_populates="session", cascade="all, delete-orphan")


class ChatHistory(Base):
    """Tabela historii wiadomości"""
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")


async def init_db():
    """Inicjalizacja bazy danych"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database initialized with new schema")


async def get_session() -> AsyncSession:
    """Dependency injection dla sesji bazy danych"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()