"""LangGraph state definitions for ASIC design workflow"""

from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class DesignStage(str, Enum):
    """Stages in the ASIC design flow"""
    SPECIFICATION = "specification"
    RTL_GENERATION = "rtl_generation"
    LINTING = "linting"
    VERIFICATION = "verification"
    HARDENING = "hardening"
    INTEGRATION = "integration"
    COMPLETE = "complete"
    FAILED = "failed"


class AgentType(str, Enum):
    """Types of agents in the system"""
    MAIN = "main"
    VERIFICATION = "verification"
    HARDENING = "hardening"
    CARAVEL = "caravel"


class Message(BaseModel):
    """Message in conversation history"""
    role: str = Field(..., description="Role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class DesignState(BaseModel):
    """State for the ASIC design workflow"""
    
    # Design specification
    specification: str = Field(..., description="Natural language design specification")
    design_name: str = Field(..., description="Name of the design/module")
    
    # Current stage
    current_stage: DesignStage = Field(
        default=DesignStage.SPECIFICATION,
        description="Current workflow stage"
    )
    
    # RTL Generation
    rtl_code: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of filename to RTL code"
    )
    rtl_files: List[str] = Field(
        default_factory=list,
        description="List of generated RTL files"
    )
    
    # Linting results
    linting_passed: bool = Field(default=False, description="Whether linting passed")
    linting_errors: List[str] = Field(default_factory=list, description="Linting errors")
    
    # Verification
    testbench_code: str = Field(default="", description="Generated testbench code")
    verification_passed: bool = Field(default=False, description="Whether verification passed")
    verification_errors: List[str] = Field(
        default_factory=list,
        description="Verification errors"
    )
    verification_iterations: int = Field(default=0, description="Number of verification iterations")
    
    # Hardening
    openlane_config: str = Field(default="", description="OpenLane configuration JSON")
    hardening_passed: bool = Field(default=False, description="Whether hardening passed")
    hardening_errors: List[str] = Field(default_factory=list, description="Hardening errors")
    hardening_iterations: int = Field(default=0, description="Number of hardening iterations")
    gds_file: Optional[str] = Field(None, description="Path to GDS file")
    
    # Integration
    caravel_config: str = Field(default="", description="Caravel integration configuration")
    integration_passed: bool = Field(default=False, description="Whether integration passed")
    integration_errors: List[str] = Field(
        default_factory=list,
        description="Integration errors"
    )
    
    # Workflow control
    messages: List[Message] = Field(
        default_factory=list,
        description="Conversation history"
    )
    iteration_count: int = Field(default=0, description="Total iteration count")
    max_iterations: int = Field(default=5, description="Maximum iterations per stage")
    
    # Error tracking and recovery
    errors: List[str] = Field(default_factory=list, description="All errors encountered")
    solutions_attempted: List[str] = Field(
        default_factory=list,
        description="Solutions attempted"
    )
    
    # Agent metadata
    current_agent: AgentType = Field(
        default=AgentType.MAIN,
        description="Current active agent"
    )
    workspace_dir: str = Field(..., description="Workspace directory path")
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True


class VerificationState(BaseModel):
    """State specific to verification workflow"""
    
    # RTL under test
    rtl_files: List[str] = Field(..., description="List of RTL files to verify")
    top_module: str = Field(..., description="Top module name")
    
    # Test configuration
    testbench_file: str = Field(..., description="Testbench file path")
    test_vectors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Test vectors"
    )
    
    # Simulation results
    simulation_log: str = Field(default="", description="Simulation log output")
    waveform_file: Optional[str] = Field(None, description="Waveform file path")
    passed: bool = Field(default=False, description="Whether tests passed")
    errors: List[str] = Field(default_factory=list, description="Test errors")
    
    # Iteration control
    iteration: int = Field(default=0, description="Current iteration number")
    max_iterations: int = Field(default=5, description="Maximum iterations")
    
    @field_validator('iteration')
    @classmethod
    def validate_iteration(cls, v, info):
        max_iter = info.data.get('max_iterations', 5)
        if v > max_iter:
            raise ValueError(f"Iteration {v} exceeds max_iterations {max_iter}")
        return v


class HardeningMetrics(BaseModel):
    """Metrics from hardening flow"""
    area_um2: Optional[float] = Field(None, description="Area in square micrometers")
    worst_slack_ns: Optional[float] = Field(None, description="Worst timing slack in ns")
    power_mw: Optional[float] = Field(None, description="Power consumption in mW")
    utilization: Optional[float] = Field(None, description="Die utilization (0.0-1.0)")
    
    @field_validator('utilization')
    @classmethod
    def validate_utilization(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("Utilization must be between 0.0 and 1.0")
        return v


class HardeningState(BaseModel):
    """State specific to hardening workflow"""
    
    # Input RTL
    rtl_files: List[str] = Field(..., description="List of RTL files")
    top_module: str = Field(..., description="Top module name")
    
    # Configuration
    config_file: str = Field(..., description="Configuration file path")
    clock_period: float = Field(default=20.0, description="Clock period in ns", gt=0)
    die_area: str = Field(default="0 0 200 200", description="Die area specification")
    target_density: float = Field(
        default=0.6,
        description="Target placement density",
        ge=0.0,
        le=1.0
    )
    
    # Flow results
    synthesis_log: str = Field(default="", description="Synthesis log")
    placement_log: str = Field(default="", description="Placement log")
    routing_log: str = Field(default="", description="Routing log")
    gds_file: Optional[str] = Field(None, description="GDS file path")
    
    # Metrics
    metrics: HardeningMetrics = Field(
        default_factory=HardeningMetrics,
        description="PPA metrics"
    )
    
    # Status
    passed: bool = Field(default=False, description="Whether hardening passed")
    errors: List[str] = Field(default_factory=list, description="Hardening errors")
    
    # Iteration control
    iteration: int = Field(default=0, description="Current iteration")
    max_iterations: int = Field(default=5, description="Maximum iterations")


def create_initial_state(
    specification: str,
    design_name: str,
    workspace_dir: str,
    max_iterations: int = 5,
) -> DesignState:
    """Create initial state for ASIC design workflow
    
    Args:
        specification: Natural language design specification
        design_name: Name of the design
        workspace_dir: Workspace directory path
        max_iterations: Maximum iterations per stage
        
    Returns:
        Initial DesignState
    """
    return DesignState(
        specification=specification,
        design_name=design_name,
        workspace_dir=workspace_dir,
        max_iterations=max_iterations,
        current_stage=DesignStage.SPECIFICATION,
        current_agent=AgentType.MAIN,
    )
