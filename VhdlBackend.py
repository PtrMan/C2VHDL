
"""

entity x is
port(
    clk : in TODO;
    a : in TODO;
    b : in TODO;
    c : in TODO;
    d : out TODO
)
end entity x;

architecture standard of x is
begin
    process0: process(TODO) is
    begin
        if rising_edge(clk) then

        end if;
    end process0;
end architecture standard;
"""

def unique(l):

    """In the absence of set in older python implementations, make list values unique"""

    return dict(zip(l, l)).keys()


# TODO< differencite between the signed and unsigned datatypes >

class VhdlBackend(object):
    def __init__(self):
        self.outputFile = None

        self.location = 0

    ## A big ugly function to crunch through all the instructions and generate the CHIP equivilent
    #
    def generate(self, input_file, name, frames, outputFile, registers, memorySize):
        self.outputFile = outputFile

        # calculate the values of jump locations
        self.location = 0
        labels = {}
        newFrames = []
        for frame in frames:
            if frame[0]["op"] == "label":
                labels[frame[0]["label"]] = self.location
            else:
                newFrames.append(frame)
                self.location += 1
        frames = newFrames
    
        # substitue real values for labeled jump locations
        for frame in frames:
            for instruction in frame:
                if "label" in instruction:
                    instruction["label"]=labels[instruction["label"]]
    
        # list all inputs and outputs used in the program
        inputs = unique([i["input"] for frame in frames for i in frame if "input" in i])
        outputs = unique([i["output"] for frame in frames for i in frame if "output" in i])
        testbench = not inputs and not outputs
    
        # Do not generate a port in testbench mode
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
    
        # create signals and ports for divider
        # NOTE< we don't do this now >
        # TODO
        divisionSignals = []
    
        divisionWires = []
    
        divisionParameters = []
    
        #create list of signals
        signals = [
                      ("timer", 16),
                      ("program_counter", len(frames)),
                      ("address", 16),
                      ("data_out", 16),
                      ("data_in", 16),
                      ("write_enable", 1),
                      ] + [
                      ("register_%s"%(register), 16) for register in registers
                  ] + [
                      ("s_output_" + i + "_stb", 16) for i in outputs
                  ] + [
                      ("s_output_" + i, 16) for i in outputs
                  ] + [
                      ("s_input_" + i + "_ack", 16) for i in inputs
                  ] + divisionSignals
    
        parameters = divisionParameters
        wires = divisionWires
    
        if testbench:
            signals.append(("clk", 1))
            signals.append(("rst", 1))
        else:
            inports.append(("clk", 1))
            inports.append(("rst", 1))
    
        # output the code in VHDL
        self._writeIntro(name, input_file, inputs, outputs)

        self._beginModule(inports, outports, signals)
        
        self._writeInports(inports)
        self._writeOutports(outports)

        #for name, size in wires:
        #    self._writeDeclaration("  wire      ", name, size)
    
        #for name, size, value in parameters:
        #    self._writeDeclaration("  parameter ", name, size, value)
    
        #memorySize = int(memorySize)
        #self.outputFile.write("  reg [15:0] memory [%i:0];\n"%(memorySize-1))
    
        # generate clock and reset in testbench mode
        if False:
            self.outputFile.write("\n")
            self.outputFile.write("  --------------------\n")
            self.outputFile.write("  -- CLOCK AND RESET GENERATION\n")
            self.outputFile.write("  --\n")
            self.outputFile.write("  -- This file was generated in test bench mode. In this mode, the VHDL\n")
            self.outputFile.write("  -- output file can be executed directly within a VHDL simulator.\n")
            self.outputFile.write("  -- In test bench mode, a simulated clock and reset signal are generated within\n")
            self.outputFile.write("  -- the output file.\n")
            self.outputFile.write("  -- VHDL files generated in testbench mode are not suitable for synthesis, \n")
            self.outputFile.write("  -- or for instantiation within a larger design.\n")
    
            self.outputFile.write("  \ninitial\n")
            self.outputFile.write("  begin\n")
            self.outputFile.write("    rst <= 1'b1;\n")
            self.outputFile.write("    #50 rst <= 1'b0;\n")
            self.outputFile.write("  end\n\n")
    
            self.outputFile.write("  \ninitial\n")
            self.outputFile.write("  begin\n")
            self.outputFile.write("    clk <= 1'b0;\n")
            self.outputFile.write("    while (1) begin\n")
            self.outputFile.write("      #5 clk <= ~clk;\n")
            self.outputFile.write("    end\n")
            self.outputFile.write("  end\n\n")
    
        # Generate a state machine to execute the instructions


        self.outputFile.write("\n")
        self.outputFile.write("  --------------------\n")
        self.outputFile.write("  -- FSM IMPLEMENTATION OF C PROCESS\n")
        self.outputFile.write("  --\n")
        self.outputFile.write("  -- This section of the file contains a Finite State Machine (FSM) implementing\n")
        self.outputFile.write("  -- the C process. In general execution is sequential, but the compiler will\n")
        self.outputFile.write("  -- attempt to execute instructions in parallel if the instruction dependencies\n")
        self.outputFile.write("  -- allow. Further concurrency can be achieved by executing multiple C\n")
        self.outputFile.write("  -- processes concurrently within the device.\n")

        self._writeFsmIntro()

        # a frame is executed in each state
        for location, frame in enumerate(frames):
            self._writePreFrame(location)
            self._writeInstructionsForFrame(frame)
            self._writePostFrame()

        self._writeFsmOutro()

    
        # Reset program counter and control signals
        #self.outputFile.write("    if (rst == 1'b1) begin\n")
        #self.outputFile.write("      program_counter <= 0;\n")
        #self.outputFile.write("      stb <= 1'b0;\n")
        #self.outputFile.write("    end\n")

        #for i in inputs:
        #    self.outputFile.write("  assign input_%s_ack = s_input_%s_ack;\n"%(i, i))
        #for i in outputs:
        #    self.outputFile.write("  assign output_%s_stb = s_output_%s_stb;\n"%(i, i))
        #    self.outputFile.write("  assign output_%s = s_output_%s;\n"%(i, i))

        self._endModule()
    
    def _writeDeclaration(self, objectType, name, size, value=None):
        initialisation = "0" * size

        self.outputFile.write("  signal %s: std_logic_vector(%s downto 0) := \"%s\";\n" % (name, size-1, initialisation))

        #if size == 1:
        #    self.outputFile.write(name)
        #    if value is not None:
        #        self.outputFile.write("= %s'd%s"%(size,value))
        #    self.outputFile.write(";\n")
        #else:
        #    self.outputFile.write("[%i:0]"%(size-1))
        #    self.outputFile.write(" ")
        #    self.outputFile.write(name)
        #    if value is not None:
        #        self.outputFile.write("= %s'd%s"%(size,value))
        #    self.outputFile.write(";\n")

    ## ...
    #
    def _writeInstructionsForFrame(self, frame):
        for instruction in frame:
            self._writeInstruction(instruction)

    ## ...
    #
    def _writeInstruction(self, instruction):
        binary_operators = ["+", "-", "*", "/", "|", "&", "^", "<<", ">>", "<",">", ">=", "<=", "==", "!="]

        if instruction["op"] == "literal":
            self._writeInstructionLiteral(instruction)
        elif instruction["op"] == "move":
            self._writeInstructionMove(instruction)
        elif instruction["op"] in ["~"]:
            self._writeInstructionNegateRegister(instruction)
        elif instruction["op"] in binary_operators and "left" in instruction:
            self._writeInstructionBinaryOperationLeft(instruction)
        elif instruction["op"] in binary_operators and "right" in instruction:
            self._writeInstructionBinaryOperationRight(instruction)
        elif instruction["op"] in binary_operators:
            self._writeInstructionBinaryOperationGeneral(instruction)
        elif instruction["op"] == "jmp_if_false":
            self._writeInstructionJumpIfFalse(instruction)
        elif instruction["op"] == "jmp_if_true":
            self._writeInstructionJumpIfTrue(instruction)
        elif instruction["op"] == "jmp_and_link":
            self._writeInstructionJumpAndLink(instruction)
        elif instruction["op"] == "jmp_to_reg":
            self._writeInstructionJumpToReg(instruction)
        elif instruction["op"] == "goto":
            self._writeInstructionGoto(instruction)
        elif instruction["op"] == "read":
            self._writeInstructionRead(instruction)
        elif instruction["op"] == "ready":
            self._writeInstructionReady(instruction)
        elif instruction["op"] == "write":
            self._writeInstructionWrite(instruction)
        elif instruction["op"] == "memory_read_request":
            self._writeInstructionMemoryReadRequest(instruction)
        elif instruction["op"] == "memory_read":
            self._writeInstructionMemoryRead(instruction)
        elif instruction["op"] == "memory_write":
            self._writeInstructionMemoryWrite(instruction)
        elif instruction["op"] == "assert":
            self._writeInstructionAssert(instruction)
        elif instruction["op"] == "wait_clocks":
            self._writeInstructionWaitClocks(instruction)
        elif instruction["op"] == "report":
            self._writeInstructionReport(instruction)
        elif instruction["op"] == "stop":
            self._writeInstructionStop(instruction)
        else:
            raise Exception

        """

                elif instruction["op"] in ["/"] and "left" in instruction:

                    self.outputFile.write(
                        "        divisor  <= $signed(16'd%i);\n"%(instruction["left"]&0xffff))
                    self.outputFile.write(
                        "        dividend <= $signed(register_%s);\n"%instruction["srcb"])
                    self.outputFile.write(
                        "        register_%s <= quotient;\n"%instruction["dest"])
                    self.outputFile.write("        stb <= 1'b0;\n")
                    self.outputFile.write("        if (ack != 1'b1) begin\n")
                    self.outputFile.write("          program_counter <= %s;\n"%self.location)
                    self.outputFile.write("          stb <= 1'b1;\n")
                    self.outputFile.write("        end\n")

                elif instruction["op"] in ["/"] and "right" in instruction:

                    self.outputFile.write(
                        "        divisor  <= $signed(register_%s);\n"%instruction["src"])
                    self.outputFile.write(
                        "        dividend <= $signed(16'd%i);\n"%(instruction["right"]&0xffff))
                    self.outputFile.write(
                        "        register_%s <= quotient;\n"%instruction["dest"])
                    self.outputFile.write("        stb <= 1'b0;\n")
                    self.outputFile.write("        if (ack != 1'b1) begin\n")
                    self.outputFile.write("          program_counter <= %s;\n"%self.location)
                    self.outputFile.write("          stb <= 1'b1;\n")
                    self.outputFile.write("        end\n")
                    self.outputFile.write("        $display(stb);")

                elif instruction["op"] in ["/"]:
                    self.outputFile.write(
                        "        divisor  <= $signed(register_%s);\n"%instruction["src"])
                    self.outputFile.write(
                        "        dividend <= $signed(register_%s);\n"%instruction["srcb"])
                    self.outputFile.write(
                        "        register_%s <= quotient;\n"%instruction["dest"])
                    self.outputFile.write("        stb <= 1'b0;\n")
                    self.outputFile.write("        if (ack != 1'b1) begin\n")
                    self.outputFile.write("          program_counter <= %s;\n"%self.location)
                    self.outputFile.write("          stb <= 1'b1;\n")
                    self.outputFile.write("        end\n")
        """



    def _writeInstructionLiteral(self, instruction):
        raise NotImplementedError
        # old orginal verilog code
        self.outputFile.write(
            "        register_%s <= 16'd%s;\n"%(
            instruction["dest"],
            instruction["literal"]&0xffff)
        )

    def _writeInstructionMove(self, instruction):
        self.outputFile.write(
            "        register_%s <= register_%s;\n"%(
            instruction["dest"],
            instruction["src"])
        )

        return

        # old orginal verilog code
        self.outputFile.write(
            "        register_%s <= register_%s;\n"%(
            instruction["dest"],
            instruction["src"])
        )

    def _writeInstructionNegate(self, instruction):
        raise NotImplementedError
        # old orginal verilog code
        self.outputFile.write(
            "        register_%s <= ~register_%s;\n"%(
            instruction["dest"],
            instruction["src"])
        )

    def _writeInstructionBinaryOperationLeft(self, instruction):
        raise NotImplementedError
        # old orginal verilog code
        self.outputFile.write(
            "        register_%s <= $signed(16'd%s) %s $signed(register_%s);\n"%(
            instruction["dest"],
            instruction["left"]&0xffff,
            instruction["op"],
            instruction["srcb"])
        )

    def _writeInstructionBinaryOperationRight(self, instruction):
        self.outputFile.write(
            "        register_%s <= std_logic_vector(unsigned(register_%s) %s unsigned(%s));\n"%(
            instruction["dest"],
            instruction["src"],
            instruction["op"],
            instruction["right"] & 0xffff)
        )
        return

        raise NotImplementedError
        # old orginal verilog code
        self.outputFile.write(
            "        register_%s <= $signed(register_%s) %s $signed(16'd%s);\n"%(
            instruction["dest"],
            instruction["src"],
            instruction["op"],
            instruction["right"] & 0xffff)
        )

    def _writeInstructionBinaryOperationGeneral(self, instruction):
        self.outputFile.write(
            "        register_%s <= std_logic_vector(unsigned(register_%s) %s unsigned(register_%s));\n"%(
            instruction["dest"],
            instruction["src"],
            instruction["op"],
            instruction["srcb"])
        )
        return

        # old orginal verilog code
        self.outputFile.write(
            "        register_%s <= $signed(register_%s) %s $signed(register_%s);\n"%(
            instruction["dest"],
            instruction["src"],
            instruction["op"],
            instruction["srcb"])
        )

    def _writeInstructionJumpIfFalse(self, instruction):
        raise NotImplementedError
        # old orginal verilog code
        self.outputFile.write("        if (register_%s == 16'h0000)\n"%(instruction["src"]));
        self.outputFile.write("          program_counter <= %s;\n"%(instruction["label"]&0xffff))

    def _writeInstructionJumpIfTrue(self, instruction):
        raise NotImplementedError
        # old orginal verilog code
        self.outputFile.write("        if (register_%s != 16'h0000)\n"%(instruction["src"]));
        self.outputFile.write("          program_counter <= 16'd%s;\n"%(instruction["label"]&0xffff))

    def _writeInstructionJumpAndLink(self, instruction):
        self.outputFile.write("        program_counter <= %s;\n" % (instruction["label"]&0xffff))
        self.outputFile.write("        register_%s <= %s;\n" % (
            instruction["dest"], (self.location+1)&0xffff))

        return
        # old orginal verilog code
        self.outputFile.write("        program_counter <= 16'd%s;\n"%(instruction["label"]&0xffff))
        self.outputFile.write("        register_%s <= 16'd%s;\n"%(
            instruction["dest"], (self.location+1)&0xffff)
    )

    def _writeInstructionJumpToReg(self, instruction):
        self.outputFile.write("        program_counter <= register_%s;\n"%instruction["src"])

        return

        # old orginal verilog code
        self.outputFile.write("        program_counter <= register_%s;\n"%instruction["src"])

    def _writeInstructionGoto(self, instruction):
        self.outputFile.write("        program_counter <= %s;\n" % (instruction["label"]&0xffff))

        return

        # old orginal verilog code
        self.outputFile.write("        program_counter <= 16'd%s;\n"%(instruction["label"]&0xffff))

    def _writeInstructionRead(self, instruction):
        self.outputFile.write("        register_%s <= input_%s;\n"%(
            instruction["dest"], instruction["input"])
        )
        self.outputFile.write("        program_counter <= %s;\n"%self.location)
        self.outputFile.write("        s_input_%s_ack <= 1'b1;\n"%instruction["input"])
        self.outputFile.write( "       if (s_input_%s_ack == 1'b1 && input_%s_stb == 1'b1) then\n"%(
            instruction["input"],
            instruction["input"])
        )
        self.outputFile.write("          s_input_%s_ack <= 1'b0;\n"%instruction["input"])
        self.outputFile.write("          program_counter <= %s;\n"%(self.location+1))
        self.outputFile.write("        end;\n")

        return

        # old orginal verilog code
        self.outputFile.write("        register_%s <= input_%s;\n"%(
            instruction["dest"], instruction["input"])
        )
        self.outputFile.write("        program_counter <= %s;\n"%self.location)
        self.outputFile.write("        s_input_%s_ack <= 1'b1;\n"%instruction["input"])
        self.outputFile.write( "       if (s_input_%s_ack == 1'b1 && input_%s_stb == 1'b1) begin\n"%(
            instruction["input"],
            instruction["input"])
        )
        self.outputFile.write("          s_input_%s_ack <= 1'b0;\n"%instruction["input"])
        self.outputFile.write("          program_counter <= 16'd%s;\n"%(self.location+1))
        self.outputFile.write("        end\n")

    def _writeInstructionReady(self, instruction):
        raise NotImplementedError
        # old orginal verilog code

        self.outputFile.write("        register_%s <= 16'd0;\n"%instruction["dest"])
        self.outputFile.write("        register_%s[0] <= input_%s_stb;\n"%(
            instruction["dest"], instruction["input"])
        )

    def _writeInstructionWrite(self, instruction):
        self.outputFile.write("        s_output_%s <= register_%s;\n"%(
            instruction["output"], instruction["src"]))
        self.outputFile.write("        program_counter <= %s;\n"%self.location)
        self.outputFile.write("        s_output_%s_stb <= 1'b1;\n"%instruction["output"])
        self.outputFile.write(
            "        if (s_output_%s_stb == 1'b1 && output_%s_ack == 1'b1) begin\n"%(
            instruction["output"],
            instruction["output"]
        ))
        self.outputFile.write("          s_output_%s_stb <= 1'b0;\n"%instruction["output"])
        self.outputFile.write("          program_counter <= %s;\n"%(self.location+1))
        self.outputFile.write("        end\n")

        return

        # old orginal verilog code

        self.outputFile.write("        s_output_%s <= register_%s;\n"%(
            instruction["output"], instruction["src"]))
        self.outputFile.write("        program_counter <= %s;\n"%self.location)
        self.outputFile.write("        s_output_%s_stb <= 1'b1;\n"%instruction["output"])
        self.outputFile.write(
            "        if (s_output_%s_stb == 1'b1 && output_%s_ack == 1'b1) begin\n"%(
            instruction["output"],
            instruction["output"]
        ))
        self.outputFile.write("          s_output_%s_stb <= 1'b0;\n"%instruction["output"])
        self.outputFile.write("          program_counter <= %s;\n"%(self.location+1))
        self.outputFile.write("        end\n")

    def _writeInstructionMemoryReadRequest(self, instruction):
        raise NotImplementedError
        # old orginal verilog code


        self.outputFile.write(
            "        address <= register_%s;\n"%(instruction["src"])
        )

    def _writeInstructionMemoryRead(self, instruction):
        raise NotImplementedError
        # old orginal verilog code


        self.outputFile.write(
            "        register_%s <= data_out;\n"%(instruction["dest"])
        )

    def _writeInstructionMemoryWrite(self, instruction):
        raise NotImplementedError
        # old orginal verilog code

        self.outputFile.write("        address <= register_%s;\n"%(instruction["src"]))
        self.outputFile.write("        data_in <= register_%s;\n"%(instruction["srcb"]))
        self.outputFile.write("        write_enable <= 1'b1;\n")

    def _writeInstructionAssert(self, instruction):
        raise NotImplementedError
        # old orginal verilog code

        self.outputFile.write( "        if (register_%s == 16'h0000) begin\n"%instruction["src"])
        self.outputFile.write( "          $display(\"Assertion failed at line: %s in file: %s\");\n"%(
            instruction["line"],
            instruction["file"]
        ))
        self.outputFile.write( "          $finish_and_return(1);\n")
        self.outputFile.write( "        end\n")

    def _writeInstructionWaitClocks(self, instruction):
        raise NotImplementedError
        # old orginal verilog code

        self.outputFile.write("        if (timer < register_%s) begin\n"%instruction["src"])
        self.outputFile.write("          program_counter <= program_counter;\n")
        self.outputFile.write("          timer <= timer+1;\n")
        self.outputFile.write("        end\n")

    def _writeInstructionReport(self, instruction):
        raise NotImplementedError
        # old orginal verilog code

        self.outputFile.write(
            "        $display (\"%%d (report at line: %s in file: %s)\", $signed(register_%s));\n"%(
            instruction["line"],
            instruction["file"],
            instruction["src"])
        )

    def _writeInstructionStop(self, instruction):
        self.outputFile.write("        program_counter <= program_counter;\n")

        return
        # old orginal verilog code

        self.outputFile.write('        $finish;\n')
        self.outputFile.write("        program_counter <= program_counter;\n")

    def _writeIntro(self, name, input_file, inputs, outputs):
        self.outputFile.write("-- name : %s\n"%name)
        self.outputFile.write("-- tag : c components\n")
        for i in inputs:
            self.outputFile.write("-- input : INPUT_%s:16\n"%i)
        for i in outputs:
            self.outputFile.write("-- output : OUTPUT_%s:16\n"%i)
        self.outputFile.write("-- source_file : %s\n"%input_file)
        self.outputFile.write("-- %s\n"%name.title())
        self.outputFile.write("-- %s\n"%"".join(["=" for i in name]))
        self.outputFile.write("-- \n")
        self.outputFile.write("-- *Created by C2VHDL*\n\n")
        self.outputFile.write("\n")

        self.outputFile.write("library ieee\n")
        self.outputFile.write("use ieee.numeric_std.all;\n")
        self.outputFile.write("use ieee.std_logic_1164.all;\n")
        self.outputFile.write("\n")

    def _beginModule(self, inports, outports, signals):
        tempString = ""

        for inport in inports:
            (name, size) = inport

            if size > 1:
                tempString += "%s: in std_logic" % (name,)
            else:
                tempString += "%s: in std_logic_vector(15 downto 0)" % (name,)

            tempString += ";\n"

        length = len(outports)
        i = 0
        for outport in outports:
            lastOutport = length - 1 <= i

            (name, size) = outport

            if size > 1:
                tempString += "%s: out std_logic" % (name,)
            else:
                tempString += "%s: out std_logic_vector(15 downto 0)" % (name,)

            if not lastOutport:
                tempString += ";"

            tempString += "\n"

            i += 1

        self.outputFile.write("entity %s is\n" % ("Generated",))
        self.outputFile.write("port(\n")
        self.outputFile.write(tempString)
        self.outputFile.write(");\n")
        self.outputFile.write("end %s;\n" % ("Generated",))

        self.outputFile.write("\n")

        self.outputFile.write("architecture arch0 of %s is\n" % ("Generated",))


        for name, size in signals:
            self._writeDeclaration("  reg       ", name, size)


        self.outputFile.write("begin\n")

    def _endModule(self):
        self.outputFile.write("end %s;\n" % ("Generated"))

    def _writeFsmIntro(self):
        sensitivityList = []

        sensitivityList.append("clk")
        # TODO< more for the sensivity list >

        self.outputFile.write("  \n")

        self.outputFile.write("  process0: process(%s) is\n" % (",".join(sensitivityList),))
        self.outputFile.write("  begin\n")
        self.outputFile.write("  if rising_edge(clk) then\n")

        self.outputFile.write("    program_counter <= program_counter + 1;\n")

        self.outputFile.write("\n")

        self.outputFile.write("    case programCounter is")


        return
        # old verilog code
        self.outputFile.write("  always @(posedge clk)\n")
        self.outputFile.write("  begin\n\n")
        self.outputFile.write("    if (write_enable == 1'b1) begin\n")
        self.outputFile.write("      memory[address] <= data_in;\n")
        self.outputFile.write("    end\n\n")
        self.outputFile.write("    data_out <= memory[address];\n")
        self.outputFile.write("    write_enable <= 1'b0;\n")
        self.outputFile.write("    program_counter <= program_counter + 1;\n")
        self.outputFile.write("    timer <= 16'h0000;\n\n")
        self.outputFile.write("    case(program_counter)\n\n")

    def _writeFsmOutro(self):
        self.outputFile.write("    end case;\n")
        self.outputFile.write("  end if;\n")
        self.outputFile.write("end process0;\n")

    def _writeInports(self, inports):
        # do nothing for vhdl
        return

        # code for verilog
        for name, size in inports:
            self._writeDeclaration("  input     ", name, size)

    def _writeOutports(self, outports):
        # do nothing for vhdl
        return

        # code for verilog
        for name, size in outports:
            self._writeDeclaration("  output    ", name, size)

    def _writePreFrame(self, location):
        self.outputFile.write("      when %s =>\n" % (location,))

        # old verilog code
        #self.outputFile.write("      %s:\n"%location)
        #self.outputFile.write("      begin\n")

    def _writePostFrame(self):
        # do nothing
        return

        # old verilog code
        #self.outputFile.write("      end\n\n")
