__author__ = "Jon Dawson"
__copyright__ = "Copyright (C) 2012, Jonathan P Dawson"
__version__ = "0.1"

class NotConstant(Exception):
    pass

## If an expression can be evaluated at compile time, return the value
#
def value(expression):
    if expression.isConstantFoldable():
        return truncate(expression.value())
    else:
        raise NotConstant

## Replace an expression with a constant if possible
#
def constant_fold(expression):
    try:
        return Constant(value(expression))
    except NotConstant:
        return expression

## Truncate arithmetic results to the target number of bits
#
def truncate(number):
    sign = number & 0x10000
    number = number & 0xffff
    if sign:
        number =  ~0xffff | number
    return number

class ParserTreeElement(object):
    class EnumElementType:
        PROCESS = 0
        FUNCTION = 1
        BREAK = 2
        CONTINUE = 3
        ASSERT = 4
        RETURN = 5
        REPORT = 6
        WAITCLOCKS = 7
        IF = 8
        SWITCH = 9
        CASE = 10
        DEFAULT = 11
        LOOP = 12
        FOR = 13
        BLOCK = 14
        COMPOUNDDECLARATION = 15
        VARIABLEDECLARATION = 16
        VARIABLEINSTANCE = 17
        #ARRAYDECLARATION = 18
        ARRAYINSTANCE = 19
        #STRUCTDECLARATION = 20
        STRUCTINSTANCE = 21
        ARGUMENT = 22
        DISCARDEXPRESSION = 23
        ANDOR = 24
        BINARY = 25
        UNARY = 26
        FUNCTIONCALL = 27
        OUTPUT = 28
        INPUT = 29
        READY = 30
        ARRAY = 31
        ARRAYINDEX = 32
        VARIABLE = 33
        BOOLEAN = 34
        ASSIGNMENT = 35
        CONSTANT = 36

    def __init__(self, elementType):
        self.elementType = elementType

class Process(ParserTreeElement):
    def __init__(self):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.PROCESS)

    def generate(self):
        instructions = []
        for function in self.functions:
            if hasattr(function, "declarations"):
                instructions.extend(function.generate())

        instructions.append({
            "op"   :"jmp_and_link",
            "dest" :self.main.return_address,
            "label":"function_%s"%id(self.main)})

        instructions.append({"op":"stop"})

        for function in self.functions:
            if not hasattr(function, "declarations"):
                instructions.extend(function.generate())

        return instructions

class Function(ParserTreeElement):
    def __init__(self, allocator):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.FUNCTION)

        self.allocator = allocator
        self.name = ""
        self.type_ = ""
        self.return_address = None
        self.arguments = []
        self.statement = None

    def generate(self):
        instructions = []
        instructions.append({"op":"label", "label":"function_%s"%id(self)})
        instructions.extend(self.statement.generate())

        if not hasattr(self, "return_value"):
            instructions.append({"op":"jmp_to_reg", "src":self.return_address})

        return instructions

class Break(ParserTreeElement):
    def __init__(self, allocator):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.BREAK)

    def generate(self):
        return [{"op":"goto", "label":"break_%s"%id(self.loop)}]

class Continue(ParserTreeElement):
    def __init__(self):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.CONTINUE)

    def generate(self):
        return [{"op":"goto", "label":"continue_%s"%id(self.loop)}]

class Assert(ParserTreeElement):
    def __init__(self):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.ASSERT)

    def generate(self):
        result = self.allocator.new()
        instructions = self.expression.generate(result)
        self.allocator.free(result)
        instructions.append({"op":"assert", "src":result, "line":self.line, "file":self.filename})

        return instructions

class Return(ParserTreeElement):
    def __init__(self):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.RETURN)

    def generate(self):
        if hasattr(self, "expression"):
            instructions = self.expression.generate(self.function.return_value)
        else:
            instructions = []

        instructions.append({"op":"jmp_to_reg", "src":self.function.return_address})
        return instructions

class Report(ParserTreeElement):
    def __init__(self):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.REPORT)

    def generate(self):
        result = self.allocator.new()
        instructions = self.expression.generate(result)
        self.allocator.free(result)
        instructions.append({"op":"report", "src":result, "line":self.line, "file":self.filename})

        return instructions

class WaitClocks(ParserTreeElement):
    def __init__(self):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.WAITCLOCKS)

    def generate(self):
        result = self.allocator.new()
        instructions = self.expression.generate(result)
        self.allocator.free(result)
        instructions.append({"op":"wait_clocks", "src":result})
        return instructions

class If(ParserTreeElement):
    def __init__(self):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.IF)

    def generate(self):
        try:
            if   value(self.expression):
                return self.true_statement.generate()
            elif self.false_statement:
                return self.false_statement.generate()
            else:
                return []

        except NotConstant:
            result = self.allocator.new()

            instructions = []
            instructions.extend(self.expression.generate(result))
            instructions.append({"op"   :"jmp_if_false",
                                 "src" :result,
                                 "label":"else_%s"%id(self)})
            self.allocator.free(result)
            instructions.extend(self.true_statement.generate())
            instructions.append({"op":"goto", "label":"end_%s"%id(self)})
            instructions.append({"op":"label", "label":"else_%s"%id(self)})

            if self.false_statement:
                instructions.extend(self.false_statement.generate())

            instructions.append({"op":"label", "label":"end_%s"%id(self)})
            return instructions

class Switch(ParserTreeElement):
    def __init__(self):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.SWITCH)

    def generate(self):
        result = self.allocator.new()
        test = self.allocator.new()
        instructions = self.expression.generate(result)

        for value, case in self.cases.iteritems():
            instructions.append({"op":"==", "dest":test, "src":result, "right":value})
            instructions.append({"op":"jmp_if_true", "src":test, "label":"case_%s"%id(case)})

        if hasattr(self, "default"):
            instructions.append({"op":"goto", "label":"case_%s"%id(self.default)})

        self.allocator.free(result)
        self.allocator.free(test)

        instructions.extend(self.statement.generate())
        instructions.append({"op":"label", "label":"break_%s"%id(self)})

        return instructions

class Case(ParserTreeElement):
    def __init__(self):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.CASE)

    def generate(self):
        return [{"op":"label", "label":"case_%s"%id(self)}]

class Default(ParserTreeElement):
    def __init__(self):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.DEFAULT)

    def generate(self):
        return [{"op":"label", "label":"case_%s"%id(self)}]

class Loop(ParserTreeElement):
    def __init__(self):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.LOOP)

    def generate(self):
        instructions = [{"op":"label", "label":"begin_%s"%id(self)}]
        instructions.append({"op":"label", "label":"continue_%s"%id(self)})
        instructions.extend(self.statement.generate())
        instructions.append({"op":"goto", "label":"begin_%s"%id(self)})
        instructions.append({"op":"label", "label":"break_%s"%id(self)})

        return instructions

class For(ParserTreeElement):
    def __init__(self):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.FOR)

    def generate(self):
        instructions = []
        if hasattr(self, "statement1"):
            instructions.extend(self.statement1.generate())
        result = self.allocator.new()
        instructions.append({"op":"label", "label":"begin_%s"%id(self)})
        if hasattr(self, "expression"):
            instructions.extend(self.expression.generate(result))
            instructions.append({"op":"jmp_if_false", "src":result, "label":"end_%s"%id(self)})
        self.allocator.free(result)
        instructions.extend(self.statement3.generate())
        instructions.append({"op":"label", "label":"continue_%s"%id(self)})
        if hasattr(self, "statement2"):
            instructions.extend(self.statement2.generate())
        instructions.append({"op":"goto", "label":"begin_%s"%id(self)})
        instructions.append({"op":"label", "label":"end_%s"%id(self)})
        instructions.append({"op":"label", "label":"break_%s"%id(self)})
        return instructions

class Block(ParserTreeElement):
    def __init__(self):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.BLOCK)

        self.statements = []

    def generate(self):
        instructions = []
        for statement in self.statements:
            instructions.extend(statement.generate())
        return instructions

class CompoundDeclaration(ParserTreeElement):
    def __init__(self, declarations):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.COMPOUNDDECLARATION)

        self.declarations = declarations

    def generate(self):
        instructions = []
        for declaration in self.declarations:
            instructions.extend(declaration.generate());
        return instructions

class VariableDeclaration(ParserTreeElement):
    def __init__(self, allocator, initializer, name, type_):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.VARIABLEDECLARATION)

        self.initializer = initializer
        self.allocator = allocator
        self.type_ = type_
        self.name = name
    def instance(self):
        register = self.allocator.new("variable "+self.name)
        return VariableInstance(register, self.initializer, self.type_)

class VariableInstance(ParserTreeElement):
    def __init__(self, register, initializer, type_):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.VARIABLEINSTANCE)

        self.register = register
        self.type_ = type_
        self.initializer = initializer

    def generate(self):
        return self.initializer.generate(self.register)

class ArrayDeclaration(object):
    def __init__(self, allocator, size, type_):
        self.allocator = allocator
        self.size = size
        self.type_ = type_

    def instance(self):
        location = self.allocator.new_array(self.size)
        register = self.allocator.new("array")
        return ArrayInstance(location, register, self.size, self.type_)

class ArrayInstance(ParserTreeElement):
    def __init__(self, location, register, size, type_):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.ARRAYINSTANCE)

        self.register = register
        self.location = location
        self.size = size
        self.type_ = type_

    def generate(self):
        return [{"op":"literal", "literal":self.location, "dest":self.register}]

class StructDeclaration(object):
    def __init__(self, members):
        self.members = members

    def instance(self):
        instances = {}
        for name, declaration in self.members.iteritems():
            instances[name] = declaration.instance()
        return StructInstance(instances)

class StructInstance(ParserTreeElement):
    def __init__(self, members):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.STRUCTINSTANCE)

        self.members = members
        self.type_ = "struct"

    def generate(self):
        instructions = []
        for member in self.members.values():
            instructions.extend(member.generate())
        return instructions

class Argument(ParserTreeElement):
    def __init__(self, name, type_, parser):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.ARGUMENT)

        self.type_=type_
        parser.scope[name] = self
        self.register = parser.allocator.new("function argument "+name)

    def generate(self):
        return []

class DiscardExpression(ParserTreeElement):
    def __init__(self, expression, allocator):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.DISCARDEXPRESSION)

        self.expression = expression
        self.allocator = allocator

    def generate(self):
        result = self.allocator.new()
        instructions = self.expression.generate(result)
        self.allocator.free(result)
        return instructions

# ...then Expressions...

# Expressions generate methods accept a result argument.
# This indicates which register to put the result in.

# Expressions may also provide a value method which returns the value of an xpression
# if it can be calculated at compile time.

def AND(left, right):
    return ANDOR(left, right, "jmp_if_false")

def OR(left, right):
    return ANDOR(left, right, "jmp_if_true")

class ANDOR(ParserTreeElement):
    def __init__(self, left, right, op):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.ANDOR)

        self.left = constant_fold(left)
        self.right = constant_fold(right)
        self.op = op
        self.type_ = "int"

    def generate(self, result):
        instructions = self.left.generate(result)
        instructions.append({"op":self.op, "src":result, "label":"end_%s"%id(self)})
        instructions.extend(self.right.generate(result))
        instructions.append({"op":"label", "label":"end_%s"%id(self)})
        return instructions

    def value(self):
        if self.op == "jmp_if_false":
            return value(self.left) and value(self.right)
        else:
            return value(self.left) or value(self.right)

class Binary(ParserTreeElement):
    def __init__(self, operator, left, right, allocator):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.BINARY)

        self.left = constant_fold(left)
        self.right = constant_fold(right)
        self.operator = operator
        self.allocator = allocator
        self.type_ = self.left.type_

    def generate(self, result):
        try:
            instructions = self.right.generate(result)
            instructions.append({"op"  :self.operator,
                                 "dest":result,
                                 "left":value(self.left),
                                 "srcb":result})
        except NotConstant:
            try:
                instructions = self.left.generate(result)
                instructions.append({"op"   :self.operator,
                                     "dest" :result,
                                     "src"  :result,
                                     "right":value(self.right)})
            except NotConstant:
                instructions = self.left.generate(result)
                right = self.allocator.new()
                instructions.extend(self.right.generate(right))
                instructions.append({"op":self.operator, "dest":result, "src":result, "srcb":right})
                self.allocator.free(right)

        return instructions

    def value(self):
        return eval("%s %s %s"%(value(self.left), self.operator, value(self.right)))

    def isConstantFoldable(self):
        return True

class Unary(ParserTreeElement):
    def __init__(self, operator, expression):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.UNARY)

        self.expression = constant_fold(expression)
        self.operator = operator
        self.type_ = self.expression.type_

    def generate(self, result):
        instructions = self.expression.generate(result)
        instructions.extend([{"op":self.operator, "dest":result, "src":result}])
        return instructions

    def value(self):
        return eval("%s%s"%(self.operator, value(self.expression)))

class FunctionCall(ParserTreeElement):
    def __init__(self):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.FUNCTIONCALL)

    def generate(self, result):
        instructions = []

        for expression, argument in zip(self.arguments, self.function.arguments):
            instructions.extend(expression.generate(argument.register))

        instructions.append({"op"   :"jmp_and_link",
                             "dest" :self.function.return_address,
                             "label":"function_%s"%id(self.function)})

        if hasattr(self.function, "return_value"):
            instructions.append({"op"   :"move",
                                 "dest" :result,
                                 "src"  :self.function.return_value})

        return instructions

    def isConstantFoldable(self):
        return False

class Output(ParserTreeElement):
    def __init__(self, name, expression):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.OUTPUT)

        self.name = name
        self.expression = expression
        self.type_ = "int"

    def generate(self, result):
        instructions = self.expression.generate(result);
        instructions.append({"op"   :"write", "src"  :result, "output":self.name})

        return instructions

class Input(ParserTreeElement):
    def __init__(self, name):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.INPUT)

        self.name = name
        self.type_ = "int"

    def generate(self, result):
        return [{"op"   :"read", "dest" :result, "input":self.name}]

class Ready(ParserTreeElement):
    def __init__(self, name):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.READY)

        self.name = name
        self.type_ = "int"

    def generate(self, result):
        return [{"op"   :"ready", "dest" :result, "input":self.name}]

class Array(ParserTreeElement):
    def __init__(self, declaration, allocator):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.ARRAY)

        self.declaration = declaration
        self.allocator = allocator
        self.storage = "register"
        self.type_ = self.declaration.type_

    def generate(self, result):
        instructions = []
        if result != self.declaration.register:
            instructions.append({"op"  :"move",
                                 "dest":result,
                                 "src" :self.declaration.register})

        return instructions

    def isConstantFoldable(self):
        return False

class ArrayIndex(ParserTreeElement):
    def __init__(self, declaration, index_expression, allocator):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.ARRAYINDEX)

        self.declaration = declaration
        self.allocator = allocator
        self.index_expression = index_expression
        self.storage = "memory"
        self.type_ = self.declaration.type_.rstrip("[]")

    def generate(self, result):
        instructions = []
        instructions.extend(self.index_expression.generate(result))
        instructions.append({"op"    :"+",
                             "dest"  :result,
                             "src"   :result,
                             "srcb"  :self.declaration.register})
        instructions.append({"op"    :"memory_read_request",
                             "src"   :result})
        instructions.append({"op"    :"memory_read",
                             "dest"  :result})
        # quick hack to work around memory latency
        instructions.append({"op"    :"memory_read",
                             "dest"  :result})
        return instructions

    def isConstantFoldable(self):
        return False

class Variable(ParserTreeElement):
    def __init__(self, declaration, allocator):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.VARIABLE)

        self.declaration = declaration
        self.allocator = allocator
        self.storage = "register"
        self.type_ = self.declaration.type_

    def generate(self, result):
        instructions = []
        if result != self.declaration.register:
            instructions.append({"op"  :"move",
                                 "dest":result,
                                 "src" :self.declaration.register})

        return instructions

    def isConstantFoldable(self):
        return False

class Boolean(ParserTreeElement):
    def __init__(self, value):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.BOOLEAN)

        self.value = value
        self.type_ = "boolean"

    def generate(self, result):
        instructions = [{"op":"literal", "dest":result, "literal":self.value}]
        return instructions

    def isConstantFoldable(self):
        return False

class Assignment(ParserTreeElement):
    def __init__(self, lvalue, expression, allocator):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.ASSIGNMENT)

        self.lvalue = lvalue
        self.expression = expression
        self.allocator = allocator
        self.type_ = "int"

    def generate(self, result):
        instructions = self.expression.generate(result)
        if self.lvalue.storage == "register":
            if result != self.lvalue.declaration.register:
                instructions.append({"op"   : "move",
                                     "dest" : self.lvalue.declaration.register,
                                     "src"  : result})

        elif self.lvalue.storage == "memory":
            index = self.allocator.new()
            instructions.extend(self.lvalue.index_expression.generate(index))
            instructions.append({"op"    :"+",
                                 "dest"  :index,
                                 "src"   :index,
                                 "srcb"  :self.lvalue.declaration.register})
            instructions.append({"op"    :"memory_write",
                                 "src"   :index,
                                 "srcb"  :result})
            self.allocator.free(index)

        return instructions

class Constant(ParserTreeElement):
    def __init__(self, value):
        ParserTreeElement.__init__(self, ParserTreeElement.EnumElementType.CONSTANT)

        self._value = value
        self.type_ = "int"

    def generate(self, result):
        instructions = [{"op":"literal", "dest":result, "literal":self._value}]
        return instructions

    def value(self):
        return self._value

    def isConstantFoldable(self):
        return True