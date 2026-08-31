from datetime import datetime
from pathlib import Path
from typing import Any

from app.pdf_report import generate_event_dashboard_pdf
from app.schemas import EventDashboard


class ReportService:
    def generate_event_dashboard_report(
        self,
        dashboard: EventDashboard | dict[str, Any],
    ) -> None:
        event_dashboard = EventDashboard.model_validate(dashboard)
        output_path = Path("reports") / f"{event_dashboard.event_title}.pdf"
        generate_event_dashboard_pdf(
            event_dashboard,
            output_path,
            datetime.now(),
        )
