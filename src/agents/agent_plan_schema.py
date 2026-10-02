from __future__ import annotations

from pydantic import BaseModel, Field


class AgentPlan(BaseModel):
    """Structured plan produced by the LLM planning agent.

    The planner decides what needs to be retrieved, but it does not
    execute tools and it does not answer the user's question.
    """

    query: str = Field(
        description="Original user query. Preserve the user's wording."
    )

    entities: list[str] = Field(
        default_factory=list,
        description=(
            "People, companies, financial instruments, products, events, "
            "documents, concepts, or other entities mentioned or implied "
            "by the query. Do not restrict entities to a predefined list."
        ),
    )

    intent: str = Field(
        description=(
            "Natural-language description of what the user is trying to "
            "accomplish."
        )
    )

    search_queries: list[str] = Field(
        default_factory=list,
        description=(
            "Text queries that retrieval tools should search against "
            "document content, news, or other textual sources."
        ),
    )

    tools: list[str] = Field(
        default_factory=list,
        description=(
            "Names of registered retrieval tools required to answer the "
            "query."
        ),
    )

    skills: list[str] = Field(
        default_factory=list,
        description=(
            "Investment research skills required after retrieval, if any."
        ),
    )

    tickers: list[str] = Field(
        default_factory=list,
        description=(
            "Known financial tickers relevant to the query, if any."
        ),
    )

    latest: bool | None = Field(
        default=None,
        description=(
            "Temporal recency flag. Set True when the user explicitly asks "
            "for the latest, current, today's, or most recent available "
            "observation. Set False when the query clearly refers to a "
            "historical period. Use None only when no recency semantics "
            "are expressed."
        ),
    )
    
    temporal_expression: str | None = Field(
        default=None,
        description=(
            "Natural-language temporal expression from the user's query, "
            "such as 'January 2024', 'Q1 2025', 'last month', "
            "'between March and June 2024', or 'since 2023'. "
            "Preserve the user's temporal meaning. Do not calculate "
            "calendar boundaries here."
        ),
    )

    requires_calculation: bool = Field(
        default=False,
        description=(
            "True when a deterministic calculation is required before "
            "answering."
        ),
    )

    analytical_question: str | None = Field(
        default=None,
        description=(
            "Explicit analytical question or calculation that should be "
            "performed by a deterministic analytical tool."
        ),
    )