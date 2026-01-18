#!/usr/bin/env python3
"""Direct test of OpenLane hardening with PDK fetch"""

import sys
import os

# Add project to path
sys.path.insert(0, '/home/devansh/brainwave')

from asic_agent.agents.hardening_agent import HardeningAgent
from asic_agent.llm_client import GeminiClient
from asic_agent.database.knowledge_base import ASICKnowledgeBase

def main():
    print("=== DIRECT OPENLANE TEST ===\n")
    
    # Initialize with CORRECT model for OpenRouter
    kb = ASICKnowledgeBase('./workspace')
    llm = GeminiClient(
        api_key='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',
        model_name='google/gemini-2.0-flash-001',  # CORRECT MODEL
        provider='openrouter',
        rate_limit_enabled=True,
        rate_limit_delay=4.0
    )
    agent = HardeningAgent(llm, kb, './workspace')
    
    print("Generating OpenLane config...")
    success, config, errors = agent.generate_openlane_config(
        design_name='counter2bit_FINAL',
        rtl_files=['counter2bit_FINAL.v'],
        clock_port='clk',
        clock_period_ns=20.0
    )
    
    if not success:
        print(f"Config generation failed: {errors}")
        return
    
    print(f"Config generated:\n{config}\n")
    
    # Run OpenLane (this will:
    # 1. Fetch Sky130 PDK (~1GB download, 2-5 min)
    # 2. Run synthesis, place & route (~5-15 min for this small design)
    # 3. Generate GDSII file
    print("=== RUNNING REAL OPENLANE DOCKER (THIS WILL TAKE 10-20 MINUTES) ===")
    print("1. Fetching Sky130 PDK (first time only, ~1GB)")
    print("2. Running synthesis with Yosys")
    print("3. Running place & route")
    print("4. Generating GDSII layout\n")
    
    success, log, metrics = agent.run_openlane_flow(timeout=1800)  # 30 min timeout
    
    print("\n=== RESULT ===")
    print(f"Success: {success}")
    print(f"Metrics: {metrics}")
    
    if not success:
        print(f"\nERROR LOG (last 2000 chars):\n{log[-2000:]}")
    else:
        print("\n🎉 SUCCESS! GDSII file generated at workspace/design.gds")
        print(f"Full log length: {len(log)} bytes")
        
        # Show final summary from log
        if "Finishing" in log:
            summary_start = log.rfind("Finishing")
            print(f"\nOpenLane summary:\n{log[summary_start:summary_start+500]}")

if __name__ == '__main__':
    main()
