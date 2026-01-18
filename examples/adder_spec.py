"""
Example: 8-bit Adder Design
"""

specification = """
Design an 8-bit ripple carry adder with the following specifications:

Inputs:
- a: 8-bit input operand A
- b: 8-bit input operand B
- cin: Carry input (1-bit)

Outputs:
- sum: 8-bit sum output
- cout: Carry output (1-bit)

Behavior:
- Compute sum = a + b + cin
- Output carry out from MSB addition
- Use ripple carry logic (simple full adder chain)
"""

design_name = "adder8"
