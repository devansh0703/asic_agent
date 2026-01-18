"""LangGraph orchestrator for ASIC design workflow"""

import os
import logging
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import DesignState, DesignStage, AgentType, create_initial_state
from ..config import Config
from ..llm_client import GeminiClient
from ..database.knowledge_base import ASICKnowledgeBase
from ..tools.hardware_tools import HardwareTools
from ..agents import MainAgent, VerificationAgent, HardeningAgent, CaravelAgent

logger = logging.getLogger(__name__)


class ASICOrchestrator:
    """LangGraph-based orchestrator for ASIC design workflow"""
    
    def __init__(self, config: Config):
        """Initialize orchestrator with configuration
        
        Args:
            config: ASIC-Agent configuration
        """
        self.config = config
        
        # Initialize components
        self.llm = GeminiClient(
            api_key=config.gemini_api_key,
            model_name=config.gemini_model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            provider=config.llm_provider,
            rate_limit_enabled=config.rate_limit_enabled,
            rate_limit_delay=config.rate_limit_delay_seconds,
        )
        
        self.kb = ASICKnowledgeBase(
            persist_directory=config.chroma_persist_directory,
            collection_name=config.chroma_collection_name,
        )
        
        self.tools = HardwareTools(
            verilator_path=config.verilator_path,
            iverilog_path=config.iverilog_path,
            vvp_path=config.vvp_path,
            yosys_path=config.yosys_path,
        )
        
        # Initialize agents
        self.main_agent = MainAgent(
            llm_client=self.llm,
            knowledge_base=self.kb,
            hardware_tools=self.tools,
            workspace_dir=config.workspace_dir,
        )
        
        self.verification_agent = VerificationAgent(
            llm_client=self.llm,
            knowledge_base=self.kb,
            hardware_tools=self.tools,
            workspace_dir=config.workspace_dir,
        )
        
        self.hardening_agent = HardeningAgent(
            llm_client=self.llm,
            knowledge_base=self.kb,
            workspace_dir=config.workspace_dir,
        )
        
        self.caravel_agent = CaravelAgent(
            llm_client=self.llm,
            knowledge_base=self.kb,
            workspace_dir=config.workspace_dir,
        )
        
        # Build workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow for ASIC design
        
        Returns:
            StateGraph workflow
        """
        # Create graph
        workflow = StateGraph(DesignState)
        
        # Add nodes
        workflow.add_node("rtl_generation", self._rtl_generation_node)
        workflow.add_node("linting", self._linting_node)
        workflow.add_node("verification", self._verification_node)
        workflow.add_node("hardening", self._hardening_node)
        workflow.add_node("integration", self._integration_node)
        
        # Set entry point
        workflow.set_entry_point("rtl_generation")
        
        # Add edges with conditional routing
        workflow.add_conditional_edges(
            "rtl_generation",
            self._route_after_rtl,
            {
                "linting": "linting",
                "failed": END,
            }
        )
        
        workflow.add_conditional_edges(
            "linting",
            self._route_after_linting,
            {
                "verification": "verification",
                "rtl_generation": "rtl_generation",  # Fix and retry
                "failed": END,
            }
        )
        
        workflow.add_conditional_edges(
            "verification",
            self._route_after_verification,
            {
                "hardening": "hardening",
                "verification": "verification",  # Retry
                "rtl_generation": "rtl_generation",  # Fix RTL
                "failed": END,
            }
        )
        
        workflow.add_conditional_edges(
            "hardening",
            self._route_after_hardening,
            {
                "integration": "integration",
                "hardening": "hardening",  # Retry with new config
                "failed": END,
            }
        )
        
        workflow.add_edge("integration", END)
        
        return workflow.compile()
    
    def _rtl_generation_node(self, state: DesignState) -> Dict:
        """RTL generation node
        
        Args:
            state: Current state
            
        Returns:
            Updated state as dict
        """
        logger.info("=== RTL Generation Stage ===")
        
        # Generate RTL
        success, rtl_code, errors = self.main_agent.generate_rtl(
            specification=state.specification,
            design_name=state.design_name,
        )
        
        updates = {
            "current_stage": DesignStage.RTL_GENERATION.value,
            "current_agent": AgentType.MAIN.value,
        }
        
        if success:
            updates["rtl_code"] = rtl_code
            updates["rtl_files"] = list(rtl_code.keys())
            logger.info(f"RTL generation successful: {list(rtl_code.keys())}")
        else:
            updates["errors"] = state.errors + errors
            updates["current_stage"] = DesignStage.FAILED.value
            logger.error(f"RTL generation failed: {errors}")
        
        return updates
    
    def _linting_node(self, state: DesignState) -> Dict:
        """Linting node
        
        Args:
            state: Current state
            
        Returns:
            Updated state as dict
        """
        logger.info("=== Linting Stage ===")
        
        # Lint RTL files
        passed, errors = self.main_agent.lint_rtl(state.rtl_files)
        
        updates = {
            "current_stage": DesignStage.LINTING.value,
            "linting_passed": passed,
            "linting_errors": errors,
        }
        
        if passed:
            logger.info("Linting passed")
        else:
            logger.warning(f"Linting failed with {len(errors)} errors")
            
            # Try to fix errors
            if state.iteration_count < state.max_iterations:
                fixed_rtl_code = dict(state.rtl_code)
                for filename, code in state.rtl_code.items():
                    success, fixed_code = self.main_agent.fix_rtl_errors(
                        filename=filename,
                        original_code=code,
                        errors=errors,
                    )
                    if success:
                        fixed_rtl_code[filename] = fixed_code
                
                updates["rtl_code"] = fixed_rtl_code
                updates["iteration_count"] = state.iteration_count + 1
        
        return updates
    
    def _verification_node(self, state: DesignState) -> Dict:
        """Verification node
        
        Args:
            state: Current state
            
        Returns:
            Updated state as dict
        """
        logger.info("=== Verification Stage ===")
        
        updates = {
            "current_stage": DesignStage.VERIFICATION.value,
            "current_agent": AgentType.VERIFICATION.value,
        }
        
        # Generate testbench if needed
        if not state.testbench_code:
            rtl_code = list(state.rtl_code.values())[0]
            success, testbench_code, errors = self.verification_agent.generate_testbench(
                rtl_code=rtl_code,
                module_name=state.design_name,
                specification=state.specification,
            )
            
            if success:
                updates["testbench_code"] = testbench_code
                testbench_file = f"test_{state.design_name}.py"
            else:
                updates["verification_errors"] = errors
                updates["current_stage"] = DesignStage.FAILED.value
                return updates
        
        testbench_file = f"test_{state.design_name}.py"
        
        # Run verification
        passed, output, errors = self.verification_agent.run_verification(
            testbench_file=testbench_file,
            rtl_files=state.rtl_files,
            top_module=state.design_name,
        )
        
        updates["verification_passed"] = passed
        updates["verification_errors"] = errors
        updates["verification_iterations"] = state.verification_iterations + 1
        
        if passed:
            logger.info("Verification passed")
        else:
            logger.warning(f"Verification failed: {errors[:3]}")
            
            # Debug and fix if not exceeded max iterations
            if state.verification_iterations < state.max_iterations:
                success, fixed_tb, fixed_rtl = self.verification_agent.debug_verification_failure(
                    testbench_code=state.testbench_code,
                    rtl_code=list(state.rtl_code.values())[0],
                    errors=errors,
                    simulation_output=output,
                )
                
                if success:
                    updates["testbench_code"] = fixed_tb
                    # Update RTL if changed
                    filename = state.rtl_files[0]
                    if fixed_rtl != list(state.rtl_code.values())[0]:
                        updated_rtl = dict(state.rtl_code)
                        updated_rtl[filename] = fixed_rtl
                        updates["rtl_code"] = updated_rtl
        
        return updates
    
    def _hardening_node(self, state: DesignState) -> Dict:
        """Hardening node
        
        Args:
            state: Current state
            
        Returns:
            Updated state as dict
        """
        logger.info("=== Hardening Stage ===")
        
        updates = {
            "current_stage": DesignStage.HARDENING.value,
            "current_agent": AgentType.HARDENING.value,
        }
        
        # Generate OpenLane config if needed
        if not state.openlane_config:
            success, config, errors = self.hardening_agent.generate_openlane_config(
                design_name=state.design_name,
                rtl_files=state.rtl_files,
                clock_port="clk",
                clock_period_ns=20.0,
                die_size_um=(200.0, 200.0),
            )
            
            if success:
                updates["openlane_config"] = config
            else:
                updates["hardening_errors"] = errors
                updates["current_stage"] = DesignStage.FAILED.value
                return updates
        
        # Run OpenLane flow
        success, log, metrics = self.hardening_agent.run_openlane_flow()
        
        updates["hardening_passed"] = success
        updates["hardening_iterations"] = state.hardening_iterations + 1
        
        if success:
            updates["gds_file"] = "design.gds"
            logger.info(f"Hardening passed - Area: {metrics.get('area_um2', 0)} um²")
        else:
            logger.warning("Hardening failed")
            updates["hardening_errors"] = [log]
            
            # Try to fix config
            if state.hardening_iterations < state.max_iterations:
                success, analysis, fixed_config = self.hardening_agent.debug_openlane_errors(
                    error_log=log,
                    config=state.openlane_config,
                )
                if success:
                    updates["openlane_config"] = fixed_config
        
        return updates
    
    def _integration_node(self, state: DesignState) -> Dict:
        """Integration node
        
        Args:
            state: Current state
            
        Returns:
            Updated state as dict
        """
        logger.info("=== Integration Stage ===")
        
        updates = {
            "current_stage": DesignStage.INTEGRATION.value,
            "current_agent": AgentType.CARAVEL.value,
        }
        
        # Generate Caravel config
        user_ios = [{"name": "in", "direction": "input", "width": "8-bit"}]
        
        success, config, errors = self.caravel_agent.generate_caravel_config(
            design_name=state.design_name,
            user_ios=user_ios,
        )
        
        if success:
            updates["caravel_config"] = config
            
            # Integrate design
            success, report = self.caravel_agent.integrate_design(
                design_gds=state.gds_file or "design.gds",
                config=config,
            )
            
            updates["integration_passed"] = success
            
            if success:
                updates["current_stage"] = DesignStage.COMPLETE.value
                logger.info("Integration complete - Design ready for tape-out!")
            else:
                updates["integration_errors"] = [report]
        else:
            updates["integration_errors"] = errors
        
        return updates
    
    def _route_after_rtl(self, state: DesignState) -> str:
        """Route after RTL generation
        
        Args:
            state: Current state
            
        Returns:
            Next node name
        """
        if state.current_stage == DesignStage.FAILED:
            return "failed"
        return "linting"
    
    def _route_after_linting(self, state: DesignState) -> str:
        """Route after linting
        
        Args:
            state: Current state
            
        Returns:
            Next node name
        """
        if state.linting_passed:
            return "verification"
        elif state.iteration_count < state.max_iterations:
            return "rtl_generation"  # Retry with fixes
        else:
            return "failed"
    
    def _route_after_verification(self, state: DesignState) -> str:
        """Route after verification
        
        Args:
            state: Current state
            
        Returns:
            Next node name
        """
        if state.verification_passed:
            return "hardening"
        elif state.verification_iterations < state.max_iterations:
            return "verification"  # Retry with fixes
        else:
            return "failed"
    
    def _route_after_hardening(self, state: DesignState) -> str:
        """Route after hardening
        
        Args:
            state: Current state
            
        Returns:
            Next node name
        """
        if state.hardening_passed:
            return "integration"
        elif state.hardening_iterations < state.max_iterations:
            return "hardening"  # Retry with new config
        else:
            return "failed"
    
    def run(
        self,
        specification: str,
        design_name: str,
    ) -> DesignState:
        """Run complete ASIC design workflow
        
        Args:
            specification: Natural language design specification
            design_name: Name of the design
            
        Returns:
            Final state
        """
        logger.info(f"Starting ASIC design workflow for: {design_name}")
        
        # Create initial state
        initial_state = create_initial_state(
            specification=specification,
            design_name=design_name,
            workspace_dir=self.config.workspace_dir,
            max_iterations=self.config.max_workflow_iterations,
        )
        
        # Run workflow
        final_state = self.workflow.invoke(initial_state.model_dump())
        
        # Convert back to Pydantic model
        result_state = DesignState(**final_state)
        
        logger.info(f"Workflow completed - Stage: {result_state.current_stage}")
        
        return result_state
