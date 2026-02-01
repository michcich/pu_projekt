from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.database.database import get_session, Company, Report
from app.models.schemas import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyDetail

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.post("/", response_model=CompanyResponse, status_code=201)
async def create_company(
    company: CompanyCreate,
    db: AsyncSession = Depends(get_session)
):
    """Utwórz nową firmę"""
    
    # Sprawdź czy firma o tej nazwie już istnieje
    result = await db.execute(
        select(Company).where(Company.name == company.name)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"Company '{company.name}' already exists")
    
    new_company = Company(
        name=company.name,
        ticker=company.ticker,
        description=company.description,
        industry=company.industry
    )
    
    db.add(new_company)
    await db.commit()
    await db.refresh(new_company)
    
    return CompanyResponse(
        id=new_company.id,
        name=new_company.name,
        ticker=new_company.ticker,
        description=new_company.description,
        industry=new_company.industry,
        created_at=new_company.created_at,
        updated_at=new_company.updated_at,
        reports_count=0
    )


@router.get("/", response_model=List[CompanyResponse])
async def get_companies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_session)
):
    """Pobierz listę wszystkich firm"""
    
    # Pobierz firmy z liczbą raportów
    result = await db.execute(
        select(
            Company,
            func.count(Report.id).label('reports_count')
        )
        .outerjoin(Report)
        .group_by(Company.id)
        .order_by(Company.name)
        .offset(skip)
        .limit(limit)
    )
    
    companies_data = result.all()
    
    return [
        CompanyResponse(
            id=company.id,
            name=company.name,
            ticker=company.ticker,
            description=company.description,
            industry=company.industry,
            created_at=company.created_at,
            updated_at=company.updated_at,
            reports_count=reports_count
        )
        for company, reports_count in companies_data
    ]


@router.get("/{company_id}", response_model=CompanyDetail)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Pobierz szczegóły firmy wraz z raportami"""
    
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Pobierz raporty
    reports_result = await db.execute(
        select(Report)
        .where(Report.company_id == company_id)
        .order_by(Report.report_year.desc(), Report.report_quarter.desc())
    )
    reports = reports_result.scalars().all()
    
    from app.models.schemas import ReportInfo
    
    return CompanyDetail(
        id=company.id,
        name=company.name,
        ticker=company.ticker,
        description=company.description,
        industry=company.industry,
        created_at=company.created_at,
        updated_at=company.updated_at,
        reports_count=len(reports),
        reports=[
            ReportInfo(
                id=r.id,
                company_id=r.company_id,
                filename=r.original_filename,
                report_type=r.report_type,
                report_period=r.report_period,
                report_year=r.report_year,
                report_quarter=r.report_quarter,
                upload_date=r.upload_date,
                file_size=r.file_size,
                status=r.status
            )
            for r in reports
        ]
    )


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    company_update: CompanyUpdate,
    db: AsyncSession = Depends(get_session)
):
    """Zaktualizuj dane firmy"""
    
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Update tylko niepustych pól
    update_data = company_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    
    await db.commit()
    await db.refresh(company)
    
    # Pobierz liczbę raportów
    reports_result = await db.execute(
        select(func.count(Report.id)).where(Report.company_id == company_id)
    )
    reports_count = reports_result.scalar()
    
    return CompanyResponse(
        id=company.id,
        name=company.name,
        ticker=company.ticker,
        description=company.description,
        industry=company.industry,
        created_at=company.created_at,
        updated_at=company.updated_at,
        reports_count=reports_count
    )


@router.delete("/{company_id}")
async def delete_company(
    company_id: int,
    db: AsyncSession = Depends(get_session)
):
    """Usuń firmę (kaskadowo usuwa wszystkie raporty)"""
    
    result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = result.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Usuń pliki raportów z dysku
    import os
    reports_result = await db.execute(
        select(Report).where(Report.company_id == company_id)
    )
    reports = reports_result.scalars().all()
    
    for report in reports:
        if os.path.exists(report.file_path):
            os.remove(report.file_path)
    
    # Usuń firmę (kaskadowo usuwa raporty i sesje)
    await db.delete(company)
    await db.commit()
    
    return {
        "message": f"Company '{company.name}' and {len(reports)} report(s) deleted successfully"
    }