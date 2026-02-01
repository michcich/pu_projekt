from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import os
import uuid
from datetime import datetime

from app.database.database import get_session, Report, Company
from app.models.schemas import ReportUploadResponse, ReportInfo, ReportDetail
from app.services.pdf_processor import PDFProcessor
from app.services.gemini_service import GeminiService
from app.config import settings

router = APIRouter(prefix="/api/reports", tags=["reports"])

pdf_processor = PDFProcessor()
gemini_service = GeminiService()


@router.post("/upload", response_model=ReportUploadResponse)
async def upload_report(
    file: UploadFile = File(...),
    company_id: int = Form(...),
    report_type: str = Form("quarterly"),
    db: AsyncSession = Depends(get_session)
):
    """Upload and process a financial report PDF"""
    
    # 1. Verify Company Exists
    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # 2. Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.max_upload_size:
        raise HTTPException(status_code=400, detail="File too large")
    
    # 3. Save file
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(settings.upload_folder, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 4. Process PDF
        processing_result = pdf_processor.process_report(file_path)
        
        if not processing_result["success"]:
            os.remove(file_path)
            raise HTTPException(status_code=500, detail=processing_result.get("error"))
        
        # 5. Create Record
        new_report = Report(
            filename=unique_filename,
            original_filename=file.filename,
            company_id=company_id,
            company_name=company.name,
            report_period=processing_result.get("report_period"),
            report_type=report_type,
            file_size=file_size,
            file_path=file_path,
            extracted_text=processing_result.get("text", "")[:50000],
            key_metrics=processing_result.get("metrics"),
            status="processing"
        )
        
        db.add(new_report)
        await db.commit()
        await db.refresh(new_report)
        
        # 6. Generate Summary (Async in real app)
        try:
            summary = await gemini_service.generate_summary(processing_result.get("text", ""))
            new_report.summary = summary
            new_report.status = "processed"
        except Exception:
            new_report.status = "processed_no_summary"
        
        await db.commit()
        
        return ReportUploadResponse(
            id=new_report.id,
            company_id=new_report.company_id,  # <-- Tego brakowało
            filename=new_report.original_filename,
            company_name=new_report.company_name,
            report_period=new_report.report_period,
            report_type=new_report.report_type,
            upload_date=new_report.upload_date,
            file_size=new_report.file_size,
            status=new_report.status
        )
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[ReportInfo])
async def get_reports(
    skip: int = 0,
    limit: int = 100,
    company_id: Optional[int] = None,
    db: AsyncSession = Depends(get_session)
):
    """Get list of reports, optionally filtered by company"""
    query = select(Report).order_by(Report.upload_date.desc()).offset(skip).limit(limit)
    
    if company_id:
        query = query.where(Report.company_id == company_id)
        
    result = await db.execute(query)
    reports = result.scalars().all()
    
    return [
        ReportInfo(
            id=report.id,
            filename=report.original_filename,
            report_period=report.report_period,
            report_type=report.report_type,
            upload_date=report.upload_date,
            status=report.status
        )
        for report in reports
    ]

@router.get("/{report_id}", response_model=ReportDetail)
async def get_report(report_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return ReportDetail(
        id=report.id,
        filename=report.original_filename,
        company_name=report.company_name,
        report_period=report.report_period,
        report_type=report.report_type,
        upload_date=report.upload_date,
        file_size=report.file_size,
        status=report.status,
        extracted_text_length=len(report.extracted_text) if report.extracted_text else 0,
        key_metrics=report.key_metrics,
        summary=report.summary
    )

@router.delete("/{report_id}")
async def delete_report(report_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if os.path.exists(report.file_path):
        try:
            os.remove(report.file_path)
        except OSError:
            pass # Ignore file not found
    
    await db.delete(report)
    await db.commit()
    return {"message": "Report deleted"}