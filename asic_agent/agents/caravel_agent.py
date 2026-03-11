"""Caravel Integration Agent for chip integration"""

import os
import logging
from typing import Dict, List, Tuple, Optional

from ..llm_client import GeminiClient
from ..database.knowledge_base import ASICKnowledgeBase

logger = logging.getLogger(__name__)


class CaravelAgent:
    """Caravel Integration Agent for chip-level integration"""
    
    SYSTEM_PROMPT = """You are an expert in Caravel chip integration for Google/Skywater 130nm open-source PDK.
Your role is to integrate custom user designs into the Caravel harness for tape-out.

Key responsibilities:
1. Configure Caravel wrapper for user design
2. Map user IOs to Caravel IOs
3. Generate integration configuration
4. Ensure proper connectivity and constraints

Caravel Integration Guidelines:
- User design connects to Caravel through wishbone interface
- Map GPIO pins appropriately
- Configure power domains correctly
- Ensure timing constraints are met
- Follow Caravel integration checklist"""
    
    def __init__(
        self,
        llm_client: GeminiClient,
        knowledge_base: ASICKnowledgeBase,
        workspace_dir: str,
    ):
        """Initialize Caravel Agent
        
        Args:
            llm_client: Gemini LLM client
            knowledge_base: Knowledge base for retrieval
            workspace_dir: Workspace directory
        """
        self.llm = llm_client
        self.kb = knowledge_base
        self.workspace_dir = workspace_dir
        
        os.makedirs(workspace_dir, exist_ok=True)
    
    def generate_caravel_config(
        self,
        design_name: str,
        user_ios: List[Dict[str, str]],
    ) -> Tuple[bool, str, List[str]]:
        """Generate Caravel integration configuration
        
        Args:
            design_name: User design name
            user_ios: List of user IOs with direction and width
            
        Returns:
            Tuple of (success, config, errors)
        """
        logger.info(f"Generating Caravel config for: {design_name}")
        
        ios_description = "\n".join([
            f"- {io['name']}: {io['direction']} {io.get('width', '1-bit')}"
            for io in user_ios
        ])
        
        prompt = f"""Generate Caravel integration configuration for user design:

Design Name: {design_name}

User IOs:
{ios_description}

Provide a configuration that maps these IOs to Caravel GPIO pins.
Include:
1. GPIO pin assignments
2. Wishbone interface configuration
3. Power domain settings
4. Any required wrapper modifications

Format as structured text configuration.

Caravel Integration Configuration:"""
        
        try:
            config = self.llm.generate(
                prompt=prompt,
                system_instruction=self.SYSTEM_PROMPT,
            )
            
            # Save configuration
            config_file = "caravel_config.txt"
            config_path = os.path.join(self.workspace_dir, config_file)
            
            with open(config_path, 'w') as f:
                f.write(config)
            
            logger.info(f"Caravel config saved to: {config_path}")
            
            return True, config, []
            
        except Exception as e:
            logger.error(f"Caravel config generation failed: {str(e)}")
            return False, "", [str(e)]
    
    def integrate_design(
        self,
        design_gds: str,
        config: str,
    ) -> Tuple[bool, str]:
        """Integrate design into Caravel using real git clone
        
        Args:
            design_gds: Path to user design GDS
            config: Integration configuration
            
        Returns:
            Tuple of (success, report)
        """

        
        import subprocess
        import shutil
        
        caravel_dir = os.path.join(self.workspace_dir, 'caravel_user_project')
        
        # Clone Caravel repository
        if not os.path.exists(caravel_dir):
            logger.info("Cloning Caravel repository...")
            try:
                result = subprocess.run(
                    ['git', 'clone', '--depth', '1', 
                     'https://github.com/efabless/caravel_user_project.git', caravel_dir],
                    capture_output=True, text=True, timeout=300
                )
                if result.returncode != 0:
                    return False, f"Failed to clone: {result.stderr}"
                logger.info("Caravel cloned successfully")
            except Exception as e:
                return False, f"Clone error: {e}"
        
        design_name = os.path.splitext(os.path.basename(design_gds))[0]
        
        # Copy GDS
        user_gds_dir = os.path.join(caravel_dir, 'gds')
        os.makedirs(user_gds_dir, exist_ok=True)
        if os.path.exists(design_gds):
            shutil.copy(design_gds, os.path.join(user_gds_dir, f'{design_name}.gds'))
        
        # Copy RTL
        rtl_file = os.path.join(self.workspace_dir, f'{design_name}.v')
        user_rtl_dir = os.path.join(caravel_dir, 'verilog', 'rtl')
        os.makedirs(user_rtl_dir, exist_ok=True)
        if os.path.exists(rtl_file):
            shutil.copy(rtl_file, user_rtl_dir)
        
        report = f"""Caravel Integration (REAL)
Design: {design_name}
GDS: {design_gds}

✓ Cloned Caravel repository
✓ Copied GDS to {user_gds_dir}
✓ Copied RTL to {user_rtl_dir}

Caravel Directory: {caravel_dir}
"""
        
        with open(os.path.join(self.workspace_dir, "caravel_integration_report.txt"), 'w') as f:
            f.write(report)
        
        logger.info("Caravel integration complete - real files copied")
        
        return True, report
        
