#!/usr/bin/env python3
"""
ASIC-Agent CLI - Main entry point for ASIC design automation
"""

import argparse
import logging
import sys
import os
from pathlib import Path

from asic_agent.config import Config
from asic_agent.workflows.orchestrator import ASICOrchestrator


def setup_logging(verbose: bool = False):
    """Setup logging configuration
    
    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('asic_agent.log'),
        ]
    )


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='ASIC-Agent: Autonomous Multi-Agent System for ASIC Design',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Design a simple counter
  python main.py "Design an 8-bit up counter with reset" --name counter8

  # Design with custom workspace
  python main.py "Design a UART transmitter" --name uart_tx --workspace ./my_workspace

  # Load specification from file
  python main.py --spec-file design_spec.txt --name my_design

Environment Variables:
  MISTRAL_API_KEY       Mistral API key (required when using Mistral)
  OPENROUTER_API_KEY    OpenRouter API key (required when using OpenRouter)

Get API keys from:
  Mistral: https://console.mistral.ai/
  OpenRouter: https://openrouter.ai/keys
"""
    )
    
    # Input specification
    spec_group = parser.add_mutually_exclusive_group(required=True)
    spec_group.add_argument(
        'specification',
        nargs='?',
        help='Design specification as a string'
    )
    spec_group.add_argument(
        '--spec-file',
        type=str,
        help='File containing design specification'
    )
    
    # Design configuration
    parser.add_argument(
        '--name',
        type=str,
        required=True,
        help='Design name (used for module name)'
    )
    
    parser.add_argument(
        '--workspace',
        type=str,
        default='./workspace',
        help='Workspace directory (default: ./workspace)'
    )
    
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=5,
        help='Maximum iterations per stage (default: 5)'
    )
    
    # API configuration
    parser.add_argument(
        '--provider',
        type=str,
        choices=['mistral', 'openrouter'],
        default='openrouter',
        help='LLM provider (default: openrouter for Gemini)'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        help='API key (or set MISTRAL_API_KEY/OPENROUTER_API_KEY env var)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help='Model name (optional, uses provider default)'
    )
    
    # Rate limiting configuration
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=6.0,
        help='Minimum seconds between API calls (default: 6.0 = 10 req/min for Gemini free tier)'
    )
    
    parser.add_argument(
        '--no-rate-limit',
        action='store_true',
        help='Disable rate limiting (not recommended for free tier)'
    )
    
    # Database configuration
    parser.add_argument(
        '--chroma-dir',
        type=str,
        default='./chroma_db',
        help='ChromaDB persist directory (default: ./chroma_db)'
    )
    
    # Workflow control
    parser.add_argument(
        '--skip-verification',
        action='store_true',
        help='Skip verification stage'
    )
    
    parser.add_argument(
        '--skip-hardening',
        action='store_true',
        help='Skip hardening stage'
    )
    
    parser.add_argument(
        '--skip-integration',
        action='store_true',
        help='Skip Caravel integration stage'
    )
    
    # Output control
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output (errors only)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose and not args.quiet)
    logger = logging.getLogger(__name__)
    
    # Print banner
    if not args.quiet:
        provider_name = "Mistral" if args.provider == "mistral" else "OpenRouter/Gemini"
        print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                         ASIC-Agent                            ║
║         Autonomous Multi-Agent System for ASIC Design         ║
║                                                               ║
║  Powered by: {provider_name} + ChromaDB + LangGraph{' ' * (23 - len(provider_name))}║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    # Load specification
    if args.spec_file:
        try:
            with open(args.spec_file, 'r') as f:
                specification = f.read()
            logger.info(f"Loaded specification from: {args.spec_file}")
        except Exception as e:
            logger.error(f"Failed to read spec file: {e}")
            sys.exit(1)
    else:
        specification = args.specification
    
    # Validate API key
    if args.provider == 'mistral':
        api_key = args.api_key or os.getenv('MISTRAL_API_KEY')
        env_var = 'MISTRAL_API_KEY'
        key_url = 'https://console.mistral.ai/'
    else:
        api_key = args.api_key or os.getenv('OPENROUTER_API_KEY')
        env_var = 'OPENROUTER_API_KEY'
        key_url = 'https://openrouter.ai/keys'
    
    if not api_key:
        logger.error(f"{env_var} not set. Get your key from {key_url}")
        sys.exit(1)
    
    # Set API key in environment
    os.environ[env_var] = api_key
    
    try:
        # Create configuration
        config_params = {
            'llm_provider': args.provider,
            'workspace_dir': args.workspace,
            'chroma_persist_directory': args.chroma_dir,
            'max_iterations': args.max_iterations,
            'max_verification_iterations': args.max_iterations,
            'max_hardening_iterations': args.max_iterations,
            'rate_limit_enabled': not args.no_rate_limit,
            'rate_limit_delay_seconds': args.rate_limit,
        }
        
        if args.provider == 'mistral':
            config_params['mistral_api_key'] = api_key
            if args.model:
                config_params['mistral_model'] = args.model
        else:
            config_params['openrouter_api_key'] = api_key
            if args.model:
                config_params['openrouter_model'] = args.model
        
        config = Config(**config_params)
        
        # Log configuration
        model = config.mistral_model if args.provider == 'mistral' else config.openrouter_model
        rate_info = f", Rate Limit: {args.rate_limit}s ({60/args.rate_limit:.1f} req/min)" if not args.no_rate_limit else ", No Rate Limit"
        logger.info(f"Configuration: Provider={args.provider}, Model={model}, Workspace={config.workspace_dir}{rate_info}")
        
        # Create orchestrator
        orchestrator = ASICOrchestrator(config)
        
        logger.info(f"Starting design workflow for: {args.name}")
        logger.info(f"Specification: {specification[:100]}...")
        
        # Run workflow
        final_state = orchestrator.run(
            specification=specification,
            design_name=args.name,
        )
        
        # Print results
        if not args.quiet:
            print("\n" + "="*60)
            print("WORKFLOW RESULTS")
            print("="*60)
            print(f"Design Name: {final_state.design_name}")
            print(f"Final Stage: {final_state.current_stage}")
            print(f"Workspace: {final_state.workspace_dir}")
            
            if final_state.rtl_files:
                print(f"\nRTL Files Generated:")
                for f in final_state.rtl_files:
                    print(f"  ✓ {f}")
            
            if final_state.linting_passed:
                print(f"\n✓ Linting: PASSED")
            elif final_state.linting_errors:
                print(f"\n✗ Linting: FAILED ({len(final_state.linting_errors)} errors)")
            
            if final_state.verification_passed:
                print(f"✓ Verification: PASSED (iterations: {final_state.verification_iterations})")
            elif final_state.verification_errors:
                print(f"✗ Verification: FAILED")
            
            if final_state.hardening_passed:
                print(f"✓ Hardening: PASSED")
                if final_state.gds_file:
                    print(f"  GDS: {final_state.gds_file}")
            elif final_state.hardening_errors:
                print(f"✗ Hardening: FAILED")
            
            if final_state.integration_passed:
                print(f"✓ Integration: PASSED")
            
            if final_state.errors:
                print(f"\nErrors Encountered: {len(final_state.errors)}")
                for err in final_state.errors[:5]:
                    print(f"  - {err}")
            
            print("\n" + "="*60)
            
            if final_state.current_stage == 'complete':
                print("\n🎉 SUCCESS! Design flow completed successfully!")
                print(f"\nOutput files in: {final_state.workspace_dir}")
            else:
                print(f"\n⚠️  Workflow ended at stage: {final_state.current_stage}")
        
        # Exit code based on success
        if final_state.current_stage == 'complete':
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
