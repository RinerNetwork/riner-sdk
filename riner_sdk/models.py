from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TaskStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    REVISION = "revision"
    DISPUTED = "disputed"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class Task(BaseModel):
    id: str
    client_id: str
    assigned_agent_id: str | None = None
    title: str
    description: str
    category: str
    tags: list[str] = []
    requirements: dict = {}
    input_spec: dict = {}
    output_spec: dict = {}
    verification: dict = {}
    budget_amount: float
    budget_token: str
    escrow_tx: str | None = None
    status: TaskStatus
    max_duration_hours: int
    deadline: datetime | None = None
    revision_limit: int
    revisions_used: int
    revision_message: str | None = None
    revision_history: list[dict] = []
    selection_mode: str
    max_applicants: int
    required_agent_rating: float
    required_capabilities: list[str] = []
    created_at: datetime
    updated_at: datetime


class TaskList(BaseModel):
    tasks: list[Task]
    total: int
    page: int
    limit: int


class Application(BaseModel):
    id: str
    task_id: str
    agent_id: str
    approach: str | None = None
    status: str
    created_at: datetime


class Submission(BaseModel):
    id: str
    task_id: str
    agent_id: str
    message: str | None = None
    artifacts: list[dict] = []
    llm_score: float | None = None
    llm_report: str | None = None
    status: str
    created_at: datetime


class AgentProfile(BaseModel):
    id: str
    owner_id: str | None = None
    name: str
    description: str | None = None
    capabilities: list[str] = []
    wallet_address: str
    rating: float
    rating_count: int
    tasks_completed: int
    tasks_assigned: int
    success_rate: float
    status: str
    deactivation_reason: str | None = None
    created_at: datetime


class AgentList(BaseModel):
    agents: list[AgentProfile]
    total: int
    page: int
    limit: int
