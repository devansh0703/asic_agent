"""Configuration management for ASIC-Agent"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import json


class Config(BaseModel):
    """Configuration for ASIC-Agent system"""
    
    # API Configuration
    llm_provider: str = Field(
        default="mistral",
        description="LLM provider: 'mistral' or 'openrouter'"
    )
    
    # Mistral API Configuration
    mistral_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("MISTRAL_API_KEY"),
        description="Mistral API key"
    )
    mistral_model: str = Field(
        default="mistral-large-latest",
        description="Mistral model name"
    )
    
    # OpenRouter API Configuration
    openrouter_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY"),
        description="OpenRouter API key"
    )
    openrouter_model: str = Field(
        default="google/gemini-2.0-flash-001",
        description="Model name (OpenRouter format)"
    )
    
    # Rate Limiting Configuration
    rate_limit_requests_per_minute: int = Field(
        default=10,
        description="Max API requests per minute (Gemini free tier: 15/min)"
    )
    rate_limit_delay_seconds: float = Field(
        default=6.0,
        description="Minimum delay between API calls in seconds (default: 6s = 10 req/min)"
    )
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting to avoid API quota errors"
    )
    
    # Legacy aliases for backward compatibility
    @property
    def gemini_api_key(self) -> Optional[str]:
        return self.openrouter_api_key if self.llm_provider == "openrouter" else self.mistral_api_key
    
    @property
    def gemini_model(self) -> str:
        return self.openrouter_model if self.llm_provider == "openrouter" else self.mistral_model
    
    # ChromaDB Configuration
    chroma_persist_directory: str = Field(
        default="./chroma_db",
        description="ChromaDB persistence directory"
    )
    chroma_collection_name: str = Field(
        default="asic_knowledge",
        description="ChromaDB collection name"
    )
    
    # Workspace Configuration
    workspace_dir: str = Field(
        default="./workspace",
        description="Workspace directory for design files"
    )
    max_iterations: int = Field(
        default=10,
        description="Maximum iterations",
        ge=1,
        le=50
    )
    
    # Tool Paths
    verilator_path: str = Field(default="verilator", description="Verilator executable path")
    iverilog_path: str = Field(default="iverilog", description="Icarus Verilog path")
    vvp_path: str = Field(default="vvp", description="VVP executable path")
    yosys_path: str = Field(default="yosys", description="Yosys executable path")
    openlane_path: str = Field(default="flow.tcl", description="OpenLane flow script")
    
    # Agent Configuration
    temperature: float = Field(
        default=0.7,
        description="LLM temperature",
        ge=0.0,
        le=2.0
    )
    max_tokens: int = Field(
        default=8192,
        description="Maximum tokens per LLM call",
        ge=100,
        le=32000
    )
    
    # Verification Configuration
    simulation_timeout: int = Field(
        default=300,
        description="Simulation timeout in seconds",
        ge=10
    )
    
    # Hardening Configuration
    openlane_timeout: int = Field(
        default=3600,
        description="OpenLane timeout in seconds",
        ge=60
    )
    target_frequency_mhz: float = Field(
        default=50.0,
        description="Target frequency in MHz",
        gt=0.0
    )
    
    # LangGraph Configuration
    max_workflow_iterations: int = Field(
        default=5,
        description="Maximum workflow iterations per stage",
        ge=1,
        le=20
    )
    enable_human_feedback: bool = Field(
        default=False,
        description="Enable human-in-the-loop feedback"
    )
    
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
    
    # No old gemini_api_key validator - now handled in individual provider validators
    
    def model_post_init(self, __context):
        """Post-initialization actions"""
        # Create directories if they don't exist
        os.makedirs(self.workspace_dir, exist_ok=True)
        os.makedirs(self.chroma_persist_directory, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "gemini_model": self.gemini_model,
            "workspace_dir": self.workspace_dir,
            "max_iterations": self.max_iterations,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
    
    @classmethod
    def from_file(cls, filepath: str) -> "Config":
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        return cls(**config_dict)
    
    def save(self, filepath: str):
        """Save configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
