# myTeam.py
# ---------
# Licensing Information:	You are free to use or extend these projects for
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
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint

SCARED_TIME = 40
MAX_STEP = 300

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
			first = 'Attacker', second = 'Defender'):
	"""
	This function should return a list of two agents that will form the
	team, initialized using firstIndex and secondIndex as their agent
	index numbers.	isRed is True if the red team is being created, and
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

class BaseAgent(CaptureAgent):
	def registerInitialState(self, gameState):
		"""
		@version 2.3
		"""
		CaptureAgent.registerInitialState(self, gameState)
		'''
		Your initialization code goes here, if you need any.
		'''
		# Agent's Attribution
		self.beginningTower = gameState.getAgentPosition(self.index)
		# print "TESTING : ", self.beginningTower
		self.teamColor = gameState.isOnRedTeam(self.index)
		self.myPosition = gameState.getAgentPosition(self.index)
		self.carryFood = 0
		self.teamFood = self.getFoodYouAreDefending(gameState).asList()
		self.isDefender = True
		self.deathNumber = -1	 #due to it will plus 1 at begining game

		self.teamCapsule = self.getCapsulesYouAreDefending(gameState)
		self.guessOppoPos = list()
		self.oppoCapsuleList = self.getCapsules(gameState)
		self.oppoScareTime = SCARED_TIME


		# Logic Attribution
		self.foodList = self.getFood(gameState).asList()
		self.maxFood = len(self.foodList)
		self.width = gameState.data.layout.width
		self.height = gameState.data.layout.height
		self.stepLeft = gameState.data.timeleft /4
		# print "!!!!!",self.stepLeft
		self.considerBack = False
		self.portals = self.getPortals(gameState)
		self.teamIndices = self.getTeam(gameState)
		for index in self.teamIndices:
			if index != self.index:
				self.teamateIndex = index
		# self.oldApproximatingQValue = 0

		numPortals = len(self.portals)
		self.midPortal = self.portals[numPortals / 2]
		self.numOfOppPac = 0
		self.opponents = self.getOpponents(gameState) # indices of opponents
		self.walls = gameState.getWalls()
		# self.lifecycleHistory = list()			#for record how many food i have done before i die
		# self.lifecycleHistory.append((1,0))	 #first element is index of life, second element is food quantity
		self.deadEndMap = self.buildDeadEndMap(gameState)	#deadEndMap[x][y] >0 means (x,y) is one of the dead End. The value of deadEndMap is the length from (x,y) to dead end corner.
		self.target = None
		# self.lastEatingStep = 0		#record the last step in which our pacman have ate food, from 1 to 300

		self.avoidingGhostTime = 0		#accumulating time for avoiding ghost, reset when stop avoiding ghost
		self.statusForAvoidGhost = False #this means Am i currently avoiding ghost
		self.oppoScare = False
		self.prevCapsuleSize = len(self.oppoCapsuleList)
		self.myScare = False

		self.safetyFoodList = self.getSafetyFoodList(gameState)
		print "TESTING SAFETY FOOD LIST: ", self.safetyFoodList
		# self.mode = -1
		# self.positionHistory = list()


	def chooseAction(self, gameState):
		"""
		@version 2.3
		Picks among the actions with the highest Q(s,a).
		"""
		start = time.time()

		if self.myPosition == self.beginningTower:
			# to set first Target
			if self.setFirstTarget(gameState):
				self.target = self.setFirstTarget(gameState)

		#update values for each action
		self.stepLeft -= 1
		self.myPosition = gameState.getAgentPosition(self.index)
		# self.positionHistory.append(self.myPosition)
		self.oppoCapsuleList = self.getCapsules(gameState)
		self.foodList = self.getFood(gameState).asList()
		self.safetyFoodList = self.getSafetyFoodList(gameState)
		print "----------------------- Now is Step %d for Agent %d ------------------------ " % (MAX_STEP - self.stepLeft, self.index)
		# if self.target != None:
		# 	self.debugDraw(self.target, [1,1,1], True)
		# 	print "debugDraw Target is:", self.target
		self.loadCurrentAgentMode(gameState)
		# self.mode = self.loadCurrentAgentMode(gameState)		#this function is for changing runing mode sometimes
		if self.isDefender:
			return self.getDenfenderActions(gameState,self.stepLeft)

		actions = gameState.getLegalActions(self.index)

		#check capsules
		self.checkCapsule(gameState)
		# check do we need to avoid Ghost and update self.statusForAvoidGhost
		if self.oppoScare == False:
			actions = self.avoidGhost(gameState, actions)
		# This is for feature&Weight
		# start = time.time()
		# values = [self.estimate(gameState, action) for action in actions]
		# print 'in Step %d, eval time for agent %d: %.4f' % (300 - self.stepLeft, self.index, time.time() - start)

		# for TESTING
		if time.time() - start >= 15:
			for i in range (100):
				print "OVERTIME"

		if len(actions) == 0:
			print "no place to go..."
			return Directions.STOP
		else:
			action = random.choice(actions)

		if self.considerBack:
		# if self.avoidingGhostTime >= 20 or self.considerBack:
			print "The considerBack is True, I'm backing Now"
			self.foodList = self.getFood(gameState).asList()
			distanceToFood = [(self.getMazeDistance(self.myPosition,food),food) for food in self.foodList]
			distanceToFood = sorted(distanceToFood, key = lambda x:x[0])
			self.target = distanceToFood[0][1]
			#double check actions or bestActions as argument
			action = self.backToSafetyPosition(gameState, actions)
			return self.updateCarryFood(gameState, action)

		try:
			if self.statusForAvoidGhost:
				if self.selfHelp(gameState) != None:
					return self.selfHelp(gameState)
				# if self.selfHelp(gameState)[0]:
				# 	return self.selfHelp(gameState)[1]	#the return value is an action
				action = self.chasingSafeTarget(gameState, actions)
			else:
				action = self.chasingNormalTarget(gameState, actions)

			print "Here is in Try()"
			# action = self.chasingNormalTarget(gameState,actions)
			print 'final action ',action
			return self.updateCarryFood(gameState, action )
		except:
			print "Here is in exception()!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
			return random.choice(actions)


	def setFirstTarget(self, gameState):
		"""
		@version 2.5
		Set Target when i am in the begining Tower, no matter after die or at begin of game
		if will return False iff there is no food anymore or i'm the defender
		"""
		if not self.isDefender:
			maxYFood = (0, -1)
			minYFood = (0, 99999)
			if len(self.foodList) == 0:
				return False
			for food in self.foodList:
				if food[1] > maxYFood[1]:
					maxYFood = food
				if food[1] < minYFood[1]:
					minYFood = food
			firstTarget = random.choice([maxYFood, minYFood])
			return firstTarget
		return False

	# def checkHistory(self, gameState):
	# 	"""
	# 	@version 2.4
	# 	return true when it is in special situation-- e.g. North-> south-> north-> south-> north
	# 	"""
	# 	# x,y = self.myPosition
	# 	# if (self.teamColor and x > 8) or (not self.teamColor and x < (self.width - 8)):
	# 	if self.myPosition in self.portals:
	# 		xList = []
	# 		yList = []
	# 		checkLength = 10
	# 		size = len(self.positionHistory)
	# 		if  size< 10:
	# 			checkLength = size
	# 		for index in range(1,checkLength):
	# 			xList.append(self.positionHistory[size-i][0])
	# 			yList.append(self.positionHistory[size-i][1])
	# 		maxX, maxY = max(xList), max(yList)
	# 		minX, minY = min(xList), min(yList)
	# 		if maxX - minX <= 3 and maxY - minY <= 3:
	# 			return True
	# 	return False

	def selfHelp(self,gameState):
		actions = gameState.getLegalActions(self.index)
		x,y = self.myPosition
		if self.deadEndMap[x][y] > 0:
			actions.remove(Directions.STOP)
			if len(actions) == 1:
				return actions[0]
			else:	#len(actions) == 2
				for action in actions:
					successor = self.getSuccessor(gameState, action)
					position = successor.getAgentPosition(self.index)
					x, y = position
					if self.deadEndMap[x][y] == 0:
						return action
		return None

	def checkCapsule(self, gameState):
		"""
		@version 2.1.1
		check have capsule ate
		"""
		if len(self.oppoCapsuleList) < self.prevCapsuleSize:
			self.prevCapsuleSize = len(self.oppoCapsuleList)
			self.oppoScare = True

		if self.oppoScare == True:
			print "ScareTime:", self.oppoScareTime
			self.statusForAvoidGhost = False
			self.avoidingGhostTime = 0
			print "TESTING statusForAvoidGhost:", self.statusForAvoidGhost
		 	if self.oppoScareTime > 0 :
				self.oppoScareTime -= 1
			else:	#self.oppoScareTime == 0
				print "self.oppoScare is False"
				self.oppoScare = False
				self.oppoScareTime = SCARED_TIME

		# return actions

	def changeTargetToSurvive(self, gameState, actions):
		"""
		@version 2.2
		"""
		# minDistanceToPortal = 99999
		# minPortal = self.portals[0]
		# minDistanceToCapsule = 99999
		potentialTarget = []
		target = None
		for capsule in self.oppoCapsuleList:
			potentialTarget.append(capsule)
		for portal in self.portals:
			potentialTarget.append(portal)

		# the distance to this target + the first action + this target
		distanceToTarget = [(self.getMazeDistance(self.myPosition,target), target)\
		 										for target in potentialTarget]
		distanceToTarget = sorted(distanceToTarget, key = lambda x:x[0])
		print('distanceToTarget',distanceToTarget)
		for i,item in enumerate(distanceToTarget):
			print "now I'm thinking of...",i,item
			path = self.aStarSearch(gameState,item[1])
			if len(path) != 0:
				if path[0] not in actions:
					print 'not in my actions list either...'
					continue
				else:
					target = item[1]
					print 'has update to a new target...',target
					# print 'made new decision..',action
					break
		if target:
			return target
		return

	def chasingNormalTarget(self, gameState, actions ):
		"""
		@version 2.3
		set target to the closest food
		when a ghost around, has to change to a new safe target
		return a safe action to get food
		"""
		distanceToFood = [(self.getMazeDistance(self.myPosition,food),food) for food in self.foodList]
		distanceToFood = sorted(distanceToFood, key = lambda x:x[0])
		newTarget = None
		# print 'distance to food',distanceToFood
		if self.target == None:
			self.target = distanceToFood[0][1]
			# only for initialization
		print 'my current target,', self.target
		# if the path -> 0, which means I've eaten this food
		# or the action is too dangerous to choose,
		# only in those 2 circumstances pacman has to change target
		pathToTarget = self.aStarSearch(gameState,self.target)
		try:
			print 'path to target',pathToTarget[0]
		except:
			print 'EXCEPTION: path to target',pathToTarget
		if len(pathToTarget) == 0:
			self.target = distanceToFood[0][1]
			print "I wanna eat my food one by one...the next food is ",self.target
			pathToTarget = self.aStarSearch(gameState,self.target)

		if pathToTarget[0] not in actions:
			# first scan food list...
			random.shuffle(distanceToFood)
			print "shuffle my list..", distanceToFood
			newTarget = self.changeTargetToFood(gameState, actions, distanceToFood)
			if not self.isInMySide(gameState,self.index):
				if newTarget:
					print "I am standing at..",self.myPosition, " the new target is...",self.target, ".. to eat more food!!"
				else:
					newTarget = self.changeTargetToSurvive(gameState, actions)
					print "I am standing at..",self.myPosition, " the new target is...",self.target, ".. to survive!!!"
		else:
			# no need to change current target
			return pathToTarget[0]

		# has change to a new target:
		if newTarget:
			print "currently available actions: ", actions
			print "there's a new target..",newTarget
			self.target = newTarget
			# now choose action based on our OPTIMIZED target
			if len(self.aStarSearch(gameState,self.target)) == 0:
				print "Have randomly chosen this final action"
				action = random.choice(actions)
			else:
				action = self.aStarSearch(gameState,self.target)[0]		#the type of return action is list()

		else:
			# need to change target, but still fail to find proper one.
			print "fail to find new target... now take random action"
			action = random.choice(actions)

		print 'I am on the way to',self.target,' the action..',action
		return action

	def changeTarget(self, gameState, actions,list):
		"""
		@version 2.3
		"""
		target = None
		distanceToTarget = [(self.getMazeDistance(self.myPosition,item), item)\
		 										for item in list]
		distanceToTarget = sorted(distanceToTarget, key = lambda x:x[0])
		print('distance to target',distanceToTarget)
		for i,item in enumerate(distanceToTarget):
			print "now I'm thinking of...",i,item
			path = self.aStarSearch(gameState,item[1])
			if len(path) != 0:
				if path[0] not in actions:
					print 'not in my actions list either...'
					continue
				else:
					target = item[1]
					print 'has update to a new target...',target
					# print 'made new decision..',action
					break
		if target:
			return target
		return



	def chasingSafeTarget(self, gameState, actions):
		"""
		@version 2.3
		switch mode to get safety food

		"""
		newTarget = None
		action = random.choice(actions)
		distanceToSafeFood = [(self.getMazeDistance(self.myPosition,food),food) for food in self.safetyFoodList]
		distanceToSafeFood = sorted(distanceToSafeFood, key = lambda x:x[0])
		if len(distanceToSafeFood) > 0:
			# if self.carryFood > 0:
			# 	if self.isInDefenderEye(gameState) > 0:
			# 		self.considerBack = True
			# 		return action
			print "distanceToSafeFood",distanceToSafeFood
			# if self.target not in distanceToSafeFood:
			if self.target not in self.safetyFoodList:
				# only for the initialization
				self.target = distanceToSafeFood[0][1]
			pathToTarget = self.aStarSearch(gameState,self.target)
			# update new target
			if len(pathToTarget) == 0:
				self.target = distanceToSafeFood[0][1]
				print "I wanna eat my next SAFE food...",self.target
				pathToTarget = self.aStarSearch(gameState,self.target)
			# while I have to avoid ghost...
			if pathToTarget[0] not in actions:
				# first scan food list...
				random.shuffle(distanceToSafeFood)
				print "shuffle my SAFE food list..", distanceToSafeFood
				newTarget = self.changeTargetToFood(gameState, actions, distanceToSafeFood)
				if newTarget:
					print "I am standing at..",self.myPosition, " the new target is...",newTarget, ".. to eat more SAFE food!!"
			else:
				# no need to change current target
				print "no need to change current target, the current target is :", self.target
				action =  pathToTarget[0]
		else:
			print "safeFood list is empty..."
			if self.carryFood >0:
				portalList = [portal for portal in self.portals]
				# print 'portal',portalList
				newTarget = self.changeTarget(gameState,actions,portalList)
				if newTarget:
					print "I'm carrying ",self.carryFood," the new target has set to portal..."
			else:
				if len(self.oppoCapsuleList) > 0:
					print "no food, not carring, looking for capsule.."
					capsuleList = [cap for cap in self.oppoCapsuleList]
					newTarget = self.changeTarget(gameState,actions,capsuleList)
					print "TEST capsuleList :", capsuleList
					print "TEST NEW TARGET :", newTarget
					if newTarget:
						print "I'm not carring food, the new target has set to capsule..."
		if newTarget:
			print "currently available actions: ", actions
			print "there's a new target..",newTarget
			self.target = newTarget
			# now choose action based on our OPTIMIZED target
			if len(self.aStarSearch(gameState,self.target)) == 0:
				print "Have randomly chosen this final action"
				action = random.choice(actions)
			else:
				action = self.aStarSearch(gameState,self.target)[0]

		return action

	def changeTargetToFood(self, gameState, actions, distanceToFood):
		"""
		@version 2.2.1
		scan foodlist descending, find the first one has satified the constrains.
		update self.target
		"""
		target = None
		searchBoundary = 10
		if len(distanceToFood) < 10:
			searchBoundary = len(distanceToFood)
		for i,food in enumerate(distanceToFood[:searchBoundary]):
			print "now I'm thinking of...",i,food
			path = self.aStarSearch(gameState,food[1])
			if len(path) != 0:
				if path[0] not in actions:
					print 'not in my actions list either...'
					continue
				else:
					# action = path[0]
					target = food[1]
					print 'has update to a new target...',target
					# print 'made new decision..',action
					break
		if target:
			return target
		return

	def getSafetyFoodList(self, gameState):
		"""
		@version 2.3
		don't need to refresh foodList in advanced
		return a list which is not in dead end
		"""
		safetyFoodList = list()
		self.foodList = self.getFood(gameState).asList()
		for food in self.foodList:
			x, y = food
			if self.deadEndMap[x][y] == 0:
				safetyFoodList.append(food)
		# print "TEST: Here is current safety food list :\n", safetyFoodList
		return safetyFoodList

	def checkAroundWalls(self, gameState, deadEndMap, x, y):
		"""
		@version 1.4.1
		check (x,y)'s around has walls
		return number of walls
		"""
		num = 0
		if x > 0 and x < self.width -1 and y > 0 and y < self.height -1:
			arounds = list()
			arounds.append((x -1,y))
			arounds.append((x +1,y))
			arounds.append((x,y -1))
			arounds.append((x,y +1))
			for around in arounds:
				aroundX, aroundY = around
				if deadEndMap[aroundX][aroundY] == -1:
					num += 1
		return num		# it doesn't matter for return 0 if (x,y) is boundary, e.g. (0,0) returns 0

	def updateDeadEndMap(self, gameState, deadEndMap, tmpVirtualWallsMap, x, y):
		"""
		@version 2.1
		this function is recursive function.
		for find dead end entry from dead end corner.
		this (x,y) in arguments are position of dead end corner.
		"""
		nextGrids = list()
		nextGrids.append((x -1,y))
		nextGrids.append((x +1,y))
		nextGrids.append((x,y -1))
		nextGrids.append((x,y +1))
		nextGridsCopy = nextGrids[:]
		for nextGrid in nextGrids:
			nextX, nextY = nextGrid
			if deadEndMap[nextX][nextY] != 0:
				nextGridsCopy.remove((nextX, nextY))
		nextGrids = nextGridsCopy

		if len(nextGrids) > 0:
			#now nextGrids should has only one next grid to the Entry, then
			nextX, nextY = nextGrids[0]	#this grid is the only grid and the value is 0
			tmpVirtualWallsNum = self.checkAroundWalls(gameState, deadEndMap, nextX, nextY) \
				+ tmpVirtualWallsMap[nextX][nextY]
			# print "TESTING: tmpVirtualWallsNum in (%d, %d) is %d" % (nextX, nextY, tmpVirtualWallsNum)
			if  tmpVirtualWallsNum == 2:
				deadEndMap[nextX][nextY] = deadEndMap[x][y] +1

			if tmpVirtualWallsNum <= 1:
				tmpVirtualWallsMap[nextX][nextY] += 1
				# print "TESTING: tmpVirtualWallsMap value in (%d, %d ) is %d " % (nextX, nextY, tmpVirtualWallsMap[nextX][nextY])
				return
			self.updateDeadEndMap(gameState, deadEndMap, tmpVirtualWallsMap, nextX, nextY)

	def buildDeadEndMap(self, gameState):
		"""
		@version 2.1
		build deadEndMap
		"""
		deadEndMap = [[0 for x in range(self.height)] for y in range(self.width)]
		#set walls as -1
		for x in range(self.width):
			for y in range(self.height):
				if gameState.hasWall(x,y):
					# print x,",",y
					deadEndMap[x][y] = -1;
		# set dead end corner as 1
		for x in range(self.width):
			for y in range(self.height):
				if self.checkAroundWalls(gameState, deadEndMap, x, y) == 3:
					deadEndMap[x][y] = 1
		tmpVirtualWallsMap = [[0 for x in range(self.height)] for y in range(self.width)] 		#this var records how many walls around this grid, even counts logic virtual walls for easy calculating.
		# Recursing (x,y) from dead end corner for find dead end entry
		for x in range(self.width):
			for y in range(self.height):
				if deadEndMap[x][y] == 1:
					self.updateDeadEndMap(gameState, deadEndMap, tmpVirtualWallsMap, x, y)
		return deadEndMap

	def avoidGhost(self, gameState, actions):
		"""
		@version 2.1.1
		check the observale ghosts
		radius <= 3, stay alert and remove certain Directions
		radius <= 5, avoid run into a dead end
		return the safe action list
		"""
		print 'my current action: ',actions
		opponentObservingList = self.getOpponentsDetail(gameState,self.index)
		# distanceToGhost = -1	# set the value when oppo is unobservable
		Ghosts = []
		if len(opponentObservingList) != 0:
			# print 'oberserving enemies...',opponentObservingList
			for opponent in opponentObservingList:
				if not self.isInMySide(gameState, opponent[0]):	#only ghost will be added in Ghost list, rather than oppo's pacman
					Ghosts.append(opponent)

		if len(Ghosts) == 0:
			self.statusForAvoidGhost = False
			self.avoidingGhostTime = 0
		else: 		#if len(Ghosts) != 0:
			# print 'ghosts, ',Ghosts
			distanceToGhosts = [(self.getMazeDistance(self.myPosition, oppo[1]),oppo[1]) for oppo in Ghosts]
			print 'distance to ghosts, ',distanceToGhosts
			print 'myPosition:', self.myPosition
			for oppo in Ghosts:
				print "GhostPosition:", oppo[1]
			for item in distanceToGhosts:
				if item[0] <= 3:			#3 is alert distance
					print 'alert!', item
					dx = item[1][0] - self.myPosition[0]
					dy = item[1][1] - self.myPosition[1]
					if dx > 0:
						if Directions.EAST in actions:
							actions.remove(Directions.EAST)
							print 'remove east'
					if dx < 0:
						if Directions.WEST in actions:
							actions.remove(Directions.WEST)
							print 'remove west'
					if dy > 0:
						if Directions.NORTH in actions:
							actions.remove(Directions.NORTH)
							print 'remove north'
					if dy < 0:
						if Directions.SOUTH in actions:
							actions.remove(Directions.SOUTH)
							print 'remove south'
				if item[0] <= 5:
					self.statusForAvoidGhost = True
					self.avoidingGhostTime += 1
					if Directions.STOP in actions:
						actions.remove(Directions.STOP)
					# nextRound = [(self.avoidDeadEnd(gameState,action),action) for action in actions]
					nextRound = list()
					for action in actions:
						successor = self.getSuccessor(gameState, action)
						position = successor.getAgentState(self.index).getPosition()
						x, y = position
						print "TESTING: if doing action", action, ", position is (", x, ",", y, ")"
						print "TESTING: deadEndMap[%d][%d] info: %d" % (int(x), int(y), self.deadEndMap[int(x)][int(y)])
						nextRound.append((self.deadEndMap[int(x)][int(y)], action))
					for next in nextRound:
						if next[0] > 0:		#this next is the entrance of a dead end
							actions.remove(next[1])
							print 'the action %s to the entrance of a dead end from (%d, %d) has been removed' % (next[1], x, y)
		# print "TESTING statusForAvoidGhost:", self.statusForAvoidGhost
		print "TESTING avoidingGhostTime:", self.avoidingGhostTime
		# if self.avoidingGhostTime >=30:
		# 	print "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
		return actions


	def checkDeath(self, gameState):
		"""
		@version 1.3
		check did I dead
		And Update self.deathNumber
		return boolean value
		"""
		position = gameState.getAgentPosition(self.index)
		# beginningTower = gameState.getAgentState(index).beginningTower
		#
		# print beginningTower, "!!!!!!!!!!"
		if position == self.beginningTower:
			# if index == self.index:	 #if this agent check is myself
			self.deathNumber += 1
			self.avoidingGhostTime = 0
			self.statusForAvoidGhost = False
			self.foodList = self.getFood(gameState).asList()
			distanceToFood = [(self.getMazeDistance(self.myPosition,food),food) for food in self.foodList]
			distanceToFood = sorted(distanceToFood, key = lambda x:x[0])
			self.target = distanceToFood[0][1]
			print "I have dead",self.deathNumber, "times.\n"
			print "DEBUG : Check DeadEndMap after I have just dead:"
			for row in self.deadEndMap:
				print row
			print ""
			return True
		return False

	def updateCarryFood(self, gameState, bestAction):
		"""
		@version 1.3
		This function won't change the return value.
		This function is only for update carry food by using the bestAction
		The return value is still bestAction.
		"""
		self.myPosition = gameState.getAgentPosition(self.index)
		if	self.myPosition == self.beginningTower:
			self.carryFood = 0
		# checkDeath(gameState, self.index)

		for portal in self.portals:
			if self.myPosition == portal:
				self.carryFood = 0
				break

		successor = self.getSuccessor(gameState, bestAction)
		successorPosition = successor.getAgentPosition(self.index)
		x, y = successorPosition
		self.foodList = self.getFood(gameState).asList()
		if gameState.hasFood(x, y):
			for foodPosition in self.foodList:
				if foodPosition == successorPosition:
					self.carryFood += 1
					# self.lastEatingStep = MAX_STEP - self.stepLeft
					# print "testing carryFood :", self.carryFood
		return bestAction

	def backToSafetyPosition(self, gameState, actions):
		"""
		@version 1.0
		"""
		bestDistance = 99999
		for action in actions:
			successor = self.getSuccessor(gameState, action)
			position = successor.getAgentPosition(self.index)
			# print "position: ", type(position)
			distance = min([self.getMazeDistance(safetyPosition, position) for safetyPosition in self.portals])
			# distance = self.getMazeDistance((16,10), position)
			if distance < bestDistance:
				bestAction = action
				bestDistance = distance
		# print type(bestAction)
		return bestAction

	def getPortals(self, gameState):
		"""
		@version 1.0
		"""
		portals = list()
		midBoundary = self.width/2
		oppoBoundary = midBoundary -1
		if self.teamColor:
			midBoundary, oppoBoundary = oppoBoundary, midBoundary
		for y in range(self.height):
			if (not gameState.hasWall(oppoBoundary, y)) and (not gameState.hasWall(midBoundary, y)):
				portals.append((midBoundary,y))
		return portals

	def getSuccessor(self, gameState, action):
		"""
		@version 1.0
		Finds the next successor which is a grid position (location tuple).
		"""
		successor = gameState.generateSuccessor(self.index, action)
		position = successor.getAgentState(self.index).getPosition()
		if position != nearestPoint(position):
			# Only half a grid position was covered
			return successor.generateSuccessor(self.index, action)
		else:
			return successor

	def estimate(self, gameState, action):
		"""
		@version 1.2.1
		Computes a linear combination of features and feature weights
		"""
		features = self.getFeatures(gameState, action)
		weights = self.getWeights(gameState, action)
		# print "---------------------\n\n", \
		#	 "stepLeft:", self.stepLeft, "\n",\
		#	 "index:", self.index , "\n",\
		#	 action, features * weights
		return features * weights

	def getOpponentsDetail(self, gameState, index):
		"""
		@version 1.1
		return a list including each opponent's index and position if this opponent can be observed.
		if not, it will return empty list.
		so, it can be check by len()
		"""
		# self.myPosition = gameState.getAgentPosition(self.index)
		state = gameState.deepCopy()
		if index in state.redTeam:
			team = state.redTeam
			otherTeam = state.blueTeam
		else:
			otherTeam = state.redTeam
			team = state.blueTeam
		enemyObservingList = list()
		for enemy in otherTeam:
			 enemyPosition = state.getAgentPosition(enemy)
			 if enemyPosition != None:
				enemyObservingList.append((enemy, enemyPosition))
		return enemyObservingList

	def isInMySide(self, gameState, agentIndex):
		"""
		@version 1.2.1
		Assuming all agents of this agentIndex can be observed
		The function return True only when the agent of this agentIndex in my side
		It return False when the agent is in other side
		"""
		agentPosition = gameState.getAgentPosition(agentIndex)
		x,y = agentPosition
		portalX, portalY = self.portals[0]
		if self.teamColor:
			if x <= portalX:
				return True
			else:
				return False
		else:
			if x >= portalX:
				return True
			else:
				return False

	def aStarSearch(self,gameState,target):
		"""
		@version 1.4
		New A* search algorithm
		"""
		position = gameState.getAgentPosition(self.index)
		visited = set()
		queue = util.PriorityQueue()

		queue.push((gameState, position, []),self.heuristic(gameState,position, target))
		visited.add(position)

		while not queue.isEmpty():

			tempState, tempPosition, path = queue.pop()
			if tempPosition == target:
				# self.debugPath(gameState, path, [0.5,0.5,0.5], False)
				return path
			else:
				for action in tempState.getLegalActions(self.index):
					successor = self.getSuccessor(tempState, action)

					sucPos = successor.getAgentPosition(self.index)

					if sucPos not in visited:
						value = self.heuristic(tempState, target, sucPos) + len(path+[action])
						queue.push((successor, sucPos, path+[action]), value)
						if not target == sucPos:
							visited.add(sucPos)
		return []


	def heuristic(self,gameState, position1, position2):
		"""
		@version 1.4
		heuristic function for A* search
		"""
		#return util.manhattanDistance(position1, position2)
		return self.getMazeDistance(position1,position2)

	def isInDefenderEye(self,gameState):
		"""
		@version 2.3
		return the number of opponents which can be observed by my teammate
		"""

		visibleEnemy = 0

		defenderPosition = gameState.getAgentPosition(self.teamateIndex)

		if self.index in gameState.redTeam:
			team = gameState.redTeam
			otherTeam = gameState.blueTeam
		else:
			otherTeam = gameState.redTeam
			team = gameState.blueTeam
		enemyList = list()

		for enemy in otherTeam:

			enemyList.append(enemy)


		for enemyIndex in enemyList:

			if gameState.getAgentState(enemyIndex).isPacman:
				visibleEnemy+=1

				print "A attacker in our side"


			else:
				defenderPosition = gameState.getAgentPosition(self.teamateIndex)
				enemyPosition = gameState.getAgentPosition(enemyIndex)

				if enemyPosition is not None:
					distance = util.manhattanDistance(defenderPosition, enemyPosition)
					if distance<5:
						visibleEnemy+=1
		print "TESTING: In isInDefenderEye(), we can see,", visibleEnemy, "opponents in our side"
		return visibleEnemy

class Attacker(BaseAgent):
	"""
	#docstring for Attacker.
	A BaseAgent agent that seeks food.
	This is an agent for offensing.
	"""
	def loadCurrentAgentMode(self, gameState):
		"""
		@version 1.2
		This function is for change running mode for Attacker.
		"""
		self.isDefender = False



		self.checkDeath(gameState)
		# this shouldn't be absolute value. it should be like rewards according to different value.
		#e.g. when it's 8, it should have high reward for backing to backToSafetyPosition,
		# And if it's 4, it should consider to back to safetyPosition, like when there're only 5 foods left.
		# if gameState.data.timeleft <= 30:
		#	 self.considerBack = True
		#	 return

		if self.carryFood == 0:
			self.considerBack = False
			# return -1
			return

		if len(self.foodList) <= 2:
			self.considerBack = True
			# return -1
			return

		if self.stepLeft <= 30 and self.carryFood > 0:
			print "Time left is ", self.stepLeft
			self.considerBack = True
			return

		for portal in self.portals:
			if self.getMazeDistance(portal, self.myPosition) <= 3:
				if self.getScore(gameState) < 0 and self.carryFood >= abs(self.getScore(gameState)):
					print "TESTING !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
					self.considerBack = True
					return


	def nearestFoodDistance(self, gameState, action):
		"""
		@version 1.0
		"""
		minDistance = 99999
		nearestFood = None
		successor = self.getSuccessor(gameState, action)
		successorPosition = successor.getAgentPosition(self.index)
		foodList = self.getFood(successor).asList()
		for food in foodList:
			distance = self.getMazeDistance(successorPosition, food)
			if distance < minDistance:
				minDistance = distance
				nearestFood = food
		return minDistance, nearestFood

	def getFeatures(self, gameState, action):
		"""
		@version 1.2.1
		"""
		self.myPosition = gameState.getAgentPosition(self.index)
		features = util.Counter()
		successor = self.getSuccessor(gameState, action)
		foodList = self.getFood(successor).asList()
		features['foodRemained'] = -len(foodList)
		if len(foodList) >0:
			distanceWithNearestFood, nearestFood = self.nearestFoodDistance(gameState, action)
			features['distanceWithNearestFood'] = distanceWithNearestFood * (-1)

		# try:
		#	 gameState.makeObservation(self.index)
		# except Exception as e:
		#	 print e
		opponentObservingList = self.getOpponentsDetail(gameState,self.index)
		# oppoGhostList = list()
		# oppoPacmanList = list()
		distanceToGhost = 10	# set the value when oppo is unobservable
		distanceToPacman = 0.1
		if len(opponentObservingList) != 0:
			for opponent in opponentObservingList:
				if not self.isInMySide(gameState, opponent[0]):
					distanceToGhost = min([self.getMazeDistance(self.myPosition, oppo[1]) for oppo in opponentObservingList])
				else:
					distanceToPacman = (-1) * min([self.getMazeDistance(self.myPosition, oppo[1]) for oppo in opponentObservingList])
		# else:
		#	 distanceToGhost = 10	# set the value when oppo is unobservable
		#	 distanceToPacman = 0.1
		features['distanceToGhost'] = distanceToGhost
		# print "distance to pacman:", distanceToPacman
		features['distanceToPacman'] = distanceToPacman
		return features

	def getWeights(self, gameState, action):
		"""
		@version 1.2
		"""
		weights = { 'foodRemained': 100,
					'distanceWithNearestFood': 1,
					'distanceToGhost': 1000,
					'distanceToPacman': 500
					}
		return weights

	# def observationFunction(self, gameState):
	# 	"""
	# 	@version 1.2
	# 	make observation and update current weights
	# 	each eposido only update once
	# 	this is a override for CaptureAgent
	# 	"""
	# 	if len(self.observationHistory) > 0:
	# 		if not self.isInMySide(gameState,self.index):
	# 			self.updateWeights(self.lastState, self.lastAction, gameState)
	# 	return gameState.makeObservation(self.index)
	#
	# def updateWeights(self, gameState, action, nextState):
	# 	"""
	# 	@version 1.2.1
	# 	This is the TDupdate function for each weight for each action
	# 	Using Q-learning as the update rule
	# 	"""
	#
	# 	# for weight in weights:
	# 	# 	weight = weight + learningRate * (immediateReward + discountFactor * )
	# 	features = self.getFeatures(gameState, action)
	# 	weights = self.getWeights(gameState, action)
	# 	newWeights = weights.copy()
	# 	print "this the currentQ..."
	# 	currentQ = self.estimate(gameState, action)
	#
	# 	# from nextState to get the best action it can make:
	# 	# actions = nextState.getLegalActions(self.index)
	# 	# values = [self.estimate(nextState, action) for action in actions]
	# 	print "this is the nextQ..."
	# 	nextQ = self.computeValueFromQValues(nextState)
	# 	# bestActions = [action for action, value in zip(actions, values) if value == nextQ]	#Note that, it's bestActions rather than bestAction
	#
	# 	print "=======now we updateWeights========"
	# 	print 'features',features
	#
	# 	for feature in features:
	# 		# if actions:
	# 		newWeights[feature] = newWeights[feature] + self.alpha * (self.immediateReward \
	# 				+ self.discountFactor * nextQ - currentQ) * features[feature]
	# 		if newWeights[feature] < 0:
	# 			newWeights[feature] = 0.1
	# 			print "!!!!!!!!!changing weight accorodingly!!!!"
	# 		print "AGENT " + str(self.index) + " weights for " + feature + ": " + str(weights[feature]) + " ---> " + str(newWeights[feature])
	#
	# 		# else:
	# 		# 	weights[feature] = weights[feature] + self.alpha * (self.immediateReward \
	# 		# 		- currentQ) * features[feature]
	# 	self.weights = newWeights.copy()

class Defender(BaseAgent):
	"""
	#docstring for Defender.

	"""
	def loadCurrentAgentMode(self, gameState):
		"""
		@version 1.2
		This function is for change running mode for Defender.
		"""
		if self.isScared(gameState):

			self.isDefender = False
		else:
			self.isDefender = True
		# return -1

	def getNearestEnemy(self, gameState, targetList):
		"""
		@version 1.2
		"""
		minDistance = 99999
		target = None
		for targetPosition in targetList:

			myPosition = gameState.getAgentPosition(self.index)
			distance = self.getMazeDistance(targetPosition,myPosition)

			if distance < minDistance:
				minDistance = distance
				target = targetPosition

		return target



	def getDenfenseTarget(self, gameState):
		"""
		@version 1.2.1
		modify logic of this function
		This function should be replaced directly
		"""

		visibleEnemy = list()

		enemyList = self.getOpponentsDetail(gameState,self.index)

		for enemy in enemyList:

			enemyIndex, enemyPosition = enemy

			if	self.isInMySide(gameState,enemyIndex) and enemyPosition is not None:
				visibleEnemy.append(enemyPosition)

		if len(visibleEnemy)>0:
			return self.getNearestEnemy(gameState,visibleEnemy)
		else:
			highValuesPosition = self.getHighValuesPosition(gameState)

			return highValuesPosition

	def getHighValuesPosition(self,gameState):
		"""
		@version 1.2.1

		modify (i,j) to (x,y) and modify values
		"""
		# still	has problem

		values = self.getFoodYouAreDefending(gameState).asList()
		minDistance = 999999
		sumDistance = 0
		bestPosition = None


		if self.teamColor:
			leftSide = 0
			rightSide = self.width/2
		else:
			leftSide = self.width/2
			rightSide = self.width

		#the following loops has been change
		#need to modify to avoid similarity check
		for x in range(leftSide,rightSide):
			for y in range(self.height):
				if not self.walls[x][y]:
					position = (x, y)
					sumDistance = 0

					for target in values:
						sumDistance += self.getMazeDistance(position,target)

					if sumDistance < minDistance:
						minDistance = sumDistance
						bestPosition = position

		return bestPosition

	def defensePortals(self,gameState,ghostPosition):
		"""
		@version 1.2
		"""
		minDistance = 99999
		nearestPortal = None

		for portal in self.portals:
			distance = self.getMazeDistance(ghostPosition,portal)

			if distance< minDistance:
				minDistance = distance
				nearestPortal = portal

		return nearestPortal


	def numberOfPacman(self,gameState):
		"""
		@version 1.2.1
		modify for loop
		this function is renamed from pacOnMySide
		it should return the number of enemy pacman
		"""
		number = 0

		enemyList = self.getOpponentsDetail(gameState,self.index)

		for enemy in enemyList:
			enemyIndex, enemyPosition = enemy
			if self.isInMySide(gameState,enemyIndex):
				number +=1

		return number

	def waitPosition(self,gameState):
		"""
		@version 2.1
		fixbug
		"""
		minDistance = 99999
		sumDistance = 0
		middleSide = self.width/2
		middleHigh = self.height/2
		counterIndex = 0
		counIndex =0
		positionIndex = 0
		coun = []

		while counIndex<5:
			coun.append(0)
			counIndex+=1

		positionList=[]

		while positionIndex<5:
			positionList.append(middleSide)
			positionIndex+=1

		if self.teamColor:
			homeSide = middleSide - 4
			while homeSide != middleSide and counterIndex < 5:

				counter = 0
				index = 0

				while not gameState.hasWall(homeSide,middleHigh+index) and not gameState.hasWall(homeSide,middleHigh-index):

					counter += 1
					index += 1

					#positionList[counterIndex]=homeSide

					if counter > coun[counterIndex]:
						coun[counterIndex] = counter
						positionList[counterIndex] = homeSide

				homeSide = homeSide + 1
				counterIndex += 1

		else:
			homeSide = middleSide + 4
			while homeSide != middleSide and counterIndex < 5:

				counter = 0
				index = 0

				while not gameState.hasWall(homeSide,middleHigh+index) and not gameState.hasWall(homeSide,middleHigh-index):

					counter +=1
					index +=1

					if counter > coun[counterIndex]:
						coun[counterIndex] = counter
						positionList[counterIndex] = homeSide

				homeSide = homeSide - 1
				counterIndex +=1

		maxValue = max(coun)

		if maxValue == 0:

			if self.teamColor:
				dx = self.width/2 - 2

				dy1 = self.height/2
				dy2 = self.height/2
				if not gameState.hasWall(self.width/2 - 2, self.height/2):
					setPosition = (self.width/2 - 2, self.height/2)
				else:

					while gameState.hasWall(dx,dy1) and gameState.hasWall(dx,dy2):
						dy1 -=1
						dy2 +=1

					if gameState.hasWall(dx,dy1):
						setPosition = (dx,dy2)
					else:
						setPosition = (dx,dy1)


			else:
				dx = self.width/2 + 2

				dy1 = self.height/2
				dy2 = self.height/2
				if not gameState.hasWall(self.width/2 + 2, self.height/2):
					setPosition = (self.width/2 + 2, self.height/2)
				else:

					while gameState.hasWall(dx,dy1) and gameState.hasWall(dx,dy2):
						dy1 -=1
						dy2 +=1

					if gameState.hasWall(dx,dy1):
						setPosition = (dx,dy2)
					else:
						setPosition = (dx,dy1)

			return setPosition

		else:

			x = positionList[coun.index(maxValue)]

			waitPosition = (x ,middleHigh)

			return waitPosition

	def guessOppoPosition(self,gameState):

		"""
		@version 2.0

		guess enermy position

		"""
		preFood = self.teamFood
		preCapsule = self.teamCapsule
		myPosition = gameState.getAgentPosition(self.index)



		preTargets = preFood + preCapsule

		self.teamFood = self.getFoodYouAreDefending(gameState).asList()
		self.teamCapsule = self.getCapsulesYouAreDefending(gameState)

		myTargets = self.teamFood + self.teamCapsule

		for target in preTargets:
			if target not in myTargets:
				self.guessOppoPos.append(target)

		if self.guessOppoPos:
			if myPosition == self.guessOppoPos[-1]:

				self.guessOppoPos[:] = []
		else:
			pass

		return self.guessOppoPos

	def isEnemyVisible(self,gameState):

		"""
		@version 2.0
		"""
		visibleEnemy = list()

		enemyList = self.getOpponentsDetail(gameState,self.index)

		for enemy in enemyList:

			enemyIndex, enemyPosition = enemy

			if	self.isInMySide(gameState,enemyIndex) and enemyPosition is not None:
				visibleEnemy.append(enemyIndex)

		if len(visibleEnemy)>0:
			return True

		else:

			return False

	def numOfAttacker(self,gameState):

		"""
		@version 2.0
		return number of attacker
		"""
		attackerNum = 0
		for enemy in self.opponents:

			if gameState.getAgentState(enemy).isPacman:
				attackerNum +=1

		return attackerNum

	def setActions(self,gameState, target):
		"""
		@version 1.4
		This functino is renamed from nextActions
		This function will return action to get the target
		"""
		minDistance = 99999
		nextAction = random.choice( gameState.getLegalActions( self.index ))

		path = self.aStarSearch(gameState,target)

		#nextAction = path[0]

		if path:

			nextAction = path[0]

		else:

			for action in gameState.getLegalActions(self.index):
				successor = self.getSuccessor(gameState, action)

				position = successor.getAgentState(self.index).getPosition()

				distance= self.getMazeDistance(position,target)

				if distance<minDistance:
					minDistance = distance
					nextAction = action

		return	nextAction




	def isEscapeing(self,gameState):

		dx,dy = gameState.getAgentPosition(self.index)

		teamSide = gameState.isOnRedTeam(self.index)
		if teamSide:

			if dx <=self.width/2:
				return False
			else:
				return True
		else:
			if dx >= self.width/2:
				return False
			else:
				return True

		return False

	def getDenfenderActions(self,gameState,stepLeft):

		"""
		@version 2.1
		add one variable and timeout methods
		this defender will change strage when step less than 100
		pickDefenseTargetAbstract method
		"""

		guessOppoPos = self.guessOppoPosition(gameState)

		#this value can be used
		number = self.numOfAttacker(gameState)

		if self.isEscapeing(gameState):
			actions = gameState.getLegalActions(self.index)
			print "------Is Escapeing------"
			return self.backToSafetyPosition(gameState, actions)
		else:
			if self.isEnemyVisible(gameState):

				target = self.getDenfenseTarget(gameState)


				print "------I can see you ------ ",target

			else:

				if number>0:
					if guessOppoPos:
						target = guessOppoPos[-1]


						print "------I can guess you ------ ",target
					else:
						target =self.getDenfenseTarget(gameState)


						print "------I know you are here ------ ",target
				else:

					target = self.waitPosition(gameState)

					print "------I am waiting you ------ ",target


			action = self.setActions(gameState,target)

			return action


	def isScared(self,gameState):

		if gameState.getAgentState(self.index).scaredTimer > 20:
			return True
		else:
			return False


	def getFeatures(self, gameState, action):
		"""
		@version 1.1
		"""
		return 0

	def getWeights(self, gameState, action):
		"""
		@version 1.1
		"""
		return 0
