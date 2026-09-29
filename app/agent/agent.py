from collections.abc import AsyncIterator

from app.agent.prompts import SYSTEM_PROMPT
from app.infrastructure.llm import LLM, AgentReply


class Agent:
    def __init__(self) -> None:
        self.llm = LLM()

    async def respond(
        self,
        conversation: list[dict[str, str]],
    ) -> AgentReply:
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *conversation,
        ]

        return await self.llm.generate(
            messages=messages
        )

    async def stream(
        self,
        conversation: list[dict[str, str]],
        language_code: str | None,
    ) -> AsyncIterator[str]:
        language_instruction = (
            f"The detected language code is {language_code}. Treat it as a hint; "
            "explicit language requests in the conversation take precedence "
            "and remain in effect until changed."
            if language_code
            else "Reply in the same language as the user's latest message, "
            "honoring any explicit language preference from the conversation."
        )
        messages = [
            {
                "role": "system",
                "content": f"{SYSTEM_PROMPT}\n\n{language_instruction}",
            },
            *conversation,
        ]

        async for chunk in self.llm.stream(messages):
            yield chunk
