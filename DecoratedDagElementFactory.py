from DagElementFactory import *
from DecoratedDagElement import *

## Factory which creates decorated DagElement objects
#
class DecoratedDagElementFactory(DagElementFactory):
    def createDagElement(self, operationType):
        return DecoratedDagElement(operationType)
