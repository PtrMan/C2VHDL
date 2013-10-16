import compiler.parse_tree

## class which tries to pattern match syntax trees against templates
#
class TreeMatcher(object):
    ## check if the input binaryExpression matches a simple tree out of +,-,*,/ operations
    #
    # doesn't check if input is a binary expression
    @staticmethod
    def doesMatchSimpleBinaryOperations(binaryExpression):
        if binaryExpression.operator == "+":
            pass
        elif binaryExpression.operator == "-":
            pass
        elif binaryExpression.operator == "*":
            pass
        elif binaryExpression.operator == "/":
            pass
        else:
            return False

        childsAreSimpleBinaryOperationsOrVariableOrConst = True

        if isinstance(binaryExpression.left, compiler.parse_tree.Binary):
            childsAreSimpleBinaryOperationsOrVariableOrConst = childsAreSimpleBinaryOperationsOrVariableOrConst and TreeMatcher.doesMatchSimpleBinaryOperations(binaryExpression.left)
        elif isinstance(binaryExpression.left, compiler.parse_tree.Variable):
            pass
        elif isinstance(binaryExpression.left, compiler.parse_tree.Constant):
            pass
        else:
            childsAreSimpleBinaryOperationsOrVariableOrConst = False

        if not childsAreSimpleBinaryOperationsOrVariableOrConst:
            return False

        if isinstance(binaryExpression.right, compiler.parse_tree.Binary):
            childsAreSimpleBinaryOperationsOrVariableOrConst = childsAreSimpleBinaryOperationsOrVariableOrConst and TreeMatcher.doesMatchSimpleBinaryOperations(binaryExpression.right)
        elif isinstance(binaryExpression.right, compiler.parse_tree.Variable):
            pass
        elif isinstance(binaryExpression.right, compiler.parse_tree.Constant):
            pass
        else:
            childsAreSimpleBinaryOperationsOrVariableOrConst = False

        if not childsAreSimpleBinaryOperationsOrVariableOrConst:
            return False

        return True
