class SignalDefinition(object):
    ##
    # \param name ...
    # \param type is a Type from RegisterDefinition.EnumType
    # \param width ...
    def __init__(self, name, type, width):
        self.name = name
        self.type = type
        self.width = width
