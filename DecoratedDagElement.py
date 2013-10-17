from DagElement import *

## is a DagElement with timing
#
class DecoratedDagElement(DagElement):
    def __self__(self, type):
        DagElement.__init__(type)

        self.timing = 0
