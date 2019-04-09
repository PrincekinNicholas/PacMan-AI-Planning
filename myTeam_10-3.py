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
		@version 1.2
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

		# Logic Attribution
		self.foodList = self.getFood(gameState).asList()
		self.width = gameState.data.layout.width
		self.height = gameState.data.layout.height
		# print "self.width:", self.width
		# print "self.height:", self.height
		self.stepLeft = 300
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

		# =================================
		# bring out new parameters as follow
		# version 1.2
		# =================================

		self.weights = {'foodRemained': 100,
					'distanceWithNearestFood': 1000,
					'distanceToGhost': 100,
					'numberOfActions':1}
		# sefl.weights = util.Counter()
		self.alpha = 0.5
		self.learningRate = 0.1
		self.immediateReward = 0
		self.discountFactor = 0.9
		self.lastState = None
		self.lastAction = None
	def chooseAction(self, gameState):
		"""
		@1.2.1
		Picks among the actions with the highest Q(s,a).
		child class has overwrite this function
		"""
		self.loadCurrentAgentMode(gameState)		#this function is for changing runing mode sometimes

		if self.isDefender:
			return self.getDenfenderActions(gameState)

		#flip a coin to balance the exploration and exploitation


	def updateCarryFood(self, gameState, bestAction):
		"""
		@version 1.1
		This function won't change the return value.
		This function is only for update carry food by using the bestAction
		The return value is still bestAction.
		"""
		self.myPosition = gameState.getAgentPosition(self.index)
		if  self.myPosition == self.beginningTower:
			self.carryFood = 0

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
		print out the feature vector only
		"""
		features = self.getFeatures(gameState, action)
		weights = self.getWeights(gameState, action)
		# print [(feature) for feature in features]
		print "---------------------\n\n", \
			"stepLeft:", self.stepLeft, "\n",\
			"index:", self.index , "\n",\
			action, features
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




class Attacker(BaseAgent):
	"""
	#docstring for Attacker.
	A BaseAgent agent that seeks food.
	This is an agent for offensing.
	"""

	def loadCurrentAgentMode(self, gameState):
		"""
		@version 1.2.1
		This function is for change running mode for Attacker.
		"""

		self.isAttacker = True
		self.isDefender = False
		# this shouldn't be absolute value. it should be like rewards according to different value.
		#e.g. when it's 8, it should have high reward for backing to backToSafetyPosition,
		# And if it's 4, it should consider to back to safetyPosition, like when there're only 5 foods left.
		if gameState.data.timeleft <= 30:
			self.considerBack = True
			return

		if self.carryFood == 0:
			self.considerBack = False
			return

		if len(self.foodList) > 10:
			if self.carryFood >= 8:
				self.considerBack = True
				return
		elif len(self.foodList) >= 6:
			if self.carryFood >= 4:
				self.considerBack = True
				return
		else:
			if self.carryFood >= 2:
				self.considerBack = True
				return

	def computeActionFromQValues(self, gameState):
		"""
		@version 1.2
		return the action gets highest Qvalue
		if it's a tie, randomly pick one
		"""

		actions = gameState.getLegalActions(self.index)
		values = [self.estimate(gameState, action) for action in actions]
		maxValue = max(values)
			# self.oldApproximatingQValue = maxValue			# just for recording the maxValue as the oldValue in next TDupdate function
		bestActions = [action for action, value in zip(actions, values) if value == maxValue]	#Note that, it's bestActions rather than bestAction
		print "=======computeActionFromQValues======="
		for action,value in zip(actions, values):
			print 'action ',action, 'values ',value
		print "my current bestAction ", bestActions
		if bestActions == None:
			return Directions.STOP
		return random.choice(bestActions)

	def computeValueFromQValues(self, gameState):
		"""
		@version 1.2
		return the highest Qvalue from given state
		--similar to function computeActionFromQValues
		"""
		actions = gameState.getLegalActions(self.index)
		if len(actions) == 0:
			return 0

		values = [self.estimate(gameState, action) for action in actions]
		maxValue = max(values)
		return maxValue

	def chooseAction(self, gameState):
		"""
		@version 1.2.1

		"""
		self.observationHistory.append(gameState)

		actions = gameState.getLegalActions(self.index)

		if len(actions) == 0:
			return None


		if util.flipCoin(self.learningRate):
			action = random.choice(actions)
			print("now do exploitation")
		else:
			action = self.computeActionFromQValues(gameState)

		self.stepLeft -= 1

		if self.considerBack:
			#double check actions or bestActions as argument
			action = self.updateCarryFood(gameState, self.backToSafetyPosition(gameState, actions))

		self.lastState = gameState
		# action = self.updateCarryFood(gameState, random.choice(bestActions))
		self.lastAction = action

		# self.updateWeights(self.lastState, self.lastAction, gameState)
		print "above all, I choose ", action
		print "============================="
		print "=============ends============"
		print "============================="

		return self.updateCarryFood(gameState, action)

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
		add new features, to calculate the potential actions in next states
		to avoid dead end
		"""
		self.myPosition = gameState.getAgentPosition(self.index)
		features = util.Counter()
		successor = self.getSuccessor(gameState, action)
		foodList = self.getFood(successor).asList()
		features['foodRemained'] = -len(foodList)
		if len(foodList) >0:
			distanceWithNearestFood, nearestFood = self.nearestFoodDistance(gameState, action)
			# features['distanceWithNearestFood'] = distanceWithNearestFood * (-1)
			features['distanceWithNearestFood'] = distanceWithNearestFood * (-1)

		# try:
		# 	gameState.makeObservation(self.index)
		# except Exception as e:
		# 	print e
		opponentObservingList = self.getOpponentsDetail(gameState,self.index)
		oppoGhostList = list()
		oppoPacmanList = list()
		if len(opponentObservingList) != 0:
			# for opponent in opponentObservingList:

			distanceToGhost = min([self.getMazeDistance(self.myPosition, oppo[1]) for oppo in opponentObservingList])
		else:
			distanceToGhost = 10	# set the value when oppo is unobservable
		features['distanceToGhost'] = distanceToGhost
		features['numberOfActions'] = self.getActionsNumber(gameState, 2)
 		return features

	def getActionsNumber(self, gameState, steps):
		"""
		@version 1.2
		return the number of future actions
		"""
		actions = gameState.getLegalActions(self.index)
		numActions = len(actions)
		for action in actions:
			if steps > 0:
				newState = self.getSuccessor(gameState,action)
				numActions += self.getActionsNumber(newState,steps-1)
		return numActions

	def getWeights(self, gameState, action):
		"""
		@version 1.2.1
		"""
		return self.weights

	def observationFunction(self, gameState):
		"""
		@version 1.2
		make observation and update current weights
		each eposido only update once
		this is a override for CaptureAgent
		"""
		if len(self.observationHistory) > 0:
			self.updateWeights(self.lastState, self.lastAction, gameState)
		return gameState.makeObservation(self.index)

	def updateWeights(self, gameState, action, nextState):
		"""
		@version 1.2.1
		This is the TDupdate function for each weight for each action
		Using Q-learning as the update rule
		"""
		# for weight in weights:
		# 	weight = weight + learningRate * (immediateReward + discountFactor * )
		features = self.getFeatures(gameState, action)
		weights = self.getWeights(gameState, action)
		newWeights = weights.copy()
		currentQ = self.estimate(gameState, action)

		# from nextState to get the best action it can make:
		# actions = nextState.getLegalActions(self.index)
		# values = [self.estimate(nextState, action) for action in actions]
		nextQ = self.computeValueFromQValues(nextState)
		# bestActions = [action for action, value in zip(actions, values) if value == nextQ]	#Note that, it's bestActions rather than bestAction

		print "=======updateWeights========"
		print 'features',features
		for feature in features:
			# if actions:
			newWeights[feature] = newWeights[feature] + self.alpha * (self.immediateReward \
					+ self.discountFactor * nextQ - currentQ) * features[feature]
			print "AGENT " + str(self.index) + " weights for " + feature + ": " + str(weights[feature]) + " ---> " + str(newWeights[feature])

			# else:
			# 	weights[feature] = weights[feature] + self.alpha * (self.immediateReward \
			# 		- currentQ) * features[feature]
		self.weights = newWeights.copy()

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
		@version 1.2
		needs to add a new function named isPacman()
		need double check for modifying
		"""
		visibleEnemy = list()
		for OppoIndex in self.opponents:
			if not gameState.getAgentState(OppoIndex).isPacman and gameState.getAgentPosition(OppoIndex) is not None:
				visibleEnemy.append(OppoIndex)

		if len(visibleEnemy)>0:
			return self.getNearestEnemy(gameState,visibleEnemy)
		else:
			highValuesPosition = self.getHighValuesPosition(gameState)

			return highValuesPosition

	def getHighValuesPosition(self,gameState):
		"""
		@version 1.2
		needs to double check
		modify (i,j) to (x,y)
		"""
		values = self.teamFood
		minDistance = 99999
		sumDistance = 0
		bestPosition = gameState.getAgentPosition(self.index)
		j=0

		if self.teamColor:
			leftSide = 0
			rightSide = self.width/2
		else:
			leftSide = self.width/2
			rightSide = self.width

		for i in range(leftSide,rightSide):
			while j < self.height:
				position = (i,j)
				if not gameState.hasWall(i,j):
					sumDistance = 0
					for target in values:
						sumDistance = sumDistance + self.getMazeDistance(position,target)
					if sumDistance < minDistance:
						minDistance = sumDistance
						bestPosition = position
				j = j+1
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

	def pacOnMySide(self,gameState):
		"""
		@version 1.2
		need to modify
		"""
		number = 0
		for i in self.opponents:
			if gameState.getAgentState(i).isPacman: 	#need to modify
				number +=1
		return number

	def waitPosition(self,gameState):
		"""
		@version 1.2
		need to modify
		"""

		minDistance = 99999
		sumDistance = 0
		middleSide = self.width/2
		middleHigh = self.height/2
		index = 0
		i =0

		counterIndex = 0
		coun = []

		while i<5:
			coun.append(0)
			i+=1


		positionList=[]

		while i<8:
			positionList.append(middleSide)
			i+=1

		if self.teamColor:
			homeSide = middleSide - 5
			while homeSide != middleSide and counterIndex < 5:

				counter = 0

				while not gameState.hasWall(homeSide,middleHigh+index) and not gameState.hasWall(homeSide,middleHigh-index):

					counrt = counter+1
					positionList[counterIndex]=homeSide

					if counter > coun[counterIndex]:
						coun[counterIndex] = counter
					index = index +1
				else:
					homeSide = homeSide + 1

		else:
			homeSide = middleSide + 5
			while homeSide != middleSide and counterIndex < 5:

				counter = 0

				while not gameState.hasWall(homeSide,middleHigh+index) and not gameState.hasWall(homeSide,middleHigh-index):

					counrt = counter+1
					positionList[counterIndex]=homeSide

					if counter > coun[counterIndex]:
						coun[counterIndex] = counter
					index = index +1

				else:
					homeSide = homeSide - 1

		maxValue = max(coun)

		if maxValue == 0:
			return self.midPortal
		else:
			x = positionList(coun.index(maxValue))

			waitPosition = (x,middleHigh)

			return waitPosition

	def nextActions(self,gameState, target):
		"""
		@version 1.2
		This functino is for .......
		"""
		minDistance = 99999
		nextAction = random.choice( gameState.getLegalActions( self.index ))


		for action in gameState.getLegalActions(self.index):
			successor = self.getSuccessor(gameState, action)

			position = successor.getAgentState(self.index).getPosition()

			distance= self.getMazeDistance(position,target)

			if distance<minDistance:
				minDistance = distance
				nextAction = action

		return  nextAction

	def getDenfenderActions(self,gameState):
		"""
		@version 1.2
		waitOppo needs timeout
		"""
		self.numOfOppPac=self.pacOnMySide(gameState)
		if self.numOfOppPac == 0:
			target = self.waitPosition(gameState)
		else:
			target = self.getDenfenseTarget(gameState)

		action = self.nextActions(gameState,target)

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

	# def getFeatures(self, gameState, action):
	# 	features = util.Counter()
	# 	successor = self.getSuccessor(gameState, action)
	#
	# 	myState = successor.getAgentState(self.index)
	# 	myPos = myState.getPosition()
	#
	# 	# Computes whether we're on defense (1) or offense (0)
	# 	features['onDefense'] = 1
	# 	if myState.isPacman: features['onDefense'] = 0
	#
	# 	# Computes distance to invaders we can see
	# 	enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
	# 	invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
	# 	features['numInvaders'] = len(invaders)
	# 	if len(invaders) > 0:
	# 		dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
	# 		features['invaderDistance'] = min(dists)
	#
	# 	if action == Directions.STOP: features['stop'] = 1
	# 	rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
	# 	if action == rev: features['reverse'] = 1
	#
	# 	return features
	#
	# def getWeights(self, gameState, action):
	# 	return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2}
