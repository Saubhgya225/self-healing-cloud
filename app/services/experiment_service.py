import os
import sqlite3
import csv
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.models.schemas import ExperimentRecord

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "results", "experiments.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "results", "experiments.csv")

class ExperimentService:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    scenario TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    recovery_time_seconds REAL,
                    initial_replicas INTEGER,
                    final_replicas INTEGER,
                    error_count INTEGER,
                    status TEXT NOT NULL,
                    notes TEXT
                )
            """)
            conn.commit()

    def record_experiment(
        self,
        scenario: str,
        initial_replicas: int,
        final_replicas: int,
        recovery_time_seconds: Optional[float] = None,
        error_count: int = 0,
        status: str = "COMPLETED",
        notes: str = ""
    ) -> ExperimentRecord:
        exp_id = f"EXP-{uuid.uuid4().hex[:8].upper()}"
        now_str = datetime.now(timezone.utc).isoformat()

        record = ExperimentRecord(
            experiment_id=exp_id,
            scenario=scenario,
            start_time=now_str,
            end_time=now_str,
            recovery_time_seconds=recovery_time_seconds,
            initial_replicas=initial_replicas,
            final_replicas=final_replicas,
            error_count=error_count,
            status=status,
            notes=notes
        )

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO experiments (
                    experiment_id, scenario, start_time, end_time,
                    recovery_time_seconds, initial_replicas, final_replicas,
                    error_count, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.experiment_id,
                record.scenario,
                record.start_time,
                record.end_time,
                record.recovery_time_seconds,
                record.initial_replicas,
                record.final_replicas,
                record.error_count,
                record.status,
                record.notes
            ))
            conn.commit()

        self._sync_csv()
        return record

    def list_experiments(self) -> List[ExperimentRecord]:
        records = []
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM experiments ORDER BY start_time DESC")
            rows = cursor.fetchall()
            for r in rows:
                records.append(ExperimentRecord(
                    experiment_id=r["experiment_id"],
                    scenario=r["scenario"],
                    start_time=r["start_time"],
                    end_time=r["end_time"],
                    recovery_time_seconds=r["recovery_time_seconds"],
                    initial_replicas=r["initial_replicas"],
                    final_replicas=r["final_replicas"],
                    error_count=r["error_count"],
                    status=r["status"],
                    notes=r["notes"]
                ))
        return records

    def _sync_csv(self):
        records = self.list_experiments()
        with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Experiment ID", "Scenario", "Start Time", "End Time",
                "Recovery Time (s)", "Initial Replicas", "Final Replicas",
                "Error Count", "Status", "Notes"
            ])
            for rec in records:
                writer.writerow([
                    rec.experiment_id,
                    rec.scenario,
                    rec.start_time,
                    rec.end_time,
                    rec.recovery_time_seconds or "",
                    rec.initial_replicas,
                    rec.final_replicas,
                    rec.error_count,
                    rec.status,
                    rec.notes or ""
                ])

experiment_service = ExperimentService()
