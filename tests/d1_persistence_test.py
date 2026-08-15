import unittest
import tempfile
import os

from agent.d1_persistence import D1Persistence
from agent.worker_contracts import WorkerIdentity, WorkerCapabilities, WorkerLivenessState
from agent.runtime_contracts import (
    RuntimeCapabilities,
    RuntimeCapability,
    RuntimeIsolation,
    RuntimeTransportKind,
)


def _make_caps(tool_classes=("bash", "file"), features=()):
    rc = RuntimeCapabilities(
        transport=RuntimeTransportKind.INPROCESS,
        isolation=RuntimeIsolation.PROCESS,
        max_concurrency=4,
        supports_heartbeat=True,
        supports_hard_timeout=True,
        supports_secrets=False,
        supports_tenant_isolation=True,
        features=frozenset(features),
    )
    return WorkerCapabilities(
        runtime_capabilities=rc,
        tool_classes=tool_classes,
        max_cpu_cores=4,
        architecture="arm64",
        network_policy="allow",
        region="in",
        compliance_boundary="default",
        runtime_version="1.0.0",
    )


def _identity(worker_id="w-1", instance="i-1", epoch=1, tenant=("t1",),
              caps=None, isolation=RuntimeIsolation.PROCESS, transport="rt-1"):
    return WorkerIdentity(
        worker_id=worker_id,
        worker_instance_id=instance,
        worker_epoch=epoch,
        tenant_scope=tenant,
        capabilities=caps,
        isolation_mode=isolation,
        transport_identity=transport,
    )


class TestD1Persistence(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for testing
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.persistence = D1Persistence(db_path=self.db_path)

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_register_new_worker(self):
        """Test registering a new worker."""
        identity = _identity(
            worker_id="worker-1",
            instance="inst-1",
            epoch=1,
            tenant=("tenant-a",),
            caps=_make_caps()
        )

        result = self.persistence.register(identity)
        self.assertTrue(result["ok"])
        
        worker = self.persistence.get("worker-1")
        self.assertIsNotNone(worker)
        self.assertEqual(worker.worker_id, "worker-1")
        self.assertEqual(worker.state, "REGISTERED")
        self.assertEqual(worker.capabilities_version, 1)
        self.assertEqual(worker.heartbeat_seq, 0)
        self.assertEqual(worker.tenant_scope, ("tenant-a",))

    def test_register_duplicate_worker(self):
        """Test registering a duplicate worker (same instance, same epoch)."""
        identity = _identity(
            worker_id="worker-1",
            instance="inst-1",
            epoch=1,
            tenant=("tenant-a",),
            caps=None
        )

        result1 = self.persistence.register(identity)
        self.assertTrue(result1["ok"])

        result2 = self.persistence.register(identity)
        self.assertTrue(result2["ok"])

        worker = self.persistence.get("worker-1")
        self.assertEqual(worker.state, "REGISTERED")

    def test_register_newer_epoch_supersedes_old(self):
        """Test that a newer epoch supersedes an older one."""
        identity = _identity(
            worker_id="worker-1",
            instance="inst-1",
            epoch=1,
            tenant=("tenant-a",),
            caps=_make_caps()
        )

        # Register with older epoch first
        result1 = self.persistence.register(identity)
        self.assertTrue(result1["ok"])

        # Update with newer epoch (simulate new registration)
        identity_v2 = _identity(
            worker_id="worker-1",
            instance="inst-2",  # new instance
            epoch=2,  # newer epoch
            tenant=("tenant-a",),
            caps=_make_caps()
        )
        result2 = self.persistence.register(identity_v2)
        self.assertTrue(result2["ok"])

        # Verify the latest state
        worker = self.persistence.get("worker-1")
        self.assertEqual(worker.state, "REGISTERED")
        self.assertEqual(worker.worker_epoch, 2)
        self.assertEqual(worker.worker_instance_id, "inst-2")

    def test_update_worker_state(self):
        """Test updating worker liveness state and heartbeat."""
        identity = _identity(
            worker_id="worker-1",
            instance="inst-1",
            epoch=1,
            tenant=("tenant-a",),
            caps=_make_caps()
        )

        self.persistence.register(identity)
        
        # Update state to LIVE with heartbeat
        result = self.persistence.update_state("worker-1", "LIVE", 1, 1000.0)
        self.assertTrue(result["ok"])

        worker = self.persistence.get("worker-1")
        self.assertEqual(worker.state, "LIVE")
        self.assertEqual(worker.heartbeat_seq, 1)
        self.assertEqual(worker.reported_at, 1000.0)

    def test_update_capabilities(self):
        """Test updating worker capabilities."""
        identity = _identity(
            worker_id="worker-1",
            instance="inst-1",
            epoch=1,
            tenant=("tenant-a",),
            caps=_make_caps(tool_classes=("old-tool",))
        )

        self.persistence.register(identity)

        new_caps = _make_caps(tool_classes=("new-tool",))
        result = self.persistence.update_capabilities("worker-1", new_caps, 2)
        self.assertTrue(result["ok"])

        worker = self.persistence.get("worker-1")
        self.assertEqual(worker.capabilities_version, 2)
        self.assertIsNotNone(worker.capabilities)
        self.assertIn("new-tool", worker.capabilities["tool_classes"])

    def test_get_worker(self):
        """Test retrieving a worker."""
        identity = _identity(
            worker_id="worker-1",
            instance="inst-1",
            epoch=1,
            tenant=("tenant-a",),
            caps=_make_caps()
        )

        self.persistence.register(identity)
        worker = self.persistence.get("worker-1")
        self.assertIsNotNone(worker)
        self.assertEqual(worker.worker_id, "worker-1")
        self.assertEqual(worker.state, "REGISTERED")
        self.assertEqual(worker.tenant_scope, ("tenant-a",))

    def test_list_workers(self):
        """Test listing all workers."""
        identity1 = _identity(
            worker_id="worker-1",
            instance="inst-1",
            epoch=1,
            tenant=("tenant-a",),
            caps=None
        )

        identity2 = _identity(
            worker_id="worker-2",
            instance="inst-2",
            epoch=1,
            tenant=("tenant-a",),
            caps=None
        )

        self.persistence.register(identity1)
        self.persistence.register(identity2)

        workers = self.persistence.list()
        self.assertEqual(len(workers), 2)
        worker_ids = [w["worker_id"] for w in workers]
        self.assertIn("worker-1", worker_ids)
        self.assertIn("worker-2", worker_ids)

    def test_list_by_tenant(self):
        """Test listing workers filtered by tenant scope."""
        identity = _identity(
            worker_id="worker-1",
            instance="inst-1",
            epoch=1,
            tenant=("tenant-a",),
            caps=_make_caps()
        )

        self.persistence.register(identity)

        workers = self.persistence.list(tenant_scope="tenant-a")
        self.assertEqual(len(workers), 1)
        self.assertEqual(workers[0]["worker_id"], "worker-1")

        workers_other = self.persistence.list(tenant_scope="tenant-b")
        self.assertEqual(len(workers_other), 0)

    def test_mark_stale(self):
        """Test marking a worker as STALE."""
        identity = _identity(
            worker_id="worker-1",
            instance="inst-1",
            epoch=1,
            tenant=("tenant-a",),
            caps=_make_caps()
        )

        self.persistence.register(identity)

        # Mark as stale
        result = self.persistence.mark_stale("worker-1", "inst-1", 1)
        self.assertTrue(result["ok"])

        worker = self.persistence.get("worker-1")
        self.assertEqual(worker.state, "STALE")

    def test_mark_stale_wrong_instance_rejected(self):
        """Test that mark_stale rejects wrong instance/epoch."""
        identity = _identity(
            worker_id="worker-1",
            instance="inst-1",
            epoch=1,
            tenant=("tenant-a",),
            caps=_make_caps()
        )

        self.persistence.register(identity)

        # Try with wrong instance
        result = self.persistence.mark_stale("worker-1", "wrong-inst", 1)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "stale (instance/epoch mismatch)")

        # Try with wrong epoch
        result = self.persistence.mark_stale("worker-1", "inst-1", 999)
        self.assertFalse(result["ok"])

    def test_depart(self):
        """Test departing a worker."""
        identity = _identity(
            worker_id="worker-1",
            instance="inst-1",
            epoch=1,
            tenant=("tenant-a",),
            caps=_make_caps()
        )

        self.persistence.register(identity)

        result = self.persistence.depart("worker-1", "inst-1", 1)
        self.assertTrue(result["ok"])

        worker = self.persistence.get("worker-1")
        self.assertEqual(worker.state, "DEPARTED")

    def test_depart_wrong_instance_rejected(self):
        """Test that depart rejects wrong instance/epoch."""
        identity = _identity(
            worker_id="worker-1",
            instance="inst-1",
            epoch=1,
            tenant=("tenant-a",),
            caps=_make_caps()
        )

        self.persistence.register(identity)

        result = self.persistence.depart("worker-1", "wrong-inst", 1)
        self.assertFalse(result["ok"])

    def test_get_nonexistent_worker(self):
        """Test getting a non-existent worker returns None."""
        worker = self.persistence.get("nonexistent")
        self.assertIsNone(worker)

    def test_list_empty(self):
        """Test listing workers when database is empty."""
        workers = self.persistence.list()
        self.assertEqual(len(workers), 0)

    def test_capabilities_none(self):
        """Test worker with no capabilities."""
        identity = _identity(
            worker_id="worker-1",
            instance="inst-1",
            epoch=1,
            tenant=("tenant-a",),
            caps=None
        )

        self.persistence.register(identity)
        worker = self.persistence.get("worker-1")
        self.assertIsNotNone(worker)
        self.assertIsNone(worker.capabilities)

    def test_cleanup(self):
        """Test database cleanup."""
        self.persistence.register(_identity(
            worker_id="cleanup-test",
            instance="inst-1",
            epoch=1,
            tenant=("tenant-a",),
            caps=_make_caps()
        ))
        self.persistence.cleanup()
        # Database file should still exist, just connection closed
        self.assertTrue(os.path.exists(self.db_path))


if __name__ == "__main__":
    unittest.main()
