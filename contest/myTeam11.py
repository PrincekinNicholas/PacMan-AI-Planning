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
		@version 1.3
		"""
		CaptureAgent.registerInitialState(self, gameState)
		'''
		Your initialization code goes here, if you need any.
		'''
		# Agent's Attribution
		self.beginningTower = gameState.getAgentPosition(self.index)
		self.teamColor = gameState.isOnRedTeam(self.index)
		self.myPosition = gameState.getAgentPosition(self.index)
		self.carryFood = 0
		self.teamFood = self.getFoodYouAreDefending(gameState).asList()
		self.isAttacker = True
		self.isDefender = True
		self.deathNumber = -1	 #due to it will plus 1 at begining game

		# Logic Attribution
		self.foodList = self.getFood(gameState).asList()
		self.maxFood = len(self.foodList)
		self.width = gameState.data.layout.width
		self.height = gameState.data.layout.height
		# print "self.width:", self.width
		# print "self.height:", self.height
		# self.stepLeft = 300
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


	# def chooseAction(self, gameState):
	#	 """
	#	 @version 1.3
	#	 Picks among the actions with the highest Q(s,a).
	#	 """
	#	 self.loadCurrentAgentMode(gameState)		#this function is for changing runing mode sometimes

	#	 self.stepLeft -= 1
	#	 if self.isDefender:
	#		 return self.getDenfenderActions(gameState,self.stepLeft)

	#	 actions = gameState.getLegalActions(self.index)
	#	 start = time.time()
	#	 values = [self.estimate(gameState, action) for action in actions]
	#	 print 'in Step %d, eval time for agent %d: %.4f' % (300 - self.stepLeft, self.index, time.time() - start)

	#	 maxValue = max(values)
	#	 # self.oldApproximatingQValue = maxValue			# just for recording the maxValue as the oldValue in next TDupdate function
	#	 bestActions = [action for action, value in zip(actions, values) if value == maxValue] #Note that, it's bestActions rather than bestAction


	#	 if self.considerBack:
	#		 #double check actions or bestActions as argument
	#		 return self.updateCarryFood(gameState, self.backToSafetyPosition(gameState, actions))

	#	 return self.updateCarryFood(gameState, random.choice(bestActions))

	def chooseAction(self, gameState):
		"""
		@version 1.4
		Picks among the actions with the highest Q(s,a).
		"""
		self.loadCurrentAgentMode(gameState)		#this function is for changing runing mode sometimes

		self.stepLeft -= 1
		if self.isDefender:
			return self.getDenfenderActions(gameState,self.stepLeft)

		actions = gameState.getLegalActions(self.index)
		actions = self.avoidGhost(gameState, actions)
		print 'my available actions...',actions
		# start = time.time(	)
		if len(actions) == 0:
			print "no place to go..."
			action = Directions.STOP
		else:
			action = random.choice(actions)


		if self.considerBack:
			#double check actions or bestActions as argument
			action = self.backToSafetyPosition(gameState, actions)
			return self.updateCarryFood(gameState, action)

		distanceToFood = [(self.getMazeDistance(self.myPosition,food),food) for food in self.foodList]
		distanceToFood = sorted(distanceToFood, key = lambda x:x[0])
		print 'distance to food',distanceToFood
		for i,food in enumerate(distanceToFood):
			print 'now the target is...',i,food
			path = self.aStarSearch(gameState,food[1])
			if len(path) != 0:
				if path[0] not in actions:
					print 'no in my actions list...'
					continue
				else:
					action = path[0]
					print 'made decision..',action
					break


		print 'final action ',action
		# num = self.getActionsNumber(gameState,action)
		# # print('now my next step have ',num,' options')
		#
		# if num == 2:
		#	 # action = Directions.STOP
		#	 actions.remove(action)
		#	 action = random.choice(actions)
		#	 print 'now I\'m running into a corner..'


		return self.updateCarryFood(gameState, action )

	def avoidGhost(self, gameState, actions):
		"""
		@version 1.4
		check is there ghost which are observation
		run if yes
		"""

		print 'my current action: ',actions
		opponentObservingList = self.getOpponentsDetail(gameState,self.index)
		# distanceToGhost = -1	# set the value when oppo is unobservable
		Ghosts = []
		if len(opponentObservingList) != 0:
			# print 'oberserving enemies...',opponentObservingList
			for opponent in opponentObservingList:
				if not self.isInMySide(gameState, opponent[0]):
					Ghosts.append(opponent)
		if len(Ghosts) != 0:
			actions.remove(Directions.STOP)
			# print 'ghosts, ',Ghosts
			distanceToGhosts = [(self.getMazeDistance(self.myPosition, oppo[1]),oppo[1]) for oppo in Ghosts]
			print 'distance to ghosts, ',distanceToGhosts
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
					nextRound = [(self.avoidDeadEnd(gameState,action),action) for action in actions]

					for item in nextRound:
						if item[0] == 2:
							actions.remove(item[1])
							print 'the enter of a dead end..',item[1]

		return actions

	def avoidDeadEnd(self,gameState,action):
		newState = self.getSuccessor(gameState,action)
		num = len(gameState.getLegalActions(self.index))
		return num

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
			print "I have dead",self.deathNumber, "times."
			# self.carryFood = 0
			# lifeIndex = len(self.lifecycleHistory)
			# self.lifecycleHistory.append(lifeIndex +1, 0)
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
		self.isAttacker = True
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
			return

		# if len(self.foodList) > 10:
		#	 if self.carryFood >= 8:
		#		 self.considerBack = True
		#		 return
		# elif len(self.foodList) >= 6:
		#	 if self.carryFood >= 4:
		#		 self.considerBack = True
		#		 return
		# else:
		#	 if self.carryFood >= 2:
		#		 self.considerBack = True
		#		 return

		if len(self.foodList) > self.maxFood -3:
			if self.deathNumber <= 4:
				if self.carryFood >= random.randint(8 - self.deathNumber *2 +1,9):
					self.considerBack = True
					print "\nin situation 1.\n"
					return
		elif len(self.foodList) > self.maxFood -10:
			if self.carryFood >= random.randint(8 - self.deathNumber,8):
				self.considerBack = True
				print "\nin situation 2.\n"
				return
		elif len(self.foodList) >= self.maxFood /2:
			if self.carryFood >= random.randint(3,5):
				self.considerBack = True
				print "\nin situation 3.\n"
				return
		else:
			if self.carryFood >= random.randint(1,4):
				self.considerBack = True
				print "\nin situation 4.\n"
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

	def updateWeights(self, weights, learningRate = 0.1, immediateReward = 0, discountFactor = 0.9):
		"""
		@version 1.2
		This is the TDupdate function for each weight for each action
		Using Q-learning as the update rule
		"""
		# for weight in weights:
		#	 weight = weight + learningRate * (immediateReward + discountFactor * )
		pass


class Defender(BaseAgent):
	"""
	#docstring for Defender.

	"""
	def loadCurrentAgentMode(self, gameState):
		"""
		@version 1.2
		This function is for change running mode for Defender.
		"""
		self.isAttacker = False
		self.isDefender = True

	def getNearestEnemy(self, gameState, targetList):
		"""
		@version 1.2
		"""
		minDistance = 99999
		target = None
		for tar in targetList:
			targetPosition = gameState.getAgentPosition(tar)
			myPosition = gameState.getAgentPosition(self.index)
			distance = self.getMazeDistance(targetPosition,myPosition)

			if distance < minDistance:
				minDistance = distance
				target = tar

		targetPosition = gameState.getAgentPosition(target)

		return targetPosition

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
				visibleEnemy.append(enemyIndex)

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
		@version 1.2.1
		modify a lot things, this function works good at this time
		This function is used for defender strategies
		It will return	a position
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
				setPosition = (self.width/2 - 2, self.height/2)
			else:
				setPosition = (self.width/2 + 2, self.height/2)
			return setPosition

		else:

			x = positionList[coun.index(maxValue)]

			waitPosition = (x ,middleHigh)

			return waitPosition

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

	def getDenfenderActions(self,gameState,stepLeft):
		"""
		@version 1.3
		add one variable and timeout methods
		this defender will change strage when step less than 100
		Abstract method
		"""

		self.numOfOppPac=self.numberOfPacman(gameState)

		# timeout = 100
		# if stepLeft > timeout:
		#	 if self.numOfOppPac == 0:
		#		 target = self.waitPosition(gameState)
		#	 else:
		#		 target = self.getDenfenseTarget(gameState)
		# else:
		#	 target = self.getDenfenseTarget(gameState)

		# please dont delete the following statement
		if self.numOfOppPac == 0:
			target = self.waitPosition(gameState)
		else:
			target = self.getDenfenseTarget(gameState)

		action = self.setActions(gameState,target)

		return action

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