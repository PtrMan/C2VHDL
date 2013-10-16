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
from compiler.verilog import generate_CHIP

from TreeMatcher import TreeMatcher
from LimitedTreeTransformer import LimitedTreeTransformer

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

        main = process.main

        if len(main.statement.statements) == 1 and isinstance(main.statement.statements[0], compiler.parse_tree.Return):
            returnStatement = main.statement.statements[0]

            if not isinstance(returnStatement.expression, compiler.parse_tree.Binary):
                print "no match"

            matchesRules = TreeMatcher.doesMatchSimpleBinaryOperations(returnStatement.expression)

            if not matchesRules:
                print "doesn't match simple binary operations!"

            treeTransformer = LimitedTreeTransformer()
            validateResult = treeTransformer.validate(returnStatement.expression)

            if not validateResult:
                print "doesn't match implemeneted operations!"

            TODO = treeTransformer.transform(returnStatement.expression)

            print matchesRules

            a = 0

            #if isinstance(returnStatment.expression, compiler.parse_tree.Binary):
            #    if returnStatment.expression.operator == "+":

            #    else:
            #        unimplemented
            #else:
            #    unimplemented
        else:
            unimplemented

        name = process.main.name
        instructions = process.generate()
        if "no_concurrent" in sys.argv:
            frames = [[i] for i in instructions]
        else:
            frames = parallelise(instructions)
        output_file = name + ".v"
        output_file = open(output_file, "w")
        generate_CHIP(input_file, name, frames, output_file, parser.allocator.all_registers,
                      parser.allocator.memory_size)
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
