import compiler.parse_tree
from Dag import Dag
from DagElement import DagElement

class LimitedTreeTransformer(object):
    ## this checks if we can generate code for the binaryExpression
    #
    # doesn't check if binaryExpression is a BinaryExpression or if everything is valid
    @staticmethod
    def validate(binaryExpression):
        if binaryExpression.operator != "+":
            return False

        childsAreSimpleBinaryOperationsOrVariableOrConst = True

        if isinstance(binaryExpression.left, compiler.parse_tree.Binary):
            childsAreSimpleBinaryOperationsOrVariableOrConst = childsAreSimpleBinaryOperationsOrVariableOrConst and LimitedTreeTransformer.validate(binaryExpression.left)
        elif isinstance(binaryExpression.left, compiler.parse_tree.Variable):
            pass
        elif isinstance(binaryExpression.left, compiler.parse_tree.Constant):
            pass
        else:
            childsAreSimpleBinaryOperationsOrVariableOrConst = False

        if not childsAreSimpleBinaryOperationsOrVariableOrConst:
            return False

        if isinstance(binaryExpression.right, compiler.parse_tree.Binary):
            childsAreSimpleBinaryOperationsOrVariableOrConst = childsAreSimpleBinaryOperationsOrVariableOrConst and LimitedTreeTransformer.validate(binaryExpression.right)
        elif isinstance(binaryExpression.right, compiler.parse_tree.Variable):
            pass
        elif isinstance(binaryExpression.right, compiler.parse_tree.Constant):
            pass
        else:
            childsAreSimpleBinaryOperationsOrVariableOrConst = False

        if not childsAreSimpleBinaryOperationsOrVariableOrConst:
            return False

        return True

    ##
    #
    # \return the id of the top dag element
    def transform(self, binaryExpression):
        self._resetDag()

        topDagElement = self._recursivlyConvertBinaryExpressionIntoDag(binaryExpression)

        return topDagElement

    def _resetDag(self):
        self.dag = Dag()

    def _recursivlyConvertBinaryExpressionIntoDag(self, expression):
        if isinstance(expression, compiler.parse_tree.Binary):
            nodeA = self._recursivlyConvertBinaryExpressionIntoDag(expression.left)
            nodeB = self._recursivlyConvertBinaryExpressionIntoDag(expression.right)

            type = None

            if expression.operator == "+":
                type = DagElement.EnumOperationType.ADD
            elif expression.operator == "-":
                type = DagElement.EnumOperationType.SUB
            elif expression.operator == "*":
                type = DagElement.EnumOperationType.MUL
            elif expression.operator == "/":
                type = DagElement.EnumOperationType.DIV
            else:
                # TODO< throw error >
                pass

            return self.dag.addOperation(type, nodeA, nodeB)
        elif isinstance(expression, compiler.parse_tree.Variable):
            return self.dag.addVariable(expression.declaration.register, True)
        elif isinstance(expression, compiler.parse_tree.Constant):
            return self.dag.addConstant(expression._value)
        else:
            # TODO< throw internal error >
            pass
