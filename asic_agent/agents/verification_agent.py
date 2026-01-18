"""Verification Agent for functional validation using cocotb"""

import os
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

from ..llm_client import GeminiClient
from ..database.knowledge_base import ASICKnowledgeBase
from ..tools.hardware_tools import HardwareTools

logger = logging.getLogger(__name__)


class VerificationAgent:
    """Verification Agent for functional validation using cocotb"""
    
    SYSTEM_PROMPT = """You are an expert hardware verification engineer specializing in cocotb (Python-based verification).
Your role is to create comprehensive testbenches that verify digital designs.

Key responsibilities:
1. Generate cocotb testbenches from RTL specifications
2. Create comprehensive test cases covering all functionality
3. Use Python's capabilities for complex stimulus generation
4. Implement proper clock and reset handling
5. Add assertions to verify expected behavior
6. Debug simulation failures and provide fixes

cocotb 2.0+ Best Practices (CRITICAL - FOLLOW EXACTLY):
- Use @cocotb.test() decorator for test functions
- Use async/await for coroutines
- Drive clock with cocotb.clock.Clock()
- Use await RisingEdge(clk) for synchronization
- Set inputs with: dut.signal.value = value
- Read outputs: actual = int(dut.signal.value) - ALWAYS use int() for comparisons
- Use assert statements to check expected values
- For logging: import logging; log = logging.getLogger(__name__)
- Handle reset properly at start of test

CRITICAL cocotb 2.0+ API RULES - THESE ARE MANDATORY:
1. NEVER import 'cocotb.log' - it does NOT exist in cocotb 2.0+
2. NEVER use SimLog() - it's removed in cocotb 2.0+
3. ALWAYS use Python's standard logging: import logging; log = logging.getLogger(__name__)
4. ALWAYS convert signal values with int(): int(dut.signal.value) before comparisons
5. CRITICAL TIMING RULE: After every await RisingEdge(dut.clk), ALWAYS add await Timer(1, units="ns")
   - This waits for delta cycles so signal values update
   - Pattern: await RisingEdge(dut.clk); await Timer(1, units="ns"); value = int(dut.signal.value)
6. SYNCHRONOUS RESET SEQUENCE (EXACT PATTERN):
   dut.reset.value = 1
   await RisingEdge(dut.clk)
   await Timer(1, units="ns")  # CRITICAL - wait for reset to take effect
   dut.reset.value = 0
   await RisingEdge(dut.clk)
   await Timer(1, units="ns")  # CRITICAL - wait for signals to stabilize
7. COUNTER LOGIC - CRITICAL UNDERSTANDING:
   - After reset release, counter INCREMENTS on the first clock edge
   - DO NOT expect count=0 after reset release + one clock cycle
   - Correct sequence: reset → count=0, release → first_clock → count=1
   - Test pattern: for i in range(1, N) after reset release, NOT range(0, N)

Generate ONLY valid Python code. Do not include markdown code blocks or explanations mixed with code.
Provide clean, ready-to-use Python that can be directly saved to a .py file."""
    
    def __init__(
        self,
        llm_client: GeminiClient,
        knowledge_base: ASICKnowledgeBase,
        hardware_tools: HardwareTools,
        workspace_dir: str,
    ):
        """Initialize Verification Agent
        
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
    
    def generate_testbench(
        self,
        rtl_code: str,
        module_name: str,
        specification: str,
    ) -> Tuple[bool, str, List[str]]:
        """Generate cocotb testbench for RTL design
        
        Args:
            rtl_code: RTL code to verify
            module_name: Name of the module under test
            specification: Design specification
            
        Returns:
            Tuple of (success, testbench_code, errors)
        """
        logger.info(f"Generating testbench for module: {module_name}")
        
        # Query knowledge base for cocotb examples
        cocotb_docs = self.kb.get_best_practices("cocotb")
        cocotb_examples = self.kb.query("cocotb testbench example", n_results=2)
        
        docs_text = "\n".join([doc['content'] for doc in cocotb_docs + cocotb_examples])
        
        # Create prompt for testbench generation
        prompt = f"""RTL Module to Verify:
```verilog
{rtl_code}
```

Module Name: {module_name}

Design Specification:
{specification}

cocotb Reference:
{docs_text}

Generate a comprehensive cocotb testbench in Python that:
1. Tests all functionality described in the specification
2. Properly handles clock and reset
3. Provides good input stimulus
4. Checks all expected outputs
5. Includes assertions to verify correctness
6. Has informative logging

Do NOT use markdown code blocks - provide raw Python code only.

Python Testbench Code:"""
        
        try:
            # Generate testbench code
            testbench_code = self.llm.generate(
                prompt=prompt,
                system_instruction=self.SYSTEM_PROMPT,
            )
            
            # Clean up code
            testbench_code = self._clean_code(testbench_code)
            
            if not testbench_code:
                return False, "", ["Failed to generate testbench"]
            
            # Add required imports if missing
            if "import cocotb" not in testbench_code:
                imports = """import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

"""
                testbench_code = imports + testbench_code
            
            # Save to file
            filename = f"test_{module_name}.py"
            filepath = os.path.join(self.workspace_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(testbench_code)
            
            logger.info(f"Testbench saved to: {filepath}")
            
            return True, testbench_code, []
            
        except Exception as e:
            logger.error(f"Testbench generation failed: {str(e)}")
            return False, "", [str(e)]
    
    def run_verification(
        self,
        testbench_file: str,
        rtl_files: List[str],
        top_module: str,
    ) -> Tuple[bool, str, List[str]]:
        """Run cocotb verification
        
        Args:
            testbench_file: Testbench Python file
            rtl_files: List of RTL files
            top_module: Top module name
            
        Returns:
            Tuple of (passed, output, errors)
        """
        logger.info(f"Running verification for module: {top_module}")
        
        # Get absolute paths
        rtl_paths = [os.path.join(self.workspace_dir, f) for f in rtl_files]
        testbench_path = os.path.join(self.workspace_dir, testbench_file)
        
        # Check files exist
        if not os.path.exists(testbench_path):
            return False, "", [f"Testbench file not found: {testbench_path}"]
        
        for rtl_path in rtl_paths:
            if not os.path.exists(rtl_path):
                return False, "", [f"RTL file not found: {rtl_path}"]
        
        # Run cocotb test
        try:
            passed, output = self.tools.run_cocotb_test(
                testbench_file=testbench_path,
                rtl_files=rtl_paths,
                top_module=top_module,
                work_dir=self.workspace_dir,
            )
            
            # Parse errors from output
            errors = []
            if not passed:
                for line in output.split('\n'):
                    if 'Error' in line or 'FAILED' in line or 'AssertionError' in line:
                        errors.append(line.strip())
            
            logger.info(f"Verification {'passed' if passed else 'failed'}")
            
            return passed, output, errors
            
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            return False, "", [str(e)]
    
    def debug_verification_failure(
        self,
        testbench_code: str,
        rtl_code: str,
        errors: List[str],
        simulation_output: str,
    ) -> Tuple[bool, str, str]:
        """Debug verification failures and provide fixes
        
        Args:
            testbench_code: Original testbench code
            rtl_code: RTL code being tested
            errors: List of errors
            simulation_output: Full simulation output
            
        Returns:
            Tuple of (success, fixed_testbench, fixed_rtl)
        """
        logger.info("Debugging verification failure...")
        
        # Query knowledge base for similar errors
        error_solutions = []
        for error in errors[:3]:
            solutions = self.kb.find_similar_errors(error, n_results=2)
            error_solutions.extend(solutions)
        
        solutions_text = "\n".join([s['content'] for s in error_solutions])
        
        # Create debugging prompt
        prompt = f"""Verification Failure Analysis

RTL Code:
```verilog
{rtl_code}
```

Testbench Code:
```python
{testbench_code}
```

Errors:
{chr(10).join(errors)}

Simulation Output (last 50 lines):
{chr(10).join(simulation_output.split(chr(10))[-50:])}

Similar Error Solutions:
{solutions_text}

Analyze the failure and determine:
1. Is the bug in the RTL or the testbench?
2. What is the root cause?
3. How to fix it?

Provide:
- Your analysis
- Fixed RTL code (if RTL has bug) between markers: ===RTL_START=== and ===RTL_END===
- Fixed testbench code (if testbench has bug) between markers: ===TB_START=== and ===TB_END===

If RTL is correct, only provide fixed testbench.
If testbench is correct, only provide fixed RTL.

Analysis and fixes:"""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                system_instruction="You are an expert at debugging hardware verification failures. Analyze carefully and provide precise fixes.",
            )
            
            # Extract fixed codes
            fixed_rtl = rtl_code
            fixed_testbench = testbench_code
            
            if "===RTL_START===" in response:
                rtl_parts = response.split("===RTL_START===")[1].split("===RTL_END===")
                if rtl_parts:
                    fixed_rtl = self._clean_code(rtl_parts[0])
            
            if "===TB_START===" in response:
                tb_parts = response.split("===TB_START===")[1].split("===TB_END===")
                if tb_parts:
                    fixed_testbench = self._clean_code(tb_parts[0])
            
            # Add imports to testbench if missing
            if fixed_testbench != testbench_code and "import cocotb" not in fixed_testbench:
                imports = """import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer

"""
                fixed_testbench = imports + fixed_testbench
            
            logger.info("Debug analysis complete")
            
            return True, fixed_testbench, fixed_rtl
            
        except Exception as e:
            logger.error(f"Debugging failed: {str(e)}")
            return False, testbench_code, rtl_code
    
    def _clean_code(self, code: str) -> str:
        """Clean generated code (remove markdown blocks, etc.)
        
        Args:
            code: Raw generated code
            
        Returns:
            Cleaned code
        """
        # Remove markdown code blocks
        for lang in ["python", "verilog", ""]:
            marker = f"```{lang}"
            if marker in code:
                parts = code.split(marker)
                if len(parts) >= 2:
                    code = parts[1].split("```")[0]
                    break
        
        # Remove leading/trailing whitespace
        code = code.strip()
        
        return code
