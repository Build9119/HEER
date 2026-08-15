#!/usr/bin/env python3
"""Deterministic Test Subprocess Worker for SubprocessTransport (HEER Phase 3.7).

Supported modes via CLI args or environment variables:
- normal (default): standard HELLO -> READY -> REQUEST -> RESPONSE flow
- crash: exit immediately or exit with non-zero status
- hang: sleep indefinitely without sending responses
- malformed: emit invalid JSON
- oversized: emit a message exceeding max_message_bytes
"""
import json
import os
import sys
import time

def main():
    mode = "normal"
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    mode = os.environ.get("TEST_WORKER_MODE", mode)

    if mode == "crash":
        sys.exit(1)

    if mode == "malformed":
        sys.stdout.write("THIS_IS_NOT_VALID_JSON\n")
        sys.stdout.flush()
        # Read READY and REQUEST so transport doesn't block on write
        sys.stdin.readline()  # READY
        sys.stdin.readline()  # REQUEST
        # Stay alive so transport can read the malformed line
        while True:
            time.sleep(1.0)

    if mode == "oversized":
        # Send HELLO, then send an oversized response line in chunks to avoid pipe deadlock
        hello = {"type": "HELLO", "worker_id": "test_worker", "worker_instance_id": "inst_1", "worker_epoch": 1, "nonce": os.environ.get("TEST_NONCE", "")}
        sys.stdout.write(json.dumps(hello) + "\n")
        sys.stdout.flush()
        # Read READY and REQUEST
        sys.stdin.readline()  # READY
        sys.stdin.readline()  # REQUEST
        huge_str = "x" * 2_000_000
        msg = {"type": "RESPONSE", "ok": True, "result": {"data": huge_str}}
        msg_bytes = (json.dumps(msg) + "\n").encode("utf-8")
        # Write in 64KB chunks to avoid filling pipe buffer
        for i in range(0, len(msg_bytes), 65536):
            chunk = msg_bytes[i:i+65536]
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
        sys.exit(0)

    if mode == "hang":
        # Emit HELLO so handshake passes, then sleep forever
        hello = {
            "type": "HELLO",
            "worker_id": os.environ.get("TEST_WORKER_ID", "test_worker"),
            "worker_instance_id": os.environ.get("TEST_WORKER_INSTANCE_ID", "inst_1"),
            "worker_epoch": int(os.environ.get("TEST_WORKER_EPOCH", 1)),
            "tenant_id": os.environ.get("TEST_TENANT_ID"),
            "nonce": os.environ.get("TEST_NONCE"),
        }
        sys.stdout.write(json.dumps(hello) + "\n")
        sys.stdout.flush()
        # Read READY and REQUEST so transport doesn't block on write
        sys.stdin.readline()  # READY
        sys.stdin.readline()  # REQUEST
        while True:
            time.sleep(1.0)

    # Default / normal mode:
    # 1. Emit HELLO
    hello = {
        "type": "HELLO",
        "worker_id": os.environ.get("TEST_WORKER_ID", "test_worker"),
        "worker_instance_id": os.environ.get("TEST_WORKER_INSTANCE_ID", "inst_1"),
        "worker_epoch": int(os.environ.get("TEST_WORKER_EPOCH", 1)),
        "tenant_id": os.environ.get("TEST_TENANT_ID", "tenant_a"),
        "nonce": os.environ.get("TEST_NONCE", "nonce_123"),
    }
    sys.stdout.write(json.dumps(hello) + "\n")
    sys.stdout.flush()

    # 2. Wait for READY
    ready_line = sys.stdin.readline()
    if not ready_line:
        sys.exit(0)

    # 3. Receive REQUEST
    req_line = sys.stdin.readline()
    if not req_line:
        sys.exit(0)

    req = json.loads(req_line)
    tool_name = req.get("tool")
    task_input = req.get("input", {})

    # Simulate heartbeat if requested in input
    if task_input.get("send_heartbeat"):
        sys.stdout.write(json.dumps({"type": "HEARTBEAT"}) + "\n")
        sys.stdout.flush()
        time.sleep(0.1)

    # Respond with tool result
    if task_input.get("fail"):
        resp = {"type": "RESPONSE", "ok": False, "error": task_input.get("error_msg", "Worker simulated error")}
    else:
        resp = {"type": "RESPONSE", "ok": True, "result": {"echo_tool": tool_name, "echo_input": task_input, "status": "completed"}}

    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()

    # Wait for SHUTDOWN or EOF
    shutdown_line = sys.stdin.readline()
    sys.exit(0)

if __name__ == "__main__":
    main()