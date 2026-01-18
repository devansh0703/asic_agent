# ASIC-Agent Tech Stack Instructions

## Overview
ASIC-Agent is an autonomous multi-agent system for digital ASIC design that extends the capabilities of Large Language Models (LLMs) with specialized tools and workflows for hardware development.

## Core Architecture

### Base Framework
- **OpenHands** (formerly OpenDevin) - Foundation for autonomous agent infrastructure
- **CodeAct System** - Underlying action execution framework for agent behaviors
- **LangGraph** - Orchestration framework for managing agent iterations and workflow states
  - Handles iterative refinement loops
  - Manages state transitions between design stages
  - Coordinates multi-agent communication
  - Enables conditional branching and error recovery flows
- **Multi-Agent Architecture** - Specialized sub-agents for different ASIC design tasks

### Language Models
- **Primary LLM**: Google Gemini 2.5 Flash (FREE tier, optimal for ASIC-Agent)
  - Used for Main Agent RTL generation and planning
  - Used for Verification Agent testbench creation
  - Used for Hardening Agent OpenLane configuration
  - Used for OpenLane debugging and log analysis
  - Free tier: 10 requests/min, 4M tokens/min
  - Fast inference with advanced reasoning capabilities
- **Unified Model Architecture**: Single Gemini 2.5 Flash model for all agents (cost-effective and consistent)

## Hardware Design Tools

### RTL Development
- **Verilator** - Static analysis and linting for Verilog code
- **iverilog** (Icarus Verilog) - Verilog compiler and simulator for syntax checking
- **Verilog HDL** - Primary hardware description language for RTL design

### Synthesis and Implementation
- **Yosys** - Open-source synthesis framework for digital logic
- **OpenLane 2** - Complete open-source ASIC implementation flow
  - Handles RTL-to-GDSII transformation
  - Physical design automation
  - Design rule checking (DRC)
  - Layout versus schematic (LVS)
  
### Chip Integration
- **Caravel** - Open-source chip harness for integration and tape-out preparation

## Verification Stack

### Testbench Framework
- **cocotb** - Python-based verification framework
  - Enables sophisticated test scenarios
  - Leverages LLM's superior Python proficiency
  - Supports complex operations (matrix multiplication, neural networks)
  - Advanced stimulus generation and reference model comparison

### Simulation Tools
- **Icarus Verilog** - Event-driven simulator for waveform generation
- **Verilator** - Fast cycle-based simulator for performance verification

## Agent Components

### Main Agent
**Responsibilities:**
- RTL generation from natural language specifications
- Code linting and static analysis
- Global project state management
- Design constraint tracking
- Adaptive planning and reasoning

**Tools:**
- Verilator (linting)
- iverilog (syntax validation)
- In-context learning and prompted reasoning

### Verification Agent
**Responsibilities:**
- Functional validation of RTL designs
- Test environment generation
- Simulation execution and analysis
- Root-cause analysis of failures
- Actionable feedback generation

**Tools:**
- cocotb framework
- Icarus Verilog
- Verilator
- Waveform analysis utilities

### Hardening Agent
**Responsibilities:**
- Physical layout implementation
- OpenLane configuration generation
- Flow parameter optimization
- Timing, power, and area (PPA) optimization
- Iterative refinement

**Tools:**
- OpenLane 2 flow
- Custom OpenLane debugging tool
- Performance metric analyzers

### Caravel Integration Agent
**Responsibilities:**
- Chip-level integration
- Interface with Caravel harness
- Final design preparation

## Knowledge Infrastructure

### Vector Database
**Implementation: ChromaDB (Local Deployment)**

**Contents:**
- Documentation and API references
- Error knowledge base
- Curated insights from open-source silicon community
- Historical debugging information
- OpenLane flow documentation and common error patterns
- cocotb examples and verification patterns

**Purpose:**
- Enhanced context retrieval
- Error pattern recognition
- Best practices guidance
- Fast local semantic search
- No external dependencies or costs

**ChromaDB Features:**
- Embedded local database (no server required)
- Efficient similarity search with embeddings
- Persistent storage for accumulated knowledge
- Integration with Gemini embedding models

## Development Environment

### Sandbox Environment
- Isolated execution environment for safe tool interaction
- Full access to hardware design toolchain
- File system management
- Process execution and monitoring

### Programming Languages
- **Verilog** - Hardware description for RTL design
- **Python** - Testbench development, scripting, automation
- **TCL** - Tool configuration (OpenLane, synthesis tools)

## Workflow Integration

### LangGraph Orchestration
**State Management:**
- Tracks current design stage and agent state
- Maintains conversation history and context
- Stores intermediate results and artifacts
- Manages iteration counters and exit conditions

**Iteration Control:**
- Automatic retry loops for verification failures
- Iterative OpenLane parameter optimization
- Conditional branching based on success/failure
- Maximum iteration limits to prevent infinite loops

**Agent Coordination:**
- Routes tasks to appropriate specialized agents
- Manages handoffs between design stages
- Aggregates results from multiple verification runs
- Coordinates parallel operations when possible

### Design Flow Stages
1. **Specification** - Natural language to requirements
2. **RTL Generation** - Verilog code synthesis (Main Agent + Gemini 2.5 Flash)
3. **Linting & Analysis** - Static validation
4. **Verification** - Functional testing with cocotb (Verification Agent + iterations)
5. **Hardening** - Physical implementation with OpenLane (Hardening Agent + iterations)
6. **Integration** - Caravel chip integration
7. **Validation** - Final design checks

**LangGraph manages transitions between stages with automatic iteration for stages 4-5**

### Error Handling
- Automated error detection at each stage
- Gemini 2.5 Flash-powered debugging assistance
- LangGraph-managed iterative refinement loops
- ChromaDB knowledge base learning from failures
- Historical error pattern matching for faster resolution

## Benchmarking

### ASIC-Agent-Bench
- First benchmark for agentic systems in hardware design
- Real-world, open-ended design scenarios
- Multi-file context support
- Dynamic tool interaction evaluation
- Iterative debugging assessment

## Dependencies & Requirements

### System Requirements
- Linux-based operating system (recommended)
- Python 3.8+
- Sufficient compute resources for LLM inference
- Storage for vector database and design artifacts

### Tool Installation
**Hardware Tools:**
- Verilator (latest stable)
- Icarus Verilog (iverilog)
- Yosys synthesis suite
- OpenLane 2 flow
- Caravel integration tools

**Python Packages:**
```bash
pip install cocotb chromadb google-generativeai langgraph langchain
```

**Configuration:**
- Set GOOGLE_API_KEY environment variable for Gemini API
- Initialize ChromaDB collection for ASIC knowledge base
- Configure LangGraph workflow definitions

### Python Dependencies
- **cocotb** - Python testbench framework
- **chromadb** - Local vector database for knowledge storage
- **google-generativeai** - Google Gemini API SDK
- **langgraph** - Agent workflow orchestration and state management
- **langchain** - LLM application framework (dependency for LangGraph)
- **OpenHands framework** - Base agent infrastructure

## Cost Considerations

### Complete FREE Stack Configuration

**100% FREE Components:**
- All open-source ASIC tools (Verilator, iverilog, Yosys, OpenLane, cocotb)
- **Google Gemini 2.5 Flash API** (free tier):
  - 10 requests/min, 4M tokens/min
  - Sufficient for all ASIC-Agent operations (Main, Verification, Hardening agents)
  - Advanced reasoning capabilities for complex ASIC tasks
- **ChromaDB** (local deployment):
  - No hosting costs
  - No external API calls
  - Persistent local storage
- **LangGraph** (open-source):
  - Free orchestration framework
  - Handles all iterative workflows
- Local compute on personal workstation

**Zero-Cost Architecture:**
- Single Gemini 2.5 Flash model for all agents = maximized free tier efficiency
- Local ChromaDB = zero database costs
- LangGraph for iterations = no additional LLM calls overhead
- All tools run locally = no cloud compute fees

**Verdict**: With Gemini 2.5 Flash + ChromaDB + LangGraph, ASIC-Agent is **COMPLETELY FREE** for typical usage. The 4M tokens/min limit is more than sufficient for iterative ASIC design workflows.

## Best Practices

### Agent Interaction
- Use clear, structured natural language specifications
- Provide comprehensive design constraints upfront
- Review agent-generated code at each stage
- Leverage iterative refinement for optimization

### Verification Strategy
- Prefer Python/cocotb over HDL testbenches
- Implement comprehensive test coverage
- Use reference models for complex designs
- Analyze waveforms for debugging

### Physical Design
- Start with conservative OpenLane parameters
- Monitor PPA metrics throughout iterations
- Use specialized debugging tool for OpenLane errors
- Validate timing closure before finalizing

## Future Extensions

### Planned Enhancements
- Additional base LLM support
- Expanded tool integration
- Enhanced error knowledge base
- Advanced optimization strategies
- Community feedback integration

## References
- GitHub Repository: https://github.com/AUCOHL/ASIC-Agent-Bench
- OpenHands: https://github.com/All-Hands-AI/OpenHands
- OpenLane: https://github.com/The-OpenROAD-Project/OpenLane
- cocotb: https://github.com/cocotb/cocotb

---

*This tech stack represents the ASIC-Agent system as described in "ASIC-Agent: An Autonomous Multi-Agent System for ASIC Design with Benchmark Evaluation" by Ahmed Allam, Youssef Mansour, and Mohamed Shalan from The American University in Cairo.*
