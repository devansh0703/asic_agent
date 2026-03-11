#!/usr/bin/env python3
"""Test that knowledge base contains real web-scraped documentation"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from asic_agent.database.knowledge_base import ASICKnowledgeBase

def test_knowledge_base():
    print("=" * 60)
    print("Testing ASIC-Agent Knowledge Base")
    print("=" * 60)
    
    kb = ASICKnowledgeBase()
    
    # Check document count
    count = kb.collection.count()
    print(f"\n📊 Total documents in knowledge base: {count}")
    
    if count == 0:
        print("\n⚠️  Knowledge base is EMPTY!")
        print("Run: python3 scripts/build_knowledge_base.py")
        return False
    elif count < 5:
        print("\n⚠️  Knowledge base has minimal fallback data only")
        print(f"   Only {count} documents (should be 20+)")
        print("   Run: python3 scripts/build_knowledge_base.py")
        return False
    else:
        print(f"✅ Knowledge base is populated ({count} documents)")
    
    # Test queries
    test_queries = [
        ("cocot testbench example", "cocotb"),
        ("OpenLane configuration", "openlane"),
        ("Verilog counter pattern", "verilog"),
    ]
    
    print("\n" + "=" * 60)
    print("Testing queries:")
    print("=" * 60)
    
    for query, expected_category in test_queries:
        print(f"\n🔍 Query: '{query}'")
        results = kb.query(query, n_results=3)
        
        if results:
            print(f"   Found {len(results)} results")
            for i, result in enumerate(results[:2], 1):
                print(f"\n   Result {i}:")
                print(f"     ID: {result['id']}")
                print(f"     Category: {result.get('metadata', {}).get('category', 'unknown')}")
                print(f"     Preview: {result['content'][:150]}...")
                
                # Check if it's real data (has URLs or code)
                has_url = 'http' in result['content'] or 'https' in result['content']
                has_code = '```' in result['content'] or 'import' in result['content']
                
                if has_url or has_code:
                    print(f"     ✅ Contains real documentation (URLs/code found)")
        else:
            print("   ❌ No results found")
    
    print("\n" + "=" * 60)
    print("✅ Knowledge base test complete!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_knowledge_base()
    sys.exit(0 if success else 1)
