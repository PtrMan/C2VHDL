#!/usr/bin/env python
"""A C to Verilog compiler"""

__author__ = "Jon Dawson"
__copyright__ = "Copyright (C) 2012, Jonathan P Dawson"
__version__ = "0.1"

import sys
import os

import compiler.parse_tree
from compiler.parser import Parser
from compiler.exceptions import C2CHIPError
from compiler.optimizer import parallelise
from compiler.tokens import Tokens

from VhdlBackend import VhdlBackend

from TreeMatcher import TreeMatcher
from LimitedTreeTransformer import LimitedTreeTransformer
from FlowChart import *
from DecoratedDagElementFactory import *

from RegisterDefinition import RegisterDefinition

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

        if False:
            main = process.main

            if len(main.statement.statements) == 1 and isinstance(main.statement.statements[0], compiler.parse_tree.Return):
                returnStatement = main.statement.statements[0]

                if not isinstance(returnStatement.expression, compiler.parse_tree.Binary):
                    print "no match"

                    raise Exception

                matchesRules = TreeMatcher.doesMatchSimpleBinaryOperations(returnStatement.expression)

                if not matchesRules:
                    print "doesn't match simple binary operations!"

                    raise Exception

                treeTransformer = LimitedTreeTransformer()
                validateResult = treeTransformer.validate(returnStatement.expression)

                if not validateResult:
                    print "doesn't match implemeneted operations!"

                    raise Exception

                decoratedDagElementFactory = DecoratedDagElementFactory()

                topDagElementIndex = treeTransformer.transform(returnStatement.expression, decoratedDagElementFactory)

                flowchartForDag = FlowChart()

                flowchartForDag.calcFlowChart(treeTransformer.getDag())



                print matchesRules

                a = 0

                #if isinstance(returnStatment.expression, compiler.parse_tree.Binary):
                #    if returnStatment.expression.operator == "+":

                #    else:
                #        unimplemented
                #else:
                #    unimplemented
            else:
                # unimplemented
                raise Exception

        name = process.main.name
        instructions = process.generate()
        if "no_concurrent" in sys.argv:
            frames = [[i] for i in instructions]
        else:
            frames = parallelise(instructions)
        output_file = name + ".v"
        output_file = open(output_file, "w")

        # we translate the registers from his format to a better format

        registers = []

        for registerI in range(0, len(parser.allocator.all_registers)):
            registers.append(RegisterDefinition(RegisterDefinition.EnumType.SIGNED, 16))

        backend = VhdlBackend()
        backend.generate(input_file, name, frames, output_file, registers, parser.allocator.memory_size)

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
