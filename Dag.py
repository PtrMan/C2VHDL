from DagElement import *

## Directed Acyclic Graph
#
class Dag(object):
    def __init__(self):
        # this is the Dag as a list
        # contains only 'DAGElement' objects
        # NOTE< can'T use pointers in the native code for this >
        self.content = []

    def addOperation(self, operationType, nodeA, nodeB = None):
        # search for the Operation with the Same Properties

        i = 0

        while i < len(self.content):
            if (self.content[i].operationType == operationType) and \
                  (self.content[i].nodeA == nodeA) and \
                  (self.content[i].nodeB == nodeB):

                # ...
                return i

            i += 1

        newElement = DagElement(operationType)
        newElement.nodeA = nodeA
        newElement.nodeB = nodeB

        self.content.append(newElement)

        return i

    ##
    #
    # \param varId ...
    # \param check when set this method checks if the Variable was allready Defined/Used
    def addVariable(self, varId, check = True):
        # search for the Operation with the Same Properties

        i = 0

        if check:
            while i < len(self.content):
                if (self.content[i].operationType == DagElement.EnumOperationType.VAR) and \
                      (self.content[i].varId == varId):

                    # ...
                    return i

                i += 1
        else:
            i = len(self.content)

        newElement = DagElement(DagElement.EnumOperationType.VAR)
        newElement.varId = varId

        self.content.append(newElement)

        return i

    def addConstant(self, value):
        i = len(self.content)

        newElement = DagElement(DagElement.EnumOperationType.CONST)

        self.content.append(newElement)

        return i


    def debug(self):
        returnvalue = ""

        for Element in self.content:
            returnvalue += Element.debug()

        return returnvalue

"""
d = Dag()

d.addVariable(0)
d.addVariable(1)
d.addOperation(DagElement.EnumOperationType.ADD, 0, 1)
LastOp = d.addOperation(DagElement.EnumOperationType.MUL, 2, 0)

d.Content[LastOp].IsOutput = True
d.Content[LastOp].VarId = 2

print(d.Content)
"""
