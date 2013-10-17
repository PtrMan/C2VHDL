from DagElement import *

# 'Flow chart' for the Operations

class FlowChart(object):
    def __init__(self):
        pass

    # Dag is a 'DAG' object
    def calcFlowChart(self, dag):
        """
        classic code

        Timing = []
        DagLength = None

        DagLength = len(Dag.Content)

        i = 0
        while i < DagLength:
           Timing.append(0)

           i += 1
        """
        i = 0
        while i < len(dag.content):
            dag.content[i].timing = 0

            i += 1

        # change the timing data until it doesn't change anymore

        while True:
            changed = False

            i = 0
            while i < len(dag.content):
                # TODO< add mov path ? >

                if dag.content[i].operationType == DagElement.EnumOperationType.VAR or \
                   dag.content[i].operationType == DagElement.EnumOperationType.CONST:
                    i += 1
                    continue

                nodeA = dag.content[i].nodeA
                nodeB = dag.content[i].nodeB

                oldTiming = dag.content[i].timing

                dag.content[i].timing = max(dag.content[nodeA].timing + 1, dag.content[nodeB].timing + 1)

                changed = changed or (oldTiming != dag.content[i].timing)

                i += 1

            if not changed:
                break
