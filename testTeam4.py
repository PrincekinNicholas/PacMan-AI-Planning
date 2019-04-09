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
import random, time, util, math
from game import Directions
from game import Actions
import game
import util
from formatter import NullFormatter
from test.test_threading_local import target

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'AttackerAgent', second = 'DefenderAgent'):
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

##########
# Agents #
##########

class PacmanAgent(CaptureAgent):
  """
  The PacmanAgent act as parent class for both the attacker and defender Agent class

  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

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

    '''
    Your initialization code goes here, if you need any.
    '''

    self.walls = gameState.getWalls()
    # self.initialAgents = gameState.getAgentPosition(self.index)
    self.width = gameState.data.layout.width
    self.isBack = False
    self.isAttacker = True
    self.isDefender = True
    self.Boundary = self.getBoundary(gameState)
    self.teamMateAgent = []
    self.teamScore = 0

  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    actions = gameState.getLegalActions(self.index)

    '''
    You should change this in your own agent.
    '''

    return random.choice(actions)

  
  def manhattanDistance(self, init, target):
    x1, y1 = init
    x2, y2 = target
    return abs(x1 - x2) + abs(y1 - y2)


  def getBoundary(self, gameState):

    boundary = list()
    middleBoundary = (gameState.data.layout.width -2)/2
    enemyBoundary = middleBoundary + 1
    if not self.red:
      middleBoundary, enemyBoundary = enemyBoundary, middleBoundary
    for y in range(1, gameState.data.layout.height -1):
      if not gameState.hasWall(middleBoundary, y):
        boundary.append((middleBoundary,y))

    return boundary

  def getEnemyMonsterIndex(self, gameState):
    monsterList = []
    for agentIndex in self.getOpponents(gameState):
      if self.isMonster(gameState, agentIndex):
        monsterList.append(agentIndex)
    return monsterList


  def getObservableEnemyMonsterIndex(self, gameState):
    monsterList = []
    for agentIndex in self.getOpponents(gameState):
      if not self.isAgentObservable(gameState, agentIndex):
        continue
      if self.isMonster(gameState, agentIndex):
        monsterList.append(agentIndex)
    return monsterList

  def getEnemyMonsterAmount(self, gameState):
    count = 0
    for agentIndex in self.getOpponents(gameState):
      if self.isMonster(gameState, agentIndex):
        count += 1
    return count


  def getObservableEnemyMonsterPosition(self, gameState):
    monsterList = []
    for agentIndex in self.getOpponents(gameState):
      if not self.isAgentObservable(gameState, agentIndex):
        continue
      if self.isMonster(gameState, agentIndex): 
        agentPos = gameState.getAgentPosition(agentIndex)
        monsterList.append(agentPos)
    return monsterList

  def getEnemyPacmanPosition(self, gameState):
    pacmanList = []
    for agentIndex in self.getOpponents(gameState):
      if not self.isAgentObservable(gameState, agentIndex):
        continue
      if not self.isMonster(gameState, agentIndex): 
        agentPos = gameState.getAgentPosition(agentIndex)
        pacmanList.append(agentPos)
    return pacmanList

  def isAgentObservable(self, gameState, index):
    if gameState.getAgentPosition(index) != None:
      return True
    return False


  def isMonster(self, gameState, index):
    return (not gameState.getAgentState(index).isPacman)






class AttackerAgent(PacmanAgent):
  """
  This is the attacker, aim at eating all dots in oppoent side.
  """

  def registerInitialState(self, gameState):
    PacmanAgent.registerInitialState(self, gameState)
    for agentIndex in self.getTeam(gameState):
      if not self.index == agentIndex:
        self.teamMateAgent.append(agentIndex)

    self.deadEnds = []  # all dead end positions
    self.deadEndPath = []   #  the path from deadend to the gateway (deadend postion, gateWay)
    self.learnMap(gameState)

  def isAtHome(self, gameState, myPos):
    middleBoundary = (gameState.data.layout.width -2)/2
    enemyBoundary = middleBoundary + 1
    if not self.red:
      middleBoundary, enemyBoundary = enemyBoundary, middleBoundary
    x, y = myPos
    if self.red:
      return x < middleBoundary
    else:
      return x > middleBoundary  
  
  
  def chooseAction(self, gameState):
    # print gameState.getAgentState(self.index).numCarrying
    foodList = self.getFood(gameState).asList()
    enemyMonstersPos = self.getObservableEnemyMonsterPosition(gameState)
    enemyMonstersIndex = self.getEnemyMonsterIndex(gameState)
    enemyMonsterAmount = self.getEnemyMonsterAmount(gameState)

    myPos = gameState.getAgentPosition(self.index)
    nearestFood = self.getNearestFood(myPos, foodList)
    carryingFood = gameState.getAgentState(self.index).numCarrying
    distToHome = self.distToHome(gameState, myPos)
    remainSteps = math.ceil(gameState.data.timeleft/4)
    actions = []
    if self.isAtHome(gameState, myPos):
      actions = self.pureAStarSearch(gameState, myPos, nearestFood)
    elif len(foodList) <= 2:
      actions = self.backHome(gameState, myPos)
    elif carryingFood > 0 and distToHome + 5 > remainSteps: # tested
      actions = self.backHome(gameState, myPos)

    elif enemyMonsterAmount > 0:
      if carryingFood > 4 :  # tested
        actions = self.backHome(gameState, myPos)
      elif len(enemyMonstersPos) == 0:
        actions = self.pureAStarSearch(gameState, myPos, nearestFood)
      else:
        obversableEnemyMonstersIndex = self.getObservableEnemyMonsterIndex(gameState)
        scaredTimer = gameState.getAgentState(self.getNearestMonsterIndex(gameState, myPos, obversableEnemyMonstersIndex)).scaredTimer
        if scaredTimer > 0:
          if distToHome >= scaredTimer - 5:
            tar = self.getHomePos(gameState, myPos)
            actions = self.pureAStarSearch(gameState, myPos, tar)
          else:
            actions = self.pureAStarSearch(gameState, myPos, nearestFood) # need revised no avoidance
        else: #scaredTimer = 0:
          distToMonster = self.distToMonster(gameState, self.getNearestMonsterPos(myPos, enemyMonstersPos))
          if distToMonster < 3:
            actions = self.escape(gameState, myPos)

          elif carryingFood > 3:
            actions = self.backHome(gameState, myPos)

          else:

            # actions = self.pureAStarSearch(gameState, myPos, nearestFood)
            actions = self.escapeAndFood(gameState, myPos, nearestFood)


    else: # all enemy  attack
      if (carryingFood > 7):
        actions = self.backHome(gameState, myPos)
      else:
        actions = self.aStarSearchAvoidingCapsule(gameState,myPos, nearestFood)

    
    if len(actions) == 0:
      return random.choice(gameState.getLegalActions(self.index))
    return actions[0]


  def aStarSearchAvoidingCapsule(self, gameState, currentPos, target):

    closeList =[]
    openList = util.PriorityQueue()
    enemyMonsters = self.getObservableEnemyMonsterPosition(gameState)

    initialState = (currentPos, [])
    openList.push(initialState, 0)
    while not openList.isEmpty():
        currentState, path = openList.pop()
        if (self.manhattanDistance(currentState, target) == 0):
          return path
        for successor in Actions.getLegalNeighbors(currentState, self.walls):

          if successor in closeList:
            continue
          if successor in enemyMonsters:
            continue

          if successor == self.getCapsules(gameState):
            h_value = self.getMazeDistance(successor, target) +2
          else:
            h_value = self.getMazeDistance(successor,target)
          g_value = len(path) + 1
          f_value = g_value + h_value
          action = Actions.vectorToDirection((successor[0] - currentState[0], successor[1] - currentState[1]))
          openList.push((successor, path + [action]), f_value)
          closeList.append(successor)
    return []


  '''
  return distance to monster
  assume that monster is observable now
  '''
  def distToMonster(self, gameState, monsterPos):
    myPos = gameState.getAgentPosition(self.index)
    return self.getMazeDistance(myPos, monsterPos)

  def getNearestMonsterPos(self, myPos, monsterPosList):
    minDis = 0x7fffffff
    target = None
    for monsterPos in monsterPosList:
      dist = self.getMazeDistance(myPos, monsterPos)
      if dist < minDis:
        minDis = dist
        target = monsterPos
    return target

  def getNearestMonsterIndex(self, gameState, myPos, monsterIndexList):
    minDis = 0x7fffffff
    target = None
    for monsterIndex in monsterIndexList:
      monsterPos = gameState.getAgentPosition(monsterIndex)
      dist = self.getMazeDistance(myPos, monsterPos)
      if dist < minDis:
        minDis = dist
        target = monsterIndex
    return target


  def getHomePos(self, gameState, myPos) :
    myPos = gameState.getAgentPosition(self.index)
    target = myPos
    mindis = 0x7fffffff
    for position in self.Boundary:
      if self.getMazeDistance(myPos,position) < mindis:
        mindis = self.getMazeDistance(myPos, position)
        target = position
    return target

  def backHome(self, gameState, myPos):
    myPos = gameState.getAgentPosition(self.index)
    target = myPos
    mindis = 0x7fffffff
    for position in self.Boundary:
      if self.getMazeDistance(myPos,position) < mindis:
        mindis = self.getMazeDistance(myPos, position)
        target = position

    actions = self.AStarSearch(gameState, myPos, target)
    return actions

  def distToHome(self, gameState, myPos):
    mindis = 0x7fffffff
    for position in self.Boundary:
      if self.getMazeDistance(myPos,position) < mindis:
        mindis = self.getMazeDistance(myPos, position)
    return mindis


  def getNearestFood(self, myPos, foodList):
    target = None
    minDist = 0x7fffffff
    for dot in foodList:
      dist = self.getMazeDistance(myPos, dot)
      if dist < minDist:
        minDist = dist
        target = dot
    return target

  def pureAStarSearch(self, gameState, currentPos, target):
    closeList =[]
    openList = util.PriorityQueue()

    initialState = (currentPos, [])
    openList.push(initialState, 0)
    while not openList.isEmpty():
        currentState, path = openList.pop()
        if (self.manhattanDistance(currentState, target) == 0):
          return path
        for successor in Actions.getLegalNeighbors(currentState, self.walls):
          if successor in closeList:
            continue
          g_value = len(path) + 1
          h_value = self.getMazeDistance(successor, target)
          f_value = g_value + h_value
          action = Actions.vectorToDirection((successor[0] - currentState[0], successor[1] - currentState[1]))
          openList.push((successor, path + [action]), f_value)
          closeList.append(successor)
    return []

  def AStarSearch(self, gameState, currentPos, target):

    closeList =[]
    openList = util.PriorityQueue()
    enemyMonstersPos = self.getObservableEnemyMonsterPosition(gameState)

    initialState = (currentPos, [])
    openList.push(initialState, 0)
    while not openList.isEmpty():
        currentState, path = openList.pop()
        if (self.manhattanDistance(currentState, target) == 0):
          return path
        for successor in Actions.getLegalNeighbors(currentState, self.walls):
          if successor in closeList:
            continue
          if successor in enemyMonstersPos:
            continue
          g_value = len(path) + 1
          h_value = self.getMazeDistance(successor, target)
          f_value = g_value + h_value
          action = Actions.vectorToDirection((successor[0] - currentState[0], successor[1] - currentState[1]))
          openList.push((successor, path + [action]), f_value)
          closeList.append(successor)
    return []


  def escape(self, gameState, currentPos):
    closeList =[]
    openList = util.PriorityQueue()
    enemyMonstersPos = self.getObservableEnemyMonsterPosition(gameState)
    initialState = (currentPos, [])
    openList.push(initialState, 0)
    while not openList.isEmpty():
      currentState, path = openList.pop()
      if len(path) == 5:
        return path
      for successor in Actions.getLegalNeighbors(currentState, self.walls):
        if successor in closeList:
          continue
        if successor in enemyMonstersPos:
          continue
        if successor in self.deadEnds:
          continue
        distToHome = self.distToHome(gameState, currentState)

        g_value = len(path) + 1
        h_value = distToHome - self.getMazeDistance(successor, enemyMonstersPos[0])
        f_value = g_value + h_value
        action = Actions.vectorToDirection((successor[0] - currentState[0], successor[1] - currentState[1]))
        openList.push((successor, path + [action]), f_value)
        closeList.append(successor)
    return []


  def escapeAndFood(self, gameState, currentPos, target):
    closeList =[]
    openList = util.PriorityQueue()
    enemyMonstersPos = self.getObservableEnemyMonsterPosition(gameState)

    initialState = (currentPos, [])
    openList.push(initialState, 0)
    while not openList.isEmpty():
        currentState, path = openList.pop()
        if (self.manhattanDistance(currentState, target) == 0):
          return path
        for successor in Actions.getLegalNeighbors(currentState, self.walls):
          if successor in closeList:
            continue
          if successor in self.deadEnds:
            continue
          # get distance to monsters
          dist = []
          for enemy in enemyMonstersPos:
            dist.append(self.getMazeDistance(currentState, enemy))
          g_value = len(path) + 1
          h_value = self.getMazeDistance(successor, target) - sum(dist)
          f_value = g_value + h_value
          action = Actions.vectorToDirection((successor[0] - currentState[0], successor[1] - currentState[1]))
          openList.push((successor, path + [action]), f_value)
          closeList.append(successor)
    return []

  def getAdjacentPos(self, position, wallPos):
    AdjacentPos = []
    x, y = position 
    if not wallPos[ x ][ y + 1]:
      AdjacentPos.append((x, y + 1))
    if not wallPos[x][y - 1]:
      AdjacentPos.append((x,y - 1))
    if not wallPos[x - 1][y]:
      AdjacentPos.append((x - 1, y))
    if not wallPos[x + 1][y]:
      AdjacentPos.append((x + 1, y))
    return AdjacentPos
    
    '''  
    for action in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
      x, y = position
      dx, dy = Actions.directionToVector(action)
      nextx, nexty = int(x + dx), int(y + dy)
      if not wallPos[nextx][nexty]:
        AdjacentPos.append((nextx, nexty))
    return AdjacentPos
    '''

  def learnMap(self, gameState):
      
    enemyHome = [] 
    gateWays = []
    wayPath = []  # (deadend position, gateway position)

    wallPos = gameState.getWalls()

    notWallPos = gameState.getWalls().asList(False)
    
    #get all non-wall position in opponent's area
    redBound = gameState.getWalls().width / 2
    if self.red:
      for (x,y) in notWallPos:
        if x > redBound:
          enemyHome.append((x,y))
    else:
      for (x,y) in notWallPos:
        if x <= redBound:
          enemyHome.append((x,y))
                
    #classified myPos into deadends and intersections
    for position in enemyHome:
      adjacentPos = self.getAdjacentPos(position, wallPos)
      if len(adjacentPos) == 1:
          self.deadEnds.append(position)
      if len(adjacentPos) >= 3:
          gateWays.append(position)


    # find the path from the deadend to the intersection



    # print numGatewayChoose

    """
    numGatewayChoose = [] # record the count of each gateWay used by dead ends as way out [(gateWay, count)...]

    # print len(self.deadEnds)

    for deadEnd in self.deadEnds:
      minDist = 0x7fffffff
      wayOut = deadEnd


      # find the closest gateway to the dead end to escape
      for gateWay in gateWays:

        number = 0

        next = False
        for w in numGatewayChoose:
          if gateWay == numGatewayChoose[0]:
            numChoose = numGatewayChoose[1]
            if len(self.getAdjacentPos(gateWay, wallPos)) - numChoose <= 2:
              next = True

        if next == True:
          continue

        dist = self.getMazeDistance(deadEnd, gateWay)
        if dist < minDist and gateWay not in numGatewayChoose:
          minDist = dist
          wayOut = gateWay

      wayPath.append((deadEnd, gateWay))
      numGatewayChoose.append((gateWay, number +1))

      currentPos = deadEnd
      prevPos = []
      prevPos.append(deadEnd)
      self.deadEndPath.append((deadEnd,wayOut))
      while not currentPos == wayOut:
        neighbourPos = self.getAdjacentPos(currentPos, wallPos)

        for neigh in neighbourPos:
          if neigh in prevPos:
            continue
          currentPos = neigh
          if neigh == wayOut:
            break
          else:
            if neigh not in self.deadEnds:
              self.deadEndPath.append((neigh,wayOut))
              prevPos.append(currentPos)
    """

  def getDeadEndMapping(self, gateWays):
    # deadPoint --> livePoint --> numChoose
    wayOutMap = dict()
    for deadPoint in self.deadEnds:
      minDist = 0x7fffffff
      for gateway in gateWays:
        dist = self.getMazeDistance(deadPoint, gateway)
        if dist < minDist:
          minDist = dist
          livePoint = gateway
      wayOutMap[deadPoint] = livePoint

    return wayOutMap


  def isOnDeadEnds(self, gameState):
    if self.isMonster(gameState, self.index):
      return False
    else:
      if gameState.getAgentPosition(self.index) in self.DeadEnds:
        return True
      else:
        return False



class DefenderAgent(PacmanAgent):
  """
  This is the defender, aim at preventing opponent from eating our dots.
  """
    
      
  def registerInitialState(self, gameState):
    PacmanAgent.registerInitialState(self, gameState)
    self.goal = None
    self.FoodBefore = self.getFoodYouAreDefending(gameState).asList()
    

  def chooseAction(self, gameState):
    """
    Picks among actions randomly.
    """
    enemyPacman = self.getEnemyPacmanPosition(gameState)
    myPos = gameState.getAgentPosition(self.index)
    foodList = self.getFoodYouAreDefending(gameState).asList()
    disapperFood = set(self.FoodBefore) - set(foodList)

    
    #no enemy
    if (len(enemyPacman) == 0):
        
      # go to the food disappear
      if (len(disapperFood) > 0):
          foodPos = disapperFood.pop()
          closestFood = foodPos
          minDis = 5
          for food in foodList:
            dist = self.manhattanDistance(foodPos, food)
            if (dist < minDis):
                minDis = dist
                closestFood = food 
             
          self.goal = closestFood
          actions = self.AStarSearch(gameState,myPos,self.goal)
          if len(actions) == 0:
              self.FoodBefore = self.getFoodYouAreDefending(gameState).asList()
              actions = self.returnRandom(gameState)
              return actions[0]
          self.FoodBefore = self.getFoodYouAreDefending(gameState).asList()
          return actions[0]
        
      # go to the goal 
      if (self.goal != None):
           if (self.manhattanDistance(myPos, self.goal) != 0):
               actions = self.AStarSearch(gameState,myPos,self.goal)
               self.FoodBefore = self.getFoodYouAreDefending(gameState).asList()
               return actions[0]
           else:
               self.goal = None  
      
      # go to the nearest food to boundary
      boundary = self.getBoundary(gameState)
      (x, y) = boundary[0]
      minDis = 0x7fffffff
      for (x1, y1) in foodList:
          if (abs(x - x1) < minDis):
              minDis = abs(x -x1)
              goal = (x1, y1)
      actions = self.AStarSearch(gameState,myPos,goal)
      if len(actions) == 0:
        self.FoodBefore = self.getFoodYouAreDefending(gameState).asList()
        actions = self.returnRandom(gameState)
        return actions[0]
      self.FoodBefore = self.getFoodYouAreDefending(gameState).asList()
      return actions[0] 
          
          
                
      # go to the closest dot
      '''minDist = 0x7fffffff
       
      for dot in foodList:
        dist = self.getMazeDistance(myPos, dot)
        if (dist < minDist):
          minDist = dist
          target = dot
 
      actions = self.AStarSearch(gameState,myPos,target)
      if len(actions) == 0:
        return random.choice(gameState.getLegalActions(self.index))
      self.FoodBefore = self.getFoodYouAreDefending(gameState).asList()
      return actions[0]
      '''          
  
    #chase enemy
    else:
      self.goal = None
      min = 0x7fffffff
      for enemy in enemyPacman:
        dist = self.getMazeDistance(myPos, enemy)
        if (dist < min):
          min = dist
          target = enemy
      actions = self.AStarSearch(gameState,myPos,target)
      self.FoodBefore = self.getFoodYouAreDefending(gameState).asList()
      return actions[0]        
      

          
    '''
    You should change this in your own agent.
    '''

    return random.choice(actions)

  def returnRandom(self, gameState):
      actions = []
      for action in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST,Directions.STOP]:
        x, y = gameState.getAgentPosition(self.index)
        dx, dy = Actions.directionToVector(action)
        nextx, nexty = int(x + dx), int(y + dy)
        if not self.walls[nextx][nexty]:
          if self.isDefAtHome(gameState,(nextx, nexty)):
            actions.append(action)
      return actions
      

    
  def isDefAtHome(self, gameState, myPos):
    middleBoundary = (gameState.data.layout.width -2)/2
    enemyBoundary = middleBoundary + 1
    if not self.red:
      middleBoundary, enemyBoundary = enemyBoundary, middleBoundary
    x, y = myPos
    if self.red:
      return x <= middleBoundary
    else:
      return x >= middleBoundary
  
  
  def AStarSearch(self, gameState, currentPos, target):

    closeList =[]
    openList = util.PriorityQueue()
    initialState = (currentPos, [])
    openList.push(initialState, 0)
    while not openList.isEmpty():
        currentState, path = openList.pop()
        if (self.manhattanDistance(currentState, target) == 0):
          return path
        for successor in Actions.getLegalNeighbors(currentState, self.walls):
          if successor in closeList:
            continue
          if not self.isDefAtHome(gameState, successor):
            continue
          g_value = len(path) + 1
          h_value = self.getMazeDistance(successor, target)
          f_value = g_value + h_value
          action = Actions.vectorToDirection((successor[0] - currentState[0], successor[1] - currentState[1]))
          openList.push((successor, path + [action]), f_value)
          closeList.append(successor)
    return[]


