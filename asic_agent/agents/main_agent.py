"""Main Agent for RTL generation and design coordination"""

import os
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from ..llm_client import GeminiClient
from ..database.knowledge_base import ASICKnowledgeBase
from ..tools.hardware_tools import HardwareTools

logger = logging.getLogger(__name__)


class MainAgent:
    """Main Agent responsible for RTL generation and design coordination"""
    
    SYSTEM_PROMPT = """You are an expert digital hardware designer specializing in Verilog RTL design.
Your role is to generate high-quality, synthesizable Verilog code from natural language specifications.

Key responsibilities:
1. Analyze design specifications and extract requirements
2. Generate complete, correct Verilog RTL code
3. Follow Verilog best practices and coding standards
4. Create modular, well-documented designs
5. Ensure code is synthesizable and lint-clean

Verilog Best Practices:
- Use synchronous logic with proper reset
- Avoid combinational loops and latches
- Use non-blocking assignments (<=) for sequential logic
- Use blocking assignments (=) for combinational logic
- Declare all signals explicitly (input, output, reg, wire)
- Add meaningful comments
- Use parameters for configurability
- Follow consistent naming conventions

Generate ONLY valid Verilog code. Do not include markdown code blocks or explanations mixed with code.
Provide clean, ready-to-use Verilog that can be directly saved to a .v file."""
    
    def __init__(
        self,
        llm_client: GeminiClient,
        knowledge_base: ASICKnowledgeBase,
        hardware_tools: HardwareTools,
        workspace_dir: str,
    ):
        """Initialize Main Agent
        
        Args:
            llm_client: Gemini LLM client
            knowledge_base: Knowledge base for retrieval
            hardware_tools: Hardware tools wrapper
            workspace_dir: Workspace directory
        """
        self.llm = llm_client
        self.kb = knowledge_base
        self.tools = hardware_tools
        self.workspace_dir = workspace_dir
        
        os.makedirs(workspace_dir, exist_ok=True)
    
    def generate_rtl(
        self,
        specification: str,
        design_name: str,
    ) -> Tuple[bool, Dict[str, str], List[str]]:
        """Generate RTL code from specification
        
        Args:
            specification: Natural language design specification
            design_name: Name of the design/module
            
        Returns:
            Tuple of (success, {filename: code}, errors)
        """
        logger.info(f"Generating RTL for design: {design_name}")
        
        # Query knowledge base for Verilog best practices
        best_practices = self.kb.get_best_practices("verilog")
        best_practices_text = "\n".join([bp['content'] for bp in best_practices])
        
        # Create prompt for RTL generation
        prompt = f"""Design Specification:
{specification}

Module Name: {design_name}

Generate a complete Verilog module implementing this specification.

Best Practices Reference:
{best_practices_text}

Requirements:
1. Module should be named '{design_name}'
2. Include all necessary input/output ports
3. Add proper reset logic
4. Use non-blocking assignments for sequential logic
5. Add comments explaining the design
6. Ensure code is synthesizable
7. Do NOT use markdown code blocks - provide raw Verilog code only

Generate the Verilog code:"""
        
        try:
            # Generate RTL code
            rtl_code = self.llm.generate(
                prompt=prompt,
                system_instruction=self.SYSTEM_PROMPT,
            )
            
            # Clean up code (remove markdown code blocks if present)
            rtl_code = self._clean_code(rtl_code)
            
            if not rtl_code:
                return False, {}, ["Failed to generate RTL code"]
            
            # Save to file
            filename = f"{design_name}.v"
            filepath = os.path.join(self.workspace_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(rtl_code)
            
            logger.info(f"Generated RTL saved to: {filepath}")
            
            return True, {filename: rtl_code}, []
            
        except Exception as e:
            logger.error(f"RTL generation failed: {str(e)}")
            return False, {}, [str(e)]
    
    def lint_rtl(
        self,
        rtl_files: List[str],
    ) -> Tuple[bool, List[str]]:
        """Lint RTL code using Verilator
        
        Args:
            rtl_files: List of RTL file paths
            
        Returns:
            Tuple of (passed, errors)
        """
        logger.info("Linting RTL code...")
        
        all_errors = []
        
        for rtl_file in rtl_files:
            filepath = os.path.join(self.workspace_dir, rtl_file)
            
            if not os.path.exists(filepath):
                all_errors.append(f"File not found: {filepath}")
                continue
            
            # Run linting
            passed, errors = self.tools.lint_verilog(filepath)
            
            if not passed:
                all_errors.extend(errors)
        
        passed = len(all_errors) == 0
        logger.info(f"Linting {'passed' if passed else 'failed'}")
        
        return passed, all_errors
    
    def fix_rtl_errors(
        self,
        filename: str,
        original_code: str,
        errors: List[str],
    ) -> Tuple[bool, str]:
        """Fix RTL errors using LLM
        
        Args:
            filename: RTL filename
            original_code: Original RTL code
            errors: List of errors to fix
            
        Returns:
            Tuple of (success, fixed_code)
        """
        logger.info(f"Fixing errors in {filename}...")
        
        # Query knowledge base for similar errors
        error_solutions = []
        for error in errors[:3]:  # Limit to top 3 errors
            solutions = self.kb.find_similar_errors(error, n_results=2)
            error_solutions.extend(solutions)
        
        solutions_text = "\n".join([s['content'] for s in error_solutions])
        
        # Create prompt for error fixing
        prompt = f"""Original Verilog Code:
```verilog
{original_code}
```

Errors Found:
{chr(10).join(errors)}

Similar Error Solutions from Knowledge Base:
{solutions_text}

Fix all the errors in the Verilog code. Provide the complete corrected code.
Do NOT use markdown code blocks - provide raw Verilog code only.

Corrected Verilog Code:"""
        
        try:
            # Generate fixed code
            fixed_code = self.llm.generate(
                prompt=prompt,
                system_instruction=self.SYSTEM_PROMPT,
            )
            
            # Clean up code
            fixed_code = self._clean_code(fixed_code)
            
            if not fixed_code:
                return False, original_code
            
            # Save fixed code
            filepath = os.path.join(self.workspace_dir, filename)
            with open(filepath, 'w') as f:
                f.write(fixed_code)
            
            logger.info(f"Fixed code saved to: {filepath}")
            
            return True, fixed_code
            
        except Exception as e:
            logger.error(f"Error fixing failed: {str(e)}")
            return False, original_code
    
    def _clean_code(self, code: str) -> str:
        """Clean generated code (remove markdown blocks, etc.)
        
        Args:
            code: Raw generated code
            
        Returns:
            Cleaned code
        """
        # Remove markdown code blocks
        if "```verilog" in code:
            code = code.split("```verilog")[1]
            code = code.split("```")[0]
        elif "```" in code:
            parts = code.split("```")
            if len(parts) >= 3:
                code = parts[1]
        
        # Remove leading/trailing whitespace
        code = code.strip()
        
        return code
    
    def analyze_specification(self, specification: str) -> Dict[str, any]:
        """Analyze design specification to extract requirements
        
        Args:
            specification: Natural language specification
            
        Returns:
            Dict with extracted requirements
        """
        prompt = f"""Analyze this hardware design specification and extract key requirements:

{specification}

Provide a structured analysis including:
1. Module name (if mentioned)
2. Input ports (names and bit widths)
3. Output ports (names and bit widths)
4. Clock and reset requirements
5. Functional requirements
6. Any timing or performance requirements

Format your response as a clear, structured list."""
        
        try:
            analysis = self.llm.generate(
                prompt=prompt,
                system_instruction="You are a hardware design analyst. Extract and structure design requirements clearly.",
            )
            
            return {
                "analysis": analysis,
                "success": True,
            }
        except Exception as e:
            logger.error(f"Specification analysis failed: {str(e)}")
            return {
                "analysis": "",
                "success": False,
                "error": str(e),
            }
