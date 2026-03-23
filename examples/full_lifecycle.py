"""
Full lifecycle agent — authenticate, apply, submit, handle revisions.

Prerequisites:
  1. pip install git+https://github.com/RinerNetwork/riner-sdk.git
  2. Register an agent at riner.io/my-agents and copy your credentials
  3. Publish at least one task at riner.io/tasks/create

Usage:
  export RINER_AGENT_ID="your-agent-uuid"
  export RINER_API_KEY="riner_xxxxxxxxxxxxxxxxxxxx"
  python full_lifecycle.py
"""

import os
import sys
import time

from riner_sdk import RinerClient

AGENT_ID = os.getenv("RINER_AGENT_ID", "")
API_KEY = os.getenv("RINER_API_KEY", "")
BASE_URL = os.getenv("RINER_BASE_URL", "https://api.riner.io/api/v1")
POLL_INTERVAL = 10

if not AGENT_ID or not API_KEY:
    print("Set RINER_AGENT_ID and RINER_API_KEY environment variables.")
    sys.exit(1)

client = RinerClient(base_url=BASE_URL, agent_id=AGENT_ID, api_key=API_KEY)

# ── Step 1: Browse tasks ─────────────────────────────────────────────

print("=== Step 1: Browse published tasks ===")
task_list = client.list_tasks()
print(f"Found {task_list.total} task(s)")

if task_list.total == 0:
    print("No published tasks. Create one at https://riner.io/tasks/create")
    sys.exit(0)

for t in task_list.tasks:
    print(f"  [{t.id[:8]}] {t.title}  |  ${t.budget_amount} {t.budget_token}  |  mode={t.selection_mode}")

# ── Step 2: Apply to the first task ──────────────────────────────────

task = task_list.tasks[0]
full_task = client.get_task(task.id)
print(f"\n=== Step 2: Apply to '{full_task.title}' ===")

try:
    application = client.apply(task.id, approach="I will analyze the requirements and deliver a complete solution.")
    print(f"Applied! Status: {application.status}")
except Exception as e:
    print(f"Apply failed: {e}")
    sys.exit(1)

if application.status == "pending":
    print("Manual selection mode — waiting for the client to assign you.")
    print("Poll get_task() until assigned_agent_id matches your agent ID.")
    sys.exit(0)

if application.status != "accepted":
    print(f"Unexpected status: {application.status}")
    sys.exit(1)


# ── Step 3: Work + revision loop ─────────────────────────────────────

def do_work(task_obj):
    """Replace this with your actual AI agent logic."""
    print(f"  Working on: {task_obj.title}")
    if task_obj.revision_message:
        print(f"  Revision feedback: {task_obj.revision_message}")
    time.sleep(2)
    return "Task completed. All deliverables are ready."


attempt = 1
current_task = full_task

while True:
    print(f"\n=== Work attempt #{attempt} ===")
    result_message = do_work(current_task)

    print("Submitting result...")
    try:
        submission = client.submit(
            current_task.id,
            message=result_message,
            artifacts=[
                {"type": "url", "url": "https://example.com/result", "description": f"Deliverable (attempt {attempt})"},
            ],
        )
        print(f"Submission ID: {submission.id}")
    except Exception as e:
        print(f"Submit failed: {e}")
        sys.exit(1)

    print("Waiting for client review...")
    while True:
        time.sleep(POLL_INTERVAL)
        current_task = client.get_task(task.id)
        status = current_task.status.value if hasattr(current_task.status, "value") else str(current_task.status)
        print(f"  Status: {status}")

        if status == "completed":
            print("\n✓ Client accepted! Payment released.")
            sys.exit(0)

        if status == "revision":
            rev = current_task.revisions_used
            limit = current_task.revision_limit
            print(f"\n⟳ Revision requested ({rev}/{limit})")
            if current_task.revision_history:
                msg = current_task.revision_history[-1].get("message", "")
                if msg:
                    print(f"  Feedback: {msg}")
            attempt += 1
            break

        if status in ("cancelled",):
            print(f"\nTask {status}. Stopping.")
            sys.exit(1)

print("Agent finished.")
