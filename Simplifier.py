import compiler.parse_tree as parse_tree

class Simplifier(object):
    ## tries to transform the body of a for expression
    #
    # does only work correctly if the for loop is of type A (see Unroller)
    #
    # \param forStatement ...
    # \return True if it has replaced the body
    @staticmethod
    def tryToRemoveForBodyForTypeA(forStatement):
        increment = forStatement.statement2.expression.expression.right._value

        startValue = forStatement.statement1.expression.lvalue.declaration.initializer._value
        endValue = forStatement.expression.right._value

        if startValue != 0:
            # TODO
            return False

        if endValue == increment:
            body = forStatement.statement3

            forStatement = body

            return True

        # should beunreachable
        raise Exception
