#!/usr/bin/env python
"""A C to Verilog compiler"""

__author__ = "Jon Dawson"
__copyright__ = "Copyright (C) 2012, Jonathan P Dawson"
__version__ = "0.1"

import sys
import os

from compiler.parser import Parser
from compiler.exceptions import C2CHIPError
from compiler.optimizer import parallelise
from compiler.tokens import Tokens

def unique(l):

  """In the absence of set in older python implementations, make list values unique"""

  return dict(zip(l, l)).keys()

def generate_CHIP(input_file, name, frames, output_file, registers, arrays):

  """A big ugly function to crunch through all the instructions and generate the CHIP equivilent"""

  #calculate the values of jump locations
  location = 0
  labels = {}
  new_frames = []
  for frame in frames:
    if frame[0]["op"] == "label":
      labels[frame[0]["label"]] = location
    else:
      new_frames.append(frame)
      location += 1
  frames = new_frames

  #substitue real values for labeled jump locations
  for frame in frames:
    for instruction in frame:
      if "label" in instruction:
        instruction["label"]=labels[instruction["label"]]

  #list all inputs and outputs used in the program
  inputs = unique([i["input"] for frame in frames for i in frame if "input" in i])
  outputs = unique([i["output"] for frame in frames for i in frame if "output" in i])
  testbench = not inputs and not outputs

  #Do not generate a port in testbench mode
  inports = [
    ("input_" + i, 16) for i in inputs
  ] + [
    ("input_" + i + "_stb", 16) for i in inputs
  ] + [
    ("output_" + i + "_ack", 16) for i in outputs
  ]

  outports = [
    ("output_" + i, 16) for i in outputs
  ] + [
    ("output_" + i + "_stb", 16) for i in outputs
  ] + [
    ("input_" + i + "_ack", 16) for i in inputs
  ]

  signals = [
    ("timer", 16),
    ("program_counter", len(frames))
  ] + [
    ("register_%s"%(register), 16) for register in registers
  ] + [
    ("s_output_" + i + "_stb", 16) for i in outputs
  ] + [
    ("s_output_" + i, 16) for i in outputs
  ] + [
    ("s_input_" + i + "_ack", 16) for i in inputs
  ]

  if testbench:
    signals.append(("clk", 1))
    signals.append(("rst", 1))
  else:
    inports.append(("clk", 1))
    inports.append(("rst", 1))

  #output the code in verilog
  output_file.write("//name : %s\n"%name)
  output_file.write("//tag : c components\n")
  for i in inputs:
      output_file.write("//input : INPUT_%s:16\n"%i)
  for i in outputs:
      output_file.write("//output : OUTPUT_%s:16\n"%i)
  output_file.write("//source_file : %s\n"%input_file)
  output_file.write("///%s\n"%name.title())
  output_file.write("///%s\n"%"".join(["=" for i in name]))
  output_file.write("///\n")
  output_file.write("///*Created by C2CHIP*\n\n")
  output_file.write("module %s"%name)

  all_ports = [name for name, size in inports + outports]
  if all_ports:
      output_file.write("(")
      output_file.write(",".join(all_ports))
      output_file.write(");\n")
  else:
      output_file.write(";\n")


  def write_declaration(object_type, name, size):
      if size == 1:
          output_file.write(object_type)
          output_file.write(name)
          output_file.write(";\n")
      else:
          output_file.write(object_type)
          output_file.write("[%i:0]"%(size-1))
          output_file.write(" ")
          output_file.write(name)
          output_file.write(";\n")

  for name, size in inports:
      write_declaration("  input  ", name, size)

  for name, size in outports:
      write_declaration("  output ", name, size)

  for name, size in signals:
      write_declaration("  reg    ", name, size)

  #Generate arrays
  for array, size in arrays:
    size = int(size)
    output_file.write("  reg [15:0] ARRAY_%s [%i:0];\n"%(array, size-1))

  #generate clock and reset in testbench mode
  if testbench:
      output_file.write("  initial\n")
      output_file.write("  begin\n")
      output_file.write("    rst <= 1'b1;\n")
      output_file.write("    #50 rst <= 1'b0;\n")
      output_file.write("  end\n")

      output_file.write("  initial\n")
      output_file.write("  begin\n")
      output_file.write("    clk <= 1'b0;\n")
      output_file.write("    while (1) begin\n")
      output_file.write("      #5 clk <= ~clk;\n")
      output_file.write("    end\n")
      output_file.write("  end\n")

  #Generate a state machine to execute the instructions
  binary_operators = ["+", "-", "*", "/", "|", "&", "^", "<<", ">>", "<",">", ">=",
    "<=", "==", "!="]

  output_file.write("  \n  always @(posedge clk)\n")
  output_file.write("  begin\n")
  output_file.write("    program_counter <= program_counter + 1;\n")
  output_file.write("    timer <= 16'h0000;\n")
  output_file.write("    case(program_counter)\n")

  #A frame is executed in each state
  for location, frame in enumerate(frames):
    output_file.write("      16'd%s:\n"%location)
    output_file.write("      begin\n")
    for instruction in frame:

      if instruction["op"] == "literal":
        output_file.write(
          "        register_%s <= 16'd%s;\n"%(
          instruction["dest"],
          instruction["literal"]&0xffff))

      elif instruction["op"] == "move":
        output_file.write(
          "        register_%s <= register_%s;\n"%(
          instruction["dest"],
          instruction["src"]))

      elif instruction["op"] in ["~"]:
        output_file.write(
          "        register_%s <= ~register_%s;\n"%(
          instruction["dest"],
          instruction["src"]))

      elif instruction["op"] in binary_operators and "left" in instruction:
        output_file.write(
          "        register_%s <= $signed(16'd%s) %s $signed(register_%s);\n"%(
          instruction["dest"],
          instruction["left"]&0xffff,
          instruction["op"],
          instruction["srcb"]))

      elif instruction["op"] in binary_operators and "right" in instruction:
        output_file.write(
          "        register_%s <= $signed(register_%s) %s $signed(16'd%s);\n"%(
          instruction["dest"],
          instruction["src"],
          instruction["op"],
          instruction["right"] & 0xffff))

      elif instruction["op"] in binary_operators:
        output_file.write(
          "        register_%s <= $signed(register_%s) %s $signed(register_%s);\n"%(
          instruction["dest"],
          instruction["src"],
          instruction["op"],
          instruction["srcb"]))

      elif instruction["op"] == "jmp_if_false":
        output_file.write("        if (register_%s == 16'h0000)\n"%(instruction["src"]));
        output_file.write("          program_counter <= %s;\n"%(instruction["label"]&0xffff))

      elif instruction["op"] == "jmp_if_true":
        output_file.write("        if (register_%s != 16'h0000)\n"%(instruction["src"]));
        output_file.write("          program_counter <= 16'd%s;\n"%(instruction["label"]&0xffff))

      elif instruction["op"] == "jmp_and_link":
        output_file.write("        program_counter <= 16'd%s;\n"%(instruction["label"]&0xffff))
        output_file.write("        register_%s <= 16'd%s;\n"%(
          instruction["dest"], (location+1)&0xffff))

      elif instruction["op"] == "jmp_to_reg":
        output_file.write(
          "        program_counter <= register_%s;\n"%instruction["src"])

      elif instruction["op"] == "goto":
        output_file.write("        program_counter <= 16'd%s;\n"%(instruction["label"]&0xffff))

      elif instruction["op"] == "read":
        output_file.write("        register_%s <= input_%s;\n"%(
          instruction["dest"], instruction["input"]))
        output_file.write("        program_counter <= %s;\n"%location)
        output_file.write("        s_input_%s_ack <= 1'b1;\n"%instruction["input"])
        output_file.write( "       if (s_input_%s_ack == 1'b1 && input_%s_stb == 1'b1) begin\n"%(
          instruction["input"],
          instruction["input"]
        ))
        output_file.write("          s_input_%s_ack <= 1'b0;\n"%instruction["input"])
        output_file.write("          program_counter <= 16'd%s;\n"%(location+1))
        output_file.write("        end\n")

      elif instruction["op"] == "ready":
        output_file.write("        register_%s <= 16'd0;\n"%instruction["dest"])
        output_file.write("        register_%s[0] <= input_%s_stb;\n"%(
          instruction["dest"], instruction["input"]))

      elif instruction["op"] == "write":
        output_file.write("        s_output_%s <= register_%s;\n"%(
          instruction["output"], instruction["src"]))
        output_file.write("        program_counter <= %s;\n"%location)
        output_file.write("        s_output_%s_stb <= 1'b1;\n"%instruction["output"])
        output_file.write(
          "        if (s_output_%s_stb == 1'b1 && output_%s_ack == 1'b1) begin\n"%(
          instruction["output"],
          instruction["output"]
        ))
        output_file.write("          s_output_%s_stb <= 1'b0;\n"%instruction["output"])
        output_file.write("          program_counter <= %s;\n"%(location+1))
        output_file.write("        end\n")

      elif instruction["op"] == "array_read":
        output_file.write(
          "        register_%s <= ARRAY_%s[register_%s %% %s];\n"%(
          instruction["dest"],
          instruction["array"],
          instruction["index"],
          instruction["size"]))

      elif instruction["op"] == "array_write":
        output_file.write(
          "        ARRAY_%s[register_%s %% %s] <= register_%s;\n"%(
          instruction["array"],
          instruction["index"],
          instruction["size"],
          instruction["src"]
        ))

      elif instruction["op"] == "assert":
        output_file.write( "        if (register_%s == 16'h0000) begin\n"%instruction["src"])
        output_file.write( "          $display(\"Assertion failed at line: %s in file: %s\");\n"%(
          instruction["line"],
          instruction["file"]
        ))
        output_file.write( "          $finish_and_return(1);\n")
        output_file.write( "        end\n")

      elif instruction["op"] == "wait_clocks":
        output_file.write("        if (timer < register_%s) begin\n"%instruction["src"])
        output_file.write("          program_counter <= program_counter;\n")
        output_file.write("          timer <= timer+1;\n")
        output_file.write("        end\n")

      elif instruction["op"] == "report":
        output_file.write(
          '        $display ("%%d (report at line: %s in file: %s)", $signed(register_%s));\n'%(
          instruction["line"],
          instruction["file"],
          instruction["src"],
        ))

      elif instruction["op"] == "stop":
        output_file.write('        $finish;\n')
        output_file.write("        program_counter <= program_counter;\n")
    output_file.write("      end\n")

  output_file.write("    endcase\n")

  #Reset program counter and control signals
  output_file.write("    if (rst == 1'b1) program_counter <= 0;\n")
  output_file.write("  end\n")
  for i in inputs:
    output_file.write("  assign input_%s_ack = s_input_%s_ack;\n"%(i, i))
  for i in outputs:
    output_file.write("  assign output_%s_stb = s_output_%s_stb;\n"%(i, i))
    output_file.write("  assign output_%s = s_output_%s;\n"%(i, i))

  output_file.write("\nendmodule\n")

#Command Line Application
####################################################################################################
if __name__ == "__main__":

  if len(sys.argv) < 2:
    print "Usage: c2verilog.py [options] <input_file>"
    print
    print "compile options:"
    print "  no_reuse      : prevent register resuse"
    print "  no_concurrent : prevent concurrency"
    print
    print "tool options:"
    print "  iverilog      : compiles using the icarus verilog compiler"
    print "  run           : runs compiled code, used with ghdl or modelsimoptions"
    sys.exit(-1)

  #parse command line
  input_file = sys.argv[-1]
  reuse = "no_reuse" not in sys.argv

  try:
      #compile into CHIP
      parser = Parser(input_file, reuse)
      process = parser.parse_process()
      name = process.main.name
      instructions = process.generate()
      if "no_concurent" in sys.argv:
        frames = [[i] for i in instructions]
      else:
        frames = parallelise(instructions)
      output_file = name + ".v"
      output_file = open(output_file, "w")
      generate_CHIP(input_file, name, frames, output_file, parser.allocator.all_registers,
        parser.allocator.all_arrays)
      output_file.close()
  except C2CHIPError as err:
      print "Error in file:", err.filename, "at line:", err.lineno
      print err.message
      sys.exit(-1)

  #run the compiled design using the simulator of your choice.
  if "iverilog" in sys.argv:
    import os
    import tempfile
    import shutil
    verilog_file = os.path.abspath("%s.v"%name)
    tempdir = tempfile.mkdtemp()
    os.chdir(tempdir)
    os.system("iverilog -o %s %s"%(name, verilog_file))
    if "run" in sys.argv:
      result = os.system("vvp %s"%name)
      if result:
        sys.exit(1)
      else:
        sys.exit(0)
    shutil.rmtree(tempdir)

  #Add more tools here ...
