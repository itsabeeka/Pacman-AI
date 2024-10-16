# mdpAgents.py
# parsons/20-nov-2017
#
# Version 1
#
# The starting point for CW2.
#
# Intended to work with the PacMan AI projects from:
#
# http://ai.berkeley.edu/
#
# These use a simple API that allow us to control Pacman's interaction with
# the environment adding a layer on top of the AI Berkeley code.
#
# As required by the licensing agreement for the PacMan AI we have:
#
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

# The agent here is was written by Simon Parsons, based on the code in
# pacmanAgents.py

from pacman import Directions
from game import Agent
import api
import random
import game
import util

class MDPAgent(Agent):

    # Constructor: this gets run when we first invoke pacman.py
    def __init__(self):
        print "Starting up MDPAgent!"
        name = "Pacman"
        # setting reward values
        self.CAPSULEREWARD = 30
        self.FOODREWARD = 10
        self.GHOSTRWARD = -50
        self.DEFAULTDIRECTION = 'EAST'
        self.DISCOUNT = 0.6

    # Gets run after an MDPAgent object is created and once there is
    # game state to access.
    def registerInitialState(self, state):
        print "Running registerInitialState for MDPAgent!"
        print "I'm at:"
        print api.whereAmI(state)
        self.currentMap = self.createInitalMap(state)

        
    # This is what gets run in between multiple games
    def final(self, state):
        print "Looks like the game just ended!"

    def getAction(self, state):
        # Get the actions we can try, and remove "STOP" if that is one of them.
        legal = api.legalActions(state)
        if Directions.STOP in legal:
            legal.remove(Directions.STOP)

        policy = self.solver(state)
        position = api.whereAmI(state)
        selected = policy[position[1]][position[0]]
        mydict = {
            'NORTH': Directions.NORTH,
            'SOUTH': Directions.SOUTH,
            'EAST': Directions.EAST,
            'WEST': Directions.WEST
        }
        direction = mydict[selected]
        return api.makeMove(direction, legal)
    
# --------------------------- MAP MAKING ---------------------------   
    # function to create an empty map when needing to copy contents of one map to another
    def createEmptyMap(self, state):
        map = []
        
        topRight = api.corners(state)[3]

        row = []
        for y in range(topRight[1]+1):
            for x in range(topRight[0]+1):
                row.append(0)
            map.append(row)
            row = []

        return map
    
    # function to create a list of all possible coordinates on sceen using the coordinate value of the top right corner
    def createListOfAllCoords(self, state):
        map = []
        topRight = api.corners(state)[3]
        for y in range(topRight[1]+1):
            for x in range(topRight[0]+1):
                map.append((x, y))

        return map

    # function to create a map with initial values
    def createInitalMap(self, state):
        map = []
        capsules = api.capsules(state)
        food = api.food(state)
        walls = api.walls(state)
        ghosts = api.ghosts(state)
        
        topRight = api.corners(state)[3]
        x = 0
        y = 0
        row = []
        for y in range(topRight[1]+1):
            for x in range(topRight[0]+1):
                reward = self.calculateReward(state, (x, y))
                row.append(reward)
            map.append(row)
            row = []
            x = 0
            y+=1

        return map
    
    # function to calculate ghost reward based on how long they are to remain edible (if they are)
    def ghostReward(self, state, coord):
        export = api.ghostStatesWithTimes(state)
        position = coord
        edibleTimer = 0
        if coord == export[0][0]:
            edibleTimer = export[0][1]
        else:
            edibleTimer = export[1][1]
        if edibleTimer < 5:
            return -10
        elif edibleTimer < 15:
            return -5
        else:
            return 0
        
    # function tp create a list of the neighbour coordinates of the ghost positions
    def checkAroundGhost(self, state, coord):
        ghostPositions = api.ghosts(state)
        walls = api.walls(state)
        returnList = []
        for pos in ghostPositions:
            returnList.append((pos[0]+1, pos[1]))
            returnList.append((pos[0]-1, pos[1]))
            returnList.append((pos[0], pos[1]+1))
            returnList.append((pos[0], pos[1]-1))

        return returnList
    
    # creating an initial policy map initialised to the default policy for all valid (non-wall) coordinates
    def createInitailPolicyMap(self, state):
        map = []
        # prettyMap = map
        walls = api.walls(state)
        
        topRight = api.corners(state)[3]
        x = 0
        y = 0
        row = []
        for y in range(topRight[1]+1):
            for x in range(topRight[0]+1):
                if (x, y) not in walls:
                    row.append(self.DEFAULTDIRECTION)
                else:
                    row.append(0)
            map.append(row)
            row = []
            x = 0
            y+=1

        return map
    
    # function to print map in visually better way
    def prinPrettytMap(self, map):
        stringLength = 7
        for x in reversed(map):
            stringg = ''
            for y in x:
                stringg+=str(y)+(' '*(stringLength-len(str(y))))
            print stringg
            print

# ------------------------------------------------------------------

# --------------------------- PLOICY ITERATION ---------------------------
    def solver(self, state):
        walls = api.walls(state)

        # creating initial utility map, empty map for making copies of maps, policy map
        currentMap = self.createInitalMap(state)
        emptyMap = self.createEmptyMap(state)
        policyMap = self.createInitailPolicyMap(state)
        allCoords = self.createListOfAllCoords(state)

        # keeping all valid coodinates in a list so that wall coordintes are not looped over
        validCoords = []
        for x in allCoords:
            if x not in walls:
                validCoords.append(x)
        
        # holding the previous version of policy map to compare
        previousPolicyMap = self.createEmptyMap(state)

        # assigning new optimal directions to policyMap
        # POLICY IMPROVEMENT
        for (x, y) in validCoords:
            previousPolicyMap[y][x] = policyMap[y][x]
        policyMap = self.policyImprovement(state, currentMap, policyMap, validCoords, emptyMap)
        emptyMap = self.createEmptyMap(state)

        # looping until convergence
        while (policyMap != previousPolicyMap):
            # assigning new optimal directions to policyMap
            # POLICY EVALUATION
            currentMap = self.policyEval(state, currentMap, policyMap, validCoords, emptyMap)
            emptyMap = self.createEmptyMap(state)

            # assigning new optimal directions to policyMap
            # POLICY IMPROVEMENT
            for (x, y) in validCoords:
                previousPolicyMap[y][x] = policyMap[y][x]
            policyMap = self.policyImprovement(state, currentMap, policyMap, validCoords, emptyMap)
            emptyMap = self.createEmptyMap(state)
            

        return policyMap

    # function for policy evaluation
    def policyEval(self, state, currentMap, policyMap, coordMap, newMap):
        # this function returns a new map of utilities(will be assigned to currentMap var)
        # utility of each state is:
        # reward of state
        # plus dicount*( total of probabilities of moving in directions accoring to current policy * utility of the next state accoring to policy)
        for (x, y) in coordMap:
            reward = self.calculateReward(state, (x, y))
            # calculate the total of (probs of directions * utility of states in those directions)
            totalProbs = self.totalOfDirectionAndPerpWithProb((x, y), currentMap, policyMap[y][x], state)
            # # multiply that total by discount factor
            discounted = self.DISCOUNT * totalProbs
            newMap[y][x] = round(reward + discounted, 2)
        return newMap
        
    # function for policy improvement
    def policyImprovement(self, state, currentMap, policyMap, coordMap, newMap):
        # this function calculates the optimal direction to move in accoring to currentMap's utilities
        # need to take the max of (each movements probaility in each direction) * (utility of the state if movement is sucessful)
        for (x, y) in coordMap:
            directionsWithUtilities = []
            for d in ['NORTH', 'EAST', 'SOUTH', 'WEST']:
                # calculate the total of (probs of directions * utility of states in those directions)
                totalProbs = self.totalOfDirectionAndPerpWithProb((x, y), currentMap, d, state)
                directionsWithUtilities.append((d, totalProbs))

            # finding the direction with max utility
            currentPolicy = policyMap[y][x]
            currentPolicyUtility = currentMap[y][x]

            max = 0
            maxDirection = currentPolicy
            for (direction, utility) in directionsWithUtilities:
                if utility > max:
                    max = utility
                    maxDirection = direction
            newMap[y][x] = maxDirection

        return newMap

    # function for calculating the total probabilities*utilities of intending to move in a specified direction
    def totalOfDirectionAndPerpWithProb(self, coord, map, direction, state):
        # total of the probaility of the direction and the two perpediculars * the utility of states in those directions
        dict = {
            'NORTH': ['EAST', 'WEST'],
            'SOUTH': ['EAST', 'WEST'],
            'EAST': ['NORTH', 'SOUTH'],
            'WEST': ['NORTH', 'SOUTH']
        }
        directions = dict[direction]
        UtilityinProperDirection = self.checkUtilityInDirection(map, direction, coord, state)
        # probabilities used: intended direction: 0.8, Perpendicular: 0.1 either way
        calc = 0.8*UtilityinProperDirection
        for x in directions:
            PerpUtility = self.checkUtilityInDirection(map, x, coord, state)
            calc += 0.1*PerpUtility
        return calc


    # function to check the utility in the specified direction
    def checkUtilityInDirection(self, currentMap, direction, coord, state):
        walls = api.walls(state)

        coordAppend = {
            'NORTH': [0, 1],
            'SOUTH': [0, -1],
            'EAST': [1, 0],
            'WEST': [-1, 0]
        }

        coordEdit = coordAppend[direction]
        newCoord = (coord[0]+coordEdit[0], coord[1]+coordEdit[1])

        if newCoord in walls:
            newCoord = coord

        return currentMap[newCoord[1]][newCoord[0]]
    
    # function to calculate the rewards of each state
    def calculateReward(self, state, coord):
        if coord in self.checkAroundGhost(state, coord):
            return self.GHOSTRWARD
        if coord in api.ghosts(state):
            return self.GHOSTRWARD
        if coord in api.capsules(state):
            return self.CAPSULEREWARD
        if coord in api.food(state):
            return self.FOODREWARD
        else:
            return 0
        