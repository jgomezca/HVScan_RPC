
class ConditionException(Exception):
    '''Exception raised by modules related to conditions.
    '''

    def __init__(self, message):
        self.args = (message, )

