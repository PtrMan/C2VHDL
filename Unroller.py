import copy

import compiler.parse_tree as parse_tree

class Unroller(object):
    class EnumForStatementUnrollType:
        UNROLLABLE = 0
        A = 1

    @staticmethod
    def getUnrollTypeOfForStatement(forStatement):
        isTypeA = Unroller._isForTypeA(forStatement)

        if isTypeA:
            return Unroller.EnumForStatementUnrollType.A

        # TODO< check other types of for loops >

        return Unroller.EnumForStatementUnrollType.UNROLLABLE

    ## this checks if the structure of the for loop is equal to this type where
    #
    # for(variable = ...; variable < CONST; variable += CONST2) {
    #   ... (variable is not set)
    # }
    #
    # the for statement is not checked if it is a for statement
    #
    # \param forStatement ...
    #
    @staticmethod
    def _isForTypeA(forStatement):
        # TODO< analyze the remaining parts >

        # analyse comparisation
        if forStatement.expression.elementType != parse_tree.ParserTreeElement.EnumElementType.BINARY:
            return False

        if forStatement.expression.operator != "<":
            # TODO< deeper analysis >
            return False

        if forStatement.expression.left.elementType != parse_tree.ParserTreeElement.EnumElementType.VARIABLE:
            # TODO< deeper analysis >
            return False

        if forStatement.expression.right.elementType != parse_tree.ParserTreeElement.EnumElementType.CONSTANT:
            # TODO< deeper analysis >
            return False

        register = forStatement.expression.left.declaration.register

        # analyse increment
        if forStatement.statement2.elementType != parse_tree.ParserTreeElement.EnumElementType.DISCARDEXPRESSION:
            return False

        if forStatement.statement2.expression.elementType != parse_tree.ParserTreeElement.EnumElementType.ASSIGNMENT:
            return False

        if forStatement.statement2.expression.lvalue.elementType != parse_tree.ParserTreeElement.EnumElementType.VARIABLE:
            return False

        if forStatement.statement2.expression.lvalue.declaration.register != register:
            return False


        if forStatement.statement2.expression.expression.elementType != parse_tree.ParserTreeElement.EnumElementType.BINARY:
            return False

        if forStatement.statement2.expression.expression.operator != "+":
            return False

        if forStatement.statement2.expression.expression.right.elementType != parse_tree.ParserTreeElement.EnumElementType.CONSTANT:
            return False

        if forStatement.statement2.expression.expression.right._value != 1:
            return False

        if forStatement.statement2.expression.expression.left.elementType != parse_tree.ParserTreeElement.EnumElementType.VARIABLE:
            return False

        if forStatement.statement2.expression.expression.left.declaration.register != register:
            return False

        if not Unroller._isRegisterNotSet(forStatement.statement3, register):
            return False

        return True

    @staticmethod
    def _isRegisterNotSet(statement, register):
        if statement.elementType == parse_tree.ParserTreeElement.EnumElementType.ASSIGNMENT:
            if statement.lvalue.declaration.register == register:
                return False

            return True
        elif statement.elementType == parse_tree.ParserTreeElement.EnumElementType.BLOCK:
            for substatement in statement.statements:
                if not Unroller._isRegisterNotSet(substatement, register):
                    return False

            return True
        elif statement.elementType == parse_tree.ParserTreeElement.EnumElementType.REPORT:
            return True
        else:
            # TODO
            raise NotImplementedError


    # doesn't check if the for statement is a for statement
    # doesn't check if loop is unrollable
    # doesn't check if the for loop type is equal to type A
    @staticmethod
    def unrollForStatementTypeA(unrollFactor, forStatement):
        rangeRegister = forStatement.statement1.expression.lvalue.declaration.register
        rangeBegin = forStatement.statement1.expression.expression._value
        rangeEnd = forStatement.expression.right._value

        # sanity check
        if ((rangeEnd - rangeBegin) % unrollFactor) != 0:
            raise Exception

        # replace the stuff we do after a loop iteration
        forStatement.statement2.expression.expression.right._value = unrollFactor

        # now we replace the for body with the unrolled variant

        orginalStatement = forStatement.statement3

        newStatement = parse_tree.Block()
        forStatement.statement3 = newStatement

        for unrolledIteration in range(unrollFactor):
            orginalStatementCopy = copy.deepcopy(orginalStatement)

            if unrolledIteration == 0:
                newStatement.statements.append(orginalStatementCopy)

                continue
            # no else

            # else we are here
            changedStatement = Unroller._entryReplaceVariableWith(orginalStatementCopy, rangeRegister, unrolledIteration)

            newStatement.statements.append(changedStatement)

    @staticmethod
    def _entryReplaceVariableWith(statement, rangeRegister, currentOffset):
        return Unroller._replaceVariableWith(statement, rangeRegister, currentOffset)

    # doesn't check for zero offset
    @staticmethod
    def _replaceVariableWith(statement, rangeRegister, currentOffset):
        if statement.elementType == parse_tree.ParserTreeElement.EnumElementType.ARRAYINDEX:
            statement.index_expression = Unroller._replaceVariableWith(statement.index_expression, rangeRegister, currentOffset)
            return statement

        elif statement.elementType == parse_tree.ParserTreeElement.EnumElementType.BINARY:
            statement.left = Unroller._replaceVariableWith(statement.left, rangeRegister, currentOffset)
            statement.right = Unroller._replaceVariableWith(statement.right, rangeRegister, currentOffset)
            return statement

        elif statement.elementType == parse_tree.ParserTreeElement.EnumElementType.CONSTANT:
            # do nothing with a constant
            return statement

        elif statement.elementType == parse_tree.ParserTreeElement.EnumElementType.DISCARDEXPRESSION:
            statement.expression = Unroller._replaceVariableWith(statement.expression, rangeRegister, currentOffset)
            return statement

        elif statement.elementType == parse_tree.ParserTreeElement.EnumElementType.ASSIGNMENT:
            statement.expression = Unroller._replaceVariableWith(statement.expression, rangeRegister, currentOffset)
            statement.lvalue = Unroller._replaceVariableWith(statement.lvalue, rangeRegister, currentOffset)
            return statement

        elif statement.elementType == parse_tree.ParserTreeElement.EnumElementType.VARIABLE:
            # this is the meat of this function
            # we replace all occurences of the variable with an addition with an offset

            if statement.declaration.register == rangeRegister:
                offsetConstant = parse_tree.Constant(currentOffset)

                declarationInitializer = parse_tree.Constant(0)
                variableDeclaration = parse_tree.VariableInstance(statement.declaration.register, statement.declaration.initializer, statement.declaration.type_)
                variableStatement = parse_tree.Variable(variableDeclaration, statement.allocator)

                newStatement = parse_tree.Binary("+", variableStatement, offsetConstant, statement.allocator)

                return newStatement
            # no else

            # else we are here

            return statement

        elif statement.elementType == parse_tree.ParserTreeElement.EnumElementType.BLOCK:
            newStatements = []

            for oldStatement in statement.statements:
                newStatement = Unroller._replaceVariableWith(oldStatement, rangeRegister, currentOffset)

                newStatements.append(newStatement)

            statement.statements = newStatements
            return statement

        elif statement.elementType == parse_tree.ParserTreeElement.EnumElementType.REPORT:
            statement.expression = Unroller._replaceVariableWith(statement.expression, rangeRegister, currentOffset)
            return statement

        # TODO
        raise NotImplementedError