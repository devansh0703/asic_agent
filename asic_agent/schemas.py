"""Pydantic schemas for ASIC-Agent components"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class RTLGenerationRequest(BaseModel):
    """Request schema for RTL generation"""
    specification: str = Field(..., description="Design specification", min_length=10)
    design_name: str = Field(..., description="Module name", pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    target_language: str = Field(default="verilog", description="HDL language")
    
    @field_validator('design_name')
    @classmethod
    def validate_design_name(cls, v):
        if v.lower() in ['module', 'endmodule', 'always', 'assign']:
            raise ValueError(f"'{v}' is a reserved keyword")
        return v


class RTLGenerationResponse(BaseModel):
    """Response schema for RTL generation"""
    success: bool = Field(..., description="Whether generation succeeded")
    rtl_code: Dict[str, str] = Field(default_factory=dict, description="Generated RTL files")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")


class LintingResult(BaseModel):
    """Linting result schema"""
    passed: bool = Field(..., description="Whether linting passed")
    errors: List[str] = Field(default_factory=list, description="Linting errors")
    warnings: List[str] = Field(default_factory=list, description="Linting warnings")
    file_path: str = Field(..., description="File that was linted")


class TestbenchGenerationRequest(BaseModel):
    """Request schema for testbench generation"""
    rtl_code: str = Field(..., description="RTL code to test")
    module_name: str = Field(..., description="Module name")
    specification: str = Field(..., description="Design specification")
    framework: str = Field(default="cocotb", description="Verification framework")


class TestbenchGenerationResponse(BaseModel):
    """Response schema for testbench generation"""
    success: bool = Field(..., description="Whether generation succeeded")
    testbench_code: str = Field(default="", description="Generated testbench")
    errors: List[str] = Field(default_factory=list, description="Errors")


class SimulationResult(BaseModel):
    """Simulation result schema"""
    passed: bool = Field(..., description="Whether simulation passed")
    output: str = Field(default="", description="Simulation output")
    errors: List[str] = Field(default_factory=list, description="Errors")
    waveform_file: Optional[str] = Field(None, description="VCD waveform file")
    coverage: Optional[float] = Field(None, description="Code coverage", ge=0.0, le=100.0)


class OpenLaneConfig(BaseModel):
    """OpenLane configuration schema"""
    DESIGN_NAME: str = Field(..., description="Design name")
    VERILOG_FILES: List[str] = Field(..., description="Verilog source files")
    CLOCK_PORT: str = Field(default="clk", description="Clock port name")
    CLOCK_PERIOD: float = Field(default=20.0, description="Clock period in ns", gt=0)
    DIE_AREA: str = Field(default="0 0 200 200", description="Die area")
    FP_SIZING: str = Field(default="absolute", description="Floorplan sizing mode")
    PL_TARGET_DENSITY: float = Field(default=0.6, description="Placement density", ge=0.0, le=1.0)
    SYNTH_STRATEGY: str = Field(default="DELAY 0", description="Synthesis strategy")
    FP_PDN_VPITCH: int = Field(default=25, description="Power grid vertical pitch")
    FP_PDN_HPITCH: int = Field(default=25, description="Power grid horizontal pitch")
    
    class Config:
        extra = "allow"  # Allow additional OpenLane parameters


class HardeningFlowResult(BaseModel):
    """Hardening flow result schema"""
    success: bool = Field(..., description="Whether flow succeeded")
    log: str = Field(default="", description="Flow log")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="PPA metrics")
    gds_file: Optional[str] = Field(None, description="Generated GDS file")
    errors: List[str] = Field(default_factory=list, description="Errors")


class ToolAvailability(BaseModel):
    """Hardware tools availability schema"""
    verilator: bool = Field(default=False, description="Verilator available")
    iverilog: bool = Field(default=False, description="Icarus Verilog available")
    vvp: bool = Field(default=False, description="VVP available")
    yosys: bool = Field(default=False, description="Yosys available")
    openlane: bool = Field(default=False, description="OpenLane available")
    cocotb: bool = Field(default=False, description="cocotb available")


class KnowledgeDocument(BaseModel):
    """Knowledge base document schema"""
    id: str = Field(..., description="Document ID")
    content: str = Field(..., description="Document content", min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    category: str = Field(..., description="Document category")
    doc_type: str = Field(..., description="Document type")
    
    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        valid_categories = ['verilog', 'cocotb', 'openlane', 'general', 'errors']
        if v not in valid_categories:
            raise ValueError(f"Category must be one of {valid_categories}")
        return v


class ErrorSolution(BaseModel):
    """Error solution schema"""
    error_type: str = Field(..., description="Type of error")
    error_message: str = Field(..., description="Error message")
    solution: str = Field(..., description="Solution description")
    category: str = Field(..., description="Error category")
    confidence: Optional[float] = Field(None, description="Solution confidence", ge=0.0, le=1.0)


class AgentMessage(BaseModel):
    """Message between agents"""
    from_agent: str = Field(..., description="Source agent")
    to_agent: str = Field(..., description="Destination agent")
    message_type: str = Field(..., description="Message type")
    content: Dict[str, Any] = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Timestamp")


class WorkflowMetrics(BaseModel):
    """Workflow execution metrics"""
    total_time_seconds: float = Field(default=0.0, description="Total execution time")
    rtl_generation_time: float = Field(default=0.0, description="RTL generation time")
    verification_time: float = Field(default=0.0, description="Verification time")
    hardening_time: float = Field(default=0.0, description="Hardening time")
    total_llm_calls: int = Field(default=0, description="Total LLM API calls")
    total_tokens: int = Field(default=0, description="Total tokens used")
    iterations_per_stage: Dict[str, int] = Field(
        default_factory=dict,
        description="Iterations per stage"
    )
