#!/usr/bin/python
#
# Simple Genetic algorithm
# By Donno
#
# Problem
# Solve: Max for x**2 between 0 and 31
import random

class BinaryString:
    LENGTH = 5
    
    def __init__(self, subits=None):
        if subits is None:
            self.bits = []
            for x in xrange(0, BinaryString.LENGTH):
                self.bits.append( random.randint(0, 1) == 1 )
        else:
            self.bits = subits

    def __str__(self):
        bitmap = ['0', '1']
        bitstr = ""
        for bit in self.bits:
            bitstr = bitstr + "%c" % (bitmap[bit])
        return bitstr

    def __getitem__( self, item ):
        if isinstance(item, slice):
            return BinaryString(self.bits[item])
        else:
            return self.bits[item]

    def __add__( self , other ):
        return BinaryString( self.bits + other.bits )
        
    def __len__( self ):
       return len(self.bits)

class SGA:
    def __init__( self , crossoverFunction, func , initalPopulationSize):
        random.seed()
        self.crossoverFunction = crossoverFunction
        self.func = func
        self.population = []
        self.generation = 0
        self.generateInitalPopulation(initalPopulationSize)

    def generateInitalPopulation( self , initalPopulationSize):
        print "initalising population"
        for x in xrange(0, initalPopulationSize):
            self.population.append(BinaryString())
        print "Generation %d" % self.generation
        self.printPopulation()

    def printPopulation(self):
        for member in self.population:
            print member

    
    def generate(self):
        self.generation = self.generation + 1
        print "Generation %d" % self.generation
        
        # CROSSOVER
        self.crossover()
        self.printPopulation()

    def crossover(self):
        offspringpool = []
        # For each pair cross over
        for a in xrange(0, len(self.population), 2):
            offspring = self.crossoverFunction(self.population[a], self.population[a+1])
            offspringpool.append(offspring[0])
            offspringpool.append(offspring[1])


    def mutate(self):
        pass

def crossover_simple( pair1, pair2):

    # Should assert len(pair1) == len(pair2)
    
    # Using 1 point split
    splitPoint = random.randint(0, len(pair1)-1)
    offspring1 = pair1[:splitPoint] + pair2[splitPoint:]
    offspring2 = pair2[:splitPoint] + pair1[splitPoint:]
    
    if 0:
        print "Performing Cross Over"
        print "pair 1: %s" % pair1
        print "     2: %s" % pair2
        print "split point: %s" % splitPoint
        print "offsprint 1: %s" % offspring1
        print "offsprint 2: %s" % offspring2

    return (offspring1, offspring2)

sga = SGA(crossover_simple, None, 2)
sga.generate()

