"""Hardening Agent for OpenLane physical design"""

import os
import json
import logging
import subprocess
import shutil
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from ..llm_client import GeminiClient
from ..database.knowledge_base import ASICKnowledgeBase

logger = logging.getLogger(__name__)


class HardeningAgent:
    """Hardening Agent for OpenLane physical design flow"""
    
    SYSTEM_PROMPT = """You are an expert ASIC physical design engineer specializing in OpenLane.
Your role is to configure and optimize the OpenLane flow for digital designs.

Key responsibilities:
1. Generate OpenLane configuration files
2. Optimize for timing, power, and area (PPA)
3. Debug OpenLane flow errors
4. Adjust parameters based on design requirements
5. Ensure successful RTL-to-GDSII flow

OpenLane Configuration Best Practices:
- Set DESIGN_NAME to top module name
- Specify all VERILOG_FILES paths
- Define CLOCK_PORT and CLOCK_PERIOD correctly
- Set appropriate DIE_AREA for design size
- Configure PL_TARGET_DENSITY (0.5-0.7 typical)
- Use SYNTH_STRATEGY AREA or DELAY based on goals
- Enable proper power grid with FP_PDN parameters
- Set realistic clock period (20ns = 50MHz is safe start)

Generate configuration in JSON format for OpenLane 2."""
    
    def __init__(
        self,
        llm_client: GeminiClient,
        knowledge_base: ASICKnowledgeBase,
        workspace_dir: str,
    ):
        """Initialize Hardening Agent
        
        Args:
            llm_client: Gemini LLM client
            knowledge_base: Knowledge base for retrieval
            workspace_dir: Workspace directory
        """
        self.llm = llm_client
        self.kb = knowledge_base
        self.workspace_dir = workspace_dir
        
        os.makedirs(workspace_dir, exist_ok=True)
    
    def generate_openlane_config(
        self,
        design_name: str,
        rtl_files: List[str],
        clock_port: str = "clk",
        clock_period_ns: float = 20.0,
        die_size_um: Tuple[float, float] = (200.0, 200.0),
    ) -> Tuple[bool, str, List[str]]:
        """Generate OpenLane configuration file
        
        Args:
            design_name: Top module name
            rtl_files: List of RTL files
            clock_port: Clock signal name
            clock_period_ns: Clock period in nanoseconds
            die_size_um: Die size (width, height) in micrometers
            
        Returns:
            Tuple of (success, config_json, errors)
        """
        logger.info(f"Generating OpenLane config for: {design_name}")
        
        # Query knowledge base for OpenLane configuration
        openlane_docs = self.kb.query("OpenLane configuration", n_results=3)
        docs_text = "\n".join([doc['content'] for doc in openlane_docs])
        
        # Create prompt
        prompt = f"""Generate an OpenLane 2 configuration file for this design:

Design Name: {design_name}
RTL Files: {', '.join(rtl_files)}
Clock Port: {clock_port}
Clock Period: {clock_period_ns} ns ({1000/clock_period_ns:.1f} MHz)
Die Size: {die_size_um[0]} x {die_size_um[1]} micrometers

OpenLane Reference:
{docs_text}

Generate a complete OpenLane configuration in JSON format with:
1. DESIGN_NAME
2. VERILOG_FILES (as list)
3. CLOCK_PORT
4. CLOCK_PERIOD
5. DIE_AREA (format: "0 0 width height")
6. FP_SIZING (use "absolute")
7. PL_TARGET_DENSITY (0.6 is good default)
8. SYNTH_STRATEGY (use "DELAY 0" for balanced)
9. FP_PDN_VPITCH and FP_PDN_HPITCH (use 25 for both)
10. Any other important parameters

Provide ONLY the JSON configuration, no explanations.

Configuration JSON:"""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                system_instruction=self.SYSTEM_PROMPT,
            )
            
            # Clean and parse JSON
            config_json = self._extract_json(response)
            
            if not config_json:
                # Generate default config
                config_json = self._generate_default_config(
                    design_name, rtl_files, clock_port, clock_period_ns, die_size_um
                )
            
            # Save config file
            config_file = "config.json"
            config_path = os.path.join(self.workspace_dir, config_file)
            
            with open(config_path, 'w') as f:
                f.write(config_json)
            
            logger.info(f"OpenLane config saved to: {config_path}")
            
            return True, config_json, []
            
        except Exception as e:
            logger.error(f"Config generation failed: {str(e)}")
            # Fallback to default config
            config_json = self._generate_default_config(
                design_name, rtl_files, clock_port, clock_period_ns, die_size_um
            )
            return True, config_json, []
    
    def run_openlane_flow(
        self,
        config_file: str = "config.json",
        timeout: int = 3600,
    ) -> Tuple[bool, str, Dict[str, any]]:
        """Run OpenLane flow (simulation - actual tool not required for demo)
        
        Args:
            config_file: Configuration file name
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (success, log, metrics)
        """
        logger.info("Running REAL OpenLane flow via Docker...")
        
        config_path = os.path.join(self.workspace_dir, config_file)
        if not os.path.exists(config_path):
            return False, f"Config not found: {config_path}", {}
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        design_name = config.get('DESIGN_NAME', 'design')
        openlane_dir = os.path.join(self.workspace_dir, 'openlane_run')
        design_dir = os.path.join(openlane_dir, 'designs', design_name)
        src_dir = os.path.join(design_dir, 'src')
        os.makedirs(src_dir, exist_ok=True)
        
        # Copy RTL and update paths in config
        updated_verilog_files = []
        for vfile in config.get('VERILOG_FILES', []):
            src = os.path.join(self.workspace_dir, vfile)
            if os.path.exists(src):
                shutil.copy(src, src_dir)
                # Update path to point to src/ directory
                updated_verilog_files.append(f"dir::src/{os.path.basename(vfile)}")
        
        # Update config with correct paths
        config['VERILOG_FILES'] = updated_verilog_files
        
        # Write updated config
        with open(os.path.join(design_dir, 'config.json'), 'w') as f:
            json.dump(config, f, indent=2)
        
        # Create PDK directory if it doesn't exist
        pdk_root = os.path.expanduser('~/.volare')
        os.makedirs(pdk_root, exist_ok=True)
        
        # First ensure PDK is installed (one-time setup)
        logger.info("Checking PDK installation...")
        pdk_check_cmd = ['docker', 'run', '--rm',
                         '-v', f'{pdk_root}:/root/.volare',
                         'efabless/openlane:latest',
                         'bash', '-c', 'volare enable --pdk sky130 bdc9412b3e468c102d01b7cf6337be06ec6e9c9a || volare fetch sky130 bdc9412b3e468c102d01b7cf6337be06ec6e9c9a']
        
        try:
            pdk_result = subprocess.run(pdk_check_cmd, capture_output=True, text=True, timeout=300)
            logger.info(f"PDK setup: {pdk_result.stdout}")
        except Exception as e:
            logger.warning(f"PDK setup issue (may already be installed): {e}")
        
        # Run OpenLane Docker with PDK mounted (use -overwrite to replace existing runs)
        cmd = ['docker', 'run', '--rm', 
               '-v', f'{os.path.abspath(design_dir)}:/openlane',
               '-v', f'{pdk_root}:/root/.volare',
               'efabless/openlane:latest', 
               'flow.tcl', '-tag', 'run1', '-overwrite']
        
        try:
            logger.info(f"Executing OpenLane for {design_name}...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            log = result.stdout + result.stderr
            success = result.returncode == 0
            metrics = {'success': success}
            
            # Log the output for debugging
            logger.info(f"OpenLane output:\n{log}")
            
            if success:
                gds = os.path.join(design_dir, 'runs', 'run1', 'results', 'final', 'gds', f'{design_name}.gds')
                if os.path.exists(gds):
                    shutil.copy(gds, os.path.join(self.workspace_dir, 'design.gds'))
                    metrics['gds_file'] = 'design.gds'
            
            return success, log, metrics
        except subprocess.TimeoutExpired:
            return False, f"Timeout after {timeout}s", {}
        except FileNotFoundError:
            return False, "Docker not installed", {}
        except Exception as e:
            return False, str(e), {}
    
    def debug_openlane_errors(
        self,
        error_log: str,
        config: str,
    ) -> Tuple[bool, str, str]:
        """Debug OpenLane errors and suggest fixes
        
        Args:
            error_log: Error log from OpenLane
            config: Current configuration
            
        Returns:
            Tuple of (success, analysis, fixed_config)
        """
        logger.info("Debugging OpenLane errors...")
        
        # Query knowledge base for similar errors
        error_solutions = self.kb.query(error_log, n_results=3)
        solutions_text = "\n".join([s['content'] for s in error_solutions])
        
        prompt = f"""OpenLane Flow Error Debug

Current Configuration:
{config}

Error Log:
{error_log}

Similar Error Solutions:
{solutions_text}

Analyze the error and provide:
1. Root cause analysis
2. Recommended fixes
3. Updated configuration (in JSON format between ===CONFIG_START=== and ===CONFIG_END===)

Analysis and solution:"""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                system_instruction="You are an expert at debugging OpenLane flows. Provide precise analysis and fixes.",
            )
            
            # Extract analysis and fixed config
            analysis = response
            fixed_config = config
            
            if "===CONFIG_START===" in response:
                config_parts = response.split("===CONFIG_START===")[1].split("===CONFIG_END===")
                if config_parts:
                    fixed_config = self._extract_json(config_parts[0])
                    if not fixed_config:
                        fixed_config = config
            
            return True, analysis, fixed_config
            
        except Exception as e:
            logger.error(f"Debug failed: {str(e)}")
            return False, str(e), config
    
    def optimize_ppa(
        self,
        current_config: str,
        current_metrics: Dict[str, float],
        optimization_goal: str = "balanced",
    ) -> Tuple[bool, str]:
        """Optimize configuration for PPA (Power, Performance, Area)
        
        Args:
            current_config: Current configuration JSON
            current_metrics: Current PPA metrics
            optimization_goal: "performance", "area", "power", or "balanced"
            
        Returns:
            Tuple of (success, optimized_config)
        """
        logger.info(f"Optimizing for: {optimization_goal}")
        
        prompt = f"""OpenLane PPA Optimization

Current Configuration:
{current_config}

Current Metrics:
- Area: {current_metrics.get('area_um2', 0)} um²
- Worst Slack: {current_metrics.get('worst_slack_ns', 0)} ns
- Power: {current_metrics.get('power_mw', 0)} mW
- Utilization: {current_metrics.get('utilization', 0)}

Optimization Goal: {optimization_goal}

Suggest configuration changes to optimize for {optimization_goal}.

For performance optimization:
- Reduce clock period if slack allows
- Use SYNTH_STRATEGY DELAY
- Increase area if needed

For area optimization:
- Increase clock period
- Use SYNTH_STRATEGY AREA
- Increase target density

For power optimization:
- Increase clock period
- Reduce switching activity
- Optimize clock tree

Provide optimized configuration in JSON format between ===CONFIG_START=== and ===CONFIG_END===.

Optimization analysis and configuration:"""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                system_instruction=self.SYSTEM_PROMPT,
            )
            
            # Extract optimized config
            optimized_config = current_config
            
            if "===CONFIG_START===" in response:
                config_parts = response.split("===CONFIG_START===")[1].split("===CONFIG_END===")
                if config_parts:
                    extracted = self._extract_json(config_parts[0])
                    if extracted:
                        optimized_config = extracted
            
            return True, optimized_config
            
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")
            return False, current_config
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text
        
        Args:
            text: Text containing JSON
            
        Returns:
            JSON string or empty string
        """
        # Remove markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 3:
                text = parts[1]
        
        text = text.strip()
        
        # Try to parse and re-serialize to ensure valid JSON
        try:
            data = json.loads(text)
            return json.dumps(data, indent=2)
        except:
            return ""
    
    def _generate_default_config(
        self,
        design_name: str,
        rtl_files: List[str],
        clock_port: str,
        clock_period_ns: float,
        die_size_um: Tuple[float, float],
    ) -> str:
        """Generate default OpenLane configuration
        
        Returns:
            JSON configuration string
        """
        config = {
            "DESIGN_NAME": design_name,
            "VERILOG_FILES": rtl_files,
            "CLOCK_PORT": clock_port,
            "CLOCK_PERIOD": clock_period_ns,
            "DIE_AREA": f"0 0 {die_size_um[0]} {die_size_um[1]}",
            "FP_SIZING": "absolute",
            "PL_TARGET_DENSITY": 0.6,
            "SYNTH_STRATEGY": "DELAY 0",
            "FP_PDN_VPITCH": 25,
            "FP_PDN_HPITCH": 25,
            "GLB_RT_ADJUSTMENT": 0.1,
        }
        
        return json.dumps(config, indent=2)
