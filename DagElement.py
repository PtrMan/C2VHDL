class DagElement(object):
    class EnumOperationType:
        ADD = 0
        SUB = 1
        MUL = 2
        DIV = 3
        VAR = 4
        MOV = 5 # moves from NodeA to VarId (VarId is the destination variable)
        FLIPFLOP = 6 # a flipflop stage, is added to ease the creation of the logic
        CONST = 7 # constant

    StringsOperationType = ["ADD", "SUB", "MUL", "DIV", "VAR", "MOV", "FLIPFLOP", "CONST"]

    def __init__(self, operationType):
        self.nodeA = None
        self.nodeB = None
        self.operationType = operationType
        self.varId = 0
        self.isOutput = False # not needed????



    def debug(self):
        returnString = ""

        returnString += "Type: {0}\n".format(DagElement.StringsOperationType[self.operationType])

        if (self.operationType == DagElement.EnumOperationType.ADD) or \
              (self.operationType == DagElement.EnumOperationType.SUB) or \
              (self.operationType == DagElement.EnumOperationType.MUL) or \
              (self.operationType == DagElement.EnumOperationType.DIV):

            # ...
            returnString += "NodeA: {0}\n".format(self.nodeA)
            returnString += "NodeB: {0}\n".format(self.nodeB)

            if self.isOutput:
                returnString += "Output Var Id: {0}\n".format(self.varId)

        elif self.operationType == DagElement.EnumOperationType.VAR:
            returnString += "VarId: {0}\n".format(self.varId)

        elif self.operationType == DagElement.EnumOperationType.MOV:
            returnString += "NodeA: {0}\n".format(self.nodeA)
            returnString += "VarId: {0}\n".format(self.nodeB)

        returnString += "---\n"

        return returnString
