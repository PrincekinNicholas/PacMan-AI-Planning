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

from game import Directions
from captureAgents import CaptureAgent
import random, time, util, sys
from util import nearestPoint
import math

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first='ReflexCaptureAgent', second='ReflexCaptureAgent'):
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
    return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########
class ReflexCaptureAgent(CaptureAgent):
    """
    A base class for reflex agents that chooses score-maximizing actions
    """

    def genericSearch(self, start_position, goal_position, open_list, cost, walls,problem,goalList,gameState):
        """
        A generic search for different data structure
        :param problem:
        :param open_list: the data structure
        :return: the selected path from initial state to goal state
        """
        open_list.push((start_position, []))

        visited = []

        # Traverse all unvisited nodes
        while not open_list.isEmpty():
            current_state, actions = open_list.pop()

            if current_state not in visited:
                visited.append(current_state)

                if problem == "findFood" or problem == "findCapsule" or problem == "goHome" or problem == "goToBoundry" or problem=="chasePacmanWhenScared":
                    if current_state in goalList:
                        if(problem == "findFood"):
                            self.lastGoalFood = current_state
                        return actions
                elif problem == "chasePacman":
                    if current_state == goal_position:
                        return actions

                for state, action, cost in self.getSuccessorsForAstar(current_state, cost,walls):
                    # and self.foodSearchHeuristic(start_position, state,gameState)<=500
                    if state not in visited :
                        open_list.push((state, actions + [(state,action)]))
        return []

    def getSuccessorsForAstar(self, state, cost,walls):
        successorList = []
        for action in self.getLegalActions(state,walls):
            nextState = self.getSuccessorPosition(state, action)
            successorList.append((nextState,action,cost))
        return successorList

    def aStarSearch(self, start_position, goal_position, cost, walls,problem,gameState,goalList):
        """Search the node that has the lowest combined cost and heuristic first."""

        if problem == "findFood" or problem == "findCapsule" or problem == "goHome":
            frontier = util.PriorityQueueWithFunction(lambda node: len(node[1]) + self.foodSearchHeuristic(start_position,node[0],gameState))
        elif problem == "chasePacman":
            frontier = util.PriorityQueueWithFunction(lambda node: len(node[1]))
        else:
            frontier = util.PriorityQueueWithFunction(lambda node: len(node[1]))
        actions = self.genericSearch(start_position, goal_position, frontier, cost, walls,problem,goalList,gameState)
        return actions

    def foodSearchHeuristic(self, start_position, next_position,gameState):
        x,y = next_position
        heuristic = 0
        if(len(self.getGhostOpponetsPositions(gameState))!=0):
            for p in self.getGhostOpponetsPositions(gameState):
                distanceToOpponent = self.getMazeDistance(next_position,p)
                if distanceToOpponent<=2:
                    if(self.isOnRedTeam):
                        if x>=self.mapWidth/2:
                            heuristic += (5 - distanceToOpponent)**6
                    else:
                        if x < self.mapWidth/2:
                            heuristic += (5 - distanceToOpponent)**6
        return heuristic

    def getOpponetsPositions(self,gameState):
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaderPositions = [a.getPosition() for a in enemies if a.getPosition() != None]
        return invaderPositions


    def getNotScaredOpponetsPositions(self,gameState):
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaderPositions = [a.getPosition() for a in enemies if (a.isPacman or (not a.isPacman and a.getPosition() in self.enemyDMZ)) and  a.scaredTimer == 0 and a.getPosition() != None]
        return invaderPositions

    def getGhostOpponetsPositions(self,gameState):
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaderPositions = [a.getPosition() for a in enemies if  not a.isPacman and  a.scaredTimer == 0 and a.getPosition() != None]
        return invaderPositions


    def getGhostOpponetsPositionsWithinDistance(self,gameState):
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaders= [a for a in enemies if not a.isPacman and a.getPosition() != None]
        invaderWithinDistance= []
        if(len(invaders)>0):
            for invader in invaders:
                if(self.getMazeDistance(gameState.getAgentPosition(self.index),invader.getPosition())<=5):
                    invaderWithinDistance.append(invader)
        return invaderWithinDistance

    def isNearOpponentScared(self,gameState):
        invaderWithinDistance = self.getGhostOpponetsPositionsWithinDistance(gameState)
        if(len(invaderWithinDistance)>0):
            for invader in invaderWithinDistance:
                if invader.scaredTimer <= 5:
                    return False
        return True

    # for chasePacman
    def getNearestOpponet(self,gameState):
        minDistance = 9999
        nearestOpponet = None
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaderPositions = [a.getPosition() for a in enemies if a.isPacman and a.getPosition() != None]
        if(len(invaderPositions)>0):
            for position in invaderPositions:
                distance = self.getMazeDistance(gameState.getAgentPosition(self.index), position)
                if(minDistance > distance):
                    minDistance = distance
                    nearestOpponet = position
        return nearestOpponet

    def getNearestGhost(self,gameState):
        minDistance = 9999
        nearestOpponet = None
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaderPositions = [a.getPosition() for a in enemies if not a.isPacman and a.getPosition() != None]
        if(len(invaderPositions)>0):
            for position in invaderPositions:
                distance = self.getMazeDistance(gameState.getAgentPosition(self.index), position)
                if(minDistance > distance):
                    minDistance = distance
                    nearestOpponet = position
        return nearestOpponet

    def getSafePositionAroundPacman(self,gameState,walls):
        pacman = self.getNearestOpponet(gameState)
        safePositionList = []
        if(pacman != None):
            if(self.getLegalSuccessorPositions(pacman,walls) != []):
                for position in self.getLegalSuccessorPositions(pacman,walls):
                    if(self.getLegalSuccessorPositions(position,walls) != []):
                        for twoStepsPosition in self.getLegalSuccessorPositions(position,walls):
                            if(not twoStepsPosition==pacman):
                                safePositionList.append(twoStepsPosition)
        return safePositionList

    def isExistPacman(self,gameState):
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaders = [a for a in enemies if a.isPacman or a.getPosition() in self.enemyDMZ]
        if(len(invaders)>0):
            return True
        return False

    def getOpponetsMinDistance(self,gameState):
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaders = [a for a in enemies if a.getPosition() != None]
        minDistance = 999999
        if(len(invaders)>0):
            minDistance = min([self.getMazeDistance(gameState.getAgentPosition(self.index), a.getPosition()) for a in invaders])
        return minDistance

    def getCapsuleMinDistance(self,gameState):
        minDistance = 9999
        distances = [self.getMazeDistance(gameState.getAgentPosition(self.index), capsule) for capsule in self.getCapsules(gameState)]
        if len(distances) >0:
            minDistance = min(distances)
        return minDistance

    def getSafeFoodList(self,foodList):
        safeFoodList = foodList[:]
        for position in self.deadEnds:
            if position in safeFoodList:
                safeFoodList.remove(position)
        return safeFoodList

    def getUpperHalfFoodList(self,foodList):
        upperHalfFoodList = foodList[:]
        for i in range(self.mapWidth):
            for j in range(self.mapHeight/2):
                if (i,j) in upperHalfFoodList:
                    upperHalfFoodList.remove((i,j))
        return upperHalfFoodList

    def getUpperHalfSafeFoodList(self,foodList):
        upperHalfSafeFoodList = self.getSafeFoodList(foodList)[:]
        for i in range(self.mapWidth):
            for j in range(self.mapHeight/2):
                if (i,j) in upperHalfSafeFoodList:
                    upperHalfSafeFoodList.remove((i,j))
        return upperHalfSafeFoodList

    def getBottomHalfSafeFoodList(self,foodList):
        bottomHalfSafeFoodList = self.getSafeFoodList(foodList)[:]
        for i in range(self.mapWidth):
            for j in range(self.mapHeight/2,self.mapHeight):
                if (i,j) in bottomHalfSafeFoodList:
                    bottomHalfSafeFoodList.remove((i,j))
        return bottomHalfSafeFoodList

    def getBottomHalfFoodList(self,foodList):
        bottomHalfFoodList = foodList[:]
        for i in range(self.mapWidth):
            for j in range(self.mapHeight/2,self.mapHeight):
                if (i,j) in bottomHalfFoodList:
                    bottomHalfFoodList.remove((i,j))
        return bottomHalfFoodList

# consider when no path  bug free
    def getDeadEnd(self,gameState,walls):
        states = util.Counter()
        index = 1
        for state in self.getGameStates(gameState):
            if(len(self.getLegalActions(state,walls))==1):
                states[state] = index
                index += 1
        return states

    def getAllDeadEnds(self,gameState,walls):
        tunnels = self.getDeadEnd(gameState,walls)
        tunnel_index = 0
        new_tunnels = tunnels.copy()
        while(len(new_tunnels) != 0):
            tunnels.update(new_tunnels)
            tunnel_temp = new_tunnels.copy()
            new_tunnels = util.Counter()
            for tunnel in tunnel_temp:
                for successor in self.getLegalSuccessorPositions(tunnel,self.walls):
                    count = 0
                    for next in self.getLegalSuccessorPositions(successor,self.walls):
                        if not next in tunnels:
                            count += 1
                        if next in tunnels:
                            tunnel_index = tunnels[next]
                    if count ==1:
                        new_tunnels[successor] = tunnel_index
        # for i in tunnels:
        #     self.debugDraw(i,[.4,.4,.4],False)
        return tunnels

    def getLegalSuccessorPositions(self,state,walls):
        successorList = []
        actionList = ["North","South","East","West"]
        for action in actionList:
            successorPosition = self.getSuccessorPosition(state,action)
            x, y = successorPosition
            if not walls[int(x)][int(y)]:
                successorList.append(successorPosition)
        return successorList

    def getLegalActions(self,state,walls):
        actions = ['South','North','East','West']
        legalActions =[]
        for a in actions:
            x,y =self.getSuccessorPosition(state,a)
            if(not walls[int(x)][int(y)]):
                legalActions.append(a)
        return legalActions

    def getSuccessorPosition(self,state,action):
        i, j = state
        if action == "North":
            nextState = (i, j+1)
        elif action == "South":
            nextState = (i, j-1)
        elif action == "East":
            nextState = (i+1, j)
        else:
            nextState = (i-1, j)
        return nextState

    def getGameStates(self, gameState):
        gameStates=[]
        walls = self.walls
        mapWidth = walls.width
        mapHeight = walls.height
        for i in range(mapWidth):
            for j in range(mapHeight):
                if not walls[i][j]:
                    gameStates.append((i,j))
        return gameStates

    def registerInitialState(self, gameState):
                # Get Walls
        self.walls = gameState.getWalls()
        self.mapWidth = self.walls.width
        self.mapHeight = self.walls.height
        self.deadEnds = self.getAllDeadEnds(gameState, self.walls)

        # get Demilitized Zone (DMZ)
        redDMZ = []
        blueDMZ = []
        for idx, e in enumerate(self.walls[self.mapWidth / 2 - 1][1:self.mapHeight - 1]):
            if e is False:
                redDMZ.append((self.mapWidth / 2 - 1, idx + 1))
        for idx, eb in enumerate(self.walls[self.mapWidth / 2][1:self.mapHeight - 1]):
            if eb is False:
                blueDMZ.append((self.mapWidth / 2, idx + 1))


        self.redWall = self.walls.copy()
        for i in range(self.mapWidth/2,self.mapWidth):
            for j in range(self.mapHeight):
                self.redWall[i][j] = True

        self.blueWall = self.walls.copy()
        for i in range(self.mapWidth/2):
            for j in range(self.mapHeight):
                self.blueWall[i][j] = True

        # all global varibles considering we are red or blue should be put after this initial function
        CaptureAgent.registerInitialState(self, gameState)
        start = time.time()
        self.defendingFoodList = self.getFoodYouAreDefending(gameState).asList()
        self.foodList = self.getFoodYouAreDefending(gameState).asList()
        self.lastRoundDefendingFoodList = self.getFoodYouAreDefending(gameState).asList()
        self.lastEatenFood = ()
        self.lastGoalFood = ()
        # self.foodListToEat = self.getFood(gameState).asList()
        # self.safeFoodListToEat = self.getSafeFoodList(self.foodListToEat)
        self.start = gameState.getAgentPosition(self.index)

        # initialize agent
        self.isOnRedTeam = gameState.isOnRedTeam(self.index)

        if self.index == 0 or self.index == 1:
            self.order = 1
            self.type = 1
        else:
            self.order = 2
            self.type = 2

        # get my and opponent's DMZ
        if self.isOnRedTeam:
            self.myDMZ = redDMZ
            self.enemyDMZ = blueDMZ
        else:
            self.myDMZ = blueDMZ
            self.enemyDMZ = redDMZ

        calTime = time.time() - start
        if calTime > 1:
            print('initial calculation Time %d: %.4f' % (self.index, time.time() - start))

    # To do
    def isOpponentScared(self, gameState):
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaders = [a for a in enemies if a.getPosition() != None]
        if len(invaders)>0:
            for a in invaders:
                if self.getMazeDistance(gameState.getAgentPosition(self.index), a.getPosition()) <= 5 and a.scaredTimer <=5:
                    return False
        return True

    def isAnyOpponentNotScared(self,gameState):
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        for a in enemies:
            if a.scaredTimer == 0:
                return True
        return False

    def getFarestFood(self,foodList,gameState):
        maxDistance = 0
        farestFood = ()
        invaders = self.getGhostOpponetsPositionsWithinDistance(gameState)
        for food in foodList:
            if len(invaders)>0:
                distance = min([self.getMazeDistance(gameState.getAgentPosition(self.index), food) for invader in invaders])
                if(distance > maxDistance):
                    maxDistance = distance
                    farestFood  = food
        return farestFood

    def getMinDistanceToFood(self,gameState,foodList):
        distance = [self.getMazeDistance(gameState.getAgentPosition(self.index),food) for food in foodList]
        if(len(distance)>0):
            minDistance = min(distance)
        return minDistance

    def getReachableFoodList(self,gameState,foodList):
        # foodList = self.getFood(gameState).asList()
        invaders = self.getOpponetsPositions(gameState)
        reachableFoodList = []
        if(len(foodList)>0):
            for food in foodList:
                minDistance = min([self.getMazeDistance(invader,food) for invader in invaders])
                if self.getMazeDistance(gameState.getAgentPosition(self.index),food) < minDistance:
                    reachableFoodList.append(food)
        return reachableFoodList

    def chooseOffensiveAction(self,gameState,eatenFood,capsuleList,safeFoodList,foodList,foodLeft):
        currentPosition = gameState.getAgentPosition(self.index)
        escapeDistance = min([self.getMazeDistance(currentPosition, dmz) for dmz in self.myDMZ])
        distance = [self.getMazeDistance(currentPosition, food) for food in foodList]
        minDistance = 9999
        if(len(distance)>0):
            minDistance = min(distance)

        if(foodLeft<=2 or (eatenFood >= 8 and not self.isOpponentScared(gameState) and minDistance>2) or (gameState.data.timeleft/4 <= escapeDistance + 5 and eatenFood > 0) or (eatenFood>=3 and eatenFood >=escapeDistance+2)):
            astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, self.walls,"goHome",gameState,self.myDMZ)
        elif self.getCapsuleMinDistance(gameState) <= 7 and self.isAnyOpponentNotScared(gameState):
            astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, self.walls,"findCapsule",gameState,capsuleList)
        elif self.getOpponetsMinDistance(gameState) <= 5:
            if self.isNearOpponentScared(gameState):
                astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, self.walls,"findFood",gameState, foodList)
            elif self.getCapsuleMinDistance(gameState) <= 5:
                astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, self.walls,"findCapsule",gameState,capsuleList)
            else:
                if(len(safeFoodList)>0):
                    astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, self.walls,"findFood",gameState,safeFoodList)
                    for i in astarActions:
                        if(self.getNearestGhost(gameState)==i[0] and self.getMazeDistance(self.getNearestGhost(gameState),currentPosition)<=2):
                            astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, self.walls,"goHome",gameState,self.myDMZ)
                else:
                    astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, self.walls,"goHome",gameState,self.myDMZ)
        else:
            astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, self.walls,"findFood",gameState,foodList)

        return astarActions

    def chooseDefensiveAction(self,gameState,foodList,safeFoodList,eatenFood,capsuleList):
        foodsLeft = self.getFoodYouAreDefending(gameState).asList()
        foodEaten = list(set(self.lastRoundDefendingFoodList).difference(set(foodsLeft)))
        currentPosition = gameState.getAgentPosition(self.index)
        escapeDistance = min([self.getMazeDistance(currentPosition, dmz) for dmz in self.myDMZ])

        if(len(foodEaten)>0):
            self.lastEatenFood = foodEaten[0]
        if(self.isOnRedTeam):
            walls = self.redWall
        else:
            walls = self.blueWall

        currentAgentState = gameState.getAgentState(self.index)
        if((not self.isExistPacman(gameState) or currentAgentState.scaredTimer>10) and self.getMinDistanceToFood(gameState,foodList)<=10):
            astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, self.walls,"findFood",gameState,safeFoodList)
        elif(currentAgentState.isPacman):
            if(eatenFood>=3 or gameState.data.timeleft/4 <= escapeDistance + 5 or eatenFood >=escapeDistance+2):
                astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, self.walls,"goHome",gameState,self.myDMZ)
            elif self.getOpponetsMinDistance(gameState) <= 5:
                if self.isNearOpponentScared(gameState):
                    astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, self.walls,"findFood",gameState, foodList)
                elif self.getCapsuleMinDistance(gameState) <= 3:
                    astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, self.walls,"findCapsule",gameState,capsuleList)
                else:
                    astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, self.walls,"findFood",gameState,safeFoodList)
            else:
                astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, self.walls,"findFood",gameState,foodList)

        elif(not currentAgentState.isPacman):
            if(self.getOpponetsMinDistance(gameState) <= 5):
                if(currentAgentState.scaredTimer>0):
                    safePositionAroundPacman = self.getSafePositionAroundPacman(gameState,walls)
                    if(safePositionAroundPacman != []):
                        astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (), 1, walls,"chasePacmanWhenScared",gameState,safePositionAroundPacman)
                    else:
                        astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, walls,"goToBoundry",gameState,self.myDMZ)
                else:
                    astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), self.getNearestOpponet(gameState), 1, walls,"chasePacman",gameState,[])
            elif(self.lastEatenFood and not self.lastEatenFood == gameState.getAgentPosition(self.index)):
                astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), self.lastEatenFood, 1, walls,"chasePacman",gameState,[])

            else:
                self.lastEatenFood = ()
                astarActions = self.aStarSearch(gameState.getAgentPosition(self.index), (0,0), 1, walls,"goToBoundry",gameState,self.myDMZ)

        return astarActions


    def chooseAction(self, gameState):
        """
        Picks among the actions with the highest Q(s,a).
        """
        start = time.time()
        actions = gameState.getLegalActions(self.index)
        actions.remove('Stop')

        currentSate = gameState.getAgentState(self.index)
        allFoodList = self.getFood(gameState).asList()
        capsuleList = self.getCapsules(gameState)
        foodLeft = len(self.getFood(gameState).asList())
        allSafeFoodList = self.getSafeFoodList(allFoodList)

        eatenFood = gameState.getAgentState(self.index).numCarrying

        astarActions = []
        if(self.type == 1):
            astarActions = self.chooseOffensiveAction(gameState,eatenFood,capsuleList,allSafeFoodList,allFoodList,foodLeft)
        elif(self.type == 2):
            astarActions = self.chooseDefensiveAction(gameState,allFoodList,allSafeFoodList,eatenFood,capsuleList)

        # record last round defending foods
        if self.type == 2:
            self.lastRoundDefendingFoodList = self.getFoodYouAreDefending(gameState).asList()

        if len(astarActions)>0:
            evalTime = time.time() - start
            if evalTime > 1:
                print('OH SHIT, the eval time to choose action for agent %d: %.4f' % (self.index, time.time() - start))

            return astarActions[0][1]

        print "astar return no path",self.type

        values = [self.evaluate(gameState, a) for a in actions]

        maxValue = max(values)

        bestActions = [a for a, v in zip(actions, values) if v == maxValue]

        if foodLeft <= 2:
            bestDist = 9999
            for action in actions:
                successor = self.getSuccessor(gameState, action)
                pos2 = successor.getAgentPosition(self.index)
                dist = self.getMazeDistance(self.start, pos2)
                if dist < bestDist:
                    bestAction = action
                    bestDist = dist
            return bestAction

        bestAction = random.choice(bestActions)

        evalTime = time.time() - start
        if evalTime > 1:
            print('OH SHIT, the eval time to choose action for agent %d: %.4f' % (self.index, time.time() - start))

        return bestAction

    def getSuccessor(self, gameState, action):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != nearestPoint(pos):
            # Only half a grid position was covered
            return successor.generateSuccessor(self.index, action)
        else:
            return successor

    def evaluate(self, gameState, action):
        """
        Computes a linear combination of features and feature weights
        """

        if self.type == 1:
            features = self.getOffensiveFeatures(gameState, action)
            weights = self.getOffensiveWeights()
        else:
            features = self.getDefensiveFeatures(gameState, action)
            weights = self.getDefensiveWeights()
        return features * weights

    def getOffensiveFeatures(self, gameState, action):

        features = util.Counter()

        successor = self.getSuccessor(gameState, action)
        foodList = self.getFood(successor).asList()
        features['successorScore'] = -len(foodList)

        successorPos = successor.getAgentState(self.index).getPosition()
        myPos = gameState.getAgentState(self.index).getPosition()

        if len(foodList) > 0:  # This should always be True,  but better safe than sorry
            minDistance = min([self.getMazeDistance(successorPos, food) for food in foodList])
            features['distanceToFood'] = minDistance

        # Consider enemies when attack
        escape = False

        if(gameState.getAgentState(self.index).scaredTimer>0):
            enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
            invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
            if(len(invaders)>0):
                dists = [self.getMazeDistance(successorPos, a.getPosition()) for a in invaders]
                if(min(dists)<=3):
                    features['invaderDistance'] = min(dists)

        if(gameState.getAgentState(self.index).isPacman):
            escape = True

        if(not gameState.getAgentState(self.index).isPacman and successor.getAgentState(self.index).isPacman):
            escape = True

        if escape == True:
            enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
            invaders = [a for a in enemies if not a.isPacman and a.scaredTimer<=2 and a.getPosition() != None]
            features['numInvaders'] = len(invaders)
            if len(invaders) > 0:
                dists = [self.getMazeDistance(successorPos, a.getPosition()) for a in invaders]
                if (min(dists) <= 3):
                    features['invaderDistance'] = min(dists)
                    if(successorPos in self.deadEnds):
                            features['deadEnds'] = self.deadEnds[successorPos]
                    safeFoodlist = self.getSafeFoodList(self.getFood(gameState).asList())

                    if len(safeFoodlist) > 0:  # This should always be True,  but better safe than sorry

                        minDistance = min([self.getMazeDistance(successorPos, food) for food in safeFoodlist])
                        features['distanceToFood'] = minDistance
                    else:
                        escapeDistance = min([self.getMazeDistance(successorPos, dmz) for dmz in self.myDMZ])
                        features['distanceToFood'] = 0
                        features['goHome'] = escapeDistance

        minCapsuleDist = 9999
        nearestCapsule = None
        for capsule in self.getCapsules(gameState):
            capsuleDist = self.getMazeDistance(myPos, capsule)
            if (minCapsuleDist > capsuleDist):
                minCapsuleDist = capsuleDist
                nearestCapsule = capsule

        if (minCapsuleDist < 6):
            enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
            invaders = [a for a in enemies if not a.isPacman and a.scaredTimer<=15 and a.getPosition() != None]
            if(len(invaders)>0):
                features['capsuleDistance'] = self.getMazeDistance(successorPos, nearestCapsule)

        eatenFood = gameState.getAgentState(self.index).numCarrying
        # if(gameState.getAgentState(self.oppIndex).scaredTimer >=15):
        if (eatenFood >= len(foodList)/6):
            escapeDistance = min([self.getMazeDistance(successorPos, dmz) for dmz in self.myDMZ])
            # To do  !!!! when scared
            enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
            invaders = [a for a in enemies if not a.isPacman and a.scaredTimer<=6 and a.getPosition() != None]
            features['numInvaders'] = len(invaders)
            if (len(invaders)>0):
                features['goHome'] = escapeDistance
            if(eatenFood >= 10 or gameState.data.timeleft/4 <= escapeDistance + 5):
                features['goHome'] = escapeDistance

        return features

    def getOffensiveWeights(self):
        return {'successorScore': 100,
                'distanceToFood': -1,
                'goHome': -3,#-2
                "numInvaders": -1,
                "invaderDistance": 10000,  #2
                "capsuleDistance": -3,
                "deadEnds": -10000
                }

    def getDefensiveFeatures(self, gameState, action):
        foods = self.getFoodYouAreDefending(gameState).asList()

        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        myState = successor.getAgentState(self.index)
        myPos = myState.getPosition()
        # Computes whether we're on defense (1) or offense (0)
        features['onDefense'] = 1
        if myState.isPacman: features['onDefense'] = 0

        # Computes distance to invaders we can see
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        features['numInvaders'] = len(invaders)
        if len(invaders) > 0:
            dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
            features['invaderDistance'] = min(dists)
            features['detected'] = 0
            features['defending'] = 0

        if len(invaders) == 0:
            dist = [self.getMazeDistance(myPos, self.myDMZ[int(len(self.myDMZ)/2)])]
            features['defending'] = min(dist)

            if len(foods) < len(self.defendingFoodList):

                foodEaten = list(set(self.defendingFoodList).difference(set(foods)))
                foodSel = list(set(self.foodList).difference(set(foods)))

                if foodSel != []:
                    dist_eaten = self.getMazeDistance(myPos, foodSel[0])
                else:
                    dist_eaten = self.getMazeDistance(myPos, foodEaten[len(foodEaten) - 1])

                features['detected'] = dist_eaten
                features['invaderDistance'] = 0

        self.foodList = foods

        if action == Directions.STOP: features['stop'] = 1
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        if action == rev: features['reverse'] = 1

        return features

    def getDefensiveWeights(self):
        return {'numInvaders': -1000,
                'onDefense': 100,
                'invaderDistance': -25,
                'stop': -100,
                'reverse': -5,
                'defending': -15,
                'detected': -25}
