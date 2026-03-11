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
            doc_count = self.collection.count()
            logger.info(f"Loaded existing collection: {collection_name} ({doc_count} documents)")
            
            # Check if collection is empty and needs initialization
            if doc_count == 0:
                logger.warning("Knowledge base is empty! Run 'python scripts/build_knowledge_base.py' to populate with real documentation.")
                self._initialize_minimal_knowledge()
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "ASIC design knowledge base"}
            )
            logger.info(f"Created new collection: {collection_name}")
            logger.warning("Knowledge base created but empty. Run 'python scripts/build_knowledge_base.py' to populate with real documentation.")
            self._initialize_minimal_knowledge()
    
    def _initialize_minimal_knowledge(self):
        """Initialize with minimal critical knowledge (fallback only - use build_knowledge_base.py for full data)"""
        logger.info("Initializing minimal fallback knowledge (NOT comprehensive - build full database with scripts/build_knowledge_base.py)")
        
        # Minimal critical cocotb 2.0+ API rules
        minimal_docs = [
            {
                "id": "cocotb_critical_api",
                "content": """CRITICAL cocotb 2.0+ API Rules:
1. NEVER import 'cocotb.log' - doesn't exist in 2.0+
2. Use Python's standard logging: import logging; log = logging.getLogger(__name__)
3. Convert signal values: int(dut.signal.value)
4. After every await RisingEdge(dut.clk), add await Timer(1, units="ns")
5. Counter timing: after reset release, first clock makes count=1 (not 0!)

Example:
```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import logging

log = logging.getLogger(__name__)

@cocotb.test()
async def test_example(dut):
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # CRITICAL
    
    dut.rst.value = 0
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")  # CRITICAL
```

WARNING: This is minimal fallback data. Build full knowledge base with:
python scripts/build_knowledge_base.py
""",
                "metadata": {"category": "cocotb", "type": "critical", "minimal": True}
            }
        ]
        
        for doc in minimal_docs:
            try:
                self.collection.add(
                    ids=[doc["id"]],
                    documents=[doc["content"]],
                    metadatas=[doc["metadata"]]
                )
            except Exception as e:
                logger.error(f"Failed to add minimal doc: {e}")
    
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
        logger.warning("Knowledge base reset. Run 'python scripts/build_knowledge_base.py' to populate from web sources.")
        logger.info("Knowledge base reset")
