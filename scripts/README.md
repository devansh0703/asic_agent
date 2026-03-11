# Scripts Directory

Utility scripts for ASIC-Agent setup and maintenance.

## Build Knowledge Base

**`build_knowledge_base.py`** - Scrapes real documentation from the web and builds ChromaDB knowledge base.

### What it does:
1. **Scrapes cocotb documentation** from docs.cocotb.org (official docs)
2. **Fetches cocotb examples** from GitHub repository
3. **Scrapes OpenLane documentation** from GitHub
4. **Adds curated Verilog patterns** (counters, shift registers, FSMs)

### Usage:

```bash
# Build knowledge base (run once during setup)
python3 scripts/build_knowledge_base.py

# Specify custom output directory
python3 scripts/build_knowledge_base.py --output ./my_kb_dir
```

### Output:
- Creates `chroma_db/` directory with vector database
- Stores ~20-50 documents from real sources
- Enables RAG-powered design assistance

### When to run:
- **First time setup** (required)
- **After major cocotb version update** (refresh docs)
- **To add new design patterns** (modify script and rebuild)

## Setup Script

**`setup_knowledge_base.sh`** - Automated setup script.

Single command to:
1. Check Python installation
2. Install web scraping dependencies (beautifulsoup4, requests)
3. Run knowledge base builder
4. Verify installation

### Usage:

```bash
chmod +x scripts/setup_knowledge_base.sh
./scripts/setup_knowledge_base.sh
```

## Requirements

Additional packages for knowledge base building:
```bash
pip install beautifulsoup4 requests lxml
```

Already included in main `requirements.txt`.

## Real Documentation Sources

### cocotb (Official)
- https://docs.cocotb.org/en/stable/
- Quickstart, coroutines, triggers, testbench guide
- Real Python examples from GitHub
- API reference for 2.0+

### OpenLane
- https://github.com/The-OpenROAD-Project/OpenLane
- Configuration reference
- Flow documentation

### Verilog Patterns
- Counters (parametrized)
- Shift registers
- Finite state machines
- Best practices

## Offline Mode

If network is unavailable, the system falls back to minimal hardcoded knowledge. However, for best results, always build the full knowledge base during setup.

To verify knowledge base:
```python
from asic_agent.database.knowledge_base import ASICKnowledgeBase

kb = ASICKnowledgeBase()
results = kb.query("cocotb testbench", n_results=3)
print(f"Found {len(results)} documents")
for r in results:
    print(f"- {r['id']}: {r['content'][:100]}...")
```

## Customization

To add custom documentation:

1. Edit `build_knowledge_base.py`
2. Add new scraping function or static documents
3. Update `scraper.scrape_all()` to include new sources
4. Rebuild knowledge base

Example:
```python
def add_custom_docs(self) -> List[Dict[str, Any]]:
    return [{
        "id": "custom_pattern",
        "content": "Your documentation here...",
        "metadata": {"category": "custom", "type": "pattern"}
    }]
```
