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
