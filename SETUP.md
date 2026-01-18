# ASIC-Agent Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Get Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy your key

### 3. Set Environment Variable

```bash
export GOOGLE_API_KEY="your-api-key-here"

# Add to ~/.bashrc or ~/.zshrc to persist:
echo 'export GOOGLE_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Run First Design

```bash
# Simple example
python3 main.py "Design a 4-bit counter" --name counter4

# Or use test script
./test_run.sh
```

## Detailed Setup

### Python Environment

ASIC-Agent works with Python 3.8+. Check your version:

```bash
python3 --version
```

Install using global environment (as requested):

```bash
pip3 install cocotb chromadb google-generativeai langgraph langchain langchain-google-genai langchain-community langchain-core tiktoken pydantic
```

### Optional: Hardware Tools

For full functionality (actual simulation/synthesis):

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install verilator iverilog yosys
```

**macOS:**
```bash
brew install verilator icarus-verilog yosys
```

**Note**: OpenLane 2 requires separate installation. See: https://github.com/The-OpenROAD-Project/OpenLane

### Verify Installation

```bash
# Check Python packages
python3 -c "import cocotb, chromadb, google.generativeai, langgraph; print('✓ All packages installed')"

# Check hardware tools (optional)
verilator --version
iverilog -v
yosys -V
```

## Configuration

### Default Configuration

ASIC-Agent uses these defaults:
- Model: `gemini-2.5-flash` (Gemini 2.5 Flash)
- Workspace: `./workspace`
- ChromaDB: `./chroma_db`
- Max iterations: 5 per stage

### Custom Configuration

Create a config file:

```python
# my_config.py
from asic_agent.config import Config

config = Config(
    gemini_model="gemini-2.5-flash",
    workspace_dir="./my_workspace",
    chroma_persist_directory="./my_chroma_db",
    max_workflow_iterations=10,
    temperature=0.7,
)
```

Use in code:

```python
from asic_agent import ASICOrchestrator
from my_config import config

orchestrator = ASICOrchestrator(config)
result = orchestrator.run("Design specification", "design_name")
```

## Usage Examples

### Basic Counter

```bash
python3 main.py "Design an 8-bit counter with reset" --name counter8
```

### From Specification File

```bash
python3 main.py --spec-file examples/simple_counter.txt --name counter4
```

### Verbose Output

```bash
python3 main.py "Design a multiplexer" --name mux --verbose
```

### Custom Workspace

```bash
python3 main.py "Design an ALU" --name alu --workspace ./my_designs
```

## Troubleshooting

### API Key Issues

**Error**: "GOOGLE_API_KEY not set"

**Solution**:
```bash
export GOOGLE_API_KEY="your-key-here"
```

### Import Errors

**Error**: "No module named 'cocotb'"

**Solution**:
```bash
pip3 install cocotb chromadb google-generativeai langgraph langchain langchain-google-genai langchain-community langchain-core
```

### Permission Errors

**Error**: "Permission denied"

**Solution**:
```bash
chmod +x main.py
chmod +x test_run.sh
```

### Rate Limits

**Error**: "Rate limit exceeded"

**Solution**: Gemini free tier allows 10 requests/min, 4M tokens/min. Wait a minute and retry.

## Project Structure

```
brainwave/
├── asic_agent/              # Main package
│   ├── agents/              # Agent implementations
│   ├── database/            # ChromaDB knowledge base
│   ├── tools/               # Hardware tools wrappers
│   ├── workflows/           # LangGraph workflows
│   ├── config.py            # Configuration
│   └── llm_client.py        # Gemini client
├── examples/                # Example specifications
├── workspace/               # Design outputs (generated)
├── chroma_db/               # Vector database (generated)
├── main.py                  # CLI entry point
├── test_run.sh              # Test script
├── requirements.txt         # Python dependencies
├── README.md                # Documentation
└── SETUP.md                 # This file
```

## Next Steps

1. ✓ Set up API key
2. ✓ Install dependencies
3. ✓ Run test: `./test_run.sh`
4. 📝 Try your own designs
5. 🔧 Install hardware tools (optional)
6. 🚀 Explore advanced features

## Getting Help

- Check logs: `asic_agent.log`
- Enable verbose mode: `--verbose`
- Read examples in `examples/`
- Check configuration in `asic_agent/config.py`

## Free Tier Limits

Gemini 2.5 Flash free tier:
- 10 requests per minute
- 4 million tokens per minute
- More than enough for ASIC-Agent workflows

ChromaDB: 100% local, no limits

## Production Deployment

For production use:
1. Consider Gemini API paid tier for higher limits
2. Install actual hardware tools (Verilator, OpenLane)
3. Set up CI/CD for automated testing
4. Use persistent ChromaDB with version control

---

**Ready to design ASICs with AI!** 🚀
