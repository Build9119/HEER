import unittest
import tempfile
import os
from datetime import datetime

from agent.d1_persistence import D1Persistence
from agent.worker_registry import WorkerIdentity

class TestD1Persistence(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for testing
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.persistence = D1Persistence(db_path=self.db_path)

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_register_new_worker(self):
        """Test registering a new worker."""
        identity = WorkerIdentity(
            worker_id="worker-1",
            worker_instance_id="inst-1",
            worker_epoch=1,
            tenant_scope="tenant-a",
            state="REGISTERED",
            capabilities={"tool_class": "example-tool"},
            capabilities_version=1,
            heartbeat_sequence=0
        )
        
        result = self.persistence.register(identity)
        self.assertTrue(result["ok"])
        self.assertEqual(result["worker_id"], "worker-1")
        self.assertEqual(result["state"], "REGISTERED")
        self.assertEqual(result["capabilities_version"], 1)

    def test_register_duplicate_worker(self):
        """Test registering a duplicate worker (same instance, same epoch)."""
        identity = WorkerIdentity(
            worker_id="worker-1",
            worker_instance_id="inst-1",
            worker_epoch=1,
            tenant_scope="tenant-a",
            state="REGISTERED",
            capabilities={"tool_class": "example-tool"},
            capabilities_version=1,
            heartbeat_sequence=0
        )
        
        result = self.persistence.register(identity)
        self.assertTrue(result["ok"])
        self.assertTrue(result["duplicate"])

    def test_register_newer_epoch_supersedes_old(self):
        """Test that a newer epoch supersedes an older one."""
        identity = WorkerIdentity(
            worker_id="worker-1",
            worker_instance_id="inst-1",
            worker_epoch=1,
            tenant_scope="tenant-a",
            state="REGISTERED",
            capabilities={"tool_class": "example-tool"},
            capabilities_version=1,
            heartbeat_sequence=0
        )
        
        # Register with older epoch first
        result1 = self.persistence.register(identity)
        self.assertTrue(result1["ok"])
        
        # Update with newer epoch
        identity.worker_epoch = 2
        result2 = self.persistence.update("worker-1", worker_epoch=2)
        self.assertTrue(result2["ok"])
        
        # Verify the latest state
        worker = self.persistence.get("worker-1")
        self.assertEqual(worker["state"], "REGISTERED")
        self.assertEqual(worker["worker_epoch"], 2)

    def test_update_worker_fields(self):
        """Test updating worker fields."""
        identity = WorkerIdentity(
            worker_id="worker-1",
            worker_instance_id="inst-1",
            worker_epoch=1,
            tenant_scope="tenant-a",
            state="REGISTERED",
            capabilities={"tool_class": "old-tool"},
            capabilities_version=1,
            heartbeat_sequence=0
        )
        
        result = self.persistence.update("worker-1", worker_epoch=2, capabilities_version=2)
        self.assertTrue(result["ok"])
        
        worker = self.persistence.get("worker-1")
        self.assertEqual(worker["worker_epoch"], 2)
        self.assertEqual(worker["capabilities_version"], 2)

    def test_get_worker(self):
        """Test retrieving a worker."""
        identity = WorkerIdentity(
            worker_id="worker-1",
            worker_instance_id="inst-1",
            worker_epoch=1,
            tenant_scope="tenant-a",
            state="REGISTERED",
            capabilities={"tool_class": "example-tool"},
            capabilities_version=1,
            heartbeat_sequence=0
        )
        
        self.persistence.register(identity)
        worker = self.persistence.get("worker-1")
        self.assertIsNotNone(worker)
        self.assertEqual(worker["worker_id"], "worker-1")
        self.assertEqual(worker["state"], "REGISTERED")

    def test_list_workers(self):
        """Test listing all workers."""
        identity1 = WorkerIdentity(
            worker_id="worker-1",
            worker_instance_id="inst-1",
            worker_epoch=1,
            tenant_scope="tenant-a",
            state="REGISTERED",
            capabilities={"tool_class": "tool-a"},
            capabilities_version=1,
            heartbeat_sequence=0
        )
        
        identity2 = WorkerIdentity(
            worker_id="worker-2",
            worker_instance_id="inst-2",
            worker_epoch=1,
            tenant_scope="tenant-a",
            state="REGISTERED",
            capabilities={"tool_class": "tool-b"},
            capabilities_version=1,
            heartbeat_sequence=0
        )
        
        self.persistence.register(identity1)
        self.persistence.register(identity2)
        
        workers = self.persistence.list()
        self.assertEqual(len(workers), 2)
        self.assertIn("worker-1", [w["worker_id"] for w in workers])
        self.assertIn("worker-2", [w["worker_id"] for w in workers])

    def test_list_by_tenant(self):
        """Test listing workers filtered by tenant scope."""
        identity = WorkerIdentity(
            worker_id="worker-1",
            worker_instance_id="inst-1",
            worker_epoch=1,
            tenant_scope="tenant-a",
            state="REGISTERED",
            capabilities={"tool_class": "example-tool"},
            capabilities_version=1,
            heartbeat_sequence=0
        )
        
        self.persistence.register(identity)
        
        workers = self.persistence.list(tenant_scope="tenant-a")
        self.assertEqual(len(workers), 1)
        self.assertEqual(workers[0]["worker_id"], "worker-1")
        
        workers_other = self.persistence.list(tenant_scope="tenant-b")
        self.assertEqual(len(workers_other), 0)

    def test_mark_stale(self):
        """Test marking a worker as STALE."""
        identity = WorkerIdentity(
            worker_id="worker-1",
            worker_instance_id="inst-1",
            worker_epoch=1,
            tenant_scope="tenant-a",
            state="REGISTERED",
            capabilities={"tool_class": "example-tool"},
            capabilities_version=1,
            heartbeat_sequence=0
        )
        
        self.persistence.register(identity)
        
        # Mark as stale (simulate heartbeat with lower sequence)
        result = self.persistence.mark_stale(worker_id="worker-1", worker_instance_id="inst-1", worker_epoch=1)
        self.assertTrue(result["ok"])
        
        worker = self.persistence.get("worker-1")
        self.assertEqual(worker["state"], "STALE")

    def test_depart(self):
        """Test departing a worker."""
        identity = WorkerIdentity(
            worker_id="worker-1",
            worker_instance_id="inst-1",
            worker_epoch=1,
            tenant_scope="tenant-a",
            state="REGISTERED",
            capabilities={"tool_class": "example-tool"},
            capabilities_version=1,
            heartbeat_sequence=0
        )
        
        self.persistence.register(identity)
        
        result = self.persistence.depart(worker_id="worker-1", worker_instance_id="inst-1", worker_epoch=1)
        self.assertTrue(result["ok"])
        
        worker = self.persistence.get("worker-1")
        self.assertEqual(worker["state"], "DEPARTED")

    def test_get_nonexistent_worker(self):
        """Test getting a non-existent worker returns None."""
        worker = self.persistence.get("nonexistent")
        self.assertIsNone(worker)

    def test_cleanup(self):
        """Test database cleanup."""
        self.persistence.register(WorkerIdentity(
            worker_id="cleanup-test",
            worker_instance_id="inst-1",
            worker_epoch=1,
            tenant_scope="tenant-a",
            state="REGISTERED",
            capabilities={"tool_class": "test"},
            capabilities_version=1,
            heartbeat_sequence=0
        ))
        self.persistence.cleanup()
        # Should not raise an exception
        self.assertFalse(os.path.exists(self.db_path))

if __name__ == "__main__":
    unittest.main()