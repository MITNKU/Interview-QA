from __future__ import annotations

import json
from dataclasses import dataclass

from openai import OpenAI

from .config import settings
from .models import NotionPageRef


class NotionMCPError(RuntimeError):
    pass


@dataclass(slots=True)
class NotionMCPClient:
    openai_api_key: str
    notion_mcp_access_token: str
    notion_parent_page_id: str
    server_url: str = settings.notion_mcp_server_url

    def _client(self) -> OpenAI:
        return OpenAI(api_key=self.openai_api_key)

    def create_markdown_page(self, *, title: str, markdown: str) -> NotionPageRef:
        if not self.openai_api_key:
            raise NotionMCPError("OPENAI_API_KEY is required for Notion MCP publishing.")
        if not self.notion_mcp_access_token:
            raise NotionMCPError("NOTION_MCP_ACCESS_TOKEN is required for Notion MCP publishing.")
        if not self.notion_parent_page_id:
            raise NotionMCPError("NOTION_PARENT_PAGE_ID is required for Notion MCP publishing.")

        prompt = (
            "Use the Notion MCP tools to create exactly one child page under the specified parent page. "
            "Set the page title to the provided title and write the provided markdown content into the new page. "
            "Return a JSON object with keys title, page_id, url and success. Do not create any extra pages."
        )
        user_payload = {
            "parent_page_id": self.notion_parent_page_id,
            "title": title,
            "markdown": markdown,
        }
        resp = self._client().responses.create(
            model="gpt-5.4",
            tools=[
                {
                    "type": "mcp",
                    "server_label": "notion",
                    "server_url": self.server_url,
                    "authorization": self.notion_mcp_access_token,
                    "allowed_tools": ["notion-create-pages", "notion-update-page", "fetch", "search"],
                    "require_approval": "never",
                }
            ],
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "notion_mcp_write_result",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "page_id": {"type": "string"},
                            "url": {"type": "string"},
                            "success": {"type": "boolean"},
                        },
                        "required": ["title", "page_id", "url", "success"],
                        "additionalProperties": False,
                    },
                }
            },
        )
        payload = json.loads(resp.output_text)
        if not payload.get("success"):
            raise NotionMCPError(f"Notion MCP create failed: {payload}")
        return NotionPageRef(title=payload["title"], mode="mcp", page_id=payload.get("page_id"), url=payload.get("url"))
