from typing import List, Dict, Any, Optional
from app.database.database import Report
from app.models.schemas import Chart, ChartData, ChartDataset

class ChartDataService:
    def __init__(self):
        pass

    def _sort_reports(self, reports: List[Report]) -> List[Report]:
        """Sort reports chronologically by year and quarter"""
        def get_sort_key(report):
            year = report.report_year or 0
            quarter = report.report_quarter or 0
            if not quarter and report.report_type == 'annual':
                quarter = 4
            return (year, quarter)
        
        return sorted(reports, key=get_sort_key)

    def _extract_metric_series(self, reports: List[Report], metric_key: str) -> Dict[str, Any]:
        """Extract a specific metric series from sorted reports"""
        labels = []
        data = []
        
        for report in reports:
            if not report.key_metrics:
                continue
                
            val = report.key_metrics.get(metric_key)
            if val is not None:
                # Create label like "Q1 2024" or "2024"
                if report.report_quarter:
                    label = f"Q{report.report_quarter} {report.report_year}"
                else:
                    label = f"{report.report_year}"
                
                labels.append(label)
                data.append(val)
        
        return {"labels": labels, "data": data}

    def prepare_chart_data(self, reports: List[Report], metric_keys: List[str], chart_type: str = "line", title: str = "") -> Optional[Chart]:
        """Prepare chart data structure for frontend"""
        if not reports:
            return None
            
        sorted_reports = self._sort_reports(reports)

        chart_labels = []
        datasets = []

        colors = [
            {"border": "rgb(75, 192, 192)", "bg": "rgba(75, 192, 192, 0.2)"},
            {"border": "rgb(54, 162, 235)", "bg": "rgba(54, 162, 235, 0.2)"},
            {"border": "rgb(255, 99, 132)", "bg": "rgba(255, 99, 132, 0.2)"},
            {"border": "rgb(255, 206, 86)", "bg": "rgba(255, 206, 86, 0.2)"},
        ]


        for report in sorted_reports:
            if report.report_quarter:
                label = f"Q{report.report_quarter} {report.report_year}"
            else:
                label = f"{report.report_year}"
            chart_labels.append(label)

        for idx, key in enumerate(metric_keys):
            data_points = []
            for report in sorted_reports:
                val = report.key_metrics.get(key) if report.key_metrics else None
                data_points.append(val if val is not None else 0) # Use 0 or None for missing? Recharts handles null ok usually.
            
            color = colors[idx % len(colors)]
            
            # Translate key to readable label
            readable_label = key.replace("_", " ").title()
            if key == "revenue": readable_label = "Przychody"
            elif key == "net_income": readable_label = "Zysk Netto"
            elif key == "total_assets": readable_label = "Aktywa Razem"
            
            datasets.append(ChartDataset(
                label=readable_label,
                data=data_points,
                borderColor=color["border"],
                backgroundColor=color["bg"]
            ))
            
        return Chart(
            chart_id=f"chart_{'_'.join(metric_keys)}",
            type=chart_type,
            title=title,
            data=ChartData(
                labels=chart_labels,
                datasets=datasets
            )
        )

    def get_available_metrics(self, reports: List[Report]) -> List[str]:
        """Scan reports to see which metrics are available"""
        metrics = set()
        for report in reports:
            if report.key_metrics:
                metrics.update(report.key_metrics.keys())
        return list(metrics)
