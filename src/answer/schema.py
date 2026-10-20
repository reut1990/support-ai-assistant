"""What the AI must return when it drafts a reply. The API enforces this shape."""

from pydantic import BaseModel, Field


class DraftReply(BaseModel):
    answered: bool = Field(description="True only if the articles contain what is needed to help with the main question.")
    reply: str = Field(description="The reply to the merchant, ready for an agent to review and send.")
    cited_articles: list[str] = Field(description="IDs of the articles the reply is based on, such as KB-201. Empty if not answered.")
    missing: str = Field(description="A private note for the agent, never shown to the merchant: what information is "
                                     "missing, or what the agent should check before sending. Empty if nothing.")
