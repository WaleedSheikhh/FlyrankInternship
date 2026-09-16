import hashlib
import json
import os
from datetime import datetime, timezone
from app.database import SessionLocal
from app.models import EnrichmentJob
from app.llm.schema import EnrichmentOutput
from app.llm_helpers import load_prompt, call_model_with_retry, extract_json
from pydantic import ValidationError


def hash_input(data: dict) -> str:
    normalized = json.dumps(data, sort_keys=True)
    return hashlib.sha256(normalized.encode()).hexdigest()


def send_alert(job_id: int, error: str):
    print(f"ALERT: Job {job_id} failed permanently: {error}")


def run_enrichment_job(job_id: int):
    db = SessionLocal()
    try:
        job = db.query(EnrichmentJob).filter(EnrichmentJob.id == job_id).first()
        if not job:
            return

        job.status = "running"
        job.attempts += 1
        db.commit()

        input_dict = json.loads(job.input_data)
        system_prompt = load_prompt()
        user_content = json.dumps(input_dict)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        raw_text = call_model_with_retry(messages)

        try:
            json_str = extract_json(raw_text)
            parsed = json.loads(json_str)
            result = EnrichmentOutput(**parsed)
        except (ValueError, json.JSONDecodeError, ValidationError):
            repaired_text = call_model_with_retry(
                messages + [
                    {"role": "assistant", "content": raw_text},
                    {"role": "user", "content": "Your previous answer was invalid JSON or wrong shape. Return only corrected JSON matching the schema."},
                ]
            )
            json_str = extract_json(repaired_text)
            parsed = json.loads(json_str)
            result = EnrichmentOutput(**parsed)

        job.status = "done"
        job.result = result.model_dump_json()
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        db.commit()
        send_alert(job_id, str(e))

    finally:
        db.close()