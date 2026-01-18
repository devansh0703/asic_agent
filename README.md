# ASIC-Agent 🔬

**Autonomous Multi-Agent System for ASIC Design** - LLM-powered end-to-end chip design workflow from natural language specification to silicon-ready GDSII.

[![OpenLane](https://img.shields.io/badge/OpenLane-RTL--to--GDSII-blue)](https://github.com/The-OpenROAD-Project/OpenLane)
[![Sky130](https://img.shields.io/badge/PDK-Sky130-green)](https://github.com/google/skywater-pdk)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow)](https://python.org)

## 🚀 Features

- **LLM-Powered RTL Generation**: Generate Verilog from natural language using Gemini/Mistral
- **Automated Verification**: cocotb testbench generation and simulation with Icarus Verilog
- **Real ASIC Hardening**: Complete RTL-to-GDSII flow using OpenLane in Docker
- **Caravel Integration**: Automatic integration with Efabless Caravel for tapeout
- **Knowledge Base**: RAG-powered design assistance using ChromaDB
- **Multi-Agent Architecture**: Specialized agents for each design stage

**NO SIMULATIONS - 100% REAL TOOLS:**
- ✅ Real Docker OpenLane execution (Yosys, OpenROAD, Magic)
- ✅ Real Sky130 PDK (2.4GB process design kit)
- ✅ Real GDSII generation (fabrication-ready layouts)
- ✅ Real git operations (Caravel clone)

## 📋 Requirements

### Software
- **Python 3.10+**
- **Docker** (for OpenLane)
- **Git** (for Caravel integration)
- **Icarus Verilog** (`iverilog`)
- **Verilator** (linting)

### Python Packages
```bash
pip install -r requirements.txt
```

Core dependencies:
- `openai` - LLM API client
- `mistralai` - Mistral LLM support
- `chromadb` - Vector database for RAG
- `cocotb` - Hardware verification framework
- `langchain` - Agent orchestration

### API Keys
- **OpenRouter API Key** (for Gemini/Claude) OR
- **Mistral API Key**

Set via environment variable:
```bash
export OPENROUTER_API_KEY="your-key-here"
# OR
export MISTRAL_API_KEY="your-key-here"
```

## 🛠️ Installation

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y docker.io git iverilog verilator python3-pip
sudo usermod -aG docker $USER  # Allow Docker without sudo
newgrp docker  # Apply group change
```

**macOS:**
```bash
brew install docker git icarus-verilog verilator python3
```

### 2. Install Python Dependencies
```bash
git clone https://github.com/yourusername/asic-agent.git
cd asic-agent
pip install -r requirements.txt
```

### 3. Set Up API Key
```bash
echo 'export OPENROUTER_API_KEY="sk-or-v1-..."' >> ~/.bashrc
source ~/.bashrc
```

### 4. First Run (Downloads Sky130 PDK ~2.4GB)
```bash
python3 main.py "Design a 4-bit counter" --name counter4bit
```

The first run will download the Sky130 PDK to `~/.volare/` (one-time, ~5 minutes).

## 💻 Usage

### Basic Usage
```bash
python3 main.py "Design a [your specification]" --name [design_name]
```

### Examples

**Simple Counter:**
```bash
python3 main.py "Design a 8-bit counter with synchronous reset" --name counter8bit
```

**Shift Register:**
```bash
python3 main.py "Design a 16-bit shift register with parallel load" --name shift_reg
```

**Custom Configuration:**
```bash
python3 main.py "Design a 2-bit counter" \
  --name counter2bit \
  --provider openrouter \
  --model google/gemini-2.0-flash-001 \
  --max-iterations 3 \
  --rate-limit 4.0
```

### Command-Line Options

```
--name NAME              Design name (required)
--provider PROVIDER      LLM provider: 'openrouter' or 'mistral' (default: openrouter)
--model MODEL           Model name (default: google/gemini-2.0-flash-001)
--max-iterations N      Max debug iterations per stage (default: 5)
--rate-limit SECONDS    Delay between API calls (default: 6.0)
--no-rate-limit         Disable rate limiting
```

## 🏗️ Workflow Stages

### 1. **RTL Generation** 🤖
- LLM generates Verilog from natural language
- Automatic module inference and port generation
- Best practices from knowledge base

### 2. **Linting** 🔍
- Verilator syntax checking
- LLM-powered error fixing
- Iterative refinement

### 3. **Verification** ✅
- Automatic cocotb testbench generation
- Icarus Verilog simulation
- Coverage-driven test generation

### 4. **Hardening** 🏭
**REAL OpenLane Docker Execution:**
- Yosys synthesis
- Floorplanning (OpenROAD)
- Placement & routing
- Clock tree synthesis
- Magic GDSII generation

**Output:** `workspace/design.gds` (818KB+ silicon-ready layout)

### 5. **Integration** 🚀
**REAL Caravel Repository Clone:**
- Git clone `efabless/caravel_user_project`
- GDS integration
- Wrapper generation
- Tapeout preparation

## 📂 Project Structure

```
asic-agent/
├── asic_agent/
│   ├── agents/           # Specialized agents
│   │   ├── main_agent.py          # RTL generation
│   │   ├── verification_agent.py   # Testbench generation
│   │   ├── hardening_agent.py      # OpenLane execution
│   │   └── caravel_agent.py        # Caravel integration
│   ├── workflows/        # Orchestration
│   │   └── orchestrator.py
│   ├── database/         # Knowledge base
│   │   └── knowledge_base.py
│   ├── llm_client.py     # LLM API wrapper
│   └── config.py         # Configuration
├── workspace/            # Design outputs (gitignored)
│   ├── design.v          # Generated RTL
│   ├── design.gds        # Final GDSII
│   └── openlane_run/     # OpenLane artifacts
├── main.py              # CLI entry point
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🎯 Output Files

After successful workflow:

```
workspace/
├── [design_name].v              # RTL Verilog
├── test_[design_name].py        # cocotb testbench
├── design.gds                   # GDSII layout (818KB+)
├── config.json                  # OpenLane configuration
├── openlane_run/
│   └── designs/[name]/runs/run1/
│       └── results/final/
│           ├── gds/            # GDSII files
│           ├── verilog/gl/    # Gate-level netlist
│           ├── lef/           # Cell abstracts
│           ├── spef/          # Parasitic extraction
│           └── sdf/           # Timing data
└── caravel_user_project/       # Cloned Caravel repo
    ├── gds/                    # Integrated GDS
    └── verilog/rtl/           # Integrated RTL
```

## 🔬 Real Tool Integration

### OpenLane (Docker)
```python
subprocess.run([
    'docker', 'run', '--rm',
    '-v', f'{design_dir}:/openlane',
    '-v', f'{pdk_root}:/root/.volare',
    'efabless/openlane:latest',
    'flow.tcl', '-tag', 'run1', '-overwrite'
])
```

### Caravel (Git)
```python
subprocess.run([
    'git', 'clone', '--depth', '1',
    'https://github.com/efabless/caravel_user_project.git',
    caravel_dir
])
```

**Runtime:** 15-30 minutes for complete RTL-to-GDSII flow (small designs)

## 🐛 Troubleshooting

### Docker Permission Denied
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### PDK Not Found
```bash
# Manual PDK fetch
docker run --rm -v ~/.volare:/root/.volare efabless/openlane:latest \
  volare fetch sky130 bdc9412b3e468c102d01b7cf6337be06ec6e9c9a
```

### Rate Limit Errors (Gemini)
```bash
# Increase delay between requests
python3 main.py "..." --rate-limit 10.0
```

### Verification Failures
Check cocotb test logic in `workspace/test_*.py` - LLM may generate incorrect timing

## 📊 Example Output

```
╔═══════════════════════════════════════════════════════════════╗
║                         ASIC-Agent                            ║
║         Autonomous Multi-Agent System for ASIC Design         ║
║  Powered by: OpenRouter/Gemini + ChromaDB + LangGraph      ║
╚═══════════════════════════════════════════════════════════════╝

Configuration: Provider=openrouter, Model=google/gemini-2.0-flash-001

=== RTL Generation Stage ===
✓ Generated RTL saved to: workspace/counter2bit.v

=== Linting Stage ===
✓ Linting passed

=== Verification Stage ===
✓ Verification passed

=== Hardening Stage ===
✓ OpenLane synthesis complete
✓ Place & route complete
✓ GDSII generated: workspace/design.gds (818KB)

=== Integration Stage ===
✓ Caravel cloned successfully
✓ GDS integrated

============================================================
WORKFLOW RESULTS
============================================================
Design Name: counter2bit
Final Stage: integration

RTL Files Generated:
  ✓ counter2bit.v

✓ Linting: PASSED
✓ Verification: PASSED
✓ Hardening: PASSED (design.gds)
✓ Integration: PASSED
============================================================
```

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- More complex design patterns in knowledge base
- Additional verification strategies
- Timing optimization heuristics
- Multi-module design support

## 📄 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- **OpenLane**: RTL-to-GDSII flow (Efabless)
- **Sky130 PDK**: Open-source process design kit (Google/Skywater)
- **Caravel**: Open-source chip harness (Efabless)
- **cocotb**: Python verification framework
- **OpenRouter**: LLM API gateway

## ⚠️ Disclaimer

This tool generates real GDSII layouts but **does not validate designs for production**. For actual tapeout:
1. Run full DRC/LVS verification
2. Perform timing closure analysis
3. Add proper power/ground distribution
4. Follow foundry design rules
5. Use professional EDA tools for sign-off

**Educational/Research Use Only**
