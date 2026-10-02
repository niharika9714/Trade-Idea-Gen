from __future__ import annotations

import json
import sys
from typing import Any

from src.agents.agent_orchestrator import AgentOrchestrator
from src.analysis.answer_engine import (
    render_answer,
)

# ============================================================
# Console formatting helpers
# ============================================================

WIDTH = 72


def print_header(title: str) -> None:
    print()
    print("=" * WIDTH)
    print(title.center(WIDTH))
    print("=" * WIDTH)


def print_section(title: str) -> None:
    print()
    print("-" * WIDTH)
    print(title)
    print("-" * WIDTH)


def print_value(label: str, value: Any) -> None:
    print(f"{label:<18}: {value}")


def print_json(data: Any) -> None:
    print(
        json.dumps(
            data,
            indent=2,
            default=str,
            ensure_ascii=False,
        )
    )


def safe_to_dict(value: Any) -> Any:
    """
    Convert project contract objects into dictionaries where possible.
    """
    if value is None:
        return None

    if hasattr(value, "to_dict"):
        try:
            return value.to_dict()
        except Exception:
            pass

    if isinstance(value, list):
        return [safe_to_dict(item) for item in value]

    if isinstance(value, dict):
        return {
            key: safe_to_dict(item)
            for key, item in value.items()
        }

    return value


# ============================================================
# Query Understanding
# ============================================================

def display_query_understanding(state) -> None:
    intent = state.query_intent

    if intent is None:
        return

    print_section("QUERY UNDERSTANDING")

    print_value(
        "Tickers",
        ", ".join(intent.tickers) if intent.tickers else "None",
    )

    print_value(
        "Intents",
        ", ".join(intent.intents) if intent.intents else "None",
    )

    print_value(
        "Metrics",
        ", ".join(intent.metrics) if intent.metrics else "None",
    )

    print_value(
        "Operations",
        ", ".join(intent.operations) if intent.operations else "None",
    )

    print_value(
        "Events",
        ", ".join(intent.event_ids) if intent.event_ids else "None",
    )

    print_value(
        "Sources",
        ", ".join(intent.requested_sources)
        if intent.requested_sources
        else "None",
    )
    print_value(
        "Date range",
        getattr(intent, "date_range", None)
        or "None",
    )

    print_value(
        "Confidence",
        getattr(intent, "confidence", None),
    )


# ============================================================
# Retrieval plan
# ============================================================

def display_retrieval_plan(state) -> None:
    plan = state.retrieval_plan

    if plan is None:
        return

    print_section("RETRIEVAL PLAN")

    print_value(
        "Tools",
        ", ".join(plan.tools) if plan.tools else "None",
    )

    print_value(
        "Tickers",
        ", ".join(plan.tickers) if plan.tickers else "None",
    )

    print_value(
        "Event",
        plan.event_id or "None",
    )
    print_value(
        "Date range",
        getattr(plan, "date_range", None)
        or "None",
    )

    if getattr(plan, "rationale", None):
        print_value("Rationale", "")
        for key, value in plan.rationale.items():
            print(f"  {key}: {value}")


# ============================================================
# Agent decision
# ============================================================

def display_agent_decision(state) -> None:
    decision = state.agent_decision

    if decision is None:
        return

    print_section("AGENT DECISION")

    print_value(
        "Action",
        decision.action,
    )

    print_value(
        "Tools",
        ", ".join(decision.selected_tools)
        if decision.selected_tools
        else "None",
    )

    print_value(
        "Tickers",
        ", ".join(decision.tickers)
        if decision.tickers
        else "None",
    )

    print_value(
        "Confidence",
        decision.confidence,
    )

    print_value(
        "Reasoning",
        decision.reasoning or "None",
    )


# ============================================================
# Tool execution
# ============================================================

def display_tool_results(tool_results) -> None:
    print_section("TOOL EXECUTION")

    if not tool_results:
        print("No tool results.")
        return

    for index, result in enumerate(tool_results, start=1):
        print()
        print(f"[Tool {index}]")

        # AgenticExecutor currently returns dictionaries.
        # Support dictionaries as the primary format and
        # object-style results for compatibility.

        if isinstance(result, dict):
            call_id = result.get("call_id")
            tool_name = result.get("tool_name")
            success = result.get("success")
            error = result.get("error")
            evidence_ids = result.get("evidence_ids", [])
            citations = result.get("citations", [])

        else:
            call_id = getattr(result, "call_id", None)
            tool_name = getattr(result, "tool_name", None)
            success = getattr(result, "success", None)
            error = getattr(result, "error", None)
            evidence_ids = getattr(result, "evidence_ids", [])
            citations = getattr(result, "citations", [])

        print_value("Call ID", call_id)
        print_value("Tool", tool_name)
        print_value("Success", success)

        if error:
            print_value("Error", error)

        print_value(
            "Evidence",
            len(evidence_ids),
        )

        print_value(
            "Citations",
            len(citations),
        )

# ============================================================
# Evidence
# ============================================================

def display_evidence(state) -> None:
    bundle = state.evidence_bundle

    if bundle is None:
        return

    evidence_items = list(bundle)

    print_section("EVIDENCE")

    print_value(
        "Total evidence",
        len(evidence_items),
    )

    if not evidence_items:
        print("No evidence retrieved.")
        return

    # Show a compact evidence manifest.
    for index, evidence in enumerate(evidence_items, start=1):

        print()
        print(
            f"[{index}] "
            f"{getattr(evidence, 'source_type', 'unknown')}"
        )

        print_value(
            "Source",
            getattr(evidence, "source", None),
        )

        print_value(
            "Locator",
            getattr(evidence, "locator", None),
        )

        print_value(
            "Ticker",
            getattr(evidence, "ticker", None),
        )

        print_value(
            "Event",
            getattr(evidence, "event_id", None),
        )

        print_value(
            "Evidence ID",
            getattr(evidence, "evidence_id", None),
        )

        print_value(
            "Citation",
            getattr(evidence, "citation", None),
        )


# ============================================================
# Skills
# ============================================================


def display_skill_results(skill_results) -> None:
    print_section("INVESTMENT RESEARCH SKILLS")

    # The console may receive either:
    #   1. AgentState
    #   2. list[SkillExecutionResult]
    #   3. list[dict]
    #
    # Normalize all three cases here.

    if hasattr(skill_results, "skill_results"):
        skill_results = skill_results.skill_results

    if skill_results is None:
        print("No skills executed.")
        return

    if not isinstance(skill_results, (list, tuple)):
        skill_results = [skill_results]

    if not skill_results:
        print("No skills executed.")
        return

    for index, result in enumerate(skill_results, start=1):
        print()
        print(f"[Skill {index}]")

        if isinstance(result, dict):
            skill_name = result.get("skill_name")
            status = result.get("status")
            evidence_ids = result.get("evidence_ids", [])
            citations = result.get("citations", [])
            result_data = result.get("result")
            error = result.get("error")

        else:
            skill_name = getattr(result, "skill_name", None)
            status = getattr(result, "status", None)
            evidence_ids = getattr(result, "evidence_ids", [])
            citations = getattr(result, "citations", [])
            result_data = getattr(result, "result", None)
            error = getattr(result, "error", None)

        print_value("Skill", skill_name)
        print_value("Status", status)

        if error:
            print_value("Error", error)

        print_value("Evidence", len(evidence_ids))
        print_value("Citations", len(citations))

        # SkillExecutionResult.result contains the underlying
        # SkillResult in the current architecture.
        if result_data is not None:
            if isinstance(result_data, dict):
                facts = result_data.get("facts", [])
                derived_metrics = result_data.get("derived_metrics", [])
                conclusions = result_data.get("conclusions", [])
                limitations = result_data.get("limitations", [])

                print_value("Facts", len(facts))
                print_value(
                    "Derived metrics",
                    len(derived_metrics),
                )
                print_value(
                    "Conclusions",
                    len(conclusions),
                )
                print_value(
                    "Limitations",
                    len(limitations),
                )

            else:
                facts = getattr(result_data, "facts", [])
                derived_metrics = getattr(
                    result_data,
                    "derived_metrics",
                    [],
                )
                conclusions = getattr(
                    result_data,
                    "conclusions",
                    [],
                )
                limitations = getattr(
                    result_data,
                    "limitations",
                    [],
                )

                print_value("Facts", len(facts))
                print_value(
                    "Derived metrics",
                    len(derived_metrics),
                )
                print_value(
                    "Conclusions",
                    len(conclusions),
                )
                print_value(
                    "Limitations",
                    len(limitations),
                )
# ============================================================
# Analysis
# ============================================================

def display_analysis(state) -> None:
    analysis = state.analysis_result

    if analysis is None:
        return

    print_section("ANALYSIS")

    facts = getattr(analysis, "facts", [])
    derived = getattr(analysis, "derived_metrics", [])

    print_value("Facts", len(facts))
    print_value("Derived metrics", len(derived))
    print_value(
        "Entities",
        ", ".join(analysis.entities)
        if getattr(analysis, "entities", None)
        else "None",
    )

    if facts:
        print()
        print("Facts:")

        for fact in facts:
            print(
                f"  - {fact.entity} | "
                f"{fact.metric} = "
                f"{fact.value}"
                f"{(' ' + fact.unit) if fact.unit else ''}"
                f"{(' | ' + fact.date) if fact.date else ''}"
            )

    if derived:
        print()
        print("Derived metrics:")

        for metric in derived:
            print(
                f"  - {metric.entity} | "
                f"{metric.metric} = "
                f"{metric.value}"
                f"{(' ' + metric.unit) if metric.unit else ''}"
            )


# ============================================================
# State summary
# ============================================================

def display_state_summary(state) -> None:
    print_section("PIPELINE SUMMARY")

    print_value(
        "Messages",
        len(state.messages),
    )

    print_value(
        "Evidence",
        len(list(state.evidence_bundle))
        if state.evidence_bundle is not None
        else 0,
    )

    print_value(
        "Skills",
        len(state.skill_results),
    )

    print_value(
        "Metadata keys",
        ", ".join(state.metadata.keys())
        if state.metadata
        else "None",
    )

# ============================================================
# Display Reasoning
# ============================================================

def display_reasoning(state) -> None:
    reasoning = state.reasoning_result

    if reasoning is None:
        return

    print_section("REASONING")

    print_value(
        "Reasoning steps",
        len(reasoning.reasoning_steps),
    )

    print_value(
        "Supporting evidence",
        len(reasoning.supporting_evidence_ids),
    )

    print_value(
        "Supporting citations",
        len(reasoning.supporting_citations),
    )

    for index, step in enumerate(
        reasoning.reasoning_steps,
        start=1,
    ):
        print()
        print(
            f"[Step {index}]"
        )

        print_value(
            "Description",
            step.description,
        )

        print_value(
            "Conclusion",
            step.conclusion,
        )

        print_value(
            "Evidence IDs",
            ", ".join(
                step.input_evidence_ids
            )
            if step.input_evidence_ids
            else "None",
        )

        print_value(
            "Citations",
            ", ".join(
                step.input_citations
            )
            if step.input_citations
            else "None",
        )

# ============================================================
# Display Answer
# ============================================================

def display_answer(state) -> None:
    answer = state.answer_result

    if answer is None:
        return

    print_section("FINAL ANSWER")

    print(
        render_answer(answer)
    )


# ============================================================
# Main query execution
# ============================================================

def run_query(
    orchestrator: AgentOrchestrator,
    query: str,
) -> None:

    print_header("PROCESSING QUERY")
    print(f"User: {query}")

    try:
        # ----------------------------------------------------
        # Execute the canonical end-to-end pipeline
        # ----------------------------------------------------

        state = orchestrator.run(query)

        # ----------------------------------------------------
        # Final user-facing answer
        # ----------------------------------------------------

        print()
        print("Assistant:")
        print(render_answer(state.answer_result))

    except Exception as exc:

        print_header("QUERY FAILED")

        print(f"Error type: {type(exc).__name__}")
        print(f"Error      : {exc}")

        print()
        print("The exception occurred while processing the query.")

        # Keep the chatbot alive for another query.
        return

# ============================================================
# Interactive console
# ============================================================

def main() -> None:

    print_header(
        "AI INVESTMENT RESEARCH ASSISTANT"
    )

    print("Data sources:")
    print("  ✓ Documents")
    print("  ✓ Market SQL")
    print("  ✓ News")
    print("  ✓ Internal APIs")
    print("  ✓ Retrieval tools")
    print("  ✓ Investment research skills")
    print("  ✓ Agentic orchestration")

    print()
    print("Commands:")
    print("  exit       - quit")
    print("  quit       - quit")
    print("  clear      - clear the console")
    print("  debug      - show additional state information")
    print()

    orchestrator = AgentOrchestrator()

    while True:

        try:
            query = input("You: ").strip()

        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not query:
            continue

        command = query.lower()

        if command in {"exit", "quit"}:
            print("Goodbye.")
            break

        if command == "clear":

            # Windows
            if sys.platform.startswith("win"):
                import os
                os.system("cls")

            # Linux/macOS
            else:
                import os
                os.system("clear")

            continue

        if command == "debug":
            print(
                "\nDebug mode is currently represented by "
                "the full pipeline output shown for every query."
            )
            continue

        run_query(
            orchestrator=orchestrator,
            query=query,
        )


if __name__ == "__main__":
    main()