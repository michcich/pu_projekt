from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database.database import get_session, Report, Company
from app.models.schemas import ChartDataResponse
from app.services.chart_data_service import ChartDataService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
chart_service = ChartDataService()

@router.get("/chart-data/{company_id}", response_model=ChartDataResponse)
async def get_company_chart_data(
    company_id: int,
    db: AsyncSession = Depends(get_session)
):
    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    reports_result = await db.execute(select(Report).where(Report.company_id == company_id))
    reports = reports_result.scalars().all()
    
    if not reports:
        return ChartDataResponse(
            company_id=company_id,
            company_name=company.name,
            timeframe={"from": "-", "to": "-"},
            charts=[],
            available_metrics=[]
        )
    
    charts = []
    
    revenue_chart = chart_service.prepare_chart_data(
        reports, 
        ["revenue"], 
        chart_type="line", 
        title="Przychody w czasie"
    )
    if revenue_chart:
        charts.append(revenue_chart)
        
    profit_chart = chart_service.prepare_chart_data(
        reports, 
        ["net_income"], 
        chart_type="bar", 
        title="Zysk Netto"
    )
    if profit_chart:
        charts.append(profit_chart)
        
    combined_chart = chart_service.prepare_chart_data(
        reports,
        ["revenue", "net_income"],
        chart_type="line",
        title="Przychody vs Zysk Netto"
    )
    if combined_chart:
        combined_chart.chart_id = "revenue_vs_profit"
        charts.append(combined_chart)

    sorted_reports = chart_service._sort_reports(reports)
    start_period = f"{sorted_reports[0].report_year} Q{sorted_reports[0].report_quarter}" if sorted_reports else "-"
    end_period = f"{sorted_reports[-1].report_year} Q{sorted_reports[-1].report_quarter}" if sorted_reports else "-"

    return ChartDataResponse(
        company_id=company_id,
        company_name=company.name,
        timeframe={"from": start_period, "to": end_period},
        charts=charts,
        available_metrics=chart_service.get_available_metrics(reports)
    )
