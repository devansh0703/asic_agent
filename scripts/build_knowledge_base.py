#!/usr/bin/env python3
"""
Build ASIC Knowledge Base from REAL Web Documentation

Scrapes REAL documentation from the web - NO HARDCODED DATA:
- cocotb: Full official documentation (docs.cocotb.org)
- cocotb: GitHub examples and source code
- OpenLane: Complete documentation from GitHub
- Verilog: ChipVerify,ASIC World tutorials (REAL web content)
- Simulators: Verilator, Icarus Verilog docs
- PDK: SkyWater SKY130 documentation

ALL KNOWLEDGE COMES FROM WEB - NOTHING IS HARDCODED
"""

import os
import sys
import json
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from pathlib import Path
import time
import chromadb
from chromadb.config import Settings
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentationScraper:
    """Scrape and process documentation from various REAL web sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        self.documents = []
    
    def scrape_cocotb_docs(self) -> List[Dict[str, Any]]:
        """Scrape COMPLETE cocotb documentation from official site"""
        logger.info("Scraping COMPLETE cocotb documentation from docs.cocotb.org...")
        
        base_url = "https://docs.cocotb.org/en/stable/"
        docs = []
        
        # COMPREHENSIVE cocotb documentation pages - ALL major sections
        pages = {
            "quickstart": "quickstart.html",
            "install": "install.html",
            "building": "building.html",
            "corout ines": "coroutines.html",
            "triggers": "triggers.html",
            "testbench": "writing_testbenches.html",
            "testbench_tools": "testbench_tools.html",
            "library_reference": "library_reference.html",
            "simulator_support": "simulator_support.html",
            "customization": "custom_flows.html",
            "extensions": "extensions.html",
            "logging": "logging.html",
            "troubleshooting": "troubleshooting.html",
            "ping_pong_tun": "examples/ping_tun_tap/ping_pong_tun.html",
            "examples": "examples.html",
        }
        
        for page_name, page_path in pages.items():
            try:
                url = base_url + page_path
                logger.info(f"Fetching {page_name} from {url}")
                
                response = self.session.get(url, timeout=15)
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract main content
                main_content = soup.find('div', {'role': 'main'}) or soup.find('article') or soup.find('div', class_='document')
                if not main_content:
                    main_content = soup.find('body')
                
                if main_content:
                    # Get text content, clean it up
                    text = main_content.get_text(separator='\\n', strip=True)
                    
                    # Extract ALL code examples
                    code_blocks = main_content.find_all('pre')
                    examples = []
                    for block in code_blocks:
                        code = block.get_text(strip=True)
                        if code and len(code) > 10:  # Skip empty blocks
                            examples.append(code)
                    
                    # Combine text and code examples
                    full_content = text
                    if examples:
                        full_content += "\\n\\n=== CODE EXAMPLES ===\\n\\n" + "\\n\\n---\\n\\n".join(examples[:10])
                    
                    docs.append({
                        "id": f"cocotb_docs_{page_name}",
                        "content": full_content[:8000],  # Larger limit for comprehensive docs
                        "metadata": {
                            "category": "cocotb",
                            "type": "official_docs",
                            "source": url,
                            "page": page_name,
                            "code_examples_count": len(examples)
                        }
                    })
                    
                    logger.info(f"Scraped {page_name}: {len(text)} chars, {len(examples)} code examples")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error scraping {page_name}: {e}")
        
        return docs
    
    def scrape_cocotb_examples(self) -> List[Dict[str, Any]]:
        """Scrape cocotb examples from GitHub"""
        logger.info("Fetching cocotb examples from GitHub...")
        
        docs = []
        
        # GitHub API to get example files
        api_url = "https://api.github.com/repos/cocotb/cocotb/contents/examples"
        
        try:
            response = self.session.get(api_url, timeout=10)
            if response.status_code == 200:
                items = response.json()
                
                # Get Python test files from examples
                for item in items[:10]:  # Limit to 10 examples
                    if item['type'] == 'dir':
                        # Get files in this example directory
                        dir_response = self.session.get(item['url'], timeout=10)
                        if dir_response.status_code == 200:
                            files = dir_response.json()
                            
                            for file in files:
                                if file['name'].endswith('.py') and 'test' in file['name']:
                                    # Get file content
                                    file_response = self.session.get(file['download_url'], timeout=10)
                                    if file_response.status_code == 200:
                                        content = file_response.text
                                        
                                        docs.append({
                                            "id": f"cocotb_example_{item['name']}_{file['name']}",
                                            "content": content,
                                            "metadata": {
                                                "category": "cocotb",
                                                "type": "example",
                                                "source": file['html_url'],
                                                "example_name": item['name']
                                            }
                                        })
                                        
                                        logger.info(f"Fetched example: {item['name']}/{file['name']}")
                                        time.sleep(0.5)
        
        except Exception as e:
            logger.error(f"Error fetching GitHub examples: {e}")
        
        return docs
    
    def scrape_openlane_docs(self) -> List[Dict[str, Any]]:
        """Scrape COMPREHENSIVE OpenLane documentation from GitHub"""
        logger.info("Scraping COMPREHENSIVE OpenLane documentation...")
        
        docs = []
        
        # OpenLane GitHub - ALL major documentation
        urls = {
            "readme": "https://raw.githubusercontent.com/The-OpenROAD-Project/OpenLane/master/README.md",
            "configuration": "https://raw.githubusercontent.com/The-OpenROAD-Project/OpenLane/master/configuration/README.md",
            "flow": "https://raw.githubusercontent.com/The-OpenROAD-Project/OpenLane/master/docs/source/flow_overview.md",
            "usage": "https://raw.githubusercontent.com/The-OpenROAD-Project/OpenLane/master/docs/source/usage.md",
            "hardening_macros": "https://raw.githubusercontent.com/The-OpenROAD-Project/OpenLane/master/docs/source/hardening_macros.md",
            "advanced": "https://raw.githubusercontent.com/The-OpenROAD-Project/OpenLane/master/docs/source/advanced_features.md",
        }
        
        for doc_name, url in urls.items():
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    content = response.text
                    
                    docs.append({
                        "id": f"openlane_doc_{doc_name}",
                        "content": content,
                        "metadata": {
                            "category": "openlane",
                            "type": "official_docs",
                            "source": url,
                            "doc_name": doc_name
                        }
                    })
                    
                    logger.info(f"Scraped OpenLane {doc_name}: {len(content)} chars")
                else:
                    logger.warning(f"Failed to fetch {url}: {response.status_code}")
                
                time.sleep(1)
            
            except Exception as e:
                logger.error(f"Error scraping {doc_name}: {e}")
        
        return docs
    
    def scrape_verilog_tutorials(self) -> List[Dict[str, Any]]:
        """Scrape Verilog tutorials from REAL web sources (ChipVerify, ASIC World)"""
        logger.info("Scraping Verilog tutorials from ChipVerify and ASIC World...")
        
        docs = []
        
        # ChipVerify Verilog tutorials (comprehensive)
        chipverify_pages = {
            "basics": "https://www.chipverify.com/verilog/verilog-tutorial",
            "syntax": "https://www.chipverify.com/verilog/verilog-syntax",
            "modules": "https://www.chipverify.com/verilog/verilog-module",
            "always": "https://www.chipverify.com/verilog/verilog-always-block",
            "blocking": "https://www.chipverify.com/verilog/verilog-blocking-nonblocking",
            "assignments": "https://www.chipverify.com/verilog/verilog-assignments",
            "operators": "https://www.chipverify.com/verilog/verilog-operators",
            "concatenation": "https://www.chipverify.com/verilog/verilog-concatenation",
            "counter": "https://www.chipverify.com/verilog/verilog-counter",
            "shift_register": "https://www.chipverify.com/verilog/verilog-shift-register",
            "fsm": "https://www.chipverify.com/verilog/verilog-fsm",
        }
        
        for page_name, url in chipverify_pages.items():
            try:
                logger.info(f"Fetching ChipVerify {page_name}...")
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Remove navigation, ads, scripts
                    for tag in soup.find_all(['nav', 'script', 'style', 'aside', 'footer']):
                        tag.decompose()
                    
                    # Extract main content
                    article = soup.find('article') or soup.find('main') or soup.find('div', class_='content')
                    if article:
                        text = article.get_text(separator='\\n', strip=True)
                        
                        # Extract code blocks
                        code_blocks = article.find_all(['pre', 'code'])
                        examples = [block.get_text(strip=True) for block in code_blocks if len(block.get_text(strip=True)) > 20]
                        
                        full_content = text
                        if examples:
                            full_content += "\\n\\n=== CODE EXAMPLES ===\\n\\n" + "\\n\\n---\\n\\n".join(examples[:5])
                        
                        docs.append({
                            "id": f"verilog_chipverify_{page_name}",
                            "content": full_content[:8000],
                            "metadata": {
                                "category": "verilog",
                                "type": "tutorial",
                                "source": url,
                                "site": "ChipVerify"
                            }
                        })
                        
                        logger.info(f"Scraped ChipVerify {page_name}: {len(text)} chars, {len(examples)} examples")
                else:
                    logger.warning(f"Failed to fetch {url}: {response.status_code}")
                
                time.sleep(1.5)  # Be polite with rate limiting
                
            except Exception as e:
                logger.error(f"Error scraping ChipVerify {page_name}: {e}")
        
        # ASIC World Verilog tutorials
        asicworld_pages = {
            "intro": "http://www.asic-world.com/verilog/intro1.html",
            "syntax": "http://www.asic-world.com/verilog/syntax1.html",
            "operators": "http://www.asic-world.com/verilog/operators1.html",
            "examples": "http://www.asic-world.com/verilog/verilog_one_day1.html",
        }
        
        for page_name, url in asicworld_pages.items():
            try:
                logger.info(f"Fetching ASIC World {page_name}...")
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    text = soup.get_text(separator='\\n', strip=True)
                    code_blocks = soup.find_all('pre')
                    examples = [block.get_text(strip=True) for block in code_blocks if len(block.get_text(strip=True)) > 20]
                    
                    full_content = text[:6000]
                    if examples:
                        full_content += "\\n\\n=== CODE EXAMPLES ===\\n\\n" + "\\n\\n---\\n\\n".join(examples[:5])
                    
                    docs.append({
                        "id": f"verilog_asicworld_{page_name}",
                        "content": full_content,
                        "metadata": {
                            "category": "verilog",
                            "type": "tutorial",
                            "source": url,
                            "site": "ASIC World"
                        }
                    })
                    
                    logger.info(f"Scraped ASIC World {page_name}: {len(examples)} examples")
                
                time.sleep(1.5)
                
            except Exception as e:
                logger.error(f"Error scraping ASIC World {page_name}: {e}")
        
        return docs
    
    def scrape_verilator_docs(self) -> List[Dict[str, Any]]:
        """Scrape Verilator documentation"""
        logger.info("Scraping Verilator documentation...")
        
        docs = []
        
        verilator_urls = {
            "manual": "https://raw.githubusercontent.com/verilator/verilator/master/docs/guide/index.rst",
            "install": "https://raw.githubusercontent.com/verilator/verilator/master/docs/guide/install.rst",
            "connecting": "https://raw.githubusercontent.com/verilator/verilator/master/docs/guide/connecting.rst",
        }
        
        for doc_name, url in verilator_urls.items():
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    content = response.text
                    
                    docs.append({
                        "id": f"verilator_{doc_name}",
                        "content": content[:8000],
                        "metadata": {
                            "category": "simulator",
                            "type": "official_docs",
                            "source": url,
                            "tool": "verilator"
                        }
                    })
                    
                    logger.info(f"Scraped Verilator {doc_name}: {len(content)} chars")
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error scraping Verilator {doc_name}: {e}")
        
        return docs
    
    def scrape_iverilog_docs(self) -> List[Dict[str, Any]]:
        """Scrape Icarus Verilog documentation"""
        logger.info("Scraping Icarus Verilog documentation...")
        
        docs = []
        
        # Icarus Verilog docs
        iverilog_urls = {
            "getting_started": "https://raw.githubusercontent.com/steveicarus/iverilog/master/README.txt",
        }
        
        for doc_name, url in iverilog_urls.items():
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    content = response.text
                    
                    docs.append({
                        "id": f"iverilog_{doc_name}",
                        "content": content[:8000],
                        "metadata": {
                            "category": "simulator",
                            "type": "official_docs",
                            "source": url,
                            "tool": "iverilog"
                        }
                    })
                    
                    logger.info(f"Scraped Icarus Verilog {doc_name}: {len(content)} chars")
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error scraping Icarus Verilog {doc_name}: {e}")
        
        return docs
    
    def scrape_skywater_pdk_docs(self) -> List[Dict[str, Any]]:
        """Scrape SkyWater SKY130 PDK documentation"""
        logger.info("Scraping SkyWater SKY130 PDK documentation...")
        
        docs = []
        
        skywater_urls = {
            "readme": "https://raw.githubusercontent.com/google/skywater-pdk/main/README.md",
            "rules": "https://raw.githubusercontent.com/google/skywater-pdk/main/docs/rules.rst",
        }
        
        for doc_name, url in skywater_urls.items():
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    content = response.text
                    
                    docs.append({
                        "id": f"skywater_pdk_{doc_name}",
                        "content": content[:8000],
                        "metadata": {
                            "category": "pdk",
                            "type": "official_docs",
                            "source": url,
                            "pdk": "sky130"
                        }
                    })
                    
                    logger.info(f"Scraped SkyWater PDK {doc_name}: {len(content)} chars")
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error scraping SkyWater PDK {doc_name}: {e}")
        
        return docs
    
    def scrape_all(self) -> List[Dict[str, Any]]:
        """Scrape ALL documentation from REAL web sources - NO HARDCODED DATA"""
        all_docs = []
        
        logger.info("\\n" + "=" * 60)
        logger.info("SCRAPING REAL DOCUMENTATION FROM WEB")
        logger.info("=" * 60)
        
        # cocotb - comprehensive official docs
        all_docs.extend(self.scrape_cocotb_docs())
        
        # cocotb - GitHub examples
        all_docs.extend(self.scrape_cocotb_examples())
        
        # OpenLane - full documentation
        all_docs.extend(self.scrape_openlane_docs())
        
        # Verilog - tutorial sites (ChipVerify, ASIC World)
        all_docs.extend(self.scrape_verilog_tutorials())
        
        # Verilator - simulator docs
        all_docs.extend(self.scrape_verilator_docs())
        
        # Icarus Verilog - simulator docs
        all_docs.extend(self.scrape_iverilog_docs())
        
        # SkyWater PDK - process design kit docs
        all_docs.extend(self.scrape_skywater_pdk_docs())
        
        logger.info("\\n" + "=" * 60)
        logger.info(f"✓ Total documents scraped from web: {len(all_docs)}")
        logger.info("=" * 60)
        
        return all_docs


def build_knowledge_base(output_dir: str = "./chroma_db"):
    """Build knowledge base from scraped documentation"""
    
    logger.info("=" * 60)
    logger.info("Building ASIC Knowledge Base from Real Documentation")
    logger.info("=" * 60)
    
    # Scrape documentation
    scraper = DocumentationScraper()
    documents = scraper.scrape_all()
    
    if not documents:
        logger.error("No documents collected! Check network connection.")
        return False
    
    # Initialize ChromaDB directly
    logger.info(f"\\nInitializing knowledge base at {output_dir}...")
    
    # Remove old database
    if os.path.exists(output_dir):
        import shutil
        logger.info("Removing old knowledge base...")
        shutil.rmtree(output_dir)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create ChromaDB client
    client = chromadb.PersistentClient(
        path=output_dir,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
        )
    )
    
    # Create collection
    collection = client.create_collection(
        name="asic_knowledge",
        metadata={"description": "ASIC design knowledge base from real documentation"}
    )
    
    # Add documents to knowledge base
    logger.info(f"\\nAdding {len(documents)} documents to knowledge base...")
    
    batch_size = 10
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        
        ids = [doc["id"] for doc in batch]
        contents = [doc["content"] for doc in batch]
        metadatas = [doc.get("metadata", {}) for doc in batch]
        
        collection.add(
            ids=ids,
            documents=contents,
            metadatas=metadatas
        )
        
        logger.info(f"Added documents {i+1}-{min(i+batch_size, len(documents))}")
    
    logger.info("\\n" + "=" * 60)
    logger.info(f"✓ Knowledge base built successfully!")
    logger.info(f"  Total documents: {len(documents)}")
    logger.info(f"  Location: {output_dir}")
    logger.info("=" * 60)
    
    # Test query
    logger.info("\\nTesting knowledge base with sample query...")
    results = collection.query(
        query_texts=["cocotb testbench example"],
        n_results=3
    )
    
    if results and results['ids']:
        logger.info(f"Query returned {len(results['ids'][0])} results")
        for i, (doc_id, doc_text) in enumerate(zip(results['ids'][0][:2], results['documents'][0][:2]), 1):
            logger.info(f"\\nResult {i}:")
            logger.info(f"  ID: {doc_id}")
            logger.info(f"  Content preview: {doc_text[:200]}...")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build ASIC knowledge base from real web documentation - NO HARDCODED DATA")
    parser.add_argument("--output", "-o", default="./chroma_db", 
                       help="Output directory for knowledge base")
    args = parser.parse_args()
    
    success = build_knowledge_base(args.output)
    sys.exit(0 if success else 1)
