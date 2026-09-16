import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session
from app.models import Task, ReportJob

REPORTS_DIR = "reports"


def generate_task_report(job_id: int, db: Session):
    job = db.query(ReportJob).filter(ReportJob.id == job_id).first()
    if not job:
        return

    try:
        job.status = "running"
        db.commit()

        # query and aggregate — real SQL work, not just a dump
        total = db.query(Task).count()
        done = db.query(Task).filter(Task.done == True).count()
        open_count = total - done

        os.makedirs(REPORTS_DIR, exist_ok=True)
        file_path = os.path.join(REPORTS_DIR, f"report-{job_id}.pdf")

        c = canvas.Canvas(file_path, pagesize=letter)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, 750, "Task Report")

        c.setFont("Helvetica", 11)
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        c.drawString(50, 725, f"Generated: {generated_at}")

        c.setFont("Helvetica", 13)
        y = 680
        for label, value in [
            ("Total tasks", total),
            ("Completed", done),
            ("Open", open_count),
        ]:
            c.drawString(50, y, f"{label}: {value}")
            y -= 25

        c.save()

        job.status = "done"
        job.file_path = file_path
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        db.commit()