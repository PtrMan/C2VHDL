def unique(l):

    """In the absence of set in older python implementations, make list values unique"""

    return dict(zip(l, l)).keys()


from SignalDefinition import SignalDefinition
from RegisterDefinition import RegisterDefinition

# TODO< differencite between the signed and unsigned datatypes >

class VhdlBackend(object):
    def __init__(self):
        self.outputFile = None

        self.location = 0

        self.wroteProgramCounter = False # if a instruction wrote to the Pc this is true
        self.wroteToRegister = [] # array with bools for the registers which were written


    ## A big ugly function to crunch through all the instructions and generate the CHIP equivilent
    #
    def generate(self, input_file, name, frames, outputFilename, registers, memorySize):
        self.outputFile = open(outputFilename + ".vhd", "w")

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

        # TODO< choose either the bit encoding (fast in hardware) or the usual slow method >
        # TODO< for the slow method we need to calculate the number of bits we need for it >
        widthOfProgramCounter = len(frames)
    
        #create list of signals
        signals = [ SignalDefinition("programCounter", RegisterDefinition.EnumType.BITVECTOR, widthOfProgramCounter) ]

        registerNumber = 0
        for register in registers:
            signals.append(SignalDefinition("register_%s" % (registerNumber,), register.type, register.width))

            registerNumber += 1

        self.wroteToRegister = [False] * len(registers)

        #[
        #              ("s_output_" + i + "_stb", 16) for i in outputs
        #          ] + [
        #              ("s_output_" + i, 16) for i in outputs
        #          ] + [
        #              ("s_input_" + i + "_ack", 16) for i in inputs
        #          ] + divisionSignals
    
        parameters = divisionParameters
        wires = divisionWires
    
        if False:# testbench:
            signals.append(("clk", 1))
            signals.append(("rst", 1))
        else:
            inports.append(SignalDefinition("clk", RegisterDefinition.EnumType.LOGIC, 1))
            inports.append(SignalDefinition("reset", RegisterDefinition.EnumType.LOGIC, 1))
    
        # output the code in VHDL
        self._writeIntro(name, input_file, inputs, outputs)

        self._beginModule(inports, outports, signals)
        
        self._writeInports(inports)
        self._writeOutports(outports)
    
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

        self._writeFsmIntro(widthOfProgramCounter)

        # a frame is executed in each state
        for location, frame in enumerate(frames):
            self._resetWriteFlags(len(registers))

            self._writePreFrame(location, widthOfProgramCounter)
            self._writeInstructionsForFrame(frame, registers, widthOfProgramCounter)
            self._writeSetUnusedRegisters(widthOfProgramCounter)
            self._writePostFrame()

        self._writeFsmOutro()

        self._writeNextstateLogic()

        self._endModule()

        self.outputFile.close()
    
    def _writeDeclaration(self, signalDefinition):

        if signalDefinition.type == RegisterDefinition.EnumType.BITVECTOR:
            initialisation = "0" * signalDefinition.width

            self._writeLine("signal {0}: std_logic_vector({1} downto 0) := \"{2}\";".format(signalDefinition.name, signalDefinition.width-1, initialisation), 1)
            self._writeLine("signal next{0}: std_logic_vector({1} downto 0) := \"{2}\";".format(signalDefinition.name, signalDefinition.width-1, initialisation), 1)

        elif signalDefinition.type == RegisterDefinition.EnumType.LOGIC:
            self._writeLine("signal {0}: std_logic := '0';".format(signalDefinition.name))
            self._writeLine("signal next{0}: std_logic := '0';".format(signalDefinition.name))

        elif signalDefinition.type == RegisterDefinition.EnumType.UNSIGNED:
            self._writeLine("signal %s: unsigned(%s downto 0) := to_unsigned(%s, %s);" % (signalDefinition.name, signalDefinition.width-1, 0, signalDefinition.width), 1)
            self._writeLine("signal next%s: unsigned(%s downto 0) := to_unsigned(%s, %s);" % (signalDefinition.name, signalDefinition.width-1, 0, signalDefinition.width), 1)

        elif signalDefinition.type == RegisterDefinition.EnumType.SIGNED:
            self._writeLine("signal {0}: signed({1} downto 0) := to_signed({2}, {3});".format(signalDefinition.name, signalDefinition.width-1, 0, signalDefinition.width), 1)
            self._writeLine("signal next{0}: signed({1} downto 0) := to_signed({2}, {3});".format(signalDefinition.name, signalDefinition.width-1, 0, signalDefinition.width), 1)

        else:
            raise Exception

    ## ...
    #
    def _writeInstructionsForFrame(self, frame, registers, widthOfProgramCounter):
        for instruction in frame:
            self._writeInstruction(instruction, registers, widthOfProgramCounter)

    ## ...
    #
    def _writeInstruction(self, instruction, registers, widthOfProgramCounter):
        binary_operators = ["+", "-", "*", "/", "|", "&", "^", "<<", ">>", "<",">", ">=", "<=", "==", "!="]

        if instruction["op"] == "literal":
            self._writeInstructionLiteral(instruction, registers)
        elif instruction["op"] == "move":
            self._writeInstructionMove(instruction)
        elif instruction["op"] in ["~"]:
            self._writeInstructionNegateRegister(instruction)
        elif instruction["op"] in binary_operators and "left" in instruction:
            self._writeInstructionBinaryOperationLeft(instruction)
        elif instruction["op"] in binary_operators and "right" in instruction:
            self._writeInstructionBinaryOperationRight(instruction, registers)
        elif instruction["op"] in binary_operators:
            self._writeInstructionBinaryOperationGeneral(instruction)
        elif instruction["op"] == "jmp_if_false":
            self._writeInstructionJumpIfFalse(instruction)
        elif instruction["op"] == "jmp_if_true":
            self._writeInstructionJumpIfTrue(instruction)
        elif instruction["op"] == "jmp_and_link":
            self._writeInstructionJumpAndLink(instruction, registers, widthOfProgramCounter)
        elif instruction["op"] == "jmp_to_reg":
            self._writeInstructionJumpToReg(instruction, widthOfProgramCounter)
        elif instruction["op"] == "goto":
            self._writeInstructionGoto(instruction, widthOfProgramCounter)
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

    def _writeInstructionLiteral(self, instruction, registers):
        # TODO< build mask >
        # TODO< do type dependent things >

        destinationBitWidth = registers[ instruction["dest"] ].width

        operationString = "nextregister_{0} <= to_signed({1}, {2});".format(
            instruction["dest"],
            instruction["literal"]&0xffff,
            destinationBitWidth
        )
        self._writeLine(operationString, 4)

        self.wroteToRegister[ instruction["dest"] ] = True
        return

        raise NotImplementedError
        # old orginal verilog code
        self.outputFile.write(
            "        register_%s <= 16'd%s;\n"%(
            instruction["dest"],
            instruction["literal"]&0xffff)
        )

    def _writeInstructionMove(self, instruction):
        # TODO< check for conversion and do conversion >

        operationString = "nextregister_{0} <= register_{1};".format(
            instruction["dest"],
            instruction["src"]
        )

        self._writeLine(operationString, 4)
        self.wroteToRegister[ instruction["dest"] ] = True

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

    def _writeInstructionBinaryOperationRight(self, instruction, registers):
        # TODO< we do this for unsigned, but for signed it is different >

        sourceRegister = instruction["src"]
        destinationRegister = instruction["dest"]

        numberOfBits = instruction["right"]
        destinationWidth = registers[ instruction["dest"] ].width

        operationString = ""

        if instruction["op"] == "<<":
            operationString += "nextregister_{0} <= ".format(instruction["dest"])

            operationString += "register_{0}({1} downto {2})".format(sourceRegister, destinationWidth-1-numberOfBits, 0)

            operationString += " & "

            if numberOfBits > 1:
                operationString += "\"" + "0"*numberOfBits + "\""
            else:
                operationString += "'0'"

            operationString += ";"

        elif instruction["op"] == ">>":
            operationString += "nextregister_{0} <= ".format(instruction["dest"])

            if numberOfBits > 1:
                operationString += "\"" + "0"*numberOfBits + "\""
            else:
                operationString += "'0'"

            operationString += " & "

            operationString += "register_{0}({1} downto {2})".format(sourceRegister, destinationWidth-1-numberOfBits, 0)

            operationString += ";"
        else:
            raise NotImplementedError

        self._writeLine(operationString, 4)

        self.wroteToRegister[ instruction["dest"] ] = True

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
        operationString = "nextregister_{0} <= register_{1} {2} register_{3};".format(
            instruction["dest"],
            instruction["src"],
            instruction["op"],
            instruction["srcb"]
        )

        self._writeLine(operationString, 4)

        self.wroteToRegister[ instruction["dest"] ] = True

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

    def _writeInstructionJumpAndLink(self, instruction, registers, widthOfProgramCounter):
        # TODO< build in the type of the link register >

        linkRegister = instruction["dest"]
        widthOfLinkRegister = registers[linkRegister].width

        operationString = "nextprogramCounter <= std_logic_vector( to_unsigned({0}, {1}) );".format(
            instruction["label"] & 0xffff,
            widthOfProgramCounter
        )
        self._writeLine(operationString, 4)

        self.wroteProgramCounter = True

        operationString = "nextregister_{0} <= to_signed({1}, {2});".format(
                linkRegister,
                (self.location+1)&0xffff,
                widthOfLinkRegister
        )
        self._writeLine(operationString, 4)

        self.wroteToRegister[ instruction["dest"] ] = True

        return

        # old orginal verilog code
        self.outputFile.write("        program_counter <= 16'd%s;\n"%(instruction["label"]&0xffff))
        self.outputFile.write("        register_%s <= 16'd%s;\n"%(
            instruction["dest"], (self.location+1)&0xffff)
    )

    def _writeInstructionJumpToReg(self, instruction, widthOfProgramCounter):
        # TODO< convert between the register width >

        operationString = "nextprogramCounter <= std_logic_vector( register_{0}({1} downto 0) );".format(instruction["src"], widthOfProgramCounter-1)
        self._writeLine(operationString, 4)

        self.wroteProgramCounter = True

        return

        # old orginal verilog code
        self.outputFile.write("        program_counter <= register_%s;\n"%instruction["src"])

    def _writeInstructionGoto(self, instruction, widthOfProgramCounter):
        operationString = "nextprogramCounter <= std_logic_vector( to_unsigned({0}, {1}) );".format(
            instruction["label"]&0xffff,
            widthOfProgramCounter
        )
        self._writeLine(operationString, 4)

        self.wroteProgramCounter = True
        return

        # old orginal verilog code
        self.outputFile.write("        program_counter <= 16'd%s;\n"%(instruction["label"]&0xffff))

    def _writeInstructionRead(self, instruction):
        self.outputFile.write("        register_%s <= input_%s;\n"%(
            instruction["dest"], instruction["input"])
        )
        self.outputFile.write("        programCounter <= %s;\n"%self.location)
        self.outputFile.write("        s_input_%s_ack <= 1'b1;\n"%instruction["input"])
        self.outputFile.write( "       if (s_input_%s_ack == 1'b1 && input_%s_stb == 1'b1) then\n"%(
            instruction["input"],
            instruction["input"])
        )
        self.outputFile.write("          s_input_%s_ack <= 1'b0;\n"%instruction["input"])
        self.outputFile.write("          programCounter <= %s;\n"%(self.location+1))
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
        self.outputFile.write("        programCounter <= %s;\n"%self.location)
        self.outputFile.write("        s_output_%s_stb <= 1'b1;\n"%instruction["output"])
        self.outputFile.write(
            "        if (s_output_%s_stb == 1'b1 && output_%s_ack == 1'b1) begin\n"%(
            instruction["output"],
            instruction["output"]
        ))
        self.outputFile.write("          s_output_%s_stb <= 1'b0;\n"%instruction["output"])
        self.outputFile.write("          programCounter <= %s;\n"%(self.location+1))
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
        operationString = "assert false report \"(report at line: {0} in file: {1}) \" & integer'image(to_integer(register_{2})) severity note;".format(
            instruction["line"],
            instruction["file"],
            instruction["src"]
        )
        self._writeLine(operationString, 4)

        return

        # old orginal verilog code

        self.outputFile.write(
            "        $display (\"%%d (report at line: %s in file: %s)\", $signed(register_%s));\n"%(
            instruction["line"],
            instruction["file"],
            instruction["src"])
        )

    def _writeInstructionStop(self, instruction):
        self._writeLine("nextprogramCounter <= programCounter;", 4)

        self.wroteProgramCounter = True

        return
        # old orginal verilog code

        self.outputFile.write('        $finish;\n')
        self.outputFile.write("        programCounter <= programCounter;\n")

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
        self.outputFile.write("-- *Created by C2VHDL*\n")
        self.outputFile.write("\n")

        self.outputFile.write("library ieee;\n")
        self.outputFile.write("use ieee.numeric_std.all;\n")
        self.outputFile.write("use ieee.std_logic_1164.all;\n")
        self.outputFile.write("\n")

    def _beginModule(self, inports, outports, signals):
        tempString = ""

        numberOfArguments = len(inports) + len(outports)
        argumentCounter = 0

        for inport in inports:
            lastArgument = numberOfArguments - 1 <= argumentCounter

            if inport.type == RegisterDefinition.EnumType.LOGIC:
                tempString += "%s: in std_logic" % (inport.name,)
            elif inport.type == RegisterDefinition.EnumType.BITVECTOR:
                tempString += "%s: in std_logic_vector(%s downto 0)" % (inport.width-1, inport.name)
            else:
                raise NotImplementedError

            if not lastArgument:
                tempString += ";"

            tempString += "\n"

            argumentCounter += 1

        for outport in outports:
            lastArgument = numberOfArguments - 1 <= argumentCounter

            if outport.size > 1:
                tempString += "%s: out std_logic" % (outport.name,)
            else:
                tempString += "%s: out std_logic_vector(%s downto 0)" % (outport.size-1, outport.name)

            if not lastArgument:
                tempString += ";"

            tempString += "\n"

            argumentCounter += 1

        self.outputFile.write("entity %s is\n" % ("Generated",))
        self.outputFile.write("port(\n")
        self.outputFile.write(tempString)
        self.outputFile.write(");\n")
        self.outputFile.write("end %s;\n" % ("Generated",))

        self.outputFile.write("\n")

        self.outputFile.write("architecture arch0 of %s is\n" % ("Generated",))


        for signal in signals:
            self._writeDeclaration(signal)


        self.outputFile.write("begin\n")

    def _endModule(self):
        self.outputFile.write("end %s;\n" % ("arch0"))

    def _writeFsmIntro(self, widthOfProgramCounter):
        sensitivityList = []

        sensitivityList.append("programCounter")
        # TODO< more for the sensivity list >

        self._writeLine("", 1)
        self._writeLine("process0: process({0}) is".format(",".join(sensitivityList)), 1)
        self._writeLine("begin", 1)

        ####self.outputFile.write("    programCounter <= std_logic_vector( unsigned(programCounter) + to_unsigned(1, {0}) );\n".format(widthOfProgramCounter))

        self._writeLine("", 2)

        self._writeLine("case programCounter is", 2)


        return
        # old verilog code
        self.outputFile.write("  always @(posedge clk)\n")
        self.outputFile.write("  begin\n\n")
        self.outputFile.write("    if (write_enable == 1'b1) begin\n")
        self.outputFile.write("      memory[address] <= data_in;\n")
        self.outputFile.write("    end\n\n")
        self.outputFile.write("    data_out <= memory[address];\n")
        self.outputFile.write("    write_enable <= 1'b0;\n")
        self.outputFile.write("    programCounter <= programCounter + 1;\n")
        self.outputFile.write("    timer <= 16'h0000;\n\n")
        self.outputFile.write("    case(programCounter)\n\n")

    def _writeFsmOutro(self):
        self._writeLine("when others =>", 4)
        self._writeLine("nextprogramCounter <= programCounter;", 5)
        self._writeLine("end case;", 3)
        self._writeLine("end process process0;", 2)

    def _writeNextstateLogic(self):
        self._writeLine("", 1)
        self._writeLine("stateReg: process(clk, reset)", 1)
        self._writeLine("begin", 1)
        #self._writeLine("if reset = '1' then", 2)
        #self._writeLine()
        self._writeLine("if rising_edge(clk) then", 2)
        self._writeLine("programCounter <= nextprogramCounter;", 3)

        # TODO< all other registers >

        self._writeLine("end if;", 2)
        self._writeLine("end process stateReg;", 1)

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

    def _writePreFrame(self, location, programCounterWidth):
        binaryEncoding = bin(location)[2:].rjust(programCounterWidth, "0")

        self._writeLine("when \"{0}\" =>".format(binaryEncoding), 3)

    def _writePostFrame(self):
        pass

    def _writeSetUnusedRegisters(self, widthOfProgramCounter):
        anyUnusedRegisters = False

        if not self.wroteProgramCounter:
            anyUnusedRegisters = True

        if not anyUnusedRegisters:
            for wroteToRegister in self.wroteToRegister:
                if not wroteToRegister:
                    anyUnusedRegisters = True

                    break

        if not anyUnusedRegisters:
            return

        # when we are here we need to write the unused registers

        self._writeLine("", 4)
        self._writeLine("-- unused variables", 4)
        self._writeLine("", 4)

        if not self.wroteProgramCounter:
            self._writeLine("nextprogramCounter <= std_logic_vector( unsigned(programCounter) + to_unsigned(1, {0}) );".format(widthOfProgramCounter), 4)

        i = 0
        while i < len(self.wroteToRegister):
            if not self.wroteToRegister[i]:
                self._writeLine("nextregister_{0} <= register_{0};".format(i), 4)

            i += 1

    # NOTE< general interface >
    def _writeLine(self, text, level):
        self.outputFile.write("   "*level + text + "\n")

    # NOTE< general interface >
    def _resetWriteFlags(self, numberOfRegisters):
        self.wroteProgramCounter = False

        i = 0
        while i < numberOfRegisters:
            self.wroteToRegister[i] = False

            i += 1

