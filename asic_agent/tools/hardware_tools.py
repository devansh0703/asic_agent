"""Hardware design tools wrapper"""

import subprocess
import os
import logging
from typing import Tuple, List, Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class HardwareTools:
    """Wrapper for hardware design tools (Verilator, iverilog, Yosys, etc.)"""
    
    def __init__(
        self,
        verilator_path: str = "verilator",
        iverilog_path: str = "iverilog",
        vvp_path: str = "vvp",
        yosys_path: str = "yosys",
    ):
        """Initialize hardware tools
        
        Args:
            verilator_path: Path to verilator executable
            iverilog_path: Path to iverilog executable
            vvp_path: Path to vvp (iverilog runtime) executable
            yosys_path: Path to yosys executable
        """
        self.verilator_path = verilator_path
        self.iverilog_path = iverilog_path
        self.vvp_path = vvp_path
        self.yosys_path = yosys_path
    
    def run_command(
        self,
        cmd: List[str],
        cwd: Optional[str] = None,
        timeout: int = 300,
    ) -> Tuple[bool, str, str]:
        """Run a shell command
        
        Args:
            cmd: Command and arguments as list
            cwd: Working directory
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            success = result.returncode == 0
            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)
    
    def lint_verilog(self, verilog_file: str) -> Tuple[bool, List[str]]:
        """Lint Verilog file using Verilator
        
        Args:
            verilog_file: Path to Verilog file
            
        Returns:
            Tuple of (passed, errors)
        """
        cmd = [
            self.verilator_path,
            "--lint-only",
            "-Wall",
            verilog_file,
        ]
        
        success, stdout, stderr = self.run_command(cmd)
        
        errors = []
        if not success:
            # Parse Verilator output for errors
            for line in stderr.split('\n'):
                if 'Error' in line or 'Warning' in line:
                    errors.append(line.strip())
        
        return success, errors
    
    def compile_verilog(
        self,
        verilog_files: List[str],
        output_file: str = "a.out",
        top_module: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Compile Verilog files using iverilog
        
        Args:
            verilog_files: List of Verilog source files
            output_file: Output executable name
            top_module: Top module name (optional)
            
        Returns:
            Tuple of (success, error_message)
        """
        cmd = [self.iverilog_path, "-o", output_file]
        
        if top_module:
            cmd.extend(["-s", top_module])
        
        cmd.extend(verilog_files)
        
        success, stdout, stderr = self.run_command(cmd)
        
        if not success:
            return False, stderr
        
        return True, ""
    
    def run_simulation(
        self,
        executable: str = "a.out",
        vcd_file: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Run iverilog simulation
        
        Args:
            executable: Compiled executable from iverilog
            vcd_file: Optional VCD output file
            
        Returns:
            Tuple of (success, output)
        """
        cmd = [self.vvp_path, executable]
        
        if vcd_file:
            cmd.extend(["-vcd", vcd_file])
        
        success, stdout, stderr = self.run_command(cmd)
        
        output = stdout + stderr
        return success, output
    
    def synthesize_with_yosys(
        self,
        verilog_files: List[str],
        top_module: str,
        output_file: str = "synth.v",
    ) -> Tuple[bool, str]:
        """Synthesize Verilog using Yosys
        
        Args:
            verilog_files: List of Verilog source files
            top_module: Top module name
            output_file: Output synthesized Verilog file
            
        Returns:
            Tuple of (success, log)
        """
        # Create Yosys script
        script = f"""
read_verilog {' '.join(verilog_files)}
hierarchy -check -top {top_module}
proc; opt; fsm; opt; memory; opt
techmap; opt
write_verilog {output_file}
"""
        
        script_file = "synth_script.ys"
        with open(script_file, 'w') as f:
            f.write(script)
        
        cmd = [self.yosys_path, "-s", script_file]
        success, stdout, stderr = self.run_command(cmd)
        
        # Clean up script file
        if os.path.exists(script_file):
            os.remove(script_file)
        
        log = stdout + stderr
        return success, log
    
    def run_cocotb_test(
        self,
        testbench_file: str,
        rtl_files: List[str],
        top_module: str,
        work_dir: str,
    ) -> Tuple[bool, str]:
        """Run cocotb testbench
        
        Args:
            testbench_file: Python testbench file
            rtl_files: List of RTL files
            top_module: Top module name
            work_dir: Working directory
            
        Returns:
            Tuple of (success, output)
        """
        # Convert RTL files to paths relative to work_dir
        relative_rtl_files = []
        for rtl_file in rtl_files:
            # If absolute path, make it relative to work_dir
            if os.path.isabs(rtl_file):
                relative_rtl_files.append(os.path.relpath(rtl_file, work_dir))
            else:
                # If just a filename, assume it's in the work_dir
                relative_rtl_files.append(os.path.basename(rtl_file))
        
        # Create Makefile for cocotb
        makefile_content = f"""
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = {' '.join(relative_rtl_files)}
TOPLEVEL = {top_module}
MODULE = {Path(testbench_file).stem}

include $(shell cocotb-config --makefiles)/Makefile.sim
"""
        
        makefile_path = os.path.join(work_dir, "Makefile")
        with open(makefile_path, 'w') as f:
            f.write(makefile_content)
        
        # Run make
        cmd = ["make"]
        success, stdout, stderr = self.run_command(cmd, cwd=work_dir)
        
        output = stdout + stderr
        return success, output
    
    def check_tool_availability(self) -> Dict[str, bool]:
        """Check which tools are available
        
        Returns:
            Dict mapping tool name to availability
        """
        tools = {
            "verilator": self.verilator_path,
            "iverilog": self.iverilog_path,
            "vvp": self.vvp_path,
            "yosys": self.yosys_path,
        }
        
        availability = {}
        for tool_name, tool_path in tools.items():
            cmd = ["which", tool_path]
            success, _, _ = self.run_command(cmd, timeout=5)
            availability[tool_name] = success
        
        return availability
