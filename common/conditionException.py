#Exception raised by modules related to conditions

class ConditionException( Exception ):

    def __init__( self, message ):
        self.args = ( message, )
