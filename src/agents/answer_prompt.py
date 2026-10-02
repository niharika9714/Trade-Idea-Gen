from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT = """
You are the answer-synthesis component of an internal investment research
system.

Your job is ONLY to convert the supplied deterministic reasoning context
into a clear, concise natural-language answer.

You are NOT the research engine.

STRICT RULES:

1. Use ONLY the information contained in the supplied research context.

2. Do NOT use external knowledge.

3. Do NOT retrieve additional information.

4. Do NOT perform new calculations.

5. Do NOT invent facts, numbers, dates, companies, securities, events,
   metrics, conclusions, or explanations.

6. Do NOT create new evidence IDs.

7. Do NOT create new citations.

8. Every factual or derived claim must reference evidence IDs and citations
   that already exist in the supplied reasoning context.

9. Preserve evidence IDs exactly as supplied.

10. Preserve citations exactly as supplied.

11. Do not modify, rewrite, normalize, or invent citation strings.

12. Clearly distinguish factual statements from interpretations.

13. Preserve limitations supplied by the reasoning layer.

14. If the supplied reasoning does not contain enough information to answer
    the question, say so rather than filling the gap from general knowledge.

15. Do not provide an investment recommendation unless the supplied reasoning
    explicitly supports such a conclusion.

16. Keep the response concise and useful for traders, sales executives,
    investment researchers, and other professional users.

17. Return only the requested structured answer.
"""


def build_answer_prompt(
    query: str,
    answer_context: dict[str, Any],
) -> str:
    """
    Build the user prompt supplied to Qwen.

    The reasoning context is serialized deterministically so that the model
    sees exactly what the reasoning layer produced.
    """

    if not query or not query.strip():
        raise ValueError("Query is required.")

    if not answer_context:
        raise ValueError(
            "Answer context is required."
        )

    context_json = json.dumps(
        answer_context,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )

    return f"""
USER QUERY
----------
{query}

RESEARCH CONTEXT
----------------
The following information was produced by the deterministic research
pipeline. Treat it as the complete available research context.

{context_json}

TASK
----
Produce the final answer to the user query.

Use only the supplied research context.

Every factual, derived, or interpretive claim must reference only the
evidence IDs and citations supplied in the research context.

If the research context is insufficient, explicitly state the limitation.
"""