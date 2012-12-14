import os

class C2CHIPError(Exception):
    def __init__(self, message, filename=None, lineno=None):
        self.message = message
        self.filename = os.path.abspath(filename)
        self.lineno = lineno
