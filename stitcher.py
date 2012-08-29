#!/usr/bin/env python
import os

class Chip:
  def __init__(self, name):
    self.instances = []
    self.signals = []
    self.inputs = []
    self.outputs = []
    self.components = []
    self.name = name

  def generate(self):
    output_file = open(self.name+".vhd", "w")
    output_file.write("library ieee;\n")
    output_file.write("use ieee.std_logic_1164.all;\n")
    output_file.write("use ieee.std_logic_1164.all;\n\n")
    output_file.write("entity %s is\n"%self.name)
    testbench = not(self.inputs or self.outputs)
    if not testbench:
      output_file.write("  port(\n")
      for i in self.inputs:
        i.generate(output_file)
      for o in self.outputs:
        o.generate(output_file)
      output_file.write("    CLK : in std_logic;\n")
      output_file.write("    RST : in std_logic\n")
      output_file.write("  );\n")
    output_file.write("end entity;\n\n")
    output_file.write("architecture RTL of %s is\n\n"%self.name)
    for signal in self.signals:
      signal.generate(output_file)
    output_file.write("\n")
    for component in self.components:
      component.generate(output_file)
    if testbench:
      output_file.write(" signal CLK : std_logic;\n")
      output_file.write(" signal RST : std_logic;\n")
    output_file.write("begin\n\n")
    if testbench:
      output_file.write("  GENERATE_CLK : process\n")
      output_file.write("  begin\n")
      output_file.write("    while True loop\n")
      output_file.write("      CLK <= '0';\n")
      output_file.write("      wait for 5 ns;\n")
      output_file.write("      CLK <= '1';\n")
      output_file.write("      wait for 5 ns;\n")
      output_file.write("    end loop;\n")
      output_file.write("    wait;\n")
      output_file.write("  end process GENERATE_CLK;\n\n")
      output_file.write("  RST <= '1', '0' after 50 ns;\n\n")
    for instance in self.instances:
      instance.generate(output_file)
    output_file.write("end architecture RTL;\n")

  def ghdl(self):
    for component in self.components:
      os.system("./cc.py %s.c"%component.filename)
      os.system("ghdl -a %s.vhd"%component.name)
    os.system("ghdl -a %s.vhd"%self.name)
    os.system("ghdl -e %s"%self.name)
    os.system("./%s"%self.name)

class CComponent:
  def __init__(self, chip, filename):
    input_file = open(filename+".c")
    self.filename = filename
    self.inputs = []
    self.outputs = []
    for line in input_file:
      if line.split()[0] == "input":
        self.inputs.append(line.split()[1].rstrip(";"))
      elif line.split()[0] == "output":
        self.outputs.append(line.split()[1].rstrip(";"))
      elif line.split()[0] == "name":
        self.name = line.split()[1].rstrip(";")
    chip.components.append(self)

  def __call__(self, chip, inputs, outputs):
    assert len(inputs) == len(self.inputs)
    assert len(outputs) == len(self.outputs)
    return Instance(chip, self, inputs, outputs)

  def generate(self, output_file):
    name = self.name
    output_file.write("  component %s is\n"%name)
    output_file.write("    port(\n")
    for i in self.inputs:
      output_file.write("    INPUT_%s     : in  std_logic_vector(15 downto 0);\n"%i)
      output_file.write("    INPUT_%s_STB : in  std_logic;\n"%i)
      output_file.write("    INPUT_%s_ACK : out std_logic;\n"%i)
    for o in self.outputs:
      output_file.write("    OUTPUT_%s     : out std_logic_vector(15 downto 0);\n"%o)
      output_file.write("    OUTPUT_%s_STB : out std_logic;\n"%o)
      output_file.write("    OUTPUT_%s_ACK : in  std_logic;\n"%o)
    output_file.write("    CLK    : in  std_logic;\n")
    output_file.write("    RST    : in  std_logic);\n")
    output_file.write("  end component %s;\n\n"%name)

class Instance:
  def __init__(self, chip, component, inputs, outputs):
    chip.instances.append(self)
    self.mapped_inputs = inputs
    self.mapped_outputs = outputs
    self.component = component
    for i in inputs:
       assert i.sink is None
       i.sink = self
    for i in outputs:
       assert i.source is None
       i.source = self

  def generate(self, output_file):
    name = self.component.name
    output_file.write("  %s_INST_%s : %s port map(\n"%(name, id(self), name))
    ports = ["INPUT_%s"%i for i in self.component.inputs]
    ports += ["INPUT_%s_STB"%i for i in self.component.inputs]
    ports += ["INPUT_%s_ACK"%i for i in self.component.inputs]
    ports += ["OUTPUT_%s"%i for i in self.component.outputs]
    ports += ["OUTPUT_%s_STB"%i for i in self.component.outputs]
    ports += ["OUTPUT_%s_ACK"%i for i in self.component.outputs]
    ports += ["CLK", "RST"]
    mappings = ["%s"%i for i in self.mapped_inputs]
    mappings += ["%s_STB"%i for i in self.mapped_inputs]
    mappings += ["%s_ACK"%i for i in self.mapped_inputs]
    mappings += ["%s"%i for i in self.mapped_outputs]
    mappings += ["%s_STB"%i for i in self.mapped_outputs]
    mappings += ["%s_ACK"%i for i in self.mapped_outputs]
    mappings += ["CLK", "RST"]
    map_expressions = ["    %s => %s"%(i, j) for i, j in zip(ports, mappings)]
    output_file.write(",\n".join(map_expressions))
    output_file.write(" );\n\n")

class Signal:
  def __init__(self, chip):
    chip.signals.append(self)
    self.source = None
    self.sink = None

  def generate(self, output_file):
    assert self.sink is not None
    assert self.source is not None
    output_file.write("  signal SIGNAL_%s : std_logic_vector(15 downto 0);\n"%id(self))
    output_file.write("  signal SIGNAL_%s_STB : std_logic;\n"%id(self))
    output_file.write("  signal SIGNAL_%s_ACK : std_logic;\n"%id(self))

  def __repr__(self):
    return "SIGNAL_%s"%id(self)

class Input:
  def __init__(self, chip, name):
    chip.signals.append(self)
    self.name = name
    self.sink = None

  def generate(self, output_file):
    assert self.sink is not None
    output_file.write("    INPUT_%s     : in  std_logic_vector(15 downto 0);\n"%self.name)
    output_file.write("    INPUT_%s_STB : in  std_logic;\n"%self.name)
    output_file.write("    INPUT_%s_ACK : out std_logic;\n"%self.name)

  def __str__(self):
    return "INPUT_%s"%self.name

class Output:
  def __init__(self, chip, name):
    chip.signals.append(self)
    self.name = name
    self.source = None

  def generate(self, output_file):
    assert self.source is not None
    output_file.write("    OUTPUT_%s : out std_logic_vector(15 downto 0);\n"%self.name)
    output_file.write("    OUTPUT_%s_STB : out std_logic;\n"%self.name)
    output_file.write("    OUTPUT_%s_ACK : in  std_logic;\n"%self.name)

  def __str__(self):
    return "OUTPUT_%s"%self.name

if __name__ == "__main__":
  chip = Chip("stitcher")
  producer = CComponent(chip, "examples/producer")
  consumer = CComponent(chip, "examples/consumer")
  signal = Signal(chip)
  producer(chip, inputs = [], outputs = [signal])
  consumer(chip, inputs = [signal], outputs = [])
  chip.generate()
  chip.ghdl()
  
    
