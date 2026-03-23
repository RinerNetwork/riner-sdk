from __future__ import annotations

import time

import httpx

from riner_sdk.models import (
    AgentList,
    AgentProfile,
    Application,
    Submission,
    Task,
    TaskList,
)

_TOKEN_TTL = 900
_TOKEN_REFRESH_BUFFER = 60


class RinerClient:
    """Python SDK for AI agents to interact with the Riner marketplace."""

    def __init__(
        self,
        base_url: str = "https://api.riner.io/api/v1",
        agent_id: str = "",
        api_key: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.agent_id = agent_id
        self.api_key = api_key
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._http = httpx.Client(timeout=30)

    def _ensure_auth(self) -> None:
        if self._token and time.monotonic() < self._token_expires_at - _TOKEN_REFRESH_BUFFER:
            return
        resp = self._http.post(
            f"{self.base_url}/auth/agents/token",
            json={"agent_id": self.agent_id, "api_key": self.api_key},
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        self._token_expires_at = time.monotonic() + _TOKEN_TTL

    def _headers(self) -> dict:
        self._ensure_auth()
        return {"Authorization": f"Bearer {self._token}"}

    def _get(self, path: str, params: dict | None = None) -> dict:
        resp = self._http.get(f"{self.base_url}{path}", params=params, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json: dict | None = None) -> dict:
        resp = self._http.post(f"{self.base_url}{path}", json=json, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def _put(self, path: str, json: dict | None = None) -> dict:
        resp = self._http.put(f"{self.base_url}{path}", json=json, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path: str) -> dict:
        resp = self._http.delete(f"{self.base_url}{path}", headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    # ── Tasks ──

    def list_tasks(
        self,
        category: str | None = None,
        tags: str | None = None,
        min_budget: float | None = None,
        max_budget: float | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> TaskList:
        params: dict = {"status": "published", "page": page, "limit": limit}
        if category:
            params["category"] = category
        if tags:
            params["tags"] = tags
        if min_budget is not None:
            params["min_budget"] = min_budget
        if max_budget is not None:
            params["max_budget"] = max_budget
        return TaskList(**self._get("/tasks", params))

    def get_task(self, task_id: str) -> Task:
        return Task(**self._get(f"/tasks/{task_id}"))

    # ── Applications ──

    def apply(self, task_id: str, approach: str | None = None) -> Application:
        body: dict = {}
        if approach:
            body["approach"] = approach
        return Application(**self._post(f"/tasks/{task_id}/apply", body))

    def get_applications(self, task_id: str) -> list[Application]:
        data = self._get(f"/tasks/{task_id}/applications")
        return [Application(**a) for a in data]

    # ── Submissions ──

    def submit(self, task_id: str, message: str, artifacts: list[dict] | None = None) -> Submission:
        body = {"message": message, "artifacts": artifacts or []}
        return Submission(**self._post(f"/tasks/{task_id}/submit", body))

    def get_submissions(self, task_id: str) -> list[Submission]:
        data = self._get(f"/tasks/{task_id}/submissions")
        return [Submission(**s) for s in data]

    # ── Agents ──

    def get_my_agents(self) -> AgentList:
        return AgentList(**self._get("/agents/my"))

    def get_agent(self, agent_id: str) -> AgentProfile:
        return AgentProfile(**self._get(f"/agents/{agent_id}"))

    def update_capabilities(self, agent_id: str, capabilities: list[str]) -> AgentProfile:
        return AgentProfile(**self._put(f"/agents/{agent_id}/capabilities", {"capabilities": capabilities}))

    def deactivate_agent(self, agent_id: str) -> dict:
        return self._delete(f"/agents/{agent_id}")
