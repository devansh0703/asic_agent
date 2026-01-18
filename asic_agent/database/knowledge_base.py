"""ChromaDB vector database for ASIC knowledge storage and retrieval"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
import logging
import os

logger = logging.getLogger(__name__)


class ASICKnowledgeBase:
    """Vector database for ASIC design knowledge, documentation, and errors"""
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "asic_knowledge",
    ):
        """Initialize ChromaDB knowledge base
        
        Args:
            persist_directory: Directory to persist database
            collection_name: Name of the collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "ASIC design knowledge base"}
            )
            logger.info(f"Created new collection: {collection_name}")
            self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Initialize knowledge base with common ASIC design knowledge"""
        
        # Verilog best practices
        verilog_docs = [
            {
                "id": "verilog_basics",
                "content": """Verilog Best Practices:
1. Use `always @(posedge clk)` for synchronous logic
2. Use `always @(*)` for combinational logic
3. Declare all signals before use (input, output, reg, wire)
4. Use non-blocking assignments (<=) in sequential blocks
5. Use blocking assignments (=) in combinational blocks
6. Always include reset logic in sequential blocks
7. Avoid latches by ensuring all paths are covered in combinational logic
8. Use parameters for configurable values
9. Add comments for complex logic
10. Follow consistent naming conventions""",
                "metadata": {"category": "verilog", "type": "best_practices"}
            },
            {
                "id": "common_verilog_errors",
                "content": """Common Verilog Errors and Solutions:
1. Syntax Error: Missing semicolon - Add semicolon at end of statement
2. Undefined signal - Declare signal as input, output, reg, or wire
3. Multiple drivers - Ensure signal is driven from only one always block
4. Latch inference - Cover all conditions in combinational logic
5. Blocking vs non-blocking - Use <= in sequential, = in combinational
6. Width mismatch - Ensure signal widths match in assignments
7. Undeclared module - Check module name spelling and instantiation
8. Sensitivity list incomplete - Use @(*) for combinational logic""",
                "metadata": {"category": "verilog", "type": "errors"}
            },
        ]
        
        # cocotb verification knowledge
        cocotb_docs = [
            {
                "id": "cocotb_basics",
                "content": """cocotb 2.0+ Testbench Structure (IMPORTANT - THESE ARE THE CORRECT APIS):
1. Import cocotb and cocotb.triggers
2. Mark test functions with @cocotb.test() decorator
3. Use async/await for test coroutines
4. Access DUT signals: dut.signal_name.value
5. Drive inputs: dut.input_signal.value = value
6. Read outputs: value = dut.output_signal.value (use int() to convert)
7. Use Clock() to drive clock signals
8. Use await Timer() for delays
9. Use await RisingEdge(clk) or FallingEdge(clk) for synchronization
10. Assert expected values: assert int(dut.output.value) == expected

CRITICAL COCOTB 2.0+ API CHANGES:
- NEVER import 'cocotb.log' - it doesn't exist in 2.0+
- Use Python's logging module instead: import logging; log = logging.getLogger(__name__)
- NEVER use SimLog() - replaced by standard logging
- NEVER use cocotb.log.getLogger() - use logging.getLogger() instead
- Convert signal values with int(): int(dut.signal.value) for comparisons
- Use cocotb.log.info() becomes log.info() with standard logging

CRITICAL TIMING AFTER RESET (COUNTERS AND SEQUENTIAL LOGIC):
For a counter with synchronous reset, the sequence is:
1. dut.reset.value = 1; await RisingEdge(clk); await Timer(1, "ns")  → count = 0
2. dut.reset.value = 0  → prepare to start counting
3. await RisingEdge(clk); await Timer(1, "ns")  → count = 1 (incremented!)
4. await RisingEdge(clk); await Timer(1, "ns")  → count = 2

COMMON MISTAKE: Expecting count=0 after reset release + 1 clock
CORRECT: After reset release, first clock edge makes count=1 (it counts!)

Counter Test Pattern:
```python
dut.reset.value = 1
await RisingEdge(dut.clk)
await Timer(1, units="ns")
# count is 0 here

dut.reset.value = 0
# Don't check yet! Counter will increment on next edge
for i in range(1, 5):  # Start from 1, not 0!
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    assert int(dut.count.value) == i  # i = 1, 2, 3, 4
```""",
                "metadata": {"category": "cocotb", "type": "best_practices"}
            },
            {
                "id": "cocotb_example",
                "content": """Example cocotb 2.0+ Testbench (CORRECT VERSION):
```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import logging

log = logging.getLogger(__name__)

@cocotb.test()
async def test_counter(dut):
    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # CRITICAL SYNCHRONOUS RESET TIMING:
    # Must wait for delta cycles after RisingEdge before checking values!
    dut.rst.value = 1
    await RisingEdge(dut.clk)  # Reset asserted ON this edge
    await Timer(1, units="ns")  # CRITICAL: Wait for delta cycles!
    
    # NOW safe to check reset value
    assert int(dut.count.value) == 0, "Reset failed"
    
    dut.rst.value = 0
    # DO NOT clock yet! Counter is at 0 right now.
    # First clock edge AFTER reset release will make it 1!
    
    log.info("Testing counter sequence")
    
    # CORRECT counter test pattern - counter starts at 0, will increment
    # Expected sequence: 0 (reset) → 1 (first clock) → 2 (second clock) → ...
    for expected in range(16):  # Test counts 0-15
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")  # Wait for signal to update!
        actual = int(dut.count.value)
        assert actual == expected, f"Expected {expected}, got {actual}"
        log.info(f"Count = {actual}")
```

CRITICAL UNDERSTANDING - COUNTER TESTING:
1. After reset: count = 0
2. Release reset (rst=0) - count STILL 0
3. First clock edge → count = 1 (NOT 0!)
4. Second clock edge → count = 2
5. Pattern: for expected in range(N) works because we clock THEN check

WRONG PATTERN (COMMON MISTAKE):
```python
# BAD - expects count=0 after reset release + clock
dut.rst.value = 0
await RisingEdge(dut.clk)
await Timer(1, units="ns")
assert int(dut.count.value) == 0  # WRONG! Counter incremented to 1!
```

WHY Timer(1, units="ns") IS REQUIRED:
- Synchronous logic updates ON the clock edge
- await RisingEdge() returns WHEN edge occurs, but before signals update
- Signals update in NEXT delta cycle
- Timer(1, units="ns") waits for delta cycles to complete
- ALWAYS use: await RisingEdge(dut.clk); await Timer(1, units="ns")

NEVER DO THIS (OLD cocotb API):
```python
# WRONG - DO NOT USE:
from cocotb.log import SimLog  # Module doesn't exist!
log = SimLog("test")  # WRONG!
log = cocotb.log.getLogger()  # WRONG!

# WRONG - Missing Timer after RisingEdge:
await RisingEdge(dut.clk)
value = int(dut.signal.value)  # May get old value!

# CORRECT:
await RisingEdge(dut.clk)
await Timer(1, units="ns")  # Wait for delta cycles
value = int(dut.signal.value)  # Gets new value
```""",
                "metadata": {"category": "cocotb", "type": "example"}
            },
        ]
        
        # OpenLane knowledge
        openlane_docs = [
            {
                "id": "openlane_config",
                "content": """OpenLane Configuration Basics:
1. DESIGN_NAME - Name of the top module
2. VERILOG_FILES - List of Verilog source files
3. CLOCK_PORT - Clock signal name
4. CLOCK_PERIOD - Target clock period in ns
5. DIE_AREA - Die dimensions "0 0 width height"
6. FP_PDN_VPITCH - Power grid vertical pitch
7. FP_PDN_HPITCH - Power grid horizontal pitch
8. FP_SIZING - absolute or relative
9. PL_TARGET_DENSITY - Target placement density (0.0-1.0)
10. SYNTH_STRATEGY - Synthesis strategy (AREA or DELAY)""",
                "metadata": {"category": "openlane", "type": "configuration"}
            },
            {
                "id": "openlane_errors",
                "content": """Common OpenLane Errors:
1. "Design has no clock" - Set CLOCK_PORT in config
2. "Timing violation" - Increase CLOCK_PERIOD or adjust constraints
3. "DRC violation" - Adjust routing parameters or die size
4. "Antenna violation" - Enable diode insertion
5. "Power grid failure" - Adjust FP_PDN parameters
6. "Placement failure" - Increase die area or reduce density
7. "Synthesis fails" - Check Verilog syntax and module names""",
                "metadata": {"category": "openlane", "type": "errors"}
            },
        ]
        
        # Add all documents
        all_docs = verilog_docs + cocotb_docs + openlane_docs
        
        for doc in all_docs:
            self.add_document(
                doc_id=doc["id"],
                content=doc["content"],
                metadata=doc["metadata"]
            )
        
        logger.info(f"Initialized knowledge base with {len(all_docs)} documents")
    
    def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add a document to the knowledge base
        
        Args:
            doc_id: Unique document ID
            content: Document content
            metadata: Optional metadata dict
        """
        self.collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata] if metadata else None,
        )
        logger.debug(f"Added document: {doc_id}")
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Query the knowledge base
        
        Args:
            query_text: Query string
            n_results: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of result dicts with 'id', 'content', 'metadata', 'distance'
        """
        # Convert filter_metadata to ChromaDB where clause format
        where_clause = None
        if filter_metadata:
            # Build proper where clause with $and operator
            conditions = [{"key": k, "$eq": v} for k, v in filter_metadata.items()]
            if len(conditions) == 1:
                # Single condition doesn't need $and
                where_clause = {conditions[0]["key"]: {"$eq": conditions[0]["$eq"]}}
            else:
                # Multiple conditions need $and
                where_clause = {"$and": [{k: {"$eq": v}} for k, v in filter_metadata.items()]}
        
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_clause,
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else 0.0,
                })
        
        return formatted_results
    
    def add_error_solution(
        self,
        error_type: str,
        error_message: str,
        solution: str,
        category: str = "general",
    ):
        """Add an error and its solution to the knowledge base
        
        Args:
            error_type: Type of error (e.g., 'syntax', 'simulation', 'openlane')
            error_message: The error message
            solution: Solution to the error
            category: Category (e.g., 'verilog', 'cocotb', 'openlane')
        """
        doc_id = f"error_{category}_{hash(error_message) % 10000}"
        content = f"Error: {error_message}\nSolution: {solution}"
        metadata = {
            "category": category,
            "type": "error_solution",
            "error_type": error_type,
        }
        self.add_document(doc_id, content, metadata)
    
    def find_similar_errors(self, error_message: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Find similar errors and their solutions
        
        Args:
            error_message: Error message to search for
            n_results: Number of results
            
        Returns:
            List of similar errors with solutions
        """
        return self.query(
            query_text=error_message,
            n_results=n_results,
            filter_metadata={"type": "error_solution"}
        )
    
    def get_best_practices(self, category: str) -> List[Dict[str, Any]]:
        """Get best practices for a category
        
        Args:
            category: Category (e.g., 'verilog', 'cocotb', 'openlane')
            
        Returns:
            List of best practice documents
        """
        return self.query(
            query_text=f"{category} best practices",
            n_results=3,
            filter_metadata={"category": category, "type": "best_practices"}
        )
    
    def reset(self):
        """Reset the knowledge base (delete all documents)"""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "ASIC design knowledge base"}
        )
        self._initialize_knowledge_base()
        logger.info("Knowledge base reset")
