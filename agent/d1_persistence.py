import sqlite3
import json
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

from .worker_contracts import WorkerIdentity, WorkerCapabilities, WorkerLivenessState

__all__ = ["D1Persistence"]


@dataclass
class _PersistedWorker:
    """Internal persisted representation - includes runtime state fields not in WorkerIdentity."""
    worker_id: str
    worker_instance_id: str
    worker_epoch: int
    tenant_scope: tuple  # tuple of strings (serialized as JSON)
    state: str  # WorkerLivenessState value
    capabilities: Optional[dict]  # serialized WorkerCapabilities or None
    capabilities_version: int  # persistence metadata version
    heartbeat_seq: int
    registered_at: float
    reported_at: Optional[float] = None
    deletion_mark: bool = False


class D1Persistence:
    """D1 Persistence Layer - stores worker identity + runtime state in SQLite.
    
    WorkerIdentity (immutable contract) is stored alongside runtime state
    (state, heartbeat_seq, timestamps) which come from WorkerRegistry._Entry.
    """

    def __init__(self, db_path: str = "data/.heer/d1_persistence.db"):
        self.db_path = db_path
        self.conn = None
        self._conn_open = False
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workers (
                    worker_id TEXT PRIMARY KEY,
                    worker_instance_id TEXT NOT NULL,
                    worker_epoch INTEGER NOT NULL,
                    tenant_scope TEXT NOT NULL,  -- JSON array of strings
                    state TEXT NOT NULL CHECK (state IN ('REGISTERED', 'LIVE', 'STALE', 'DEPARTED')),
                    capabilities TEXT,  -- JSON serialized WorkerCapabilities or NULL
                    capabilities_version INTEGER NOT NULL DEFAULT 1,
                    heartbeat_seq INTEGER NOT NULL DEFAULT 0,
                    registered_at REAL NOT NULL,
                    reported_at REAL,
                    deletion_mark BOOLEAN NOT NULL DEFAULT 0
                )
            """)
            # Create indices
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tenant ON workers (tenant_scope)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_epoch ON workers (worker_epoch)")

    def _get_conn(self):
        if not self._conn_open or self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA synchronous = FULL")
            self.conn.execute("PRAGMA journal_mode = WAL")
            self.conn.execute("PRAGMA busy_timeout = 5000")
            self.conn.execute("PRAGMA foreign_keys = 1")
            self._conn_open = True
        return self.conn

    def _commit(self):
        if self.conn and self._conn_open:
            self.conn.commit()
        else:
            raise RuntimeError("No active connection")

    def _rollback(self):
        if self.conn and self._conn_open:
            self.conn.rollback()
        raise RuntimeError("Commit failed")

    def _serialize_capabilities(self, caps: Optional[WorkerCapabilities]) -> Optional[str]:
        """Serialize WorkerCapabilities to JSON string."""
        if caps is None:
            return None
        from .worker_contracts import to_dict as worker_contract_to_dict
        return json.dumps(worker_contract_to_dict(caps), sort_keys=True)

    def _deserialize_capabilities(self, data: Optional[str]) -> Optional[WorkerCapabilities]:
        """Deserialize JSON string to WorkerCapabilities."""
        if data is None:
            return None
        from .worker_contracts import from_dict as worker_contract_from_dict
        return worker_contract_from_dict(json.loads(data), WorkerCapabilities)

    def _serialize_tenant_scope(self, tenant_scope: tuple) -> str:
        """Serialize tenant_scope tuple to JSON array string."""
        return json.dumps(list(tenant_scope))

    def _deserialize_tenant_scope(self, data: str) -> tuple:
        """Deserialize JSON array string to tuple."""
        return tuple(json.loads(data))

    def register(self, worker: WorkerIdentity, *, state: str = "REGISTERED",
                 heartbeat_seq: int = 0, registered_at: Optional[float] = None) -> dict:
        """Persist a worker registration with runtime state.
        
        Args:
            worker: WorkerIdentity (immutable contract fields only)
            state: WorkerLivenessState value (REGISTERED, LIVE, STALE, DEPARTED)
            heartbeat_seq: fabric-local heartbeat sequence
            registered_at: registration timestamp (defaults to now)
        """
        try:
            conn = self._get_conn()
            
            now = datetime.now().timestamp()
            data = {
                "worker_id": worker.worker_id,
                "worker_instance_id": worker.worker_instance_id,
                "worker_epoch": worker.worker_epoch,
                "tenant_scope": self._serialize_tenant_scope(worker.tenant_scope),
                "state": state,
                "capabilities": self._serialize_capabilities(worker.capabilities),
                "capabilities_version": 1,  # persistence schema version
                "heartbeat_seq": heartbeat_seq,
                "registered_at": registered_at if registered_at is not None else now,
                "reported_at": None,
                "deletion_mark": False
            }
            cursor = conn.cursor()
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

    def update_state(self, worker_id: str, state: str, heartbeat_seq: int,
                     reported_at: Optional[float] = None) -> dict:
        """Update worker liveness state and heartbeat."""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            now = datetime.now().timestamp()
            cursor.execute("""
                UPDATE workers
                SET state = ?, heartbeat_seq = ?, reported_at = ?
                WHERE worker_id = ?
            """, (state, heartbeat_seq, reported_at if reported_at is not None else now, worker_id))
            if cursor.rowcount == 0:
                return {"ok": False, "error": "Worker not found"}
            self._commit()
            return {"ok": True, "message": "State update persisted"}
        except Exception as e:
            self._rollback()
            return {"ok": False, "error": str(e)}

    def update_capabilities(self, worker_id: str, capabilities: Optional[WorkerCapabilities],
                            capabilities_version: int) -> dict:
        """Update worker capabilities (mutable at registration per gate §3)."""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE workers
                SET capabilities = ?, capabilities_version = ?
                WHERE worker_id = ?
            """, (self._serialize_capabilities(capabilities), capabilities_version, worker_id))
            if cursor.rowcount == 0:
                return {"ok": False, "error": "Worker not found"}
            self._commit()
            return {"ok": True, "message": "Capabilities update persisted"}
        except Exception as e:
            self._rollback()
            return {"ok": False, "error": str(e)}

    def mark_stale(self, worker_id: str, worker_instance_id: str, worker_epoch: int) -> dict:
        """Mark worker as STALE (registry-local transition)."""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            # Verify instance/epoch match before transition
            cursor.execute("""
                SELECT worker_instance_id, worker_epoch FROM workers WHERE worker_id = ?
            """, (worker_id,))
            row = cursor.fetchone()
            if not row:
                return {"ok": False, "error": "worker not registered"}
            if row[0] != worker_instance_id or row[1] != worker_epoch:
                return {"ok": False, "error": "stale (instance/epoch mismatch)"}
            
            cursor.execute("""
                UPDATE workers SET state = 'STALE' WHERE worker_id = ?
            """, (worker_id,))
            self._commit()
            return {"ok": True, "worker_id": worker_id, "state": "STALE"}
        except Exception as e:
            self._rollback()
            return {"ok": False, "error": str(e)}

    def depart(self, worker_id: str, worker_instance_id: str, worker_epoch: int) -> dict:
        """Mark worker as DEPARTED (terminal state)."""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT worker_instance_id, worker_epoch FROM workers WHERE worker_id = ?
            """, (worker_id,))
            row = cursor.fetchone()
            if not row:
                return {"ok": False, "error": "worker not registered"}
            if row[0] != worker_instance_id or row[1] != worker_epoch:
                return {"ok": False, "error": "stale (instance/epoch mismatch)"}
            
            cursor.execute("""
                UPDATE workers SET state = 'DEPARTED' WHERE worker_id = ?
            """, (worker_id,))
            self._commit()
            return {"ok": True, "worker_id": worker_id, "state": "DEPARTED"}
        except Exception as e:
            self._rollback()
            return {"ok": False, "error": str(e)}

    def get(self, worker_id: str) -> Optional[_PersistedWorker]:
        """Retrieve persisted worker by ID."""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
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
                tenant_scope=self._deserialize_tenant_scope(row[3]),
                state=row[4],
                capabilities=json.loads(row[5]) if row[5] else None,
                capabilities_version=row[6],
                heartbeat_seq=row[7],
                registered_at=row[8],
                reported_at=row[9],
                deletion_mark=bool(row[10])
            )
        except Exception:
            return None

    def list(self, tenant_scope: Optional[str] = None) -> list:
        """List all workers, optionally filtered by tenant."""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            if tenant_scope is not None:
                # Filter by tenant_scope containing the tenant using json_each
                cursor.execute("""
                    SELECT * FROM workers 
                    WHERE EXISTS (
                        SELECT 1 FROM json_each(tenant_scope) WHERE value = ?
                    )
                """, (tenant_scope,))
            else:
                cursor.execute("SELECT * FROM workers")
            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append({
                    "worker_id": row[0],
                    "worker_instance_id": row[1],
                    "worker_epoch": row[2],
                    "tenant_scope": self._deserialize_tenant_scope(row[3]),
                    "state": row[4],
                    "capabilities": json.loads(row[5]) if row[5] else None,
                    "capabilities_version": row[6],
                    "heartbeat_seq": row[7],
                    "registered_at": row[8],
                    "reported_at": row[9],
                    "deletion_mark": bool(row[10])
                })
            return result
        except Exception:
            return []

    def cleanup(self):
        """Close database connection."""
        if self.conn and self._conn_open:
            self.conn.close()
            self.conn = None
            self._conn_open = False