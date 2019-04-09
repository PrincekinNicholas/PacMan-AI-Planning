# myTeam.py
# ---------
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


from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game
from util import manhattanDistance
from game import Actions
from math import sqrt


global pathMapDebugMode
pathMapDebugMode = False
global defenseWallDebugMode
defenseWallDebugMode = False
global agentPathDebugMode
agentPathDebugMode = False
global targetDebugMode
targetDebugMode = False
#python capture.py -r myTeam -b baselineTeam2


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'DummyAgent', second = 'DummyAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

'''
This is the base class for targets
'''
class o0Target:
    def isFoodTarget(self):
        return False
    def isDefenseTarget(self):
        return False
    def getKillTarget(self):
        return None
    def getPathToKillTarget(self):
        return None
    def getTargetValue(self,gameState):
        util.raiseNotDefined()
    def getEvaluateValueToTarget(self,gameState):
        util.raiseNotDefined()
    def updateTarget(self,gameState):
        return
    def getDebugDrawPositions(self):
        return []
    def getDiePenalty(self, gameState):
        global agentInDeadEnd
        for oppoIndex in self.dummyAgent.visiableOpposites:
            if manhattanDistance(self.startGameState.getAgentPosition(oppoIndex), gameState.getAgentPosition(oppoIndex)) > self.dummyAgent.depth:#dead
                return 999
            
        if manhattanDistance(self.startGameState.getAgentPosition(self.dummyAgent.index), gameState.getAgentPosition(self.dummyAgent.index)) > self.dummyAgent.depth:#dead
            if self.dummyAgent.pathMap.isDeadEnd(self.startGameState.getAgentPosition(self.dummyAgent.index)):
                return 999
            elif not agentInDeadEnd[self.dummyAgent.index]:   
                return - 999
            else:
                return 999
            '''
                walls = gameState.getWalls().copy()                
                for oppoIndex in self.dummyAgent.getVisiableOpposites(gameState):
                    oppoPos = gameState.getAgentPosition(oppoIndex)
                    walls[oppoPos[0]][oppoPos[1]] = True
                if mazeDistance(self.startGameState.getAgentPosition(self.dummyAgent.index), self.startGameState.getInitialAgentPosition(self.dummyAgent.index), self.startGameState, walls) is 0:
                    print 'Blocked'
                    return 999999 * 1/(mazeDistance(gameState.getAgentPosition(self.dummyAgent.index), gameState.getInitialAgentPosition(self.dummyAgent.index), gameState, gameState.getWalls().copy())+1)
                else:
                    return - 999'''
        return 0
    def getTargetPos(self):
        return None
    def getTargetName(self):
        return "target"
        
        
targets = {}
global agentInDeadEnd
agentInDeadEnd = {}
global lastEattenFoodAreDefendingPos
lastEattenFoodAreDefendingPos = None
global totalFood
global leftFood
global pathMap
pathMap = None
global enemyScaredTime
enemyScaredTime = 0.0
global defenseWall
defenseWall = []
global defensePositions
defensePositions = []

#class o0KillSelfTarget(o0Target):
'''
Target to eat capsule
'''
class o0EatCapsuleTarget(o0Target):
    def getTargetName(self):
        return "o0EatCapsuleTarget"
    def  __init__(self, dummyAgent, gameState):
        self.dummyAgent = dummyAgent
        self.startGameState = gameState
        
        
        self.targetPosition = None
        if len(self.dummyAgent.getCapsules(gameState)) is not 0:
            walls = gameState.getWalls().copy()     
            for oppoIndex in dummyAgent.visiableOpposites:
                if not inOppositeArea(gameState, oppoIndex) and gameState.getAgentState(oppoIndex).scaredTimer is 0 and manhattanDistance(gameState.getAgentPosition(dummyAgent.index), gameState.getAgentPosition(oppoIndex)) <= 4:
                    oppoPos = gameState.getAgentPosition(oppoIndex)
                    walls[oppoPos[0]][oppoPos[1]] = True     
            position = gameState.getAgentPosition(self.dummyAgent.index) 
            path = aStarSearch(AnyTargetSearchProblem(gameState,self.dummyAgent.getCapsules(gameState),position,None,walls),nullHeuristic)
            if len(path) is not 0:
                self.targetPosition = performActions(position,path)

    def getTargetValue(self,gameState):
        global enemyScaredTime
        global agentInDeadEnd
        if self.targetPosition is None:
            return 0
        if not inOppositeArea(gameState, self.dummyAgent.index):
            return 0
        if enemyScaredTime > 0:
            return 0
        if not agentInDeadEnd[self.dummyAgent.index]:
            enemyCarrying = 0
            for enemy in self.dummyAgent.getOpponents(gameState):
                enemyCarrying += gameState.getAgentState(enemy).numCarrying 
            if enemyCarrying is not 0:
                return 0
            else:
                return 9999
        return 9999

    def getEvaluateValueToTarget(self,gameState): 
        global agentInDeadEnd
        value = 0
        if self.targetPosition is None:
            return value
        position = gameState.getAgentPosition(self.dummyAgent.index)        
        costGrid = getInitCostGrid(gameState)  
        #if not agentInDeadEnd[self.dummyAgent.index]:                      
        for index in self.dummyAgent.visiableOpposites:
            if not inOppositeArea(gameState, index)and gameState.getAgentState(index).scaredTimer is 0:
                agentPos = gameState.getAgentPosition(index)
                costGrid = drawEnemyAsCostOnGrid(costGrid, agentPos,gameState,self.dummyAgent.index)                
        prob = InEquivalentCostSearchProblem(gameState.getWalls(), position, self.targetPosition, costGrid)
                
        value += 1.0/float(len(aStarSearch(prob))+1)
        return value

'''
Target to defense
'''
class o0DefenseTarget(o0Target):
    def getTargetName(self):
        return "o0DefenseTarget"
    def isDefenseTarget(self):
        return True
    def  __init__(self, dummyAgent, gameState):
        self.dummyAgent = dummyAgent
        self.startGameState = gameState
        self.targetPosition = self._getDefensePosition()
        
    def getTargetValue(self,gameState):
        if self.targetPosition is None:
            return 0
        global defensePositions
        if len(defensePositions) > len(self.dummyAgent.getTeam(self.startGameState)):
            return 0
        if gameState.getAgentState(self.dummyAgent.index).scaredTimer > manhattanDistance(gameState.getAgentPosition(self.dummyAgent.index), self.targetPosition):
            return 0
        enemyCarrying = 0
        for enemy in self.dummyAgent.getOpponents(gameState):
            enemyCarrying += gameState.getAgentState(enemy).numCarrying 
        '''mateCarrying = 0
        for mate in self.dummyAgent.getTeam(gameState):
            mateCarrying += gameState.getAgentState(mate).numCarrying '''
        if enemyCarrying >= 1:
            return 0
        if len(defensePositions) < len(self.dummyAgent.getTeam(self.startGameState)):
            return 9997
        if self.dummyAgent.getScore(gameState) <= 0:
            return 0
        #print 'block'
        return 9997

    def getEvaluateValueToTarget(self,gameState): 
        global agentInDeadEnd
        value = self.getDiePenalty(gameState)
        if self.targetPosition is None:
            return value
        position = gameState.getAgentPosition(self.dummyAgent.index)        
        costGrid = getInitCostGrid(gameState)  
        if not agentInDeadEnd[self.dummyAgent.index]:                      
            for index in self.dummyAgent.visiableOpposites:
                if not inOppositeArea(gameState, index)and gameState.getAgentState(index).scaredTimer is 0:
                    agentPos = gameState.getAgentPosition(index)
                    costGrid = drawEnemyAsCostOnGrid(costGrid, agentPos,gameState,self.dummyAgent.index)                
        prob = InEquivalentCostSearchProblem(gameState.getWalls(), position, self.targetPosition, costGrid)
                
        value += 1.0/float(len(aStarSearch(prob))+1)
        return value
    def _getDefensePosition(self):
        aveilablePositions = {}
        for position in defensePositions:
            for index in self.dummyAgent.teamMates:
                if not (targets[index] is not None and targets[index].isDefenseTarget() and targets[index].targetPosition is not None and targets[index].targetPosition[0] is position[0] and targets[index].targetPosition[1] is position[1]):
                    aveilablePositions[manhattanDistance(self.startGameState.getAgentPosition(self.dummyAgent.index), position)] = position
        if len(aveilablePositions.keys()) is 0:
            return None
        return aveilablePositions[min(aveilablePositions.keys())]

'''
Target to kill enemy'''
class o0KillEnemyTarget(o0Target):
    def getTargetName(self):
        return "o0KillEnemyTarget"
    def  __init__(self, dummyAgent, gameState):
        self.dummyAgent = dummyAgent     
        self.startGameState = gameState
        
        self.targetIndex = None
        for mate in self.dummyAgent.teamMates:
            if targets[mate] is not None and targets[mate].getKillTarget() is not None and gameState.getAgentState(targets[mate].getKillTarget()).numCarrying is not 0:
                self.targetIndex = targets[mate].getKillTarget()
           
        if self.targetIndex is None:
            enemyFoodCarrying = {}
            for enemy in self.dummyAgent.getOpponents(gameState):
                self.targetIndex = enemy
                enemyFoodCarrying[gameState.getAgentState(enemy).numCarrying] = enemy            
            self.targetIndex = enemyFoodCarrying[max(enemyFoodCarrying.keys())]
        
        self.pathToTarget = None
        global lastEattenFoodAreDefendingPos        
        if not self.dummyAgent.visiable(gameState, self.targetIndex):
            if lastEattenFoodAreDefendingPos is not None:
                self.pathToTarget = self._getPathToTarget(gameState, lastEattenFoodAreDefendingPos)
        else:
            self.pathToTarget = self._getPathToTarget(gameState, gameState.getAgentPosition(self.targetIndex))
        self.positionRecord = gameState.getAgentPosition(self.dummyAgent.index)
        
    def getDebugDrawPositions(self):
        return actionsToPositions(self.positionRecord, self.getPathToKillTarget())
        
    def isFoodTarget(self):
        return False
    def getKillTarget(self):
        return self.targetIndex
    def getPathToKillTarget(self):
        return self.pathToTarget
    def getTargetValue(self,gameState):
        global lastEattenFoodAreDefendingPos
        global leftFood
        global enemyScaredTime
        if enemyScaredTime > 0:
            return 0
        if gameState.getAgentState(self.dummyAgent.index).scaredTimer >= gameState.getWalls().width / 2:
            return 0.0
        if not self.dummyAgent.visiable(gameState, self.targetIndex) and lastEattenFoodAreDefendingPos is None:
            return 0.0
        selfNumFoodCarrying = gameState.getAgentState(self.targetIndex).numCarrying  
        if selfNumFoodCarrying is 0:
            return 0.0
        value = 0.015 * selfNumFoodCarrying
        for mate in self.dummyAgent.teamMates:
            if targets[mate] is not None and targets[mate].getKillTarget() is self.targetIndex:
                value += 5
                value *= 2
        '''if gameState.getAgentState(self.targetIndex).isPacman and self.dummyAgent.visiable(gameState, self.targetIndex):
            value += 0.5#'''
        if not inOppositeArea(gameState, self.dummyAgent.index):
            value *= 2
        return value
    def getEvaluateValueToTarget(self,gameState):
        global lastEattenFoodAreDefendingPos
        value = self.getDiePenalty(gameState) 
        '''
        if not inOppositeArea(gameState, self.dummyAgent.index):
            value += 1'''
        if not self.dummyAgent.visiable(gameState, self.targetIndex):
            #print 'in visiable'
            if lastEattenFoodAreDefendingPos is not None:
                value += 1.0 / (float(len(self._getPathToTarget(gameState, lastEattenFoodAreDefendingPos))) + 1)
        else:
            value += 1.0 /(float(len(self._getPathToTarget(gameState, gameState.getAgentPosition(self.targetIndex)))) + 1)
        return value
    def _getPathToTarget(self,gameState,targetPos):
        position = gameState.getAgentPosition(self.dummyAgent.index)        
        costGrid = getInitCostGrid(gameState)
                        
        if not agentInDeadEnd[self.dummyAgent.index]: 
            for index in self.dummyAgent.visiableOpposites:
                if not inOppositeArea(gameState, index):
                    agentPos = gameState.getAgentPosition(index)
                    costGrid = drawEnemyAsCostOnGrid(costGrid, agentPos,gameState,self.dummyAgent.index)
                
        for index in self.dummyAgent.teamMates:
            if not inOppositeArea(gameState, index) and targets[index].getPathToKillTarget() is not None and len(targets[index].getPathToKillTarget()) - 1 <= len(aStarSearch(InEquivalentCostSearchProblem(gameState.getWalls(), position, targetPos, costGrid))):
                costGrid = drawPathAsCurveCostOnGrid(costGrid,targets[index].positionRecord,targets[index].getPathToKillTarget(),99)
                costGrid[targets[index].positionRecord[0]][targets[index].positionRecord[1]] = 1                
                
        costGrid = heavyCostGridSidesWeight(costGrid)
        
        prob = InEquivalentCostSearchProblem(gameState.getWalls(), position, targetPos, costGrid)
        return aStarSearch(prob)    
            
    def updateTarget(self,gameState):
        return

'''
Target to return food to self side
'''
class o0FoodReturnTarget(o0Target):
    def getTargetName(self):
        return "o0FoodReturnTarget"
    def  __init__(self, dummyAgent, gameState):
        self.dummyAgent = dummyAgent
        self.startGameState = gameState
    def isFoodTarget(self):
        return False
    def getKillTarget(self):
        return None
    def getTargetValue(self,gameState):
        selfNumFoodCarrying = gameState.getAgentState(self.dummyAgent.index).numCarrying    
        if selfNumFoodCarrying is 0:
            return 0
        from capture import MIN_FOOD
        global leftFood
        if leftFood <= MIN_FOOD:
            return 999999
        distanceToTarget = self._getDistanceToTarget(gameState)
        if distanceToTarget >= (gameState.data.timeleft / gameState.getNumAgents()) - 1:
            return 999999
        global enemyScaredTime
        if enemyScaredTime > distanceToTarget:
            return 0
        return 0.15 * pow(selfNumFoodCarrying,2) / (float(distanceToTarget) + 1.0)
    def getEvaluateValueToTarget(self,gameState):  
        global agentInDeadEnd
        value = 0
        #if not agentInDeadEnd[self.dummyAgent.index]:
        value += self.getDiePenalty(gameState)
        
        value += 1.0/(float(self._getDistanceToTarget(gameState)) + 1.0)
        return value
    def _getDistanceToTarget(self,gameState):   
        global agentInDeadEnd   
        costGrid = getInitCostGrid(gameState)
        if not agentInDeadEnd[self.dummyAgent.index]:                        
            for index in self.dummyAgent.visiableOpposites:
                if not inOppositeArea(gameState, index) and gameState.getAgentState(index).scaredTimer is 0:
                    agentPos = gameState.getAgentPosition(index)
                    costGrid = drawEnemyAsCostOnGrid(costGrid, agentPos,gameState,self.dummyAgent.index) 
                
        return foodReturnDistance(gameState,self.dummyAgent.getFood(gameState),gameState.getAgentPosition(self.dummyAgent.index), self.dummyAgent.index, gameState.getWalls().copy(),costGrid)

    def updateTarget(self,gameState):
        return

'''
Target to eat food
'''
class o0FoodTarget(o0Target):
    def getTargetName(self):
        return "o0FoodTarget"
    def  __init__(self, dummyAgent, gameState):
        self.dummyAgent = dummyAgent
        self.startGameState = gameState
        self.foodPos = None
        self.actionsToFood = None
        self.positionRecord = gameState.getAgentPosition(self.dummyAgent.index)
        self.updateTarget(gameState)
        #print self.foodPos
        #self.carryFoodSoftLimit = 5
        #self.carryFoodForceLimit = 10
    def isFoodTarget(self):
        return True
    def getKillTarget(self):
        return None
    def getTargetValue(self,gameState):
        global leftFood
        if leftFood is 0:
            return 0.0
        if self.foodPos is None:
            return 0.0  
        if not gameState.hasFood(self.foodPos[0],self.foodPos[1]):
            return 0.0
        
        allEnemyEating = True
        futureScore = self.dummyAgent.getScore(gameState)
        for enemy in self.dummyAgent.getOpponents(gameState):
            futureScore -= gameState.getAgentState(enemy).numCarrying
            if gameState.getAgentState(enemy).numCarrying is 0:
                allEnemyEating = False
        for mate in self.dummyAgent.getTeam(gameState):
            futureScore += gameState.getAgentState(mate).numCarrying
        if self.dummyAgent.getScore(gameState) >= 0 and allEnemyEating is True:
            return self.getEvaluateValueToTarget(gameState) * 100#'''
        return self.getEvaluateValueToTarget(gameState)
    def getEvaluateValueToTarget(self,gameState):  
        global agentInDeadEnd
        value = 0 
        value += self.getDiePenalty(gameState)
        position = gameState.getAgentPosition(self.dummyAgent.index)
        if self.foodPos is None:
            return value
        if position[0] is self.foodPos[0] and position[1] is self.foodPos[1]:
            return value + 1        
        if not gameState.hasFood(self.foodPos[0],self.foodPos[1]):
            return value
        
        costGrid = getInitCostGrid(gameState)
        #walls = gameState.getWalls().copy()  
        #print 'is'
        if not agentInDeadEnd[self.dummyAgent.index]:  
            #print 'notInDeadEnd'
            for oppoIndex in self.dummyAgent.visiableOpposites:
                if not inOppositeArea(gameState, oppoIndex) and gameState.getAgentState(oppoIndex).scaredTimer is 0:
                    oppoPos = gameState.getAgentPosition(oppoIndex)
                    costGrid = drawEnemyAsCostOnGrid(costGrid,oppoPos,gameState,self.dummyAgent.index)
                    #walls[oppoPos[0]][oppoPos[1]] = True
                
        return value + 1.0 /(float(len(aStarSearch(InEquivalentCostSearchProblem(gameState.getWalls().copy(), position, self.foodPos, costGrid)))) + 1)
    def updateTarget(self,gameState):    
        global agentInDeadEnd    
        position = gameState.getAgentPosition(self.dummyAgent.index)  
        costGrid = getInitCostGrid(gameState)
        FoodGrid = self.dummyAgent.getFood(gameState)   
        FoodList = FoodGrid.asList()
        if len(FoodList) is 0:
            self.foodPos = None
            self.actionsToFood = None
        
        if not agentInDeadEnd[self.dummyAgent.index]: 
            for oppoIndex in self.dummyAgent.visiableOpposites:
                if not inOppositeArea(gameState, oppoIndex) and gameState.getAgentState(oppoIndex).scaredTimer is 0:
                    oppoPos = gameState.getAgentPosition(oppoIndex)
                    costGrid = drawEnemyAsCostOnGrid(costGrid,oppoPos,gameState,self.dummyAgent.index)            
                    
        for mate in self.dummyAgent.teamMates:
            if targets[mate] is not None and targets[mate].isFoodTarget():
                mateTargetFood = targets[mate].foodPos
                if mateTargetFood is not None:
                    FoodGrid[mateTargetFood[0]][mateTargetFood[1]] = False
                    costGrid[mateTargetFood[0]][mateTargetFood[1]] += 5
                    if targets[mate].actionsToFood is not None and len(targets[mate].actionsToFood) - 1 <= len(aStarSearch(InEquivalentCostSearchProblem(gameState.getWalls(), position, mateTargetFood, costGrid))):
                        costGrid = drawPathAsCurveCostOnGrid(costGrid,targets[mate].positionRecord,targets[mate].actionsToFood,10)
                
            #print 'actionsToFood'
        self.actionsToFood = aStarSearch(AnyFoodSearchProblem(gameState.getWalls(),FoodGrid,position,costGrid),nullHeuristic)
        if len(self.actionsToFood) is not 0:
            self.foodPos = performActions(position,self.actionsToFood)
        else:
            self.foodPos = None

    def getTargetPos(self):
        return self.foodPos
    def getDebugDrawPositions(self):
        return actionsToPositions(self.positionRecord, self.actionsToFood)

##########
# Agents #
##########

class DummyAgent(CaptureAgent):
    """
    A Dummy agent to serve as an example of the necessary agent structure.
    You should look at baselineTeam.py for more details about how to
    create an agent as this is the bare minimum.
    """
    
    def visiable(self, gameState, index):
        return gameState.getAgentPosition(index) is not None

    def getVisiableOpposites(self, gameState):
        opposites = self.getOpponents(gameState)
        visiableOpposites = []
        for opposite in opposites:
            if self.visiable(gameState, opposite):
                visiableOpposites.append(opposite)
        return visiableOpposites
    
    '''
    def getTeamMates(self,gameState):
        return self.teamMates     #'''

    def registerInitialState(self, gameState):
        """
        This method handles the initial setup of the
        agent to populate useful fields (such as what team
        we're on).
        
        A distanceCalculator instance caches the maze distances
        between each pair of positions, so your agents can use:
        self.distancer.getDistance(p1, p2)
        
        IMPORTANT: This method may run for at most 15 seconds.
        """
        
        '''
        Make sure you do not delete the following line. If you would like to
        use Manhattan distances instead of maze distances in order to save
        on initialization time, please take a look at
        CaptureAgent.registerInitialState in captureAgents.py.
        '''
        CaptureAgent.registerInitialState(self, gameState)
        
        
        self.teamMates = []
        for mate in self.getTeam(gameState):
            if mate is not self.index:
                self.teamMates.append(mate)
        
        def getSuccessors(walls, state):
            successors = []
            for action in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
                x,y = state
                dx, dy = Actions.directionToVector(action)
                nextx, nexty = int(x + dx), int(y + dy)
                if not walls[nextx][nexty]:
                    nextState = (nextx, nexty)
                    cost = 1
                    successors.append( ( nextState, action, cost) )
            return successors
        
        
                
        class o0State:
            def  __init__(self, pos, node = None):
                self.pos = pos
                self.node = node
                self.deadEndDepth = 0.0
                self.successors = {}
                self.successorsByNodePos = {}
            def isDeadEndNode(self):
                if self.node is None:
                    return False
                noneDeadEndCount = 0
                for successor in self.successors.values():
                    if not successor.isDeadEnd:
                        noneDeadEndCount += 1
                return noneDeadEndCount is 1
        class o0Node:
            def  __init__(self, pos):
                self.pos = pos
                self.isDeadEnd = False
        class o0Successor:
            def  __init__(self, direction, nextPos, nextNodePos = None):
                self.direction = direction
                self.nextPos = nextPos
                self.nextNodePos = nextNodePos
                self.isDeadEnd = False

        class o0PathMap:
            def  __init__(self, gameState):
                #print 'init pathMap'
                walls = gameState.getWalls()
                positions = walls.asList(False)
                self.states = {}
                self.nodes = {}
                for pos in positions:
                    self.states[pos] = o0State(pos)
                    for successor in getSuccessors(walls,pos):
                        self.states[pos].successors[successor[1]] = o0Successor(successor[1],successor[0])
                    successorCount = len(self.states[pos].successors)
                    if successorCount is not 2:
                        node = o0Node(pos)
                        self.nodes[pos] = node
                        self.states[pos].node = node
                
                def connectNode(node):
                    for nodeSuccessor in self.states[node.pos].successors.values():
                        if nodeSuccessor.nextNodePos is None:
                            forwardSuccessors = [nodeSuccessor]
                            backwardSuccessors = []
                            previousPos = node.pos
                            currentPos = nodeSuccessor.nextPos
                            while currentPos not in self.nodes.keys():
                                #print node.pos
                                #print currentPos
                                if len(self.states[currentPos].successors) is not 2:
                                    print 'not a path'
                                for successor in self.states[currentPos].successors.values():
                                    #print successor.nextPos
                                    if successor.nextPos[0] is previousPos[0] and successor.nextPos[1] is previousPos[1]:
                                        backwardSuccessors.append(successor)
                                    else:
                                        forwardSuccessors.append(successor)
                                previousPos = currentPos
                                currentPos = forwardSuccessors[len(forwardSuccessors) - 1].nextPos
                            for successor in self.states[currentPos].successors.values():
                                if successor.nextPos is previousPos:
                                    backwardSuccessors.append(successor)
                                    
                            for successor in forwardSuccessors:
                                successor.nextNodePos = currentPos
                            for successor in backwardSuccessors:
                                successor.nextNodePos = node.pos
                                
                #connectNode(self.nodes.values()[0])
                #connectNode(self.nodes.values()[1])
                #connectNode(self.nodes.values()[2])
                #connectNode(self.nodes.values()[3])
                #connectNode(self.nodes.values()[4])
                #connectNode(self.nodes.values()[5])
                
                for node in self.nodes.values():
                    connectNode(node)#'''
                for state in self.states.values():
                    for successor in self.states[state.pos].successors.values():
                        self.states[state.pos].successorsByNodePos[successor.nextNodePos] = successor
                
                updatedNodes = self.nodes.values()
                while(len(updatedNodes) is not 0):
                    nodePool = updatedNodes
                    updatedNodes = []
                    for node in nodePool:
                        if self.states[node.pos].isDeadEndNode():
                            self.nodes[node.pos].isDeadEnd = True
                            for successor in self.states[node.pos].successors.values():
                                self.states[successor.nextNodePos].successorsByNodePos[node.pos].isDeadEnd = True
                                updatedNodes.append(self.states[successor.nextNodePos])
                            
                        #node.isDeadEnd = self.states[node.pos].isDeadEndNode()#'''
                
                '''
                for node in self.nodes.values():
                    if self.states[node.pos].isDeadEndNode():
                        node.isDeadEnd = True#'''
                
                deadEndNodes = {}
                noneDeadEndNodes = {}
                for node in self.nodes.values():
                    if not node.isDeadEnd:
                        noneDeadEndNodes[node.pos] = node
                    else:
                        deadEndNodes[node.pos] = node
                        
                for node in deadEndNodes.values():#
                    actions = breadthFirstSearch(AnyTargetSearchProblem(gameState,noneDeadEndNodes.keys(),node.pos))
                    nodeConnectedTo = self.nodes[performActions(node.pos, actions)]                    
                    actions = reverseActions(actions)
                    pos = nodeConnectedTo.pos
                    deadEndDepth = 0.0
                    for action in actions:
                        pos = performActions(pos,[action])
                        deadEndDepth += 1.0
                        self.states[pos].deadEndDepth = deadEndDepth
            def willDie(self, position, distance, scaredTime = 0):#distance from our agent to closest enemy
                deadEndDepth = self.states[position].deadEndDepth
                if deadEndDepth >= distance - deadEndDepth and deadEndDepth >= scaredTime:
                    return True
                return False
            def isDeadEnd(self, position):
                return self.states[position].deadEndDepth >= 0.5
            #def getAllStatesInDeadEnd(self, anyState):
                

        global pathMap
        if pathMap is None:
            pathMap = o0PathMap(gameState)
        self.pathMap = pathMap
        targets[self.index] = None
        global lastEattenFoodAreDefendingPos
        lastEattenFoodAreDefendingPos = None       
        global totalFood
        totalFood = len(self.getFood(gameState).asList())
        global leftFood
        leftFood = totalFood
        #self.debugDraw(pathMap.deadEndNodes.keys(),[1,0,0])
        #self.debugDraw(pathMap.nodes.keys(),[0,1,0])
        
        global pathMapDebugMode
        if pathMapDebugMode:
            for state in self.pathMap.states.values():
                deadEndColor = 0.3 + state.deadEndDepth * 0.1
                if deadEndColor>1.0:
                    deadEndColor = 1.0
                if state.deadEndDepth == 0:
                    deadEndColor = 0.0
                
                nodeColor = 0.0
                if state.node is not None:
                    nodeColor = 0.5
                self.debugDraw(state.pos,[deadEndColor,0,0])

        self.curryFoodScore = 0.8
        
        
        
        global defenseWall
        global defensePositions
        if len(defenseWall) is 0:
            foods = self.getFoodYouAreDefending(gameState)
            for capsule in self.getCapsulesYouAreDefending(gameState):
                foods[capsule[0]][capsule[1]] = True
            defenseWall = actionsToPositions((0,0), aStarSearch(DefenseSearchProblem(gameState, foods, self.index),nullHeuristic))
            defensePositions = getPositionsNeededToDefense(gameState)
        global defenseWallDebugMode
        if defenseWallDebugMode is True:
            self.debugDraw(defenseWall,[0,0.5,0])
            self.debugDraw(defensePositions,[0.5,0,0])
       
        global agentInDeadEnd
        agentInDeadEnd[self.index] = False



    def chooseAction(self, gameState): 
        global leftFood
        leftFood = len(self.getFood(gameState).asList())
        self.startGameState = gameState
        self.depth = 1
        selfIndex = self.index
        self.visiableOpposites = self.getVisiableOpposites(gameState)
        visiableOpposites = self.visiableOpposites
         
        isInDeadEnd(self, gameState)
        #print agentInDeadEnd[self.index]
        
        
        
        global lastEattenFoodAreDefendingPos
        global defenseWall
        global defensePositions
        position = gameState.getAgentPosition(self.index) 
        originalPos = position
        if lastEattenFoodAreDefendingPos is not None and manhattanDistance(lastEattenFoodAreDefendingPos, position) <=1:
            lastEattenFoodAreDefendingPos = None

        if self.getPreviousObservation() is not None:
            foodsWas = self.getFoodYouAreDefending(self.getPreviousObservation()).copy()
            foodList = self.getFoodYouAreDefending(gameState).asList()
            for food in foodList:
                foodsWas[food[0]][food[1]] = False

            foodEatten = foodsWas.asList()

            if len(foodEatten) is not 0:
                lastEattenFoodAreDefendingPos = foodEatten[0] 
                    
            if len(foodList) is not len(foodsWas.asList()):
                foods = self.getFoodYouAreDefending(gameState)
                for capsule in self.getCapsulesYouAreDefending(gameState):
                    foods[capsule[0]][capsule[1]] = True
                defenseWall = actionsToPositions((0,0), aStarSearch(DefenseSearchProblem(gameState, foods, self.index),nullHeuristic))
                defensePositions = getPositionsNeededToDefense(gameState)
                global defenseWallDebugMode
                if defenseWallDebugMode is True:
                    self.debugClear() 
                    self.debugDraw(defenseWall,[0,0.5,0])
                    self.debugDraw(defensePositions,[0.5,0,0])
           
                
                
        
        global enemyScaredTime
        
        from capture import SCARED_TIME
        enemyScaredTime = SCARED_TIME
        for enemy in self.getOpponents(gameState):
            scaredTime = gameState.getAgentState(enemy).scaredTimer
            if scaredTime < enemyScaredTime:
                enemyScaredTime = scaredTime
        
        
        
        
        
        
        def findNewTarget():
            newTarget = {}
            foodTarget = o0FoodTarget(self,gameState)
            newTarget[foodTarget.getTargetValue(gameState)] = foodTarget
            foodReturnTarget = o0FoodReturnTarget(self,gameState)
            newTarget[foodReturnTarget.getTargetValue(gameState)] = foodReturnTarget
            killEnemyTarget = o0KillEnemyTarget(self,gameState)
            newTarget[killEnemyTarget.getTargetValue(gameState)] = killEnemyTarget
            #getOutDeadEndTarget = o0GetOutDeadEndTarget(self,gameState)
            #newTarget[getOutDeadEndTarget.getTargetValue(gameState)] = getOutDeadEndTarget
            defenseTarget = o0DefenseTarget(self,gameState)
            newTarget[defenseTarget.getTargetValue(gameState)] = defenseTarget
            eatCapsuleTarget = o0EatCapsuleTarget(self,gameState)
            newTarget[eatCapsuleTarget.getTargetValue(gameState)] = eatCapsuleTarget
            
            #print defenseTarget.getAgentNeededToDefense()
            
            
            targets[self.index] = newTarget[max(newTarget.keys())]    
            
            global targetDebugMode
            if targetDebugMode is True:
                print (self.index,targets[self.index].getTargetName())
        
        findNewTarget()
        
        
        global agentPathDebugMode
        if agentPathDebugMode:
            self.debugClear()            
            if self.index is 0:
                self.debugDraw(targets[self.index].getDebugDrawPositions(),[0,0.5,0])
            else:
                self.debugDraw(targets[self.index].getDebugDrawPositions(),[0,0,0.5])
        
        
        
        #print agentInDeadEnd[self.index]
        
        
        
        
        def inTeam(agentIndex):
            if agentIndex in self.getTeam(gameState):
                return True
            else:
                return False
                
        def evaluationFunction(gameState):
            position = gameState.getAgentPosition(self.index)
                
            #print gameState.getRedFood().width
            if self.pathMap.isDeadEnd(position):
                for enemyIndex in visiableOpposites:
                    if inOppositeArea(gameState, selfIndex) and self.pathMap.willDie(position, self.getMazeDistance(position, gameState.getAgentPosition(enemyIndex)), gameState.getAgentState(enemyIndex).scaredTimer):
                        return -99-self.pathMap.states[position].deadEndDepth
            
            
            score = 0
            
            for enemyIndex in visiableOpposites:#not fixed
                if manhattanDistance(self.startGameState.getAgentPosition(enemyIndex), gameState.getAgentPosition(enemyIndex)) > self.depth:#enemy dead
                    #print 'enemyDie'
                    score += 999
                    
            if targets[self.index] is not None:
                score += targets[self.index].getEvaluateValueToTarget(gameState)
            
            if originalPos[0] is position[0] and originalPos[1] is position[1]:
                score -= 0.000001
            

            return score
        
        def getAlphaBetaAgentAction(gameState, depth, agentIndex = 0, alpha = 999999, beta = -999999):
            #if gameState.isWin() or gameState.isLose() or depth == 0:
            if (agentIndex is self.index and depth is 0) or gameState.isOver():
                evaluationResult = evaluationFunction(gameState)
                return (None,evaluationResult)
            
            newAgentIndex = agentIndex + 1
            if agentIndex + 1 >= gameState.getNumAgents():
                newAgentIndex = 0
            newDepth = depth
            if agentIndex is self.index:
                newDepth -= 1
                
            if not self.visiable(gameState,agentIndex) or agentIndex in self.teamMates:
                return getAlphaBetaAgentAction(gameState, newDepth, newAgentIndex, alpha, beta);
                
            minOrMax = (max if inTeam(agentIndex) else min)
            score = newAlphaBetaScore = (beta if inTeam(agentIndex) else alpha)
            actionsWithScores = []
            #print (agentIndex,inTeam(agentIndex),gameState.makeObservation(agentIndex))
            for action in gameState.getLegalActions(agentIndex):
                alphaBetaResult = getAlphaBetaAgentAction(gameState.generateSuccessor(agentIndex,action), newDepth, newAgentIndex, (alpha if inTeam(agentIndex) else newAlphaBetaScore), (newAlphaBetaScore if inTeam(agentIndex) else beta))
                score = alphaBetaResult[1]
                newAlphaBetaScore = minOrMax(score,newAlphaBetaScore)
                if (inTeam(agentIndex) and score > alpha) or (not inTeam(agentIndex) and score < beta):
                    return (action,score)
                actionsWithScores.append((action,score))
            scores = [actionWithScore[1] for actionWithScore in actionsWithScores]
            return actionsWithScores[scores.index(minOrMax(scores))]
        
        

        #return getAgentAction(gameState, 3)[0]#'''
        result = getAlphaBetaAgentAction(self.getCurrentObservation(), self.depth, self.index)#'''
        #print targets[self.index].foodPos
        #print result
        return result[0]
    

############################################################
class SearchProblem:
    def getStartState(self):
        util.raiseNotDefined()
    def isGoalState(self, state):
        util.raiseNotDefined()
    def getSuccessors(self, state):
        util.raiseNotDefined()
    def getCostOfActions(self, actions):
        util.raiseNotDefined()

class PositionSearchProblem(SearchProblem):
    def __init__(self, gameState ,costFn = lambda x: 1, goal=(1,1), start=None, walls=None, warn=True, visualize=True):
        self.costGrid = None
        if walls is None:
            self.walls = gameState.getWalls()
        else:
            self.walls = walls
        if start is None: 
            self.startState = gameState.getPacmanPosition()
        else:
            self.startState = start
        self.goal = goal
        self.costFn = costFn
        self.visualize = visualize
        if warn and (gameState.getNumFood() != 1 or not gameState.hasFood(*goal)):
            print 'Warning: this does not look like a regular search maze'
        self._visited, self._visitedlist, self._expanded = {}, [], 0 # DO NOT CHANGE

    def getStartState(self):
        return self.startState

    def isGoalState(self, state):
        isGoal = state == self.goal
        if isGoal and self.visualize:
            self._visitedlist.append(state)
            import __main__
            if '_display' in dir(__main__):
                if 'drawExpandedCells' in dir(__main__._display): #@UndefinedVariable
                    __main__._display.drawExpandedCells(self._visitedlist) #@UndefinedVariable

        return isGoal

    def getSuccessors(self, state):
        successors = []
        for action in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
            x,y = state
            dx, dy = Actions.directionToVector(action)
            nextx, nexty = int(x + dx), int(y + dy)
            if not self.walls[nextx][nexty]:
                nextState = (nextx, nexty)
                if self.costGrid is None:
                    successors.append( ( nextState, action, self.costFn(nextState)) )
                else:
                    successors.append( ( nextState, action, self.costGrid[nextx][nexty]) )
                    

        # Bookkeeping for display purposes
        self._expanded += 1 # DO NOT CHANGE
        if state not in self._visited:
            self._visited[state] = True
            self._visitedlist.append(state)

        return successors

    def getCostOfActions(self, actions):
        if actions == None: return 999999
        x,y= self.getStartState()
        cost = 0
        for action in actions:
            # Check figure out the next state and see whether its' legal
            dx, dy = Actions.directionToVector(action)
            x, y = int(x + dx), int(y + dy)
            if self.walls[x][y]: return 999999
            cost += self.costFn((x,y))
        return cost
class AnyFoodSearchProblem(PositionSearchProblem):
    def __init__(self, walls, foods, position, costGrid = None):
        self.food = foods
        self.walls = walls
        self.startState = position
        self.costFn = lambda x: 1
        self.costGrid = costGrid
        self._visited, self._visitedlist, self._expanded = {}, [], 0 # DO NOT CHANGE

    def isGoalState(self, state):
        x,y = state
        return self.food[x][y]

class Queue:
    "A container with a first-in-first-out (FIFO) queuing policy."
    def __init__(self):
        self.list = []

    def push(self,item):
        "Enqueue the 'item' into the queue"
        self.list.insert(0,item)

    def pop(self):
        """
          Dequeue the earliest enqueued item still in the queue. This
          operation removes the item from the queue.
        """
        return self.list.pop()

    def isEmpty(self):
        "Returns true if the queue is empty"
        return len(self.list) == 0
import heapq
class PriorityQueue:
    """
      Implements a priority queue data structure. Each inserted item
      has a priority associated with it and the client is usually interested
      in quick retrieval of the lowest-priority item in the queue. This
      data structure allows O(1) access to the lowest-priority item.
    """
    def  __init__(self):
        self.heap = []
        self.count = 0

    def push(self, item, priority):
        entry = (priority, self.count, item)
        heapq.heappush(self.heap, entry)
        self.count += 1

    def pop(self):
        (_, _, item) = heapq.heappop(self.heap)
        return item

    def isEmpty(self):
        return len(self.heap) == 0

    def update(self, item, priority):
        # If item already in priority queue with higher priority, update its priority and rebuild the heap.
        # If item already in priority queue with equal or lower priority, do nothing.
        # If item not in priority queue, do the same thing as self.push.
        for index, (p, c, i) in enumerate(self.heap):
            if i == item:
                if p <= priority:
                    break
                del self.heap[index]
                self.heap.append((priority, c, item))
                heapq.heapify(self.heap)
                break
        else:
            self.push(item, priority)

def generatePathFromActionsTree(actionsTree, GoalState):#added method
    actions = []
    i = actionsTree[GoalState]
    while i[0] is not None:
        actions.append(i[0])        
        i = actionsTree[i[1]]
    actions.reverse()
    return actions    
def breadthFirstSearch(problem):
    """Search the shallowest nodes in the search tree first."""
    "*** YOUR CODE HERE ***"
    borders = Queue()
    borders.push(problem.getStartState())    
    actionsTree = {problem.getStartState():(None,None)}#action,last state
    GoalState = None
    while not borders.isEmpty():
        currentState = borders.pop()
        if problem.isGoalState(currentState):
            GoalState = currentState
            break
        for successor in problem.getSuccessors(currentState):
            if successor[0] not in actionsTree:
                actionsTree[successor[0]]=(successor[1],currentState)
                borders.push(successor[0])
    if GoalState is None:
        #print 'bfs cannot find goal'
        return []
    return generatePathFromActionsTree(actionsTree,GoalState)
    util.raiseNotDefined()
def manhattanHeuristic(position, problem, info={}):
    "The Manhattan distance heuristic for a PositionSearchProblem"
    xy1 = position
    xy2 = problem.goal
    return abs(xy1[0] - xy2[0]) + abs(xy1[1] - xy2[1])
def nullHeuristic(state, problem=None):
    return 0
def aStarSearch(problem, heuristic = manhattanHeuristic):
    borders = PriorityQueue()
    borders.push(problem.getStartState(),0)
    
    actionsTree = {problem.getStartState():(None,None,0)}#action,last state
    
    GoalState = None
    while not borders.isEmpty():
        currentState = borders.pop()
        if problem.isGoalState(currentState):
            GoalState = currentState
            break
        for successor in problem.getSuccessors(currentState):
            totalStateCost = actionsTree[currentState][2]+successor[2]
            heuristicCost = heuristic(successor[0],problem)
            aStarCost = totalStateCost + heuristicCost
            if successor[0] not in actionsTree:
                actionsTree[successor[0]]=(successor[1],currentState,totalStateCost)
                borders.push(successor[0],aStarCost)
            elif aStarCost < actionsTree[successor[0]][2] + heuristicCost:#border repeat
                actionsTree[successor[0]]=(successor[1],currentState,totalStateCost)
                borders.update(successor[0], aStarCost)
    
    if GoalState is None:
        #print 'astar cannot find goal'
        return []
    return generatePathFromActionsTree(actionsTree,GoalState)
    util.raiseNotDefined()
def closestFoodRealDistance(gameState, foods, position):
    prob = AnyFoodSearchProblem(gameState, foods, position)
    return len(breadthFirstSearch(prob))
def mazeDistance(point1, point2, gameState, givenWalls = None):
    prob = PositionSearchProblem(gameState, start=point1, walls=givenWalls, goal=point2, warn=False, visualize=False)
    return len(aStarSearch(prob))







def inOppositeArea(gameState, agentIndex, state = None):
    if state is None:
        state = gameState.getAgentPosition(agentIndex)
    if state[0] < gameState.getWalls().width / 2:
        return not gameState.isOnRedTeam(agentIndex)
    else:
        return gameState.isOnRedTeam(agentIndex)  
class FoodReturnProblem(PositionSearchProblem):
    def __init__(self, gameState, foods, position,agentIndex, walls = None, costGrid = None):
        self.costGrid = costGrid
        self.gameState = gameState
        self.agentIndex = agentIndex
        self.food = foods
        if walls is None:
            self.walls = gameState.getWalls()
        else:
            self.walls = walls            
        self.startState = position
        self.costFn = lambda x: 1
        self._visited, self._visitedlist, self._expanded = {}, [], 0 # DO NOT CHANGE

    def isGoalState(self, state):#on opposite
        return not inOppositeArea(self.gameState,self.agentIndex, state)   
def foodReturnDistance(gameState, foods, position, agentIndex,walls, costGrid = None):
    prob = FoodReturnProblem(gameState, foods, position, agentIndex,walls,costGrid)
    return len(aStarSearch(prob,nullHeuristic))

    

class InEquivalentCostSearchProblem(PositionSearchProblem):
    def __init__(self, walls, start, goal ,costs):
        self.goal = goal
        self.walls = walls
        self.startState = start
        self.costs = costs
        self.costFn = lambda x: 1
        self.visualize = False
        self._visited, self._visitedlist, self._expanded = {}, [], 0 # DO NOT CHANGE

    def getSuccessors(self, state):
        successors = []
        for action in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
            x,y = state
            dx, dy = Actions.directionToVector(action)
            nextx, nexty = int(x + dx), int(y + dy)
            if not self.walls[nextx][nexty]:
                nextState = (nextx, nexty)
                cost = self.costs[nextx][nexty]
                successors.append( ( nextState, action, cost) )

        # Bookkeeping for display purposes
        self._expanded += 1 # DO NOT CHANGE
        if state not in self._visited:
            self._visited[state] = True
            self._visitedlist.append(state)

        return successors   



class DefenseSearchProblem(PositionSearchProblem):
    def __init__(self, gameState, foods, agentIndex):
        self.gameState = gameState
        self.walls = gameState.getWalls().copy()
        self.agentIndex = agentIndex
        self.costFn = lambda x: 1
        self.visualize = False
        self._visited, self._visitedlist, self._expanded = {}, [], 0 # DO NOT CHANGE
        if gameState.isOnRedTeam(agentIndex):
            #self.startState = (self.walls.width/2 -1,0)
            self.startState = (0,0)
            self.goal = (self.walls.width/2 -1,self.walls.height-1)
            
            self.foods = [0 for _ in range(foods.height)]
            for y in range(foods.height):
                for x in reversed(range(0, foods.width/2)):
                    if foods[x][y] is True:
                        self.foods[y] = x
                        break
        else:
            #self.startState = (self.walls.width/2,0)
            self.startState = (0,0)
            self.goal = (self.walls.width/2,self.walls.height-1)
            
            self.foods = [foods.width - 1 for _ in range(foods.height)]
            for y in range(foods.height):
                for x in range(foods.width/2, foods.width):
                    if foods[x][y] is True:
                        #print (x,y)
                        self.foods[y] = x
                        break
            
    def inMap(self, x, y):
        if x > 0 and y >= 0 and x < (self.walls.width - 1) and y < self.walls.height:
            return True
        return False 
    def inMapAndIsWall(self, x, y):
        if self.inMap(x,y) and self.walls[x][y]:
            return True
        return False 

    def getSuccessors(self, state):
        successors = []
        for action in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
            x,y = state
            dx, dy = Actions.directionToVector(action)
            nextx, nexty = int(x + dx), int(y + dy)
            if self.inMap(nextx,nexty):
                nextState = (nextx, nexty)
                if self.gameState.isOnRedTeam(self.agentIndex):
                    if (nextx >= self.walls.width/2 and (nexty is not 0 or nexty is not (self.walls.height-1))) or nextx <= self.foods[nexty]:
                        cost = 999
                    elif not self.walls[nextx][nexty]:
                        cost = 1
                    elif self.walls[x][y]:
                        cost = 0
                    else:
                        cost = 0.5
                else:
                    if (nextx < self.walls.width/2 and (nexty is not 0 or nexty is not (self.walls.height-1))) or nextx >= self.foods[nexty]:
                        cost = 999
                    elif not self.walls[nextx][nexty]:
                        cost = 1
                    elif self.walls[x][y]:
                        cost = 0
                    else:
                        cost = 0.5
                successors.append( ( nextState, action, cost) )

        # Bookkeeping for display purposes
        self._expanded += 1 # DO NOT CHANGE
        if state not in self._visited:
            self._visited[state] = True
            self._visitedlist.append(state)

        return successors



def performActions(position, actions):
    x = position[0]
    y = position[1]
    for action in actions:
        vector = Actions.directionToVector(action)
        x += vector[0]
        y += vector[1]
    return (int(x),int(y))

def reverseActions(actions):
    reversedActions = []
    for action in actions:
        reversedActions.append(Actions.reverseDirection(action))
    reversedActions.reverse()
    return reversedActions

def drawPathAsCostOnGrid(costGrid, position, actions, cost):
    for action in actions:
        costGrid[position[0]][position[1]] = cost
        position = performActions(position, [action]) 
    return costGrid
def drawPathAsCurveCostOnGrid(costGrid, position, actions, cost):
    distanceToTarget = len(actions)
    for action in actions:
        costGrid[position[0]][position[1]] = cost / distanceToTarget
        position = performActions(position, [action])
        distanceToTarget -= 1
    return costGrid
def drawLastNumberOfPathAsCostOnGrid(costGrid, position, actions, cost, number):
    unDraw = len(actions) - number
    for action in actions:
        if unDraw <= 0:
            costGrid[position[0]][position[1]] = cost
        position = performActions(position, [action])
        unDraw -= 1
    return costGrid
def drawEnemyAsCostOnGrid(costGrid, position, gameState,index , value = 20):
    costGrid[position[0]][position[1]] += value
    state = (position[0] + 1,position[1])
    if inOppositeArea(gameState, index, state):
        costGrid[state[0]][state[1]] += value
    state = (position[0] - 1,position[1])
    if inOppositeArea(gameState, index, state):
        costGrid[state[0]][state[1]] += value
    state = (position[0],position[1] + 1)
    if inOppositeArea(gameState, index, state):
        costGrid[state[0]][state[1]] += value
    state = (position[0],position[1] - 1)
    if inOppositeArea(gameState, index, state):
        costGrid[state[0]][state[1]] += value
    return costGrid
        
    
def assignCostToGrid(costGrid, states, cost):
    for state in states:
        costGrid[state[0]][state[1]] = cost
    return costGrid
def getInitCostGrid(gameState):
    costGrid = gameState.getWalls().copy()
    costGrid = assignCostToGrid(costGrid, costGrid.asList(), 1)
    return costGrid
def heavyCostGridSidesWeight(costGrid):#side add 2 mid add 0
    halfWIndex = float(costGrid.width - 1.0)/2.0
    for w in range(costGrid.width):
        for h in range(costGrid.height):
            costGrid[w][h] += abs(float(w) - halfWIndex) / halfWIndex * 2
    return costGrid#

def weightedMazeDistance(point1, point2, gameState, costGrid = None):
    if costGrid is None:
        costGrid = getInitCostGrid(gameState)
    prob = InEquivalentCostSearchProblem(gameState.getWalls(), point1, point2, costGrid)
    return len(aStarSearch(prob))

def actionsToPositions(startPosition, actions):
    positions = []
    if actions is not None:
        position = startPosition
        for action in actions:
            position = performActions(position, [action])
            positions.append(position)
    return positions


def getAgentNeededToDefense(gameState):
    global defenseWall
    walls = gameState.getWalls().copy()
    empty = 0
    agent = 0
    for state in defenseWall:
        if not walls[state[0]][state[1]]:
            empty += 1
        else:
            agent += (empty + 2) / 3
            empty = 0
    return agent
def getPositionsNeededToDefense(gameState):
    global defenseWall
    walls = gameState.getWalls().copy()
    segments = []
    states = []
    for state in defenseWall:
        if not walls[state[0]][state[1]]:
            states.append(state)
        elif len(states) is not 0:
            segments.append(states)
            states = []        
    positions = []
    for segment in segments:
        agentNum = (len(segment) + 2) / 3
        length = float(len(segment)) / agentNum
        for i in range(agentNum):
            positions.append(segment[int((0.5 + i)*length)])            
    return positions



def isInDeadEnd(dummyAgent, gameState):
    global agentInDeadEnd
    if agentInDeadEnd[dummyAgent.index] is True:
        if not inOppositeArea(gameState, dummyAgent.index):
            agentInDeadEnd[dummyAgent.index] = False
            return False
        else:
            return True
    
    if inOppositeArea(gameState, dummyAgent.index):
        walls = gameState.getWalls().copy()     
        for oppoIndex in dummyAgent.visiableOpposites:
            if not inOppositeArea(gameState, oppoIndex) and gameState.getAgentState(oppoIndex).scaredTimer is 0:
                oppoPos = gameState.getAgentPosition(oppoIndex)
                walls[oppoPos[0]][oppoPos[1]] = True
        if  mazeDistance(gameState.getAgentPosition(dummyAgent.index), gameState.getInitialAgentPosition(dummyAgent.index), gameState, walls) is 0:
            agentInDeadEnd[dummyAgent.index] = True
            return True
    return False




class AnyTargetSearchProblem(PositionSearchProblem):
    def __init__(self, gameState, targets, position, costGrid = None,walls = None):
        self.costGrid = costGrid
        self.targets = targets#list
        if walls is None:  
            self.walls = gameState.getWalls()
        else:
            self.walls = walls
        self.startState = position
        self.costFn = lambda x: 1
        self._visited, self._visitedlist, self._expanded = {}, [], 0 # DO NOT CHANGE        
    def isGoalState(self, state):
        for target in self.targets:
            if target[0] is state[0] and target[1] is state[1]:
                return True
        return False
