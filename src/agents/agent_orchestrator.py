from src.agents.agent_state import AgentState
from src.agents.agent_contract import AgentResponse
from src.agents.llm_adapter import LLMAdapter, MockLLMAdapter
from src.agents.agent_planner import (
    OllamaAgentPlanner,
)
from src.agents.semantic_plan_adapter import (
    agent_plan_to_query_intent,
)

from src.data_access.retrieval_policy import (
    build_retrieval_plan_from_intent,
)

from src.tools.retrieval_tools import (
    get_retrieval_tool_definitions,
)
from src.data_access.retrieval_executor import execute_retrieval_plan

from src.agents.skill_agent_executor import (
    SkillAgentExecutor,
)

from src.analysis.evidence_analysis import AnalysisResult

from src.analysis.reasoning_engine import (
    build_reasoning,
)

from src.analysis.answer_engine import (
    validate_answer,
)

from src.agents.answer_llm_adapter import (
    AnswerLLMAdapter,
    MockAnswerLLMAdapter,
    OllamaAnswerLLMAdapter,
)

from src.analysis.answer_context import (
    build_answer_context,
)

class AgentOrchestrator:
    """
    Step 3A agent orchestration shell.

    Current responsibility:

        query
          ↓
        understand
          ↓
        LLM decision
          ↓
        validate decision

    Tool execution is intentionally NOT performed here yet.

    That becomes Step 3B.
    """
    def __init__(
        self,
        llm: LLMAdapter | None = None,
        llm_adapter: LLMAdapter | None = None,
        answer_llm: AnswerLLMAdapter | None = None,
    ):
        if llm is not None and llm_adapter is not None:
            if llm is not llm_adapter:
                raise ValueError(
                    "Provide either llm or llm_adapter, "
                    "not two different adapters."
                )
    
        adapter = (
            llm
            if llm is not None
            else llm_adapter
        )
    
        if adapter is None:
            adapter = MockLLMAdapter()
    
        if not isinstance(adapter, LLMAdapter):
            raise TypeError(
                "llm must implement LLMAdapter"
            )
    
        self.llm = adapter
    
        if answer_llm is None:
            answer_llm = OllamaAnswerLLMAdapter()
    
        if not isinstance(
            answer_llm,
            AnswerLLMAdapter,
        ):
            raise TypeError(
                "answer_llm must implement AnswerLLMAdapter"
            )
    
        self.answer_llm = answer_llm
    
        self.skill_executor = SkillAgentExecutor()
        self.semantic_planner = OllamaAgentPlanner()



    
    def create_state(
        self,
        query: str,
    ) -> AgentState:

        if not isinstance(query, str):
            raise TypeError(
                "query must be a string"
            )

        if not query.strip():
            raise ValueError(
                "query must not be empty"
            )

        return AgentState(
            query=query.strip()
        )

    def understand(
        self,
        state: AgentState,
    ):
        """
        Use Qwen3:8b as the semantic authority for the user query,
        then convert its AgentPlan into the canonical QueryIntent
        consumed by deterministic retrieval and analytical layers.

        Semantic meaning belongs to Qwen.
        Temporal grounding, retrieval, calculations, provenance,
        reasoning validation, and answer validation remain deterministic.
        """

        tools = self.get_tool_definitions()

        agent_plan = self.semantic_planner.plan(
            query=state.query,
            available_tools=tools,
        )

        query_intent = agent_plan_to_query_intent(
            agent_plan
        )

        state.query_intent = query_intent

        # Preserve the semantic plan for observability without
        # requiring an AgentState schema change.
        state.metadata["semantic_agent_plan"] = (
            agent_plan.model_dump()
        )

        state.add_message(
            role="user",
            content=state.query,
        )

        state.add_message(
            role="assistant",
            content=agent_plan.model_dump(),
        )

        return query_intent


    def build_plan(
        self,
        state: AgentState,
    ):

        if state.query_intent is None:
            raise ValueError(
                "Query intent must be created first."
            )

        plan = build_retrieval_plan_from_intent(
            state.query_intent
        )

        state.retrieval_plan = plan

        return plan

    def get_tool_definitions(self):

        return get_retrieval_tool_definitions()

    def ask_llm(
        self,
        state: AgentState,
    ):

        if state.query_intent is None:
            raise ValueError(
                "Query intent must be created before "
                "calling the LLM."
            )

        tools = self.get_tool_definitions()

        decision = self.llm.generate_agent_decision(
            query=state.query,
            query_intent=state.query_intent,
            available_tools=tools,
        )
        

        state.agent_decision = decision
        if state.query_intent.date_range:
            state.agent_decision.parameters["date_range"] = (
                state.query_intent.date_range
            )

        state.add_message(
            role="assistant",
            content=(
                "Generated structured agent decision."
            ),
        )

        return state.agent_decision
    
    def select_skills(self, state):

        if state.query_intent is None:
            raise ValueError(
                "Query intent is required "
                "before skill selection."
            )

        decision = (
            self.skill_executor.select_skills(
                state.query_intent
            )
        )

        state.skill_decision = decision

        state.metadata[
            "selected_skills"
        ] = decision.skill_names

        state.metadata[
            "skill_selection_reasoning"
        ] = decision.reasoning

        state.add_message(
            role="skill_selector",
            content=decision.to_dict(),
        )

        return decision
    
    def _combine_skill_analysis(self, results):
        from src.analysis.evidence_analysis import AnalysisResult
    
        combined = AnalysisResult()
    
        for execution_result in results:
            skill_result = getattr(execution_result, "result", None)
    
            if skill_result is None:
                continue
            
            # ---------------------------------------------------------
            # 1. Some skills populate SkillResult.analysis_result
            # ---------------------------------------------------------
            analysis = getattr(skill_result, "analysis_result", None)
    
            if analysis is not None:
                for fact in getattr(analysis, "facts", []):
                    combined.add_fact(fact)
    
                for derived_metric in getattr(
                    analysis,
                    "derived_metrics",
                    []
                ):
                    combined.add_derived_metric(derived_metric)
    
                for entity in getattr(
                    analysis,
                    "entities",
                    []
                ):
                    if entity not in combined.entities:
                        combined.entities.append(entity)
    
                for citation in getattr(
                    analysis,
                    "citations",
                    []
                ):
                    if citation not in combined.citations:
                        combined.citations.append(citation)
    
            # ---------------------------------------------------------
            # 2. Some skills populate SkillResult.facts directly
            # ---------------------------------------------------------
            for fact in getattr(skill_result, "facts", []):
                combined.add_fact(fact)
    
            for derived_metric in getattr(
                skill_result,
                "derived_metrics",
                []
            ):
                combined.add_derived_metric(derived_metric)
    
            # ---------------------------------------------------------
            # 3. Preserve skill-level entities/citations
            # ---------------------------------------------------------
            for entity in getattr(
                skill_result,
                "entities",
                []
            ):
                if entity not in combined.entities:
                    combined.entities.append(entity)
    
            for citation in getattr(
                skill_result,
                "citations",
                []
            ):
                if citation not in combined.citations:
                    combined.citations.append(citation)
    
        return combined


    def execute_skills(self, state):
        if state.evidence_bundle is None:
            raise ValueError(
                "Evidence bundle is required before skill execution."
            )
    
        decision, results = self.skill_executor.execute(
            query=state.query,
            query_intent=state.query_intent,
            evidence_bundle=state.evidence_bundle,
        )
    
        state.skill_decision = decision
        state.skill_results = results
    
        state.metadata["skill_execution_results"] = [
            result.to_dict()
            for result in results
        ]

        state.analysis_result = self._combine_skill_analysis(
            results
        )

        state.metadata["analysis_facts"] = len(
            state.analysis_result.facts
        )

        state.metadata["analysis_derived_metrics"] = len(
            state.analysis_result.derived_metrics
        )
    
        state.metadata["skill_execution_evidence_ids"] = list(
            dict.fromkeys(
                evidence_id
                for result in results
                for evidence_id in result.evidence_ids
            )
        )
    
        state.metadata["skill_execution_citations"] = list(
            dict.fromkeys(
                citation
                for result in results
                for citation in result.citations
            )
        )
    
        for result in results:
            state.add_message(
                role="skill",
                content=result.to_dict(),
            )
    
        return results

    def run_skills(self, state):

        self.select_skills(state)

        return self.execute_skills(state)


    def validate_decision(
        self,
        state: AgentState,
    ):

        if state.agent_decision is None:
            raise ValueError(
                "No agent decision exists."
            )

        available_tools = {
            tool["name"]
            for tool in self.get_tool_definitions()
        }

        for tool_name in (
            state.agent_decision.selected_tools
        ):

            if tool_name not in available_tools:
                raise ValueError(
                    "LLM selected unknown tool: "
                    f"{tool_name}"
                )

        plan_tickers = set()

        if state.retrieval_plan is not None:
            plan_tickers.update(
                getattr(
                    state.retrieval_plan,
                    "tickers",
                    [],
                )
            )

        decision_tickers = set(
            state.agent_decision.tickers
        )

        if (
            plan_tickers
            and decision_tickers
            and not decision_tickers.issubset(
                plan_tickers
            )
        ):
            raise ValueError(
                "LLM selected ticker(s) outside "
                "the query retrieval plan."
            )

        return True


    def run(
        self,
        query: str,
    ):
        """
        Execute the canonical end-to-end research pipeline.
    
        Flow:
            User query
            -> Qwen semantic planning
            -> canonical QueryIntent
            -> deterministic RetrievalPlan
            -> deterministic retrieval
            -> EvidenceBundle
            -> deterministic analytical skills
            -> reasoning
            -> Qwen answer synthesis
            -> deterministic answer validation
        """
    
        # 1. Create state
        state = self.create_state(query)
    
        # 2. Qwen semantic understanding
        self.understand(state)
    
        # 3. Deterministic retrieval planning
        self.build_plan(state)
    
        # 4. Deterministic retrieval execution
        state.evidence_bundle = execute_retrieval_plan(
            state.retrieval_plan
        )
    
        # 5. Deterministic analytical skills
        self.run_skills(state)
    
        # 6. Reasoning + Qwen answer synthesis + validation
        self.generate_answer(state)
    
        return state

    def generate_answer(self, state):
        """
        Execute the post-retrieval reasoning and answer pipeline.

        Flow:

            AnalysisResult
                ↓
            ReasoningResult
                ↓
            AnswerContext
                ↓
            AnswerLLM
                ↓
            AnswerResult
                ↓
            Citation / evidence validation
        """

        # ---------------------------------------------------------
        # 1. Analysis is mandatory
        # ---------------------------------------------------------

        if state.analysis_result is None:
            raise ValueError(
                "AnalysisResult is required before generating an answer."
            )

        # ---------------------------------------------------------
        # 2. Build deterministic reasoning
        # ---------------------------------------------------------

        reasoning_result = build_reasoning(
            query=state.query,
            analysis_result=state.analysis_result,
            query_intent=state.query_intent,
        )

        state.reasoning_result = reasoning_result

        # ---------------------------------------------------------
        # 3. Build controlled context for the answer LLM
        # ---------------------------------------------------------
        #
        # Important:
        #
        # The answer LLM does NOT receive direct access to:
        #
        #   - SQL
        #   - files
        #   - retrieval tools
        #   - databases
        #
        # It receives the already-derived reasoning and provenance.
        #

        answer_context = build_answer_context(
            query=state.query,
            reasoning_result=reasoning_result,
        )

        # ---------------------------------------------------------
        # 4. Generate AnswerResult through answer LLM
        # ---------------------------------------------------------

        answer_result = self.answer_llm.generate_answer(
            query=state.query,
            reasoning_result=reasoning_result,
            answer_context=answer_context,
        )

        # ---------------------------------------------------------
        # 5. Deterministically validate the answer
        # ---------------------------------------------------------
        #
        # The LLM does not get to decide whether its own claims
        # are valid.
        #
        # The existing validation layer checks:
        #
        #   claim → evidence ID
        #   claim → citation
        #   citation → reasoning provenance
        #

        validate_answer(
            answer=answer_result,
            reasoning_result=reasoning_result,
        )

        # ---------------------------------------------------------
        # 6. Store final answer in AgentState
        # ---------------------------------------------------------

        state.answer_result = answer_result

        # ---------------------------------------------------------
        # 7. Store pipeline metadata
        # ---------------------------------------------------------

        state.metadata[
            "reasoning_steps"
        ] = len(
            reasoning_result.reasoning_steps
        )

        state.metadata[
            "answer_llm_adapter"
        ] = (
            self.answer_llm.__class__.__name__
        )

        state.metadata[
            "answer_claims"
        ] = len(
            answer_result.collect_claims()
        )

        state.metadata[
            "answer_citations"
        ] = len(
            answer_result.collect_citations()
        )

        # ---------------------------------------------------------
        # 8. Add assistant message
        # ---------------------------------------------------------

        state.add_message(
            role="assistant",
            content=(
                "Generated citation-validated answer."
            ),
        )

        return answer_result
    