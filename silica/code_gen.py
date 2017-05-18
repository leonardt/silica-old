"""
Various constructs used for backend code generation
"""


class Source:
    """
    An object that represents a generated source file
    """
    def __init__(self):
        self._source = ""

    def add_line(self, line):
        self._source += line + "\n"

    def __str__(self):
        return self._source.rstrip()
