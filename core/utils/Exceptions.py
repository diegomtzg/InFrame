class FilmingError(Exception):
    """Base class for exceptions in this module"""
    pass

class BadState(FilmingError):
    """Exception raised for commands received in an unexpected state.

    Attributes:
        current -- state the machine is currently in
        expects -- state the command is expecting the system to be in
    """
    def __init__(self, current, expects):
        self.current = current
        self.expects = expects
