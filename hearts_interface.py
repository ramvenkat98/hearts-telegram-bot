import random

# N, E, S, W are 0, 1, 2, 3
passing_order_list = [
	[1, 2, 3, 0],
	[3, 2, 1, 0],
	[2, 3, 0, 1],
	None
]

global_values = [str(i) for i in range(2, 11)] + ['J', 'Q', 'K', 'A']
global_suits = ['C', 'D', 'H', 'S']
global_all_cards = tuple([
	val + suit for val in global_values for suit in global_suits])

def get_points(card):
	if card == "QS":
		return 13
	#if card == "JD":
	#	return -10
	if card[1] == "H":
		return 1
	return 0

class HeartsMatch:
	def __init__(self):
		self.players = [HeartsPlayer() for i in range(4)] # N, E, S, W
		self.game_no = 0
		self.game = HeartsRound(self)
		self.match_over = False

	def next_game(self):
		self.game_no += 1
		self.game = HeartsRound(self)

	def end_match(self):
		self.match_over = True
		return ['match_over']

class HeartsRound:
	def __init__(self, match):
		self.match = match
		HeartsRound.deal_cards(self.match.players)

		# passing related
		self.not_passed = [0, 1, 2, 3]
		self.passing_order = passing_order_list[match.game_no % 4]

		# playing related
		self.round_no = 0
		self.first_player_no = None
		self.current_player_no = None
		self.cards_on_table = []
		self.hearts_broken = False

		# game state - can be 'passing', 'playing' or 'game_over'
		self.game_state = 'passing' if self.passing_order else 'playing'

	def make_move(self, player_no, move):
		if self.game_state == 'passing':
			self.make_move_passing(player_no, move)
		elif self.game_state == 'playing':
			self.make_move_playing(player_no, move)

	def make_move_passing(self, player_no, move):
		player = self.match.players[player_no]
		# check validity of player
		if player_no not in self.not_passed:
			raise NameError('Passed already')
		# check validity of move
		cards_to_pass = move.upper().split()
		if len(set(cards_to_pass)) != 3:
			raise NameError('Select three distinct cards to pass')
		for card in cards_to_pass:
			if card not in player.current_hand:
				raise NameError('Select three valid cards to pass')
		# make move
		for card in cards_to_pass:
			player.current_hand.remove(card)
			player.to_pass.append(card)
		self.not_passed.remove(player_no)
		if len(self.not_passed) == 0:
			return self.pass_cards_and_start_play()

	def make_move_playing(self, player_no, move):
		player = self.match.players[player_no]
		# check validity of player
		if player_no != self.current_player_no:
			raise NameError('Not your turn')
		# check validity of move
		move = move.upper()
		try:
			print("OK")
			# check length of move, valid suit
			assert(len(move) in (2, 3) and move[:-1] in global_values and
				move[-1] in global_suits)
			print("Still ok")
			val, suit = move[:-1], move[-1]
			# assert that player has that card in his hand
			assert(move in player.current_hand)
			print("Still still ok")
			if len(self.cards_on_table) == 0:
				print("Still still still ok")
				if suit == 'H' and not self.hearts_broken:
					# assert only hearts left
					print("Wut")
					assert(len(set(map(lambda x: x[1],
						player.current_hand))) == 1)
			else:
				first_suit = self.cards_on_table[0][1]
				# assert same suit or no cards of that suit
				assert(suit == first_suit or first_suit not in
					set(map(lambda x: x[1], player.current_hand)))

		except:
			raise NameError('This card cannot be played')
		# make move
		# if hearts, hearts broken
		if suit == 'H':
			self.hearts_broken = True
		# update cards on table
		self.cards_on_table .append(move)
		# update cards in hand
		player.current_hand.remove(move)
		# update next player
		self.current_player_no = (self.current_player_no + 1) % 4
		# if all cards on table, calculate points and start next round
		if len(self.cards_on_table) == 4:
			return self.end_round()
		return []

	def end_round(self):
		cards_on_table = self.cards_on_table
		# find highest card and owner
		orig_suit = cards_on_table[0][1]
		highest_card_index = 0
		highest_card_val = cards_on_table[0][0]
		for (i, card) in enumerate(cards_on_table):
			if (card[-1] == orig_suit and
				global_values.index(card[:-1]) >
				global_values.index(highest_card_val)):
				highest_card_index, highest_card_val = i, card[:-1]
		# sum points, give it to owner
		total_points = sum(list(map(get_points, cards_on_table)))
		player_no = (self.first_player_no + highest_card_index) % 4
		self.match.players[player_no].current_points += total_points
		# update first, current player, cards on table
		self.first_player_no, self.current_player_no = player_no, player_no
		self.cards_on_table = []
		# increase round no. by one
		self.round_no += 1
		# return result contains info about who got the hand
		res = [player_no]
		# if 13 rounds finished, then end game
		if self.round_no > 13:
			return res + self.end_game()
		return res

	def end_game(self):
		# add points
		ended_match = False
		res_current = []
		res_total = []
		for player in self.match.players:
			if player.current_points != 26:
				res_current.append(player.current_points)
				player.overall_points += player.current_points
				res_total.append(player.overall_points)
				player.current_points = 0
				if player.current_points > 50:
					ended_match = True
			else:
				# shoot the moon
				res_current.append(-26)
				player.overall_points -= 26
				res_total.append(player.overall_points)
				player.current_points = 0
		# change game state
		self.game_state = 'game_over'
		# end match if needed
		if ended_match:
			return [(res_current, res_total),] + self.match.end_match()
		return [(res_current, res_total),]

	def pass_cards_and_start_play(self):
		players = self.match.players
		# pass cards
		for (player_no, player) in enumerate(players):
			pass_to = players[self.passing_order[player_no]]
			pass_to.current_hand += player.to_pass
			pass_to.current_hand.sort(key = card_key)
			player.to_pass = []
		# start play
		self.round_no = 1
		self.first_player_no = HeartsRound.find_2_clubs(players)
		self.current_player_no = (self.first_player_no + 1) % 4
		players[self.first_player_no].current_hand.remove('2C')
		self.cards_on_table = ['2C',]
		self.game_state = 'playing'

	def find_2_clubs(players):
		for (player_no, player) in enumerate(players):
			if '2C' in player.current_hand:
				return player_no

	def deal_cards(players):
		hands = list(global_all_cards)
		random.shuffle(hands)
		for (i, player) in enumerate(players):
			player.current_hand = hands[13*i:13*(i+1)]
			player.current_hand.sort(key = card_key)

def card_key(c):
	return 13 * global_suits.index(c[-1]) + global_values.index(c[:-1])

class HeartsPlayer:
	def __init__(self):
		self.overall_points = 0
		self.current_hand = []
		self.to_pass = []
		self.current_points = 0

print("Imported hearts interface")

