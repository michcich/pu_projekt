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

    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.max_upload_size:
        raise HTTPException(status_code=400, detail="File too large")

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(settings.upload_folder, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        processing_result = pdf_processor.process_report(file_path)
        
        if not processing_result["success"]:
            os.remove(file_path)
            raise HTTPException(status_code=500, detail=processing_result.get("error"))

        text_sample = processing_result.get("text", "")[:5000]
        company_info = await gemini_service.extract_company_info(text_sample)
        
        report_period = processing_result.get("report_period")
        report_year = None
        report_quarter = None
        
        if company_info:
            if company_info.get("report_period"):
                report_period = company_info.get("report_period")
            report_year = company_info.get("report_year")
            report_quarter = company_info.get("report_quarter")
            
            # Update report type based on AI findings if possible
            if report_quarter:
                report_type = "quarterly"
            elif report_year and not report_quarter:
                report_type = "annual"

        print("Extracting metrics with AI...")
        metrics = processing_result.get("metrics", {})
        try:
            ai_metrics = await gemini_service.extract_financial_metrics_ai(processing_result.get("text", ""))
            for key, value in ai_metrics.items():
                if value is not None:
                    metrics[key] = value
        except Exception as e:
            print(f"AI extraction failed: {e}")
            
        processing_result["metrics"] = metrics

        new_report = Report(
            filename=unique_filename,
            original_filename=file.filename,
            company_id=company_id,
            company_name=company.name,
            report_period=report_period,
            report_year=report_year,
            report_quarter=report_quarter,
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

        try:
            summary = await gemini_service.generate_summary(processing_result.get("text", ""))
            new_report.summary = summary
            new_report.status = "processed"
        except Exception:
            new_report.status = "processed_no_summary"
        
        await db.commit()
        
        return ReportUploadResponse(
            id=new_report.id,
            company_id=new_report.company_id,
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


@router.post("/auto-upload", response_model=ReportUploadResponse)
async def auto_upload_report(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session)
):
    """Automatycznie rozpoznaj firmę z PDF i przypisz raport"""
    
    # 1. Validate file
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.max_upload_size:
        raise HTTPException(status_code=400, detail="File too large")

    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(settings.upload_folder, unique_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        processing_result = pdf_processor.process_report(file_path)
        
        if not processing_result["success"]:
            os.remove(file_path)
            raise HTTPException(status_code=500, detail=processing_result.get("error"))

        text_sample = processing_result.get("text", "")[:5000]
        company_info = await gemini_service.extract_company_info(text_sample)
        
        if not company_info or not company_info.get("name"):
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Could not identify company from report")
            
        company_name = company_info.get("name")

        result = await db.execute(select(Company).where(Company.name == company_name))
        company = result.scalar_one_or_none()
        
        if not company:
            company = Company(
                name=company_name,
                ticker=company_info.get("ticker"),
                industry=company_info.get("industry"),
                description=company_info.get("description")
            )
            db.add(company)
            await db.commit()
            await db.refresh(company)

        print("Extracting metrics with AI...")
        metrics = processing_result.get("metrics", {})
        try:
            ai_metrics = await gemini_service.extract_financial_metrics_ai(processing_result.get("text", ""))
            for key, value in ai_metrics.items():
                if value is not None:
                    metrics[key] = value
        except Exception as e:
            print(f"AI extraction failed: {e}")
            
        processing_result["metrics"] = metrics

        new_report = Report(
            filename=unique_filename,
            original_filename=file.filename,
            company_id=company.id,
            company_name=company.name,
            report_period=company_info.get("report_period") or processing_result.get("report_period"),
            report_year=company_info.get("report_year"),
            report_quarter=company_info.get("report_quarter"),
            report_type="quarterly" if company_info.get("report_quarter") else "annual",
            file_size=file_size,
            file_path=file_path,
            extracted_text=processing_result.get("text", "")[:50000],
            key_metrics=processing_result.get("metrics"),
            status="processing"
        )
        
        db.add(new_report)
        await db.commit()
        await db.refresh(new_report)

        try:
            summary = await gemini_service.generate_summary(processing_result.get("text", ""))
            new_report.summary = summary
            new_report.status = "processed"
        except Exception:
            new_report.status = "processed_no_summary"
        
        await db.commit()
        
        return ReportUploadResponse(
            id=new_report.id,
            company_id=new_report.company_id,
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
            try:
                os.remove(file_path)
            except:
                pass
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
            pass
    
    await db.delete(report)
    await db.commit()
    return {"message": "Report deleted"}