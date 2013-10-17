## abstract factory which creates DAG Elements
#
class DagElementFactory(object):
    def createDagElement(self, operationType):
        raise NotImplementedError
