import sqlite3
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

from .worker_registry import WorkerRegistry, WorkerIdentity

__all__ = ["D1Persistence"]

@dataclass
class _PersistedWorker:
    worker_id: str
    worker_instance_id: str
    worker_epoch: int
    tenant_scope: str
    state: str
    capabilities: dict
    capabilities_version: int
    heartbeat_seq: int
    registered_at: float
    reported_at: Optional[float] = None
    deletion_mark: bool = False

class D1Persistence:
    def __init__(self, db_path: str = "data/.heer/d1_persistence.db"):
        self.db_path = db_path
        self.conn = None
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workers (
                    worker_id TEXT PRIMARY KEY,
                    worker_instance_id TEXT NOT NULL,
                    worker_epoch INTEGER NOT NULL,
                    tenant_scope TEXT NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('REGISTERED', 'LIVE', 'STALE', 'DEPARTED')),
                    capabilities TEXT NOT NULL,
                    capabilities_version INTEGER NOT NULL DEFAULT 1,
                    heartbeat_seq INTEGER NOT NULL,
                    registered_at REAL NOT NULL,
                    reported_at REAL,
                    deletion_mark BOOLEAN NOT NULL DEFAULT 0
                )
            """)
            # Create indices
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tenant ON workers (tenant_scope)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_epoch ON workers (worker_epoch)")

    def _get_conn(self):
        if not self.conn or self.conn.closed:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA synchronous = FULL")
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.conn.execute("PRAGMA busy_timeout = 5000")
            self.conn.execute("PRAGMA foreign_keys = 1")
            self.conn.execute("BEGIN IMMEDIATE")

    def _commit(self):
        if self.conn:
            self.conn.commit()
            self.conn.execute("COMMIT")
        else:
            raise RuntimeError("No active connection")

    def _rollback(self):
        if self.conn:
            self.conn.rollback()
            raise RuntimeError("Commit failed")

    def register(self, worker: WorkerIdentity) -> dict:
        try:
            self._get_conn()
            data = {
                "worker_id": worker.worker_id,
                "worker_instance_id": worker.worker_instance_id,
                "worker_epoch": worker.worker_epoch,
                "tenant_scope": worker.tenant_scope,
                "state": worker.state.value if worker.state else "REGISTERED",
                "capabilities": json.dumps(worker.capabilities, sort_keys=True),
                "capabilities_version": worker.capabilities_version,
                "heartbeat_seq": worker.heartbeat_sequence,
                "registered_at": datetime.now().timestamp(),
                "reported_at": None,
                "deletion_mark": False
            }
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO workers (
                    worker_id, worker_instance_id, worker_epoch,
                    tenant_scope, state, capabilities, 
                    capabilities_version, heartbeat_seq,
                    registered_at, reported_at, deletion_mark
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["worker_id"], data["worker_instance_id"], data["worker_epoch"],
                data["tenant_scope"], data["state"], data["capabilities"],
                data["capabilities_version"], data["heartbeat_seq"],
                data["registered_at"], data["reported_at"], data["deletion_mark"]
            ))
            self._commit()
            return {"ok": True, "message": "Registration persisted"}
        except Exception as e:
            self._rollback()
            return {"ok": False, "error": str(e)}

    def update(self, worker_id: str, **kwargs) -> dict:
        try:
            self._get_conn()
            cursor = self.conn.cursor()
            set_clause = ", ".join(f"{k}=?" for k in kwargs.keys())
            values = list(kwargs.values())
            cursor.execute(f"""
                UPDATE workers
                SET {set_clause}
                WHERE worker_id = ?
            """, tuple(values) + [worker_id])
            if cursor.rowcount == 0:
                return {"ok": False, "error": "Worker not found"}
            self._commit()
            return {"ok": True, "message": "Update persisted"}
        except Exception as e:
            self._rollback()
            return {"ok": False, "error": str(e)}

    def get(self, worker_id: str) -> Optional[_PersistedWorker]:
        try:
            self._get_conn()
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM workers WHERE worker_id = ?
            """, (worker_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return _PersistedWorker(
                worker_id=row[0],
                worker_instance_id=row[1],
                worker_epoch=row[2],
                tenant_scope=row[3],
                state=row[4],
                capabilities=json.loads(row[5]),
                capabilities_version=row[6],
                heartbeat_seq=row[7],
                registered_at=row[8],
                reported_at=row[9],
                deletion_mark=row[10]
            )
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def cleanup(self):
        if self.conn:
            self.conn.close()