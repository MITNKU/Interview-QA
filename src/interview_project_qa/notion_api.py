from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from .config import settings
from .models import NotionPageRef


class NotionAPIError(RuntimeError):
    pass


@dataclass(slots=True)
class NotionAPIClient:
    token: str
    version: str = settings.notion_version
    timeout_seconds: int = 60

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": self.version,
        }

    def create_markdown_page(self, *, parent_page_id: str, markdown: str, title: str) -> NotionPageRef:
        body: dict[str, Any] = {
            "parent": {"page_id": parent_page_id},
            "properties": {
                "title": {
                    "title": [
                        {"type": "text", "text": {"content": title}}
                    ]
                }
            },
            "markdown": markdown,
        }
        resp = requests.post(
            "https://api.notion.com/v1/pages",
            headers=self.headers,
            json=body,
            timeout=self.timeout_seconds,
        )
        if not resp.ok:
            raise NotionAPIError(f"Create page failed: {resp.status_code} {resp.text}")
        payload = resp.json()
        return NotionPageRef(title=title, mode="api", page_id=payload.get("id"), url=payload.get("url"))

    def replace_markdown_page(self, *, page_id: str, markdown: str, title: str) -> NotionPageRef:
        update_resp = requests.patch(
            f"https://api.notion.com/v1/pages/{page_id}/markdown",
            headers=self.headers,
            json={"type": "replace_content", "replace_content": {"new_str": markdown}},
            timeout=self.timeout_seconds,
        )
        if not update_resp.ok:
            raise NotionAPIError(f"Replace markdown failed: {update_resp.status_code} {update_resp.text}")
        meta_resp = requests.get(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=self.headers,
            timeout=self.timeout_seconds,
        )
        if not meta_resp.ok:
            raise NotionAPIError(f"Retrieve page failed: {meta_resp.status_code} {meta_resp.text}")
        payload = meta_resp.json()
        return NotionPageRef(title=title, mode="api", page_id=page_id, url=payload.get("url"))
