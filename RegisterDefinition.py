class RegisterDefinition(object):
    class EnumType:
        UNSIGNED = 0
        SIGNED = 1
        BITVECTOR = 2
        LOGIC = 3

    def __init__(self, type, width):
        self.type = type
        self.width = width
