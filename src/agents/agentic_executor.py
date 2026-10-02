from src.agents.agent_state import AgentState
from src.agents.llm_adapter import LLMAdapter
from src.agents.tool_executor import (
    AgentToolExecutor,
)
from src.agents.tool_call_contract import (
    ToolCall,
)
from src.provenance.evidence import EvidenceBundle


class AgenticExecutor:
    """
    Step 3B agentic loop.

    Flow:

        AgentDecision
             ↓
        LLM ToolCall
             ↓
        Validate
             ↓
        Execute registered tool
             ↓
        Collect result
             ↓
        Ask LLM for next tool call
             ↓
        Repeat until no calls remain
    """

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        tool_executor: AgentToolExecutor | None = None,
        max_iterations: int = 5,
    ):

        if not isinstance(
            llm_adapter,
            LLMAdapter,
        ):
            raise TypeError(
                "llm_adapter must implement "
                "LLMAdapter"
            )

        if max_iterations < 1:
            raise ValueError(
                "max_iterations must be >= 1"
            )

        self.llm = llm_adapter

        self.tool_executor = (
            tool_executor
            or AgentToolExecutor()
        )

        self.max_iterations = (
            max_iterations
        )

    def execute(
        self,
        state: AgentState,
    ):
        if state.evidence_bundle is None:
            state.evidence_bundle = EvidenceBundle()

        if state.agent_decision is None:
            raise ValueError(
                "Agent decision must exist "
                "before tool execution."
            )

        previous_results = []

        all_evidence_ids = []
        all_citations = []

        for iteration in range(
            1,
            self.max_iterations + 1,
        ):

            tool_calls = (
                self.llm.generate_tool_calls(
                    query=state.query,
                    agent_decision=(
                        state.agent_decision
                    ),
                    previous_tool_results=(
                        previous_results
                    ),
                )
            )

            if not tool_calls:
                break

            for tool_call in tool_calls:

                if not isinstance(
                    tool_call,
                    ToolCall,
                ):
                    raise TypeError(
                        "LLM returned an invalid "
                        "ToolCall object."
                    )

                execution_result = (
                    self.tool_executor.execute(
                        tool_call
                    )
                )
                if execution_result.success:
                    result = execution_result.result
                    if isinstance(
                        result,
                        EvidenceBundle,
                    ):
                        state.evidence_bundle.merge(
                            result
                        )

                result_dict = (
                    execution_result.to_dict()
                )

                previous_results.append(
                    result_dict
                )

                all_evidence_ids.extend(
                    execution_result.evidence_ids
                )

                all_citations.extend(
                    execution_result.citations
                )

                # Preserve the tool result in the
                # agent conversation state.
                state.add_message(
                    role="tool",
                    content=str(
                        result_dict
                    ),
                )

        state.metadata[
            "tool_execution_iterations"
        ] = iteration

        state.metadata[
            "tool_execution_results"
        ] = previous_results

        state.metadata[
            "tool_execution_evidence_ids"
        ] = list(
            dict.fromkeys(
                all_evidence_ids
            )
        )

        state.metadata[
            "tool_execution_citations"
        ] = list(
            dict.fromkeys(
                all_citations
            )
        )

        return previous_results