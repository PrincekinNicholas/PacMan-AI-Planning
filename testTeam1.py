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
import distanceCalculator
from game import Directions,Actions
import game,random


# <HelloKitty>
# Xingping Ding
# Jiachuan Yu
# Yanchuan Chang

#################
# Team creation #
#################


def createTeam(firstIndex, secondIndex, isRed,
               first = 'OffenseAgent', second = 'DefendAgent'):
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

class SuperAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        # Static game data
        self.sanctuary = gameState.getAgentPosition(self.index)
        self.totalSteps = 1200
        # true:red team   false:blue team
        self.side = gameState.isOnRedTeam(self.index)
        self.width = gameState.data.layout.width
        self.height = gameState.data.layout.height
        if self.side:
            self.left = 0
            self.right = self.width/2
        else:
            self.left = self.width/2
            self.right = self.width
        self.portals = self.getPortals(gameState)
        numPortals = len(self.portals)
        self.midPortal = self.portals[numPortals/2]
        gap = numPortals/3
        self.portal3_1 = self.portals[gap]
        self.portal3_2 = self.portals[numPortals-gap-1]
        print(self.portal3_1,self.portal3_2)
        self.opponents = self.getOpponents(gameState)   #indices of opponents
        self.team = self.getTeam(gameState)        #indices of teammates
        for i in self.team:
            if i!= self.index:
                self.teammate = i
        self.walls = gameState.getWalls()
        self.depth = dict()
        self.learnTheMap(gameState)
        self.teamDepth = self.reverseDepth()

        #dynamic game data
        self.oppoAttackingTimer = 0
        self.remainFood = self.getFood(gameState).asList()
        self.mySafeFood = list()
        self.mateSafeFood = list()
        self.safeFood = dict()
        self.agentPos = dict()
        self.agentState = dict()
        self.oppoGhosts = list()
        self.oppoActGhosts = list()
        self.carryFood = dict()
        self.myScore = 0
        self.oppoScore = 0
        self.stepLeft = 300
        self.oppoScareTimer = dict()
        self.mode = True
        self.master = True
        self.remainCaps = gameState.getCapsules()
        self.myCaps = self.getCapsulesYouAreDefending(gameState)
        self.oppoCaps = self.getCapsules(gameState)
        self.oppoPacSeen = list()
        self.oppoPacGuess = list()
        self.oppoPacPos = list()
        self.numOppoPac = 0 #0-no pac on my side   #1-one pac on my side #2-two pac on my side
        self.teamFood = self.getFoodYouAreDefending(gameState).asList()
        self.numInitFood =len(self.teamFood)
        self.lastSeen = list()
        self.effective = 0
        self.defenceTimer = 0
        #debug var
        self.lastState = None
        self.lastDecision = True

    def learnTheMap(self,gameState):
        if self.side:
            left = self.width/2
            right = self.width
        else:
            left = 0
            right = self.width/2
        Q = util.Queue()
        Q.push(self.sanctuary)
        visited = [self.sanctuary]
        while not Q.isEmpty():
            curPos = Q.pop()
            neighbors = Actions.getLegalNeighbors(curPos,self.walls)
            checkPoint = None
            n = len(neighbors)
            for nb in neighbors:
                if nb not in visited:
                    visited.append(nb)
                    x,y = nb
                    if x in range(left,right):
                        checkPoint = nb
                        if n == 3:    #a 2 way corridor may lead to dead road
                            isDeadRoad = self.isDeadRoad(curPos, checkPoint)
                            if isDeadRoad: #calculate all depth in the dead road
                                self.depth[curPos] = (1,curPos)
                                self.depth[checkPoint] = (2,curPos)
                                Qd = util.Queue()
                                Qd.push(checkPoint)
                                while not Qd.isEmpty():
                                    pd = Qd.pop()
                                    deadNeis = Actions.getLegalNeighbors(pd, self.walls)
                                    for dn in deadNeis:
                                        if dn not in self.depth:
                                            self.depth[dn] = (self.getMazeDistance(dn, curPos)+1,curPos)
                                            visited.append(dn)
                                            Qd.push(dn)
                                continue
                        if n == 4:
                            isDeadRoad = self.isDeadRoad(curPos, checkPoint)
                            if isDeadRoad:
                                self.depth[checkPoint] = (1,curPos)
                                Qd = util.Queue()
                                Qd.push(checkPoint)
                                while not Qd.isEmpty():
                                    pd = Qd.pop()
                                    deadNeis = Actions.getLegalNeighbors(pd, self.walls)
                                    for dn in deadNeis:
                                        if dn not in self.depth and dn not in visited:
                                            self.depth[dn] = (self.getMazeDistance(dn, curPos),curPos)
                                            visited.append(dn)
                                            Qd.push(dn)
                                continue
                    Q.push(nb)
            if n == 2:  # a dead end, depth is 1
                self.depth[curPos] = (1,curPos)

    def reverseDepth(self):
        rDepth = dict()
        for pos in self.depth.keys():
            d, ent = self.depth[pos]
            rDepth[self.reversePos(pos)] = (d,self.reversePos(ent))
        return rDepth

    def reversePos(self, pos):
        x,y = pos
        return self.width-x-1,self.height-y-1
    def isDeadRoad(self, block, checkPoint):
        target = self.sanctuary
        Q = util.PriorityQueue()
        Q.push(checkPoint,1)
        visited = [block,checkPoint]
        while not Q.isEmpty():
            curPos = Q.pop()
            neighbors = Actions.getLegalNeighbors(curPos,self.walls)
            for nb in neighbors:
                if nb not in visited:
                    if nb == target:
                        return False
                    visited.append(nb)
                    priority = self.getMazeDistance(nb, target)
                    Q.push(nb, priority)
        return True

    def getPortals(self, gameState):
        portals = list()
        middle = self.width/2
        oppo = middle-1
        if self.side:
            middle, oppo = oppo, middle
        for y in range(self.height):
            if not gameState.hasWall(middle,y) and not gameState.hasWall(oppo,y):
                portals.append((middle,y))

        return sorted(portals, key=lambda s:s[1])

    def getMinTarget(self, targetList, gameState, bias=True):
        minDist = 9999
        minTarget = None
        for tar in targetList:
            dist = self.getMazeDistance(tar,self.agentPos[self.index])
            if bias:
                if self.master:
                    dist += self.height - tar[1]
                else:
                    dist += tar[1]
            if dist < minDist:
                minDist = dist
                minTarget = tar
        return minTarget

    def guessoppoPacGuess(self,gameState):
        lastMyFood = self.teamFood
        lastMyCaps = self.myCaps
        lastMyTargets = lastMyCaps + lastMyFood
        self.teamFood = self.getFoodYouAreDefending(gameState).asList()
        self.myCaps = self.getCapsulesYouAreDefending(gameState)
        myTargets = self.teamFood + self.myCaps
        self.oppoPacGuess = list()
        for tar in lastMyTargets:
            if tar not in myTargets:
                self.oppoPacGuess.append(tar)
    def pacOnMySide(self):
        num = 0
        for i in self.opponents:
            if self.agentState[i].isPacman:
                num +=1
        return num

    def observeGame(self,gameState):
        if self.stepLeft<280 and gameState.getAgentPosition(self.index)==self.sanctuary:
            lx,ly = self.agentPos[self.index]
            if lx >= self.width/2:
                print(self.lastDecision)
                print(self.index,"die")
                print("my position ",self.agentPos[self.index])
                print("my targets ",self.mySafeFood)
        n = gameState.getNumAgents()
        #myTargets = self.getFoodYouAreDefending(gameState).asList()# + self.myCaps()
        self.stepLeft = math.ceil(gameState.data.timeleft/4)
        self.remainCaps = gameState.getCapsules()
        self.myScore = 0
        self.oppoScore = 0
        

        self.oppoCaps = self.getCapsules(gameState)
        self.remainFood = self.getFood(gameState).asList()
        self.oppoGhosts = list()
        self.oppoActGhosts = list()
        self.oppoPacSeen = list()
        for i in range(n):
            self.agentPos[i] = gameState.getAgentPosition(i)
            self.agentState[i] = gameState.getAgentState(i)
            self.carryFood[i] = self.agentState[i].numCarrying
            self.oppoScareTimer[i] = self.agentState[i].scaredTimer
            if i in self.opponents:
                if not self.agentPos[i] is None:
                    if not self.agentState[i].isPacman:
                        self.oppoGhosts.append(i)
                        if self.agentState[i].scaredTimer <= 0:
                            self.oppoActGhosts.append(i)
                    else:
                        self.oppoPacSeen.append(i)
                self.oppoScore += self.agentState[i].numReturned
            else:
                self.myScore += self.agentState[i].numReturned
        
        self.guessoppoPacGuess(gameState)
        self.oppoPacPos = list(self.oppoPacGuess)
        for i in self.oppoPacSeen:
            if self.agentPos[i] not in self.oppoPacPos:
                self.oppoPacPos.append(self.agentPos[i])
        if len(self.oppoPacPos)>0:
            self.lastSeen = list(self.oppoPacPos)
            self.effective = 5
        else:
            if self.effective>0:
                self.effective-=1
        self.numOppoPac = self.pacOnMySide()
        #self.calSafeFood()
        self.mySafeFood = self.getSafeFood(self.index)
        for i in self.team:
            self.safeFood[i] = self.getSafeFood(i)
        self.mateSafeFood = self.getSafeFood(self.teammate)
        #if self.index ==0:
        #    print(len(self.mySafeFood))
        #for debug
        self.lastState = gameState
        
    def getSafeFood(self, index):
        safeFood = list()
        poTargets = list(self.remainFood)
        if self.oppoScareTimer[self.opponents[0]]<=0 or self.oppoScareTimer[self.opponents[0]]<=0:
            poTargets += self.oppoCaps
        for food in poTargets:
            closeGhost = None
            myCost = self.getMazeDistance(self.agentPos[index], food)
            oppoCost = 9999
            if food in self.depth:
                depth, ent = self.depth[food]
                myCost += depth
                for g in self.oppoGhosts:
                    dist = self.getMazeDistance(self.agentPos[g], ent)-1
                    if dist < oppoCost:
                        oppoCost = dist
                        closeGhost = g
            else:
                for g in self.oppoGhosts:
                    dist = self.getMazeDistance(self.agentPos[g], food)
                    if dist < oppoCost:
                        oppoCost = dist
                        closeGhost = g
            if myCost < oppoCost or myCost < self.oppoScareTimer[closeGhost]-1:
                safeFood.append(food)
        return safeFood

   
    def onMySide(self, pos):
        x,y = pos
        return y in range(self.left,self.right)

    def getStrongHold(self):
        targets = self.teamFood + self.myCaps
        if self.side:
            left = 0
            right = self.width/2
        else:
            left = self.width/2
            right = self.width
        minDist = 999999
        bestPos = None
        for i in range(left,right):
            for j in range(self.height):
                pos = (i,j)
                if not self.walls[i][j]:
                    sumDist = 0
                    for tar in targets:
                        sumDist += self.getMazeDistance(pos,tar)
                    if sumDist<minDist:
                        minDist = sumDist
                        bestPos = pos
        if self.effective>0:
            #print("tttt",self.lastSeen)
            minDist = 9999
            for g in self.lastSeen:
                dist = self.getMazeDistance(g,self.agentPos[self.index])
                if dist<minDist:
                    minDist = dist
                    bestPos = g
        return bestPos
    def pickDefenseTarget(self, gameState):
        enemyInMySight = list()
        for i in self.opponents:
            if self.agentPos[i] is not None and self.agentState[i].isPacman:
                enemyInMySight.append(self.agentPos[i])
        for p in self.oppoPacGuess:
            if p not in enemyInMySight:
                enemyInMySight.append(p)
        isScared = self.agentState[self.index].scaredTimer > 0
        if len(enemyInMySight) >0:
            return self.getMinTarget(enemyInMySight,False)
        strongHold = self.getStrongHold()
        return strongHold

    def makeDecision(self, gameState):
        myDecision = False
        mateDecision = False
        if len(self.remainFood) <= 2:
            return False,False
        myDecision = len(self.safeFood[self.index]) > 0
        mateDecision = len(self.safeFood[self.teammate]) > 0
        if myDecision and mateDecision:
            if len(self.remainFood)>=self.numInitFood/2:
                return True,True
            myCount = len(self.mySafeFood)
            mateCount = len(self.mateSafeFood)
            if myCount > mateCount:
                return True,False
            if myCount < mateCount:
                return False,True
            myDist = 0
            for food in self.mySafeFood:
                myDist += self.getMazeDistance(self.agentPos[self.index], food)
            mateDist = 0
            for food in self.mateSafeFood:
                mateDist += self.getMazeDistance(self.agentPos[self.teammate],food)
            if myDist< mateDist:
                return True,False
            if myDist> mateDist:
                return False,True
            if self.master:
                return True,False
            else:
                return False,True
        return myDecision,mateDecision
    

    def protectThePortal(self,gameState,gPos):
        minDist = 9999
        minPot = None
        for pot in self.portals:
            dist = self.getMazeDistance(gPos,pot)
            if dist< minDist:
                minDist = dist
                minPot = pot
        return minPot
       
    def chooseAction(self, gameState):
        isToPortal = False
        self.observeGame(gameState)
        #decide attack or defend
        myDec, mateDec = self.makeDecision(gameState)
        #print(self.index, myDec, mateDec)
        # if self.lastDecision and not myDec:# and self.agentState[self.index].isPacman:
        #     self.defenceTimer = 0
        # self.defenceTimer -=1
        # if self.defenceTimer>0:
        #     myDec = False
        self.lastDecision = myDec
        if myDec:
            poTargets = list(self.mySafeFood)
            if self.carryFood[self.index]>1:
                poTargets += self.portals
            # if mateDec and self.master and self.numOppoPac > 0 and self.agentState[self.index].scaredTimer<=0:
            #     oppoOnMySide = self.oppoPacGuess
            #     for i in self.oppoPacSeen:
            #         if self.agentPos[i] not in oppoOnMySide:
            #             oppoOnMySide.append(self.agentPos[i])
            #     poTargets += oppoOnMySide
            target = self.getMinTarget(poTargets,gameState,mateDec)
            if self.agentState[self.index].scaredTimer<=0:
                for g in self.oppoPacPos:
                    if g in self.teamDepth:
                        d, ent = self.teamDepth[g]
                        myDist = self.getMazeDistance(self.agentPos[self.index],ent)
                        mateDist = self.getMazeDistance(self.agentPos[self.teammate],ent)
                        if myDist <= d:
                            print("attacker defend",self.index)
                            if self.agentState[self.teammate].scaredTimer>0:
                                target = g
                                isToPortal = True
                                break
                            if mateDist>myDist:
                                target = g
                                isToPortal = True
                                break
                            if mateDist==myDist and self.master:
                                target = g
                                isToPortal = True
                                break

            if target in self.portals:
                isToPortal = True
        else:
            #carrying food, find best route to portal
            if self.agentState[self.index].numCarrying > 0:
                isToPortal = True
                target = self.getMinTarget(self.portals,gameState,False)
            else:
                if mateDec:    #one defending
                    if self.numOppoPac == 0:
                        target = self.midPortal
                    else:
                        target = self.pickDefenseTarget(gameState)
                else:   #both defending
                    #foodCenter = self.getStrongHold()
                    if self.numOppoPac==0:
                        if len(self.oppoGhosts)==0:
                            if self.master:
                                target = self.portal3_1
                            else:
                                target = self.portal3_2
                        if len(self.oppoGhosts)==1:
                            if self.master:
                                target = self.portal3_1
                            else:
                                target = self.pickDefenseTarget(gameState)
                        if len(self.oppoGhosts)==2:
                            if self.master:
                                target = self.protectThePortal(gameState, self.agentPos[self.oppoGhosts[0]])
                            else:
                                target = self.protectThePortal(gameState, self.agentPos[self.oppoGhosts[1]])
                    if self.numOppoPac==1:
                        oppoPacGuess = list(self.oppoPacGuess)
                        for i in self.opponents:
                            if self.agentState[i].isPacman and self.agentPos[i] is not None:
                                if self.agentPos[i] not in oppoPacGuess:
                                    oppoPacGuess += self.agentPos[i]
                        if self.master:
                        #if self.master or True:
                            target = self.pickDefenseTarget(gameState)
                        else:
                            target = self.pickDefenseTarget(gameState)
                    if self.numOppoPac==2:
                        target = self.pickDefenseTarget(gameState)
                        #    target = self.protectThePortal(gameState)

        if target is None:
            print("error",self.index)
            print("error",gameState)
            target = self.sanctuary
        path = self.aStarSearch(gameState,target,True,isToPortal)
        # except:
        #     print(target)


        if len(path)==0:
            if target!=self.agentPos[self.index]:
                try:
                    actions = gameState.getLegalActions(self.index)
                    threat = None
                    tDist = 9999
                    for g in self.oppoActGhosts:
                        dist = self.getMazeDistance(self.agentPos[self.index], self.agentPos[g])
                        if dist<tDist:
                            tDist = dist
                            threat = self.agentPos[g]
                    bestAction = None
                    for a in actions:
                        dx,dy = Actions.directionToVector(a)
                        x,y = self.agentPos[self.index]
                        pos = (x+dx,y+dy)
                        dist = self.getMazeDistance(pos, threat)
                        if dist>tDist:
                            if pos not in self.depth:
                                bestAction = a
                                break
                    if bestAction is None:
                        return Directions.STOP
                        print("aaaa",threat, self.agentPos[self.index])
                    else:
                        print("cccc",threat, self.agentPos[self.index])
                        print(bestAction,tDist)
                        return bestAction
                except:
                    return Directions.STOP
            else:
                return Directions.STOP
        return path[0]

    def getSuccessor(self, gameState, action):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != util.nearestPoint(pos):
            # Only half a grid position was covered
            return successor.generateSuccessor(self.index, action)
        else:
            return successor

    def aStarSearch(self, gameState, target, isConsideringOpponentGhosts=False, isToPortal=False):
        agentPosition = self.agentPos[self.index]

        # opponentGhostPositions = []
        # if isConsideringOpponentGhosts:
        #     opponentStates = [self.agentState[index] for index in self.opponents]
        #     opponentGhostStates = [oppo for oppo in opponentStates if not oppo.isPacman and oppo.getPosition() != None and oppo.scaredTimer <= 0]
        #     opponentGhostPositions = [oppo.getPosition() for oppo in opponentGhostStates]
        opponentGhostPositions = list()
        for i in self.oppoActGhosts:
            opponentGhostPositions.append(self.agentPos[i])
        if isToPortal:
            neighbors = list()
            for o in opponentGhostPositions:
                neighbors += Actions.getLegalNeighbors(o,self.walls)
            opponentGhostPositions+=neighbors
        if agentPosition == target:
            return [] # ==> should confirm
        
        q = util.PriorityQueue()

        q.push( (gameState, agentPosition, []), self.heuristic(agentPosition, target))

        set_visited_queued_states = set()
        set_visited_queued_states.add(agentPosition)

        while not q.isEmpty():

            currentState, currentPosition, path = q.pop()
            if currentPosition == target:
                return path
            else:
                for action in currentState.getLegalActions(self.index):
                    if action == Directions.STOP: 
                        continue
                    successor = self.getSuccessor(currentState, action)
                    dx, dy = Actions.directionToVector(action)
                    successorPosition = (int(currentPosition[0]+dx), int(currentPosition[1]+dy))
                    # successorPosition = successor.getAgentState(self.index).getPosition()     #it will return wrong value
                    if successorPosition in opponentGhostPositions:
                        continue
                    if successorPosition not in set_visited_queued_states:
                        priority = self.heuristic(target, successorPosition) + len(path+[action])
                        q.push( (successor, successorPosition, path+[action]), priority)
                        if not target == successorPosition:
                            set_visited_queued_states.add(successorPosition)

        return []
    def heuristic(self, position1, position2):
        return util.manhattanDistance(position1, position2)
        

class OffenseAgent(SuperAgent):
    def registerInitialState(self, gameState):
        SuperAgent.registerInitialState(self, gameState)
        self.mode = True
        self.master = True

class DefendAgent(SuperAgent):
    def registerInitialState(self, gameState):
        SuperAgent.registerInitialState(self, gameState)
        self.mode = True
        self.master = False