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
from game import Directions, Actions
import game


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
			   first='AttackAgent', second='DefenseAgent'):
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


class MyAgent(CaptureAgent):
	"""
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
		self.step = 300
		self.myselfGhost = 0
		self.preSpecialMode = False
		self.specialMode = False
		self.specialPosition = None
		self.specialTop = None
		self.specialLow = None
		self.specialGoal = None
		self.specialAttackGoal = None
		self.readyToAttack = False
		self.readyStep = 0
		self.specialMode2 = False
		self.foodNumber = 0
		self.history = []
		self.memoryEnemy = None
		self.memoryGoal = None
		self.specialStep = 0

		self.defenseMode = False
		self.defenseModeFirst = False
		self.attackMode = False
		self.initial = gameState.getAgentPosition(self.index)
		self.isAttackAgent = False
		self.isDefenseAgentPacman = False
		self.width = gameState.data.layout.width
		self.height = gameState.data.layout.height
		self.side = gameState.isOnRedTeam(self.index)
		if self.side:
			self.left = 0
			self.right = self.width / 2
		else:
			self.left = self.width / 2
			self.right = self.width
		self.gate = self.getGate(gameState)
		self.gate3_1 = self.gate[len(self.gate) / 3]
		self.gate3_2 = self.gate[len(self.gate) * 2 / 3]

		self.foodOnMySide = self.getFoodYouAreDefending(gameState).asList()
		self.foodToEat = self.getFood(gameState).asList()
		self.opponents = self.getOpponents(gameState)
		self.team = self.getTeam(gameState)
		'''
		self.teamMate = 0
		for i in self.team:
			if i != self.index:
				self.teamMate = i
		'''

		# self.remainFood = list(self.foodOnMySide)
		self.enemyGhost = []
		self.enemyPacman = []
		self.enemyPacmanNumber = 0
		self.enemyPacmanNumberLast = 0
		self.capsulesToEat = []
		self.oppoScaredTimer = 0
		self.hideStep = 0

		self.opponentsIndex = self.getOpponents(gameState)
		self.birthSpot = gameState.getAgentPosition(self.index)
		self.teamIndex = self.getTeam(gameState)
		for i in self.teamIndex:
			if i != self.index:
				self.teamate = i
		self.walls = gameState.getWalls()
		self.cap = self.getCapsulesYouAreDefending(gameState)
		self.formerCap = self.cap

		self.enemyEliminated = False
		self.ourFood = self.getFoodYouAreDefending(gameState).asList()
		self.formerFood = self.ourFood
		self.targetFood = self.getFood(gameState).asList()
		self.holdPoint = self.getHoldPoint(gameState)

		self.attackCounter = 0
		self.attackerCounter = 0
		self.potentionalAttackLocation = list()
		self.hasAttack = False
		self.inRoundAttackCounter = 0
		self.lastRoundAttackCounter = 0
		self.lostFoodLog = dict()
		self.attackerOne = None
		self.formerState = gameState

		self.lostFoodLog[self.attackCounter] = 0

		self.foodLog = dict()

		self.foodLog[self.attackCounter] = 0

		self.inRoundlostFoodLogPosition = list()
		self.lastRoundlostFoodLogPosition = list()

		self.foodBeenTaken = dict()
		self.foodBeenTaken[self.attackCounter] = 0
		self.isScared = False


		self.approximateLog = list()
		self.nextEneTar = list()
		self.potentionalAttackLocation = list()


		'''
		Your initialization code goes here, if you need any.
		'''

	def getSpecialPosition(self, gameState):
		middleWidth = self.gate[0][0]

		if self.side:
			topX = middleWidth - 3
			topY = self.height - 2
			lowX = middleWidth - 3
			lowY = 2

			while gameState.hasWall(topX, topY):
				topX -= 1
			self.specialTop = (topX, topY)
			while gameState.hasWall(lowX, lowY):
				lowX -= 1
			self.specialLow = (lowX, lowY)
		else:
			topX = middleWidth + 3
			topY = self.height - 2
			lowX = middleWidth + 3
			lowY = 2

			while gameState.hasWall(topX, topY):
				topX += 1
			self.specialTop = (topX, topY)
			while gameState.hasWall(lowX, lowY):
				lowX += 1
			self.specialLow = (lowX, lowY)

		self.specialPosition = [self.specialLow, self.specialTop]

	def defenseAgentMCT(self, gameState):
		
		allActions = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
		self.foodToEat = self.getFood(gameState).asList()
		position = gameState.getAgentPosition(self.index)
		legalAction = []
		for action in allActions:
			dx, dy = Actions.directionToVector(action)
			if not gameState.hasWall(int(position[0] + dx), int(position[1] + dy)):
				legalAction.append(action)
		#print legalAction
		branch = {}
		for action in legalAction:
			branch[action] = 0

		mini = 9999
		for gate in self.gate:
			dis = self.getMazeDistance(gate, position)
			if dis < mini:
				mini = dis

		for i in range(100):
			mark = 0
			action = random.choice(legalAction)
			thisAction = action
			dx, dy = Actions.directionToVector(action)
			nextPosition = (int(position[0] + dx), int(position[1] + dy))
			if nextPosition in self.foodToEat:
				mark += 1
			if nextPosition in self.gate:
				return action
			if len(self.enemyGhost) > 0:
				if nextPosition in self.enemyGhost:
					mark -= 1000

			j = 1
			while j < 4:
				legalAction1 = []
				for action in allActions:
					dx, dy = Actions.directionToVector(action)
					if not gameState.hasWall(int(nextPosition[0] + dx), int(nextPosition[1] + dy)):
						legalAction1.append(action)
				action = random.choice(legalAction1)
				dx, dy = Actions.directionToVector(action)
				nextPosition = (int(nextPosition[0] + dx), int(nextPosition[1] + dy))
				
				if nextPosition in self.foodToEat:
					mark += 1 * (0.8 ** j)
				if nextPosition in self.gate:
					mark += 100 * (0.8 ** j)
				if len(self.enemyGhost) > 0:
					if nextPosition in self.enemyGhost:
						mark -= 1000 * (0.8 ** j)
				
				mini2 = 9999
				for gate in self.gate:
					dis = self.getMazeDistance(gate, nextPosition)
					if dis < mini2:
						mini2 = dis

				mark += 25 * (mini - mini2)
				j += 1

			mark += 25 * (mini - mini2)
			branch[thisAction] += mark

		#print branch
		maxMark = -99999
		bestAction = []
		for action in branch:
			if branch[action] == maxMark:
				bestAction.append(action)
			if branch[action] > maxMark:
				bestAction = [action]
				maxMark = branch[action]
		#print bestAction
		return random.choice(bestAction)









	def getHoldPoint(self, gameState):
		return (self.width / 2 - 2, self.height / 2)

	def isScaredAgent(self, gameState):
		if gameState.getAgentState(self.index).scaredTimer > 0:
			self.isScared = True
		else:
			self.isScared = False

	# max method
	def aStarSearch(self, gameState, target):
		"""Search the node that has the lowest combined cost and heuristic first."""
		actions = gameState.getLegalActions(self.index)
		cost = 9999
		chosenAction = list()
		for action in actions:
			successor = self.getSuccessor(gameState, action)
			if self.getMazeDistance(successor.getAgentPosition(self.index), target) < cost:
				cost = self.getMazeDistance(successor.getAgentPosition(self.index), target)
				chosenAction = list()
				chosenAction.append(action)
			elif self.getMazeDistance(successor.getAgentPosition(self.index), target) == cost:
				chosenAction.append(action)
		return chosenAction

	def getAttackerCounter(self, gameState):
		counter = 0
		for index in self.opponentsIndex:
			if gameState.getAgentState(index).isPacman:
				counter = counter + 1
		return counter

	def getAttacker(self, gameState):
		invaders = [a for a in self.opponentsIndex if gameState.getAgentState(a).isPacman]
		return invaders


	def approximateAttack(self):
		formerDots = self.formerFood + self.formerCap
		currentDots = self.currentFoodToProtect + self.cap
		for pos in formerDots:
			if pos not in currentDots:
				#print pos
				self.potentionalAttackLocation.append(pos)
				self.inRoundlostFoodLogPosition.append(pos)
		if len(self.potentionalAttackLocation) > 0:
			return True
		else:
			return False

	def getPotentialNextTarget(self):
		wish = list()
		dis = 999
		if len(self.potentionalAttackLocation) > 0 :
			#print 'next target'
			for pos in self.currentFoodToProtect:
				if self.getMazeDistance(pos, self.potentionalAttackLocation[-1]) < dis:
					dis = self.getMazeDistance(pos, self.potentionalAttackLocation[-1])
					wish = list()
					wish.append(pos)
				elif self.getMazeDistance(pos, self.potentionalAttackLocation[-1]) == dis:
					wish.append(pos)
		#print len(wish)
		return wish

	def shouldNextpostion(self):
		n = False
		if len(self.approximateLog) > 20:
			for pos in enumerate(self.approximateLog, -20):
				if pos:
					n = True
		else:
			for pos in enumerate(self.approximateLog, -len(self.approximateLog)):
				if pos:
					n = True
		return n


	def nearestFoodtoProtect(self, gameState):
		dist = 9999
		foods = list()
		for food in self.ourFood:
			if self.getMazeDistance(gameState.getAgentPosition(self.index), food) < dist:
				foods = list()
				dist = self.getMazeDistance(gameState.getAgentPosition(self.index), food)
				foods.append(food)
			elif self.getMazeDistance(gameState.getAgentPosition(self.index), food) < dist:
				foods.append(food)
		return foods

	def getAttackTime(self, gameState):
		if not self.hasAttack:
			if self.attackerCounter > 0:
				self.hasAttack = True
				self.attackCounter += 1
				self.foodBeenTaken[self.attackCounter] = 0
		elif self.hasAttack:
			if self.formerAttacker != self.attacker:
				for att in self.formerAttacker:
					if att not in self.attacker:
						if self.currentFoodToProtect == self.formerFood:
							self.foodBeenTaken[self.attackCounter] += self.getPreviousObservation().getAgentState(
								att).numCarrying
							self.attackCounter += 1
							self.foodBeenTaken[self.attackCounter] = 0
						else:
							self.foodBeenTaken[self.attackCounter] = 0
							self.attackCounter += 1
							self.foodBeenTaken[self.attackCounter] = 0

	def getPriorityzone(self):
		dis = 9999
		zone = None
		for dot in self.currentFoodToProtect:
			(x, y) = dot

			if self.walls[self.width / 2][y]:
				togate = 9999
				tar = None
				for gate in self.gate:
					if self.getManhattnDistance(gate, (self.width / 2, y)) < togate:
						tar = gate
						togate = self.getManhattnDistance(gate, (self.width / 2, y))
			else:
				tar = (self.width / 2, y)
			if self.getMazeDistance(dot, tar) < dis:
				zone = dot
				dis = self.getMazeDistance(dot, tar)
		return zone

	def attackerInsight(self, gameState):
		inSight = list()
		for ater in self.attacker:
			if gameState.getAgentState(ater).getPosition() != None:
				inSight.append(ater)
		return inSight

	def getNearestAttacker(self, gameState):
		a = list()
		dis = 9999
		for e in self.enemyInsight:
			if self.getMazeDistance(gameState.getAgentPosition(self.index), gameState.getAgentPosition(e)) < dis:
				dis = self.getMazeDistance(gameState.getAgentPosition(self.index), gameState.getAgentPosition(e))
				a = list()
				a.append(e)
			elif self.getMazeDistance(gameState.getAgentPosition(self.index), gameState.getAgentPosition(e)) == dis:
				a.append(e)
		return a

	def getTargetGate(self, gameState):
		dis = 0
		self.targetGate = list()
		for gate in self.gate:
			if self.getMazeDistance(self.birthSpot, gate) > dis:
				dis = self.getMazeDistance(gameState.getAgentPosition(self.index), gate)
				self.targetGate = list()
				self.targetGate.append(gate)
			elif self.getMazeDistance(gameState.getAgentPosition(self.index), gate) == dis:
				self.targetGate.append(gate)

	def getNearTargetGate(self, gameState):
		dis = 9999
		self.targetGate = list()
		for gate in self.gate:
			if self.getMazeDistance(gameState.getAgentPosition(self.index), gate) < dis:
				dis = self.getMazeDistance(gameState.getAgentPosition(self.index), gate)
				self.targetGate = list()
				self.targetGate.append(gate)
			elif self.getMazeDistance(gameState.getAgentPosition(self.index), gate) == dis:
				self.targetGate.append(gate)

	def getPastApproximateAttackZone(self):
		if self.red:
			left = 0
			right = self.width / 2
		else:
			left = self.width / 2
			right = self.width
		dis = 9999
		zone = None
		lastRoundlostFood = self.getSpreadLocation()
		for i in range(left, right):
			for j in range(self.height):
				dot = (i, j)
				if not self.walls[i][j]:
					sum = 0
					for pri in lastRoundlostFood:
						sum += self.getMazeDistance(dot, pri)
					if sum < dis:
						dis = sum
						zone = dot
		return zone


	def evaluate(self, gameState, action):
		features = self.getFeatures(gameState, action)
		weights = self.getWeights(gameState, action)
		return features * weights

	def getFeatures(self, gameState, action):
		features = util.Counter()
		successor = self.getSuccessor(gameState, action)
		enemies = [successor.getAgentState(i) for i in self.opponentsIndex]
		invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
		features['NumEnemy'] = len(invaders)
		if len(invaders) > 0:
			dists = [self.getMazeDistance(successor.getAgentPosition(self.index), a.getPosition()) for a in invaders]
			features['EnemyDistance'] = min(dists)
		features['homePod'] = self.getManhattnDistance(successor.getAgentPosition(self.index), self.birthSpot)
		return features

	def getWeights(self, gameState, action):
		return {'NumEnemy': -40, 'EnemyDistance': 100, 'homePod': -80}

	def getManhattnDistance(self, pos1, pos2):
		return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

	# my method

	def getGate(self, gameState):
		gate = []
		middleLine = self.width / 2
		oppoMiddleLine = middleLine - 1
		if self.side:
			middleLine = oppoMiddleLine
			oppoMiddleLine = oppoMiddleLine + 1
		for i in range(self.height):
			if not gameState.hasWall(middleLine, i) and not gameState.hasWall(oppoMiddleLine, i):
				gate.append((middleLine, i))
		return sorted(gate, key = lambda s:s[1])

	def isDeadRoad(self, gameState, givenAction, givenPosition):
		#allActions = [Directions.NOR]





		nodeExpand = 1
		initialState = gameState
		queue = util.Queue()
		dx, dy = Actions.directionToVector(givenAction)
		initialPosition = (int(givenPosition[0] + dx), int(givenPosition[1] + dy))
		traversalList = [givenPosition] + self.enemyGhost
		initialNode = [initialState, nodeExpand, initialPosition]
		queue.push(initialNode)

		while not queue.isEmpty():
			state, expandNumber, position = queue.pop()

			if self.side:
				if position[0] < self.width / 2 - 2:
					return False
			else:
				if position[0] > self.width / 2 + 2:
					return False

			if expandNumber >= 100:
				return False

			else:
				if not position in traversalList:
					for action in state.getLegalActions(self.index):
						if action != Directions.STOP:
							successor = self.getSuccessor(state, action)
							expandNumber += 1
							dx, dy = Actions.directionToVector(action)
							nextPosition = (int(position[0] + dx), int(position[1] + dy))
							if not nextPosition in traversalList:
								queue.push([successor, expandNumber, nextPosition])
				traversalList.append(position)
		# print 'isDeadRoad'
		# print expandNumber
		# print position
		return True

	def getMostCloestFood(self, gameState):
		minDistance = 9999
		bestFood = self.foodToEat[0]
		position = gameState.getAgentPosition(self.index)
		dic = {}

		for food in self.foodToEat:
			dic[food] = self.getMazeDistance(food, position)

		sortedFood = sorted(dic.items(), key=lambda item: item[1])
		i = 0



		return sortedFood[i][0]


	def getAttackGoal(self, gameState):

		self.foodToEat = self.getFood(gameState).asList()
		self.foodHasEaten = gameState.getAgentState(self.index).numCarrying
		self.capsulesToEat = self.getCapsules(gameState)
		position = gameState.getAgentPosition(self.index)
		if len(self.enemyGhost) > 0:
			minimum = 9999
			cloestEnemy = self.enemyGhost[0]
			for enemyPosition in self.enemyGhost:
				distance = self.getMazeDistance(enemyPosition, position)
				if distance < minimum:
					minimum = distance
					cloestEnemy = enemyPosition
		# cloest gate
		minDistance = 9999
		cloestGate = None
		for i in self.gate:
			distance = self.getMazeDistance(position, i)
			if distance < minDistance:
				minDistance = distance
				cloestGate = i
		goal = cloestGate

		if len(self.foodToEat) > 2:
			if self.foodHasEaten < 2:
				goal = self.getMostCloestFood(gameState)
			elif self.foodHasEaten >= 2 and len(self.enemyGhost) == 0:
				goal = self.getMostCloestFood(gameState)
			elif self.foodHasEaten >= 2 and self.oppoScaredTimer > 0:
				goal = self.getMostCloestFood(gameState)
			elif self.foodHasEaten >= 2 and self.getMazeDistance(cloestEnemy, position) > 5:
				goal = self.getMostCloestFood(gameState)
			elif self.foodHasEaten >= 2 and self.getMazeDistance(cloestEnemy, position) > 3 and self.step >= 30 + 220 * self.foodHasEaten / self.foodNumber:
				goal = self.getMostCloestFood(gameState)
			else:
				return goal

		if self.step < 30 and self.foodHasEaten > 0:
			goal = cloestGate

		# print goal
		return goal
		
	def getSuccessor(self, gameState, action):
		successor = gameState.generateSuccessor(self.index, action)
		pos = successor.getAgentState(self.index).getPosition()
		if pos != util.nearestPoint(pos):
			return successor.generateSuccessor(self.index, action)
		else:
			return successor

	def aStar(self, gameState, goal):
		# print goal
		priorityqueue = util.PriorityQueue()
		traversallist = []
		#traversal = set()
		position = gameState.getAgentPosition(self.index)
		traversallist.append(position)
		initialnode = [gameState, position, []]
		priorityqueue.push(initialnode, util.manhattanDistance(position, goal))
		if position == goal:
			return Directions.STOP

		i = 0
		while not priorityqueue.isEmpty():
			i += 1
			if i > 1500:
				print 'astarbigbigbigbug'
				break
			curState, curPosition, actions = priorityqueue.pop()
			if curPosition == goal:
				return actions[0]
			else:
				# print curState.getLegalActions(self.index)
				for action in curState.getLegalActions(self.index):
					if action == Directions.STOP:
						continue
					successor = self.getSuccessor(curState, action)
					dx, dy = Actions.directionToVector(action)
					successorPosition = (int(curPosition[0] + dx), int(curPosition[1] + dy))
					if successorPosition in self.enemyGhost and self.oppoScaredTimer <= 0:
						continue
					if successorPosition not in traversallist:
						priority = util.manhattanDistance(goal, successorPosition) + len(actions + [action])
						priorityqueue.push((successor, successorPosition, actions + [action]), priority)
						if not goal == successorPosition:
							traversallist.append(successorPosition)
		print 'aStarBug'
		#print gameState.getAgentPosition(self.index)
		#print gameState.getLegalActions(self.index)
		distance = 999
		for action in gameState.getLegalActions(self.index):
			if action == Directions.STOP:
				continue
			dx, dy = Actions.directionToVector(action)
			nextPosition = (int(position[0] + dx), int(position[1] + dy))
			if self.getMazeDistance(nextPosition, goal) < distance:
				distance = self.getMazeDistance(nextPosition, goal)
				bestAction = action

		return bestAction

	def attackDecision(self, gameState, goal):
		# print goal
		#try:
		position = gameState.getAgentPosition(self.index)
		self.capsulesToEat = self.getCapsules(gameState)
		if len(self.enemyGhost) > 0 and self.oppoScaredTimer <= 0:
			self.hideStep += 1
			# print self.hideStep
			# print 1
			minimum = 9999
			cloestEnemy = self.enemyGhost[0]
			for enemyPosition in self.enemyGhost:
				distance = self.getMazeDistance(enemyPosition, position)
				if distance < minimum:
					minimum = distance
					cloestEnemy = enemyPosition
			if minimum <= 3:
				actions = []
				for action in gameState.getLegalActions(self.index):
					if action == Directions.STOP:
						continue
					nextState = self.getSuccessor(gameState, action)
					deadRoad = self.isDeadRoad(nextState, action, position)
					if not deadRoad:
						dx, dy = Actions.directionToVector(action)
						nextPosition = (int(position[0] + dx), int(position[1] + dy))
						actions.append([action, nextPosition])
				if len(actions) == 1:
					return actions[0][0]  # return the action which not to the deadroad
				elif len(actions) > 1:
					maximumDis = 0
					actDisPair = []
					bestAction = []
					for action in actions:
						distance = self.getMazeDistance(cloestEnemy, action[1])
						actDisPair.append([action, distance])
						if distance > maximumDis:
							maximumDis = distance
					for item in actDisPair:
						if item[1] == maximumDis:
							bestAction.append(item[0])  # furthest to ghost
					if len(bestAction) == 1:
						return bestAction[0][0]  # return the action which furthest to ghost
					else:
						#print self.capsulesToEat
						if self.hideStep > 30:
							print self.hideStep
							if gameState.getAgentState(self.index).isPacman:  # if I am pacman
								bestChoice = []
								for action in bestAction:
									mini = 9999
									for gate in self.gate:
										dis = self.getMazeDistance(gate, action[1])
										if dis < mini:
											mini = dis
									bestChoice.append([action, mini])
								miniDis = 9999
								for item in bestChoice:
									if item[1] < miniDis:
										miniDis = item[1]
								for item in bestChoice:
									if item[1] == miniDis:
										return item[0][0]
							else:
								return self.aStar(gameState, self.initial)

						if len(self.capsulesToEat) > 0:  # has capsule
							bestChoice = []
							for action in bestAction:
								mini = 9999
								for capsules in self.capsulesToEat:
									dis = self.getMazeDistance(capsules, action[1])
									if dis < mini:
										mini = dis
								bestChoice.append([action, mini])
							miniDis = 9999
							for item in bestChoice:
								if item[1] < miniDis:
									miniDis = item[1]
							for item in bestChoice:
								if item[1] == miniDis:
									return item[0][0]
						# return the action cloest to the capsule
						else:
							if len(self.foodToEat) < 3:  # go home if remain food < 3
								bestChoice = []
								for action in bestAction:
									mini = 9999
									for gate in self.gate:
										dis = self.getMazeDistance(gate, action[1])
										if dis < mini:
											mini = dis
									bestChoice.append([action, mini])
								miniDis = 9999
								for item in bestChoice:
									if item[1] < miniDis:
										miniDis = item[1]
								for item in bestChoice:
									if item[1] == miniDis:
										return item[0][0]
							else:
								# select the position cloest to foods
								bestChoice = []
								# minDis = 9999
								for action in bestAction:
									mini = 9999
									for food in self.foodToEat:
										dis = self.getMazeDistance(food, action[1])
										if dis < mini:
											mini = dis
									bestChoice.append([action, mini])
								miniDis = 9999
								for item in bestChoice:
									if item[1] < miniDis:
										miniDis = item[1]
								for item in bestChoice:
									if item[1] == miniDis:
										return item[0][0]  # return the action cloest to foods
				else:
					print 'pacmanIsDead'
					#print gameState.getAgentPosition(self.index)
					#print gameState.getLegalActions(self.index)
					return random.choice(gameState.getLegalActions(self.index))

		self.hideStep = 0
		return self.aStar(gameState, goal)
	

	def chooseActionForDefenseAgent(self, gameState):

		self.isScaredAgent(gameState)
		self.attackerCounter = self.getAttackerCounter(gameState)
		actions = gameState.getLegalActions(self.index)
		self.onOffense = gameState.getAgentState(self.index).isPacman

		self.attacker = self.getAttacker(gameState)

		self.formerAttacker = self.getAttacker(self.formerState)
		self.enemyInsight = self.attackerInsight(gameState)

		self.currentFoodToProtect = self.getFoodYouAreDefending(gameState).asList()

		self.cap = self.getCapsulesYouAreDefending(gameState)
		self.approximate = self.approximateAttack()
		self.getAttackTime(gameState)

		self.currentPosition = gameState.getAgentPosition(self.index)
		self.getTargetGate(gameState)
		self.nextEneTar = self.getPotentialNextTarget()

		action = Directions.STOP
		#print self.attackCounter

		if not self.isScared:
			if not gameState.getAgentState(self.index).isPacman:
				if self.attackCounter == 0:
					action = random.choice(self.aStarSearch(gameState, random.choice(self.targetGate)))
				if self.attackerCounter > 0:
					if len(self.enemyInsight) > 0:
						if len(self.enemyInsight) == 1:
							action = random.choice(
								self.aStarSearch(gameState, gameState.getAgentPosition(self.enemyInsight[0])))
						elif len(self.enemyInsight) == 2:
							if gameState.getAgentState(self.enemyInsight[0]).numCarrying == gameState.getAgentState(
									self.enemyInsight[1]).numCarrying:
								d1 = self.getMazeDistance(
									self.currentPosition, gameState.getAgentPosition(self.enemyInsight[0]))
								d2 = self.getMazeDistance(
									self.currentPosition, gameState.getAgentPosition(self.enemyInsight[1]))
								if (d1 > d2):
									action = random.choice(
										self.aStarSearch(gameState,
														 gameState.getAgentPosition(self.enemyInsight[1])))
								else:
									action = random.choice(
										self.aStarSearch(gameState,
														 gameState.getAgentPosition(self.enemyInsight[0])))
							else:
								if gameState.getAgentState(
										self.enemyInsight[0]).numCarrying > gameState.getAgentState(
									self.enemyInsight[1]).numCarrying:
									action = random.choice(
										self.aStarSearch(gameState,
														 gameState.getAgentPosition(self.enemyInsight[0])))
									d1 = self.getMazeDistance(
											self.currentPosition, gameState.getAgentPosition(self.enemyInsight[0]))
									d2 = self.getMazeDistance(
											self.currentPosition, gameState.getAgentPosition(self.enemyInsight[1]))
									if (d1 > d2):
										action = random.choice(
													self.aStarSearch(gameState,
														 gameState.getAgentPosition(self.enemyInsight[1])))
									else:
										action = random.choice(
													self.aStarSearch(gameState,
														 gameState.getAgentPosition(self.enemyInsight[0])))
								else:
									if gameState.getAgentState(
											self.enemyInsight[0]).numCarrying > gameState.getAgentState(
										self.enemyInsight[1]).numCarrying:
										action = random.choice(
											self.aStarSearch(gameState,
															 gameState.getAgentPosition(self.enemyInsight[1])))
										d1 = self.getMazeDistance(
												self.currentPosition, gameState.getAgentPosition(self.enemyInsight[0]))
										d2 = self.getMazeDistance(
												self.currentPosition, gameState.getAgentPosition(self.enemyInsight[1]))
										if (d1 > d2):
											action = random.choice(
														self.aStarSearch(gameState,
														 	gameState.getAgentPosition(self.enemyInsight[1])))
										else:
											action = random.choice(
														self.aStarSearch(gameState,
															 gameState.getAgentPosition(self.enemyInsight[0])))
					elif len(self.enemyInsight) == 0:
						if self.approximate:
							#print 'approximate'
							action = random.choice(self.aStarSearch(gameState, random.choice(self.getPotentialNextTarget())))

							if len(self.getPotentialNextTarget()) == 0:
								#print'No'
								action = random.choice(self.aStarSearch(gameState, self.getPriorityzone()))
							elif len(self.getPotentialNextTarget()) > 0:
								#print'should'
								action = random.choice(self.aStarSearch(gameState, random.choice(self.getPotentialNextTarget())))
						else:
							action = random.choice(self.aStarSearch(gameState, self.getPriorityzone()))
				else:
					action = random.choice(self.aStarSearch(gameState, self.getPriorityzone()))
			else:
				action = self.defenseAgentMCT(gameState)
		else:
			# attacker method
			position = gameState.getAgentPosition(self.index)
			if self.preSpecialMode:
				#print 'openprespecialmode'
				self.specialStep += 1
				if self.specialStep >= 5:
					goal = self.getAttackGoal(gameState)
					if goal != self.memoryGoal:
						print 'closemode'
						self.preSpecialMode = False
						self.memoryEnemy = None
						self.memoryGoal = None
						self.history = []
						self.specialStep = 0

				position = gameState.getAgentPosition(self.index)
				if self.preSpecialMode and self.oppoScaredTimer > 0:
					self.preSpecialMode = False
					self.history = []
					self.memoryEnemy = None
					self.memoryGoal = None
					self.specialStep = 0
				if self.preSpecialMode and self.oppoScaredTimer <= 0:
					print 'openprespecialmode'
					bestActions = []
					for action in gameState.getLegalActions(self.index):
						if action == Directions.STOP:
							continue
						successor = self.getSuccessor(gameState, action)
						deadRoad = self.isDeadRoad(successor, action, position)
						if not deadRoad:
							dx, dy = Actions.directionToVector(action)
							position = gameState.getAgentPosition(self.index)
							nextPosition = (int(position[0] + dx), int(position[1] + dy))
							bestActions.append([action, self.getMazeDistance(nextPosition, self.memoryEnemy)])

					#print bestActions
					bestAction = []
					maxDistance = -1
					for action in bestActions:
						if action[1] == maxDistance:
							bestAction.append(action[0])
						if action[1] > maxDistance:
							bestAction = [action[0]]
							maxDistance = action[1]
					#print bestAction
					#if len(bestAction) > 0:

					return random.choice(bestAction)
					#else:
					#	return random.choice(gameState.getLegalActions(self.index))

			if self.specialMode:
				if self.readyToAttack == True and gameState.getAgentPosition(self.index) != self.specialAttackGoal:
					return self.aStar(gameState, self.specialAttackGoal)

				if gameState.getAgentPosition(self.index) == self.specialAttackGoal and self.readyToAttack == True:
					print 'get ready'
					self.readyToAttack = False
					self.specialMode = False
					self.history = []
					goal = self.getAttackGoal(gameState)
					return self.attackDecision(gameState, goal)

				if gameState.getAgentPosition(self.index) == self.specialGoal:
					print 'ready to attack'
					self.readyToAttack = True
					self.specialAttackGoal = self.setSpecialAttackGoal(gameState)
					return self.aStar(gameState, self.specialAttackGoal)
				
				return self.aStar(gameState, self.specialGoal)



			boo = gameState.getAgentState(self.index).isPacman
			if self.step <= 260:
				if len(self.history) < 15:
					self.history.append([position, boo])
				else:
					self.history.pop(0)
					self.history.append([position, boo])
					x = []
					y = []
					for i in range(15):
						x.append(self.history[i][0][0])
						y.append(self.history[i][0][1])
					xMax, yMax = max(x), max(y)
					xMin, yMin = min(x), min(y)
					if xMax - xMin <= 3 and yMax - yMin <= 3:
						status = []
						for i in range(15):
							status.append(self.history[i][1])
						if status.count(False) >= 4:
							self.specialMode = True
							self.getSpecialPosition(gameState)
							self.setSpecialGoal(gameState)
							return self.aStar(gameState, self.specialGoal)
						else:
							#print 'openprespecialmode'
							#print self.history
							goal = self.getAttackGoal(gameState)
							if len(self.enemyGhost) == 0:
								return self.aStar(gameState, goal)
							if len(self.enemyGhost) > 0:
								distance = 999
								for enemy in self.enemyGhost:
									if self.getMazeDistance(position, enemy) < distance:
										distance = self.getMazeDistance(position, enemy)
										cloestEnemy = enemy
								self.memoryEnemy = cloestEnemy
								self.memoryGoal = goal
								self.preSpecialMode = True
								#print self.memoryGoal, self.memoryEnemy
								#print "i love you"
								return self.attackDecision(gameState, goal)
			
			goal = self.getAttackGoal(gameState)
		
			return self.attackDecision(gameState, goal)
			# attack method ends


		self.formerFood = self.currentFoodToProtect
		self.formerCap = self.cap
		self.formerAttackerCounter = self.attackerCounter
		self.formerState = gameState




		#print action
		return action

	def setSpecialGoal(self, gameState):
		middleHeight = self.height / 2

		if gameState.getAgentPosition(self.index)[1] <= middleHeight + 2 and gameState.getAgentPosition(self.index)[1] >= middleHeight - 2:
			self.specialGoal = random.choice(self.specialPosition)
		elif gameState.getAgentPosition(self.index)[1] < middleHeight - 2:
			self.specialGoal = self.specialTop
		else:
			self.specialGoal = self.specialLow

	def setSpecialAttackGoal(self, gameState):
		middleWidth = self.gate[0][0]

		if self.side:
			x = middleWidth - 1
			while gameState.hasWall(x, gameState.getAgentPosition(self.index)[1]):
				x -= 1
		else:
			x = middleWidth + 1
			while gameState.hasWall(x, gameState.getAgentPosition(self.index)[1]):
				x += 1
		return (x, gameState.getAgentPosition(self.index)[1])

		



	def chooseAction(self, gameState):
		# print gameState.getAgentPosition(self.index)
		#print self.gate
		#print self.width
		self.step -= 1
		self.enemyGhost = []
		self.enemyPacman = []
		self.enemyPacmanNumber = 0
		for enemy in self.opponents:
			self.oppoScaredTimer = gameState.getAgentState(enemy).scaredTimer
			if gameState.getAgentState(enemy).isPacman:
				self.enemyPacmanNumber += 1
				if gameState.getAgentPosition(enemy) is not None:
					self.enemyPacman.append(gameState.getAgentPosition(enemy))
			if not gameState.getAgentState(enemy).isPacman:
				if gameState.getAgentPosition(enemy) is not None:
					self.enemyGhost.append(gameState.getAgentPosition(enemy))
		# try:
		if self.isAttackAgent:
			#print gameState.getLegalActions(self.index)
			#print self.myselfGhost
			#print self.step

			position = gameState.getAgentPosition(self.index)
			if self.preSpecialMode:
				print 'in pre-special mode'
				if not gameState.getAgentState(self.index).isPacman:
					self.preSpecialMode = False
					self.memoryEnemy = None
					self.memoryGoal = None
					self.history = []
					self.specialStep = 0

					self.specialMode = True
					self.getSpecialPosition(gameState)
					self.setSpecialGoal(gameState)
					return self.aStar(gameState, self.specialGoal)


				self.specialStep += 1
				if self.specialStep >= 5:
					goal = self.getAttackGoal(gameState)
					if goal != self.memoryGoal:
						print 'close pre-special mode'
						self.preSpecialMode = False
						self.memoryEnemy = None
						self.memoryGoal = None
						self.history = []
						self.specialStep = 0

				if self.specialStep >= 20:
					if len(self.enemyGhost) >= 0:
						goal = self.getAttackGoal(gameState)
						return self.attackDecision(gameState, goal)

				position = gameState.getAgentPosition(self.index)
				if self.preSpecialMode and self.oppoScaredTimer > 0:
					self.preSpecialMode = False
					self.history = []
					self.memoryEnemy = None
					self.memoryGoal = None
					self.specialStep = 0
				if self.preSpecialMode and self.oppoScaredTimer <= 0:
					#print 'openprespecialmode'
					bestActions = []
					for action in gameState.getLegalActions(self.index):
						if action == Directions.STOP:
							continue
						successor = self.getSuccessor(gameState, action)
						deadRoad = self.isDeadRoad(successor, action, position)
						if not deadRoad:
							dx, dy = Actions.directionToVector(action)
							position = gameState.getAgentPosition(self.index)
							nextPosition = (int(position[0] + dx), int(position[1] + dy))
							bestActions.append([action, self.getMazeDistance(nextPosition, self.memoryEnemy)])

					#print bestActions
					bestAction = []
					maxDistance = -1
					for action in bestActions:
						if action[1] == maxDistance:
							bestAction.append(action[0])
						if action[1] > maxDistance:
							bestAction = [action[0]]
							maxDistance = action[1]
					#print bestAction
					if len(bestAction) > 0:
						return random.choice(bestAction)
					else:
						return random.choice(gameState.getLegalActions(self.index))








			if self.specialMode:
				print 'in special mode'
				if self.readyToAttack == True and gameState.getAgentPosition(self.index) != self.specialAttackGoal:
					return self.aStar(gameState, self.specialAttackGoal)

				if gameState.getAgentPosition(self.index) == self.specialAttackGoal and self.readyToAttack == True:
					print 'get ready'
					self.readyToAttack = False
					self.specialMode = False
					self.history = []
					goal = self.getAttackGoal(gameState)
					return self.attackDecision(gameState, goal)

				if gameState.getAgentPosition(self.index) == self.specialGoal:
					print 'ready to attack'
					self.readyToAttack = True
					self.specialAttackGoal = self.setSpecialAttackGoal(gameState)
					return self.aStar(gameState, self.specialAttackGoal)
				
				return self.aStar(gameState, self.specialGoal)



			boo = gameState.getAgentState(self.index).isPacman
			if self.step <= 260:
				if len(self.history) < 20:
					self.history.append([position, boo])
				else:
					self.history.pop(0)
					self.history.append([position, boo])
					x = []
					y = []
					for i in range(20):
						x.append(self.history[i][0][0])
						y.append(self.history[i][0][1])
					xMax, yMax = max(x), max(y)
					xMin, yMin = min(x), min(y)
					if xMax - xMin <= 3 and yMax - yMin <= 3:
						status = []
						for i in range(20):
							status.append(self.history[i][1])
						if status.count(False) >= 4:
							self.specialMode = True
							self.getSpecialPosition(gameState)
							self.setSpecialGoal(gameState)
							return self.aStar(gameState, self.specialGoal)
						else:
							#print 'openprespecialmode'
							#print self.history
							goal = self.getAttackGoal(gameState)
							if len(self.enemyGhost) == 0:
								return self.aStar(gameState, goal)
							if len(self.enemyGhost) > 0:
								distance = 999
								for enemy in self.enemyGhost:
									if self.getMazeDistance(position, enemy) < distance:
										distance = self.getMazeDistance(position, enemy)
										cloestEnemy = enemy
								self.memoryEnemy = cloestEnemy
								self.memoryGoal = goal
								self.preSpecialMode = True
								#print self.memoryGoal, self.memoryEnemy
								#print "i love you"
								return self.attackDecision(gameState, goal)



			goal = self.getAttackGoal(gameState)
			

			return self.attackDecision(gameState, goal)

		else:
			# print gameState.getLegalActions(self.index), gameState.getAgentPosition(self.index)
			if self.defenseModeFirst:
				if self.enemyPacmanNumberLast > self.enemyPacmanNumber:
					self.defenseModeFirst = False
					self.attackMode = True
				else:
					self.enemyPacmanNumberLast = self.enemyPacmanNumber
					# goal = self.goalOfDefenseAgentInDefenseModeFirst(gameState)
					return self.chooseActionForDefenseAgent(gameState)
			if self.attackMode:
				if self.isDefenseAgentPacman == True and gameState.getAgentState(self.index).isPacman == False:
					# print 2
					self.attackMode = False
				else:
					# print 1
					self.isDefenseAgentPacman = gameState.getAgentState(self.index).isPacman
					goal = self.getAttackGoal(gameState)
					return self.attackDecision(gameState, goal)

			return self.chooseActionForDefenseAgent(gameState)


class AttackAgent(MyAgent):

	def registerInitialState(self, gameState):
		MyAgent.registerInitialState(self, gameState)
		self.isAttackAgent = True
		self.defenseMode = False
		self.attackMode = False
		self.foodNumber = len(self.getFood(gameState).asList())
		#print self.foodNumber


class DefenseAgent(MyAgent):

	def registerInitialState(self, gameState):
		MyAgent.registerInitialState(self, gameState)
		self.isAttackAgent = False
		self.defenseMode = False
		self.defenseModeFirst = False
		self.attackMode = False
		self.foodNumber = len(self.getFood(gameState).asList())


