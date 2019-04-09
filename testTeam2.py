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
#coding:utf-8

from captureAgents import CaptureAgent
import random, time, util, math
import distanceCalculator
from game import Directions,Actions
import game,random



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
        # 敌方的豆子坐标
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
        # 先得到地图的左右边界信息
        if self.side:
            left = self.width/2
            right = self.width
        else:
            left = 0
            right = self.width/2
        Q = util.Queue()
        Q.push(self.sanctuary)
        # 这是初始点
        visited = [self.sanctuary]
        while not Q.isEmpty():
            curPos = Q.pop()
            # 邻居的坐标（不能是墙）
            neighbors = Actions.getLegalNeighbors(curPos,self.walls)
            checkPoint = None
            n = len(neighbors)
            for nb in neighbors:
                if nb not in visited:
                    # 如果不是墙的邻居没有被访问过，访问之。
                    visited.append(nb)
                    x,y = nb
                    if x in range(left,right):
                        checkPoint = nb
                        # 如果有三个邻居，判断每个邻居是否是死路(能否绕回到原点)，如果是死路算出死路的深度
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
                        # 如果有四个邻居，判断每个邻居是否是死路(能否绕回远点)，如果是死路算出死路的深度
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
            # 如果队友是处于进攻状态
            if bias:
                # 如果自己是master？？？dist这个距离需要加上游戏棋盘高度减去这个食物的纵坐标。。。。这里不是很理解为啥
                if self.master:
                    dist += self.height - tar[1]
                # 如果自己不是master，dist距离加上这个食物的纵坐标
                else:
                    dist += tar[1]
            if dist < minDist:
                minDist = dist
                minTarget = tar
        return minTarget

    def guessoppoPacGuess(self,gameState):
        # 这是上一次的我方剩余豆子和剩余胶囊
        lastMyFood = self.teamFood
        lastMyCaps = self.myCaps
        # 这个应该是指上一次我方保护所有的目标，即要保护的豆子和胶囊
        lastMyTargets = lastMyCaps + lastMyFood
        # 在这里更新我方现在要保护的豆子和胶囊。
        self.teamFood = self.getFoodYouAreDefending(gameState).asList()
        self.myCaps = self.getCapsulesYouAreDefending(gameState)
        myTargets = self.teamFood + self.myCaps
        # 清空oppoPacGuess列表
        self.oppoPacGuess = list()
        # 上一次的目标中有的，现在的保护目标没有(即已经被敌方吃豆人吃掉了)，将被吃掉的豆子或者胶囊加入到oppoPacGuess的列表里面
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
        # 在这里更新剩余步数，剩余胶囊
        self.stepLeft = math.ceil(gameState.data.timeleft/4)
        self.remainCaps = gameState.getCapsules()
        self.myScore = 0
        self.oppoScore = 0
        
        # 在这里更新地方胶囊，敌方的所有豆子
        self.oppoCaps = self.getCapsules(gameState)
        self.remainFood = self.getFood(gameState).asList()
        self.oppoGhosts = list()
        self.oppoActGhosts = list()
        self.oppoPacSeen = list()
        # i为所有人的索引
        for i in range(n):
            # 如果i为敌人，距离自己大于5，返回一个none
            self.agentPos[i] = gameState.getAgentPosition(i)
            self.agentState[i] = gameState.getAgentState(i)
            # 每个人带的吃过的豆子数量。
            self.carryFood[i] = self.agentState[i].numCarrying
            self.oppoScareTimer[i] = self.agentState[i].scaredTimer
            # 如果i为敌人的话，且距离小于等于5(没有返回none而是返回的敌人具体位置)，如果他是个幽灵的话并且不处于惊吓状态，在oppoActGhosts这个列表里面添加一个幽灵(添加i)。
            if i in self.opponents:
                if not self.agentPos[i] is None:
                    if not self.agentState[i].isPacman:
                        self.oppoGhosts.append(i)
                        if self.agentState[i].scaredTimer <= 0:
                            self.oppoActGhosts.append(i)
                    # 如果他是pacman，就在oppoPacSeen列表里面添加i
                    else:
                        self.oppoPacSeen.append(i)
                # 敌人的分值逐渐累加，我猜测numReturned应该表示的是这个敌人得到的分值？？？
                self.oppoScore += self.agentState[i].numReturned
            # 如果i不是敌人，自己的分值累加。
            else:
                self.myScore += self.agentState[i].numReturned

        # 这一步就是更新一下oppoPacGuess列表，里面的内容是敌方吃豆人刚刚吃掉的我方豆子或者胶囊。
        self.guessoppoPacGuess(gameState)
        # 复制一下oppoPacGuess列表
        self.oppoPacPos = list(self.oppoPacGuess)
        # 对于每一个敌方吃豆人，如果敌人的位置不在oppoPacPos里面(即刚刚被吃掉的豆子或者胶囊的位置)，在oppoPacPos里面添加这个敌方吃豆人i的位置。
        for i in self.oppoPacSeen:
            if self.agentPos[i] not in self.oppoPacPos:
                self.oppoPacPos.append(self.agentPos[i])
        # 如果oppoPacPos的长度大于0，即自己的豆子或者胶囊被吃掉了
        if len(self.oppoPacPos)>0:
            # lastSeen列表复制oppoPacPos，即刚刚被吃掉的豆子或者胶囊，设置effective为5
            self.lastSeen = list(self.oppoPacPos)
            self.effective = 5
        # 如果没有豆子，胶囊被吃掉，如果effective大于0的话，该值减1。
        else:
            if self.effective>0:
                self.effective-=1
        # 这个值为敌方吃豆人的数量，这里更新一下。
        self.numOppoPac = self.pacOnMySide()
        #self.calSafeFood()
        # 这个mySafeFood是安全食物的列表，这个功能很🐂🍺
        self.mySafeFood = self.getSafeFood(self.index)
        for i in self.team:
            # safeFood是个词典，自己队伍有俩人，分别对应各自的safefood
            self.safeFood[i] = self.getSafeFood(i)
        self.mateSafeFood = self.getSafeFood(self.teammate)
        #if self.index ==0:
        #    print(len(self.mySafeFood))
        #for debug
        self.lastState = gameState
        
    def getSafeFood(self, index):
        safeFood = list()
        # 这里复制一下敌方剩余豆子
        poTargets = list(self.remainFood)
        # 这里感觉程序写错了，大体意思可能为如果敌方的scare时间小于等于0，poTargets这个列表中增加敌方的胶囊。
        if self.oppoScareTimer[self.opponents[0]]<=0 or self.oppoScareTimer[self.opponents[0]]<=0:
            poTargets += self.oppoCaps
        for food in poTargets:
            closeGhost = None
            # 这个myCost为自己到每个food的迷宫距离
            myCost = self.getMazeDistance(self.agentPos[index], food)
            oppoCost = 9999
            # 这个depth一直没搞太懂，感觉像是现在位置的可能路径。如果食物在这个路径里面，myCost需要加上深度
            if food in self.depth:
                depth, ent = self.depth[food]
                myCost += depth
                # 这个好像是求到最近的幽灵以及幽灵到自己的距离？？？
                for g in self.oppoGhosts:
                    dist = self.getMazeDistance(self.agentPos[g], ent)-1
                    if dist < oppoCost:
                        oppoCost = dist
                        closeGhost = g
            # 如果食物不在路径里面，求得最近的幽灵及其到食物的距离？？？
            else:
                for g in self.oppoGhosts:
                    dist = self.getMazeDistance(self.agentPos[g], food)
                    if dist < oppoCost:
                        oppoCost = dist
                        closeGhost = g
            # 如果自己的myCost比幽灵的oppoCost小，或者比幽灵的惊吓时间-1要小的话，这个food就添加到safeFood列表里面
            if myCost < oppoCost or myCost < self.oppoScareTimer[closeGhost]-1:
                safeFood.append(food)
        return safeFood

   
    def onMySide(self, pos):
        x,y = pos
        return y in range(self.left,self.right)

    def getStrongHold(self):
        # targets里面存着自己的食物和自己的胶囊
        targets = self.teamFood + self.myCaps
        # 红队，从左到中。蓝队，从中到右
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
                # 如果不是墙，距离之和sumDist为该点到己方每一个食物和胶囊的距离加在一起。并求得最小的sumDist及其对应的位置坐标。
                if not self.walls[i][j]:
                    sumDist = 0
                    for tar in targets:
                        sumDist += self.getMazeDistance(pos,tar)
                    if sumDist<minDist:
                        minDist = sumDist
                        bestPos = pos
        # 如果effective值大于0，
        if self.effective>0:
            #print("tttt",self.lastSeen)
            minDist = 9999
            # 对于每一个刚刚被吃掉的豆子或者胶囊，求出自己到被吃掉的地方的迷宫距离，如果该距离小于刚才的最佳距离，最小距离就等于该距离，最好的位置就是刚刚被吃掉的豆子或胶囊的位置。
            # 我觉得这是因为刚刚被吃掉的位置就是敌方吃豆人的位置，所以如果这个距离小于刚才求得的最佳位置对应的距离，那么这个位置显然是最佳位置。因为自己的防守幽灵第一目标是吃掉对方吃豆人。
            # 第二目标应该是保护这个所谓的最佳位置。这个最佳位置对应的是从这个位置，到所有豆子和胶囊的位置最短，意味着从这个位置出发，很容易吃更多的豆子或者胶囊。故当自己到这个最佳位置的距离
            # 大于自己到敌方吃豆人的距离的时候，最佳位置显然是要更新成刚刚被吃掉的豆子或胶囊位置。这个策略挺🐂🍺。
            for g in self.lastSeen:
                dist = self.getMazeDistance(g,self.agentPos[self.index])
                if dist<minDist:
                    minDist = dist
                    bestPos = g
        return bestPos
    def pickDefenseTarget(self, gameState):
        enemyInMySight = list()
        # 如果敌方吃豆人再我的视野里，更新enemyInMySight列表
        for i in self.opponents:
            if self.agentPos[i] is not None and self.agentState[i].isPacman:
                enemyInMySight.append(self.agentPos[i])
        # 把刚刚被吃掉的豆子或胶囊的位置，添加到enemyInMySight列表中
        for p in self.oppoPacGuess:
            if p not in enemyInMySight:
                enemyInMySight.append(p)
        isScared = self.agentState[self.index].scaredTimer > 0
        # 如果有敌方吃豆人在视野内或者刚刚有豆子胶囊被吃掉，选出最近的位置并返回
        if len(enemyInMySight) >0:
            return self.getMinTarget(enemyInMySight,False)
        # 如果没有敌方吃豆人在视野内或者刚刚没有豆子胶囊被吃掉，得到最佳位置并返回
        strongHold = self.getStrongHold()
        return strongHold

    def makeDecision(self, gameState):
        myDecision = False
        mateDecision = False
        # 如果敌方的豆子总数小于等于2，直接返回两个false
        if len(self.remainFood) <= 2:
            return False,False
        # 如果自己和队友的安全事物大于等于0的话(即有安全食物可以吃)，进行分类讨论
        myDecision = len(self.safeFood[self.index]) > 0
        mateDecision = len(self.safeFood[self.teammate]) > 0
        if myDecision and mateDecision:
            # 如果敌方剩余豆子总数超过双方一开始的半数，返回两个ture
            if len(self.remainFood)>=self.numInitFood/2:
                return True,True
            # 如果没到半数，自己的安全食物数量大于队友的，就返回true，false。队友的安全食物数量大于自己的，返回false, true.
            myCount = len(self.mySafeFood)
            mateCount = len(self.mateSafeFood)
            if myCount > mateCount:
                return True,False
            if myCount < mateCount:
                return False,True
            # 如果没到半数且自己和队友安全食物数量相等的话，算距离。自己到自己所有安全食物距离总和如果小于队友的，就返回true，false。队友大于自己的，返回false, true.
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
            # 这个master目前不知道是什么意思
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
        # 这里更新一下游戏情况
        self.observeGame(gameState)
        #decide attack or defend
        myDec, mateDec = self.makeDecision(gameState)
        #print(self.index, myDec, mateDec)
        # if self.lastDecision and not myDec:# and self.agentState[self.index].isPacman:
        #     self.defenceTimer = 0
        # self.defenceTimer -=1
        # if self.defenceTimer>0:
        #     myDec = False
        # 这里的lastDecision保存下观察游戏情况之后做出的进攻防守决定，true为进攻，false为防守。
        self.lastDecision = myDec
        # 如果决定为进攻
        if myDec:
            # poTargets里面复制了自己的安全食物列表
            poTargets = list(self.mySafeFood)
            # 如果自己携带的豆子(即已经吃掉的豆子)数量大于1
            if self.carryFood[self.index]>1:
                # poTargets列表中添加上自己的大门位置，现在的poTargets列表里面存着自己的安全食物位置以及己方大门位置坐标
                poTargets += self.portals
            # 这里得到了自己最近的目标，这个目标是从安全食物和大门位置坐标里面筛选出来距离最近的
            target = self.getMinTarget(poTargets,gameState,mateDec)
            # 如果自己不是处于惊吓状态
            if self.agentState[self.index].scaredTimer<=0:
                # 对于每一个刚刚被吃掉的豆子或胶囊位置g
                for g in self.oppoPacPos:
                    # 这个teamDepth是相反坐标，不理解它的用处？？？
                    if g in self.teamDepth:
                        # d值为1，2啥的，不知道啥意思，ent为g的坐标。
                        d, ent = self.teamDepth[g]
                        # 算出自己到g的距离以及队友到g的距离
                        myDist = self.getMazeDistance(self.agentPos[self.index],ent)
                        mateDist = self.getMazeDistance(self.agentPos[self.teammate],ent)
                        # 如果自己到g距离小于d的话
                        if myDist <= d:
                            print("attacker defend",self.index)
                            # 队友处于惊吓状态，目标变为g。isToPortal我理解为向大门走去，因为自己现在是进攻状态，我需要回防去干敌方吃豆人
                            if self.agentState[self.teammate].scaredTimer>0:
                                target = g
                                isToPortal = True
                                break
                            # 如果队友不是惊吓状态，队友到g的距离大于自己到g的距离，我的目标变为g
                            if mateDist>myDist:
                                target = g
                                isToPortal = True
                                break
                            # 如果队友和自己到g距离相等，但我是master，我的目标更新为g
                            if mateDist==myDist and self.master:
                                target = g
                                isToPortal = True
                                break
            # 这么一圈下来，target如果是大门的话，isToPortal为true
            if target in self.portals:
                isToPortal = True
        # 如果决定为防守
        els e:
            #carrying food, find best route to portal
            # 自己的豆子数量大于0，isToPortal变为true，target更新为最近的大门位置
            if self.agentState[self.index].numCarrying > 0:
                isToPortal = True
                target = self.getMinTarget(self.portals,gameState,False)
            else:
                # 自己豆子数量为0，队友是进攻的话(这时候自己是防守)
                if mateDec:    #one defending
                    # 如果敌方吃豆人数量为0，目标是中间的大门。若敌方有吃豆人，目标更新为最佳防守目标(可能是在视野内的吃豆人，可能是刚刚被吃掉的豆子胶囊位置，可能是距离所有豆子最近的位置)
                    if self.numOppoPac == 0:
                        target = self.midPortal
                    else:
                        target = self.pickDefenseTarget(gameState)
                # 自己豆子数量为0，队友是防守
                else:   #both defending
                    #foodCenter = self.getStrongHold()
                    # 敌方吃豆人数量为0，这块儿懵逼了，很奇怪。敌方没吃豆人，幽灵数量怎么可能为0或1？？？
                    if self.numOppoPac==0:
                        # 对面没有幽灵，自己是master的话，目标为三分之一处的大门，不是master目标为三分之二的大门
                        if len(self.oppoGhosts)==0:
                            if self.master:
                                target = self.portal3_1
                            else:
                                target = self.portal3_2
                        # 对方一个幽灵，自己是master，目标变成三分之一处的大门，不是master的话，更新最佳防守目标(可能是在视野内的吃豆人，可能是刚刚被吃掉的豆子胶囊位置，可能是距离所有豆子最近的位置)
                        if len(self.oppoGhosts)==1:
                            if self.master:
                                target = self.portal3_1
                            else:
                                target = self.pickDefenseTarget(gameState)
                        # 对方俩幽灵，目标变成保护大门
                        if len(self.oppoGhosts)==2:
                            if self.master:
                                target = self.protectThePortal(gameState, self.agentPos[self.oppoGhosts[0]])
                            else:
                                target = self.protectThePortal(gameState, self.agentPos[self.oppoGhosts[1]])
                    # 如果对面有一个吃豆人
                    if self.numOppoPac==1:
                        oppoPacGuess = list(self.oppoPacGuess)
                        # 对于每一个敌人
                        for i in self.opponents:
                            # 如果这个敌人是吃豆人并且他在视野范围内
                            if self.agentState[i].isPacman and self.agentPos[i] is not None:
                                # 如果这个吃豆人位置还不是刚刚被吃掉的豆子或胶囊位置，更新这个位置到oppoPacGuess列表当中
                                if self.agentPos[i] not in oppoPacGuess:
                                    oppoPacGuess += self.agentPos[i]
                        # 如果自己是master，更新最佳防守目标
                        if self.master:
                        #if self.master or True:
                            target = self.pickDefenseTarget(gameState)
                        # 如果自己不是master，更新最佳防守目标
                        else:
                            target = self.pickDefenseTarget(gameState)
                    # 如果对面有两个吃豆人，更新最佳防守目标
                    if self.numOppoPac==2:
                        target = self.pickDefenseTarget(gameState)
                        #    target = self.protectThePortal(gameState)

        # 如果目标为none，报错？？目标更新为初始位置sanctuary??
        if target is None:
            print("error",self.index)
            print("error",gameState)
            target = self.sanctuary
        # 路径为A*
        path = self.aStarSearch(gameState,target,True,isToPortal)
        # except:
        #     print(target)

        # 如果路径长度为0
        if len(path)==0:
            # 如果目标不是自己的位置
            if target!=self.agentPos[self.index]:
                # 尝试：
                try:
                    actions = gameState.getLegalActions(self.index)
                    threat = None
                    tDist = 9999
                    # 对于每一个敌方幽灵，算出自己到它的距离，更新tDist为最短的到幽灵的距离，threat为这个幽灵的位置
                    for g in self.oppoActGhosts:
                        dist = self.getMazeDistance(self.agentPos[self.index], self.agentPos[g])
                        if dist<tDist:
                            tDist = dist
                            threat = self.agentPos[g]
                    bestAction = None
                    # 对于合法的动作，求得每个动作执行后的位置(pos),然后算出每个pos到threat的距离。如果这个距离比现在自己到幽灵距离(tDist)要远且这个pos不在depth里面，更新这个动作为最佳动作
                    for a in actions:
                        dx,dy = Actions.directionToVector(a)
                        x,y = self.agentPos[self.index]
                        pos = (x+dx,y+dy)
                        dist = self.getMazeDistance(pos, threat)
                        if dist>tDist:
                            if pos not in self.depth:
                                bestAction = a
                                break
                    # 如果没有最佳动作，返回stop动作。有最佳动作就返回最佳动作
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

    # 调用函数为path = self.aStarSearch(gameState,target,True,isToPortal)
    def aStarSearch(self, gameState, target, isConsideringOpponentGhosts=False, isToPortal=False):
        agentPosition = self.agentPos[self.index]

        # opponentGhostPositions = []
        # if isConsideringOpponentGhosts:
        #     opponentStates = [self.agentState[index] for index in self.opponents]
        #     opponentGhostStates = [oppo for oppo in opponentStates if not oppo.isPacman and oppo.getPosition() != None and oppo.scaredTimer <= 0]
        #     opponentGhostPositions = [oppo.getPosition() for oppo in opponentGhostStates]
        opponentGhostPositions = list()
        # opponentGhostPositions列表里面存着每个敌方幽灵的位置
        for i in self.oppoActGhosts:
            opponentGhostPositions.append(self.agentPos[i])
        # 如果是去大门
        if isToPortal:
            # neighbors列表里面存着敌方每个幽灵的邻居位置。更新opponentGhostPositions列表加上现在的幽灵的每个邻居位置坐标
            neighbors = list()
            for o in opponentGhostPositions:
                neighbors += Actions.getLegalNeighbors(o,self.walls)
            opponentGhostPositions+=neighbors
        # 如果现在自己位置就是目标位置，返回一个空列表
        if agentPosition == target:
            return [] # ==> should confirm
        
        q = util.PriorityQueue()
        # q这个优先队列中，键为元祖(gameState,自己位置，空列表)，权重为自己位置到目标位置的曼哈顿距离
        q.push( (gameState, agentPosition, []), self.heuristic(agentPosition, target))

        set_visited_queued_states = set()
        set_visited_queued_states.add(agentPosition)

        while not q.isEmpty():

            currentState, currentPosition, path = q.pop()
            if currentPosition == target:
                return path
            else:
                # 对于每个合法动作，如果是stop直接continue。如果不是，求successor及其位置坐标。如果successor位置在敌方幽灵位置上，continue。如果不在且不在set集合内
                # 权重更新为目标到successor的曼哈顿距离加上从原地到successor的路径长度。这时候如果目标不是successor，在set里面添加successor位置(即已经遍历过了)
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
