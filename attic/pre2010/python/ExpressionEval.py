"""
    Expression Machine by Donno

    Version 0.1

    A postfix expression machine with independant
    data and code stack
"""
class ExpressionMachine:
    """
        Construct an expression machine
    """
    def __init__( self ):
        print "ExpressionMachine Created"
        self.stack   = []
        self.opstack = []

    def pushData( self, obj ):
        self.stack.append( obj )

    def pushOperation( self, op ):
        self.opstack.append( op )

    def __str__( self ):
        ol = len( self.opstack )
        opstack = ""
        if (ol > 0):
            opstack = self.opstack[0].__str__()
            for i in xrange(1, len( self.opstack )):
                opstack +=  ", " + self.opstack[i].__str__()
        return "ExpressionMachine [Data: %s ## Code: %s]" % ( self.stack.__str__(), opstack )

    def run( self ):
        print "running EM"
        while (len(self.opstack) > 0):
            op = self.opstack.pop()
            operand2 = self.stack.pop()
            operand1 = self.stack.pop()
            result = op.op( operand1, operand2 )
            self.stack.append( result )

class Op:
    def op( self, operand1, operand2 ):
        # this means it will [ a b ] into just [ a ] 
        return operand1

    def __str__( self ):
        return "op(%s)" % self.__class__.__name__

class Add(Op):
    def op( self, operand1, operand2 ):
        return operand1 + operand2

em = ExpressionMachine()
em.pushData(4)
em.pushData(3)
em.pushData(6)
em.pushData("Hello ")
em.pushData("World")
em.pushOperation( Add() )
print em
em.run()
print em
