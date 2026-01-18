"""
Example: Simple 4-bit Counter Design
"""

specification = """
Design a 4-bit synchronous up counter with the following specifications:

Inputs:
- clk: Clock signal
- rst: Synchronous reset (active high)
- enable: Counter enable signal

Outputs:
- count: 4-bit counter output

Behavior:
- On reset, counter goes to 0
- When enable is high, counter increments on each clock edge
- Counter wraps around from 15 to 0
- When enable is low, counter holds its value
"""

design_name = "counter4"

# This specification can be used with:
# python3 main.py "$(cat examples/counter_spec.py | grep -A 20 'specification =')" --name counter4
