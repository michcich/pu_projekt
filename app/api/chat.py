from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid
from datetime import datetime

from app.database.database import get_session, Report, ChatSession, ChatHistory, Company
from app.models.schemas import (
    ChatRequest, ChatResponse, ChatMessage, MessageRole, 
    AnalysisResponse, AnalysisRequest
)
from app.services.gemini_service import GeminiService
from app.services.chart_data_service import ChartDataService

router = APIRouter(tags=["chat"])

gemini_service = GeminiService()
chart_service = ChartDataService()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_session)
):
    """Send a message to the chatbot"""

    session_id = request.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        new_session = ChatSession(
            session_id=session_id,
            company_id=request.company_id
        )
        db.add(new_session)
        await db.commit()
    else:
        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            new_session = ChatSession(
                session_id=session_id,
                company_id=request.company_id
            )
            db.add(new_session)
            await db.commit()
            session = new_session

        if request.company_id and session.company_id != request.company_id:
            session.company_id = request.company_id
            await db.commit()

    company_name = None
    all_reports_text = []
    reports_used = []
    reports_for_charts = []

    target_company_id = request.company_id
    if not target_company_id and session_id:
        session_result = await db.execute(select(ChatSession).where(ChatSession.session_id == session_id))
        session_rec = session_result.scalar_one_or_none()
        if session_rec:
            target_company_id = session_rec.company_id

    if target_company_id:
        company_res = await db.execute(select(Company).where(Company.id == target_company_id))
        company = company_res.scalar_one_or_none()
        if company:
            company_name = company.name

        report_res = await db.execute(
            select(Report)
            .where(Report.company_id == target_company_id)
            .where(Report.status == "processed")
            .order_by(Report.upload_date.desc())
        )
        all_reports = report_res.scalars().all()
        reports_for_charts = all_reports

        for report in all_reports[:3]:
            if report.extracted_text:
                all_reports_text.append({
                    "period": report.report_period or report.filename,
                    "text": report.extracted_text[:10000]
                })
                reports_used.append(f"{report.report_period} ({report.filename})")

    history_result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.timestamp.asc())
    )
    history_records = history_result.scalars().all()
    
    chat_history = [
        ChatMessage(
            role=MessageRole(record.role),
            content=record.content,
            timestamp=record.timestamp
        )
        for record in history_records
    ]

    user_message = ChatHistory(
        session_id=session_id,
        role=MessageRole.USER.value,
        content=request.message
    )
    db.add(user_message)
    await db.commit()

    try:
        context_message = request.message
        if company_name and not all_reports_text:
            context_message = f"[Pytanie dotyczy firmy: {company_name}] {request.message}"

        gemini_response = await gemini_service.generate_response(
            user_message=context_message,
            company_name=company_name or "Nieznana firma",
            all_reports_text=all_reports_text,
            chat_history=chat_history
        )
        
        if not gemini_response["success"]:
            error_msg = "Przepraszam, mam problem z połączeniem z AI."
            assistant_message = ChatHistory(
                session_id=session_id,
                role=MessageRole.ASSISTANT.value,
                content=error_msg
            )
            db.add(assistant_message)
            await db.commit()
            return ChatResponse(
                response=error_msg, 
                session_id=session_id,
                company_name=company_name or "",
                reports_used=0
            )

        chart_data = None
        has_chart = False
        chart_config = gemini_response.get("chart_config")
        
        if chart_config and reports_for_charts:
            try:
                metrics = chart_config.get("metrics", ["revenue"])
                chart_type = chart_config.get("chart_type", "line")
                title = chart_config.get("title", "Wykres finansowy")
                
                chart_data = chart_service.prepare_chart_data(
                    reports=reports_for_charts,
                    metric_keys=metrics,
                    chart_type=chart_type,
                    title=title
                )
                if chart_data:
                    has_chart = True
            except Exception as e:
                print(f"Error generating chart: {e}")

        assistant_message = ChatHistory(
            session_id=session_id,
            role=MessageRole.ASSISTANT.value,
            content=gemini_response["response"]
        )
        db.add(assistant_message)
        await db.commit()
        
        return ChatResponse(
            response=gemini_response["response"],
            session_id=session_id,
            company_name=company_name or "",
            has_chart=has_chart,
            chart_data=chart_data,
            reports_used=len(reports_used),
            suggestions=gemini_response.get("suggestions", [])
        )
        
    except Exception as e:
        print(f"Error generation: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


@router.post("/analyze/{company_id}", response_model=AnalysisResponse)
async def analyze_company(
    company_id: int,
    request: Optional[AnalysisRequest] = None,
    db: AsyncSession = Depends(get_session)
):
    """Analyze company trends based on all reports"""

    company_res = await db.execute(select(Company).where(Company.id == company_id))
    company = company_res.scalar_one_or_none()
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    reports_res = await db.execute(
        select(Report)
        .where(Report.company_id == company_id)
        .where(Report.status == "processed")
        .order_by(Report.upload_date.asc()) # Od najstarszego do najnowszego
    )
    reports = reports_res.scalars().all()
    
    if not reports:
        return AnalysisResponse(
            company_id=company_id,
            company_name=company.name,
            analysis_type="trends",
            result={"error": "Brak przetworzonych raportów do analizy"},
            reports_analyzed=0,
            generated_at=datetime.utcnow()
        )

    reports_data = []
    for report in reports:
        if not report.extracted_text or len(report.extracted_text) < 100:
            continue

        reports_data.append({
            "period": report.report_period or report.filename,
            "metrics": report.key_metrics or {},
            "summary": report.summary or ""
        })

    analysis_result = await gemini_service.analyze_company_trends(
        company_name=company.name,
        all_reports_data=reports_data
    )
    
    return AnalysisResponse(
        company_id=company_id,
        company_name=company.name,
        analysis_type="trends",
        result=analysis_result,
        reports_analyzed=len(reports_data),
        generated_at=datetime.utcnow()
    )


@router.get("/history/{session_id}", response_model=List[ChatMessage])
async def get_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_session)
):
    """Get chat history for a session"""
    result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.timestamp.asc())
    )
    history = result.scalars().all()
    
    return [
        ChatMessage(
            role=MessageRole(record.role),
            content=record.content,
            timestamp=record.timestamp
        )
        for record in history
    ]


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_session)
):
    """Delete session"""
    await db.execute(
        ChatHistory.__table__.delete().where(ChatHistory.session_id == session_id)
    )
    result = await db.execute(select(ChatSession).where(ChatSession.session_id == session_id))
    session = result.scalar_one_or_none()
    if session:
        await db.delete(session)
        await db.commit()
    return {"message": "Session deleted"}