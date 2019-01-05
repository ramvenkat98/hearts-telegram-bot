from hearts_interface import *
import telegram
import sys
sys.path.insert(0, '../TelegramsHeartsAPIKey')
from api_key import tok
import random

import logging
logging.basicConfig(format = 
	'%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.INFO)

# Commands:
# start - in group chat
# end - in group chat
# join - in group chat
# give [c1] [c2] [c3] - in private chat (to give away 3 cards)
# play [c] - in private chat (to play a card)
# general message - in private chat, echoed to all private chats

def start(bot, update):
	chat = update.message.chat
	user = update.message.from_user
	if chat.id == user.id:
		return send_private_message(bot,
			"Can only start a game in a group",
			user)
	else:
		if chat.id in GroupChat.active_groups:
			return send_public_message(bot,
				"A game has already been started \
				in this group", user, chat, user_specific = False)
		else:
			GroupChat(chat)
			return send_public_message(bot,
				"Successfully started a game, \
				message /join to join", user, chat, user_specific = False)

def end(bot, update):
	chat = update.message.chat
	user = update.message.from_user
	if chat.id == user.id:
		return send_private_message(bot,
			"End a game by sending /end in the \
			group chat where the game was created", user)
	else:
		if chat.id not in GroupChat.active_groups:
			return send_public_message(bot,
				"There is no ongoing game in this \
				group", user, chat)
		else:
			group = GroupChat.active_groups[chat.id]
			group.remove_group_and_active_users()
			return send_public_message(bot, "Game ended", user, chat)

def join(bot, update):
	print("Entered join")
	chat = update.message.chat
	user = update.message.from_user
	if chat.id == user.id:
		return send_private_message(bot,
			"Please join the game via a group",
			user)
	else:
		print("Entered public join function")
		return join_game_public(bot, user, chat)

def join_game_public(bot, user, chat):
	# game not initiated in the group
	if chat.id not in GroupChat.active_groups:
		return send_public_message(bot,
			"Please initiate a hearts\
			game in the group first", user, chat)
	group = GroupChat.active_groups[chat.id]
	# user joined a game already
	if user.id in PrivateChat.user_ids_to_group:
		joined_group = PrivateChat.user_ids_to_group[user.id]
		if group == joined_group:
			return send_public_message(bot,
				"Already joined the game in this \
				group", user, chat)
		else:
			send_public_message(bot,
				"Already joined the game in another group",
				user, chat)
			return send_private_message(bot,
				"Aready joined the game in the \
				group %s"%(joined_group.chat.title), user)
	# game in the group is full/started already
	if group.match_started or len(group.private_chats) == 4:
		return send_public_message(bot,
			"Game in this group is already full",
			user, chat)
	# game has been initiated, has available spots, user also available
	# user successfully joins game
	return successful_join_game_public(bot, user, group)

def successful_join_game_public(bot, user, group):
	# add user
	group.private_chats.append(PrivateChat(user, group))
	send_public_message(bot, "%s successfully joined the game"%(
		user.first_name), user, group.chat,
		user_specific = False)
	send_private_message(bot, "Successfully joined the game in %s"%(
		group.chat.title), user)
	# start match if full
	if len(group.private_chats) == 4:
		group.start_match(bot)

def give(bot, update, args):
	chat = update.message.chat
	user = update.message.from_user
	if chat.id != user.id:
		return send_public_message(bot,
			"Please give cards in private chat",
			chat)
	if user.id not in PrivateChat.user_ids_to_group:
		return send_private_message(bot, "Please join a game first", user)
	joined_group = PrivateChat.user_ids_to_group[user.id]
	if not joined_group.match_started:
		return send_private_message(bot, "Match hasn't started yet", user)
	if joined_group.match.game.game_state != 'passing':
		return send_private_message(bot,
			"Now is not the time to give cards \
			away", user)
	try:
		player_no = find_player_no(user, joined_group.private_chats)
		joined_group.match.game.make_move_passing(player_no, ' '.join(args))
		send_to_all_private(bot,
			"%s has passed his cards"%user.first_name,
			joined_group.private_chats)
		if joined_group.match.game.game_state == 'playing':
			send_to_all_private(bot,
				"All cards have been passed",
				joined_group.private_chats)
			for (i, private_chat) in enumerate(joined_group.private_chats):
				send_private_message(bot, craft_cards_list(
					joined_group.match.players[i].current_hand),
				private_chat.user)
			return joined_group.prompt_move(bot)
	except NameError as err:
		print("Error:", err)
		return send_private_message(bot, err.args[0], user)


def find_player_no(user, private_chats):
	for (i, pc) in enumerate(private_chats):
		if pc.user.id == user.id:
			return i
	raise NameError("No such user!")

def play(bot, update, args):
	chat = update.message.chat
	user = update.message.from_user
	if chat.id != user.id:
		return send_public_message(bot, "Please play in private chat",
			user, chat)
	if user.id not in PrivateChat.user_ids_to_group:
		return send_private_message(bot, "Please join a game first", user)
	joined_group = PrivateChat.user_ids_to_group[user.id]
	if not joined_group.match_started:
		return send_private_message(bot, "Match hasn't started yet", user)
	if joined_group.match.game.game_state != 'playing':
		return send_private_message(bot, "Now is not the time to play cards",
			user)
	try:
		player_no = find_player_no(user, joined_group.private_chats)
		res = joined_group.match.game.make_move_playing(player_no,
			' '.join(args))
		send_to_all_private(bot, "%s has played the move %s"%(
			user.first_name, args[0]), joined_group.private_chats)
		if len(res) == 0:
			joined_group.prompt_move(bot)
		else:
			send_to_all_private(bot, "%s got the cards from the round"%(
				joined_group.private_chats[res[0]].user.first_name),
				joined_group.private_chats)
			if len(res) == 1:
				joined_group.prompt_move(bot)
			else:
				names, points = (list(map(lambda x: x.user.first_name,
					joined_group.private_chats)), res[1])
				send_to_all_private(bot, "The current game finished!\n\
					%s got %s points in this round and %s points overall \
					so far"%(names, points[0], points[1]),
					joined_group.private_chats)
				if len(res) > 2:
					return joined_group.end_match()
				else:
					send_to_all_private(bot, "The next game starts!",
						joined_group.private_chats)
					joined_group.start_game(bot)
	except NameError as err:
		print("Error: ", err)
		return send_private_message(bot, err.args[0], user)
	pass

## MIGHT EVENTUALLY WANNA GROUP THESE AS METHODS
# attach user's name to distinguish
def send_public_message(bot, msg, user, chat, user_specific = True):
	if user_specific:
		msg_str = "%s:\n%s"%(user.first_name, msg)
	else:
		msg_str = msg
	return bot.send_message(chat_id = chat.id, text = msg_str)

def send_private_message(bot, msg, user):
	return bot.send_message(chat_id = user.id, text = msg)

def send_to_all_private(bot, msg, private_chats):
	for pc in private_chats:
		bot.send_message(chat_id = pc.user.id, text = msg)

# Helpers to craft messages
def craft_general_prompt_move(cards_on_table, user_to_play,
	round_no, order):
	return "Round no. %d\n%s's turn\nCards on table: %s\nOrder: %s"%(
		round_no, user_to_play.first_name, cards_on_table, order)

def craft_cards_list(cards):
	by_suit = [[], [], [], []]
	for card in cards:
		by_suit[global_suits.index(card[-1])].append(card)
	msg = "Your cards are:"
	for suit in by_suit:
		msg += "\n" + " ".join(suit)
	return msg

class GroupChat:
	active_groups = {}
	def __init__(self, chat):
		self.chat = chat
		self.private_chats = []
		self.match_started = False
		self.match = None
		GroupChat.active_groups[self.chat.id] = self
	def __eq__(self, other):
		return (isinstance(other, GroupChat) and
			self.chat.id == other.chat.id)
	def __hash__(self):
		return self.chat_id
	def start_match(self, bot):
		self.match_started = True
		self.match = HeartsMatch()
		random.shuffle(self.private_chats) # order players NESW randomly
		# announce positions of players
		send_to_all_private(bot,
			"Match starting!\nN: %s\nE: %s\nS: %s\nW: %s\n"%(
			tuple(map(lambda x: x.user.first_name, self.private_chats))),
			self.private_chats)
		return self.start_game(bot)
	def start_game(self, bot):
		# announce cards privately to each player
		for (i, private_chat) in enumerate(self.private_chats):
			send_private_message(bot, craft_cards_list(
				self.match.players[i].current_hand), private_chat.user)
		# tell them to give away 3 accordingly if needed
		if self.match.game.game_state == 'playing':
			return self.prompt_move(bot)
		else:
			send_to_all_private(bot,
				"Select three cards to pass by sending \
				/give [card1] [card2] [card3]", self.private_chats)
	def prompt_move(self, bot):
		game = self.match.game
		cards_on_table = game.cards_on_table
		user_to_play = self.private_chats[game.current_player_no].user
		round_no = game.round_no
		playing_order = [(game.first_player_no + i) % 4 for i in range(4)]
		playing_order = list(map(lambda x:
			self.private_chats[x].user.first_name,
			playing_order))
		# public msg about the next turn
		msg = craft_general_prompt_move(cards_on_table, user_to_play,
			round_no, playing_order)
		send_to_all_private(bot, msg, self.private_chats)
		# private msg to next player
		private_msg = ("Your turn! " +
			craft_cards_list(
			self.match.players[game.current_player_no].current_hand) +
			"\nEnter /play [card] to play")
		send_private_message(bot, private_msg, user_to_play)
	def end_match(self):
		pts_list = list(map(lambda x: x.overall_points, self.match.players))
		pts = min(pts_list)
		winner = self.private_chats[pts_list.index(pts)].user.first_name
		msg = "The match is over! The winner is %s with %d points"%(winner,
			pts)
		send_to_all_private(bot, msg, self.private_chats)
		return self.remove_group_and_active_users()
	def remove_group_and_active_users(self):
		GroupChat.active_groups.remove(self.chat.id)
		for private_chat in self.private_chats:
			private_chat.remove_active_user()


class PrivateChat:
	user_ids_to_group = {}
	def __init__(self, user, group):
		self.user = user
		self.last_hand_message_id = None
		PrivateChat.user_ids_to_group[user.id] = group
	def start_new_round(self, round_info):
		pass
	def edit_ongoing_round(self, round_info):
		pass
	def delete_last_hand(self):
		pass
	def remove_active_user(self):
		PrivateChat.user_ids_to_group.remove(self.user.id)

# initialize
from telegram.ext import Updater
updater = Updater(token = tok)

dispatcher = updater.dispatcher

# add telegram commands
from telegram.ext import CommandHandler
# start
start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
# end
end_handler = CommandHandler('end', end)
dispatcher.add_handler(end_handler)
# join
join_handler = CommandHandler('join', join)
dispatcher.add_handler(join_handler)
# give (with args)
give_handler = CommandHandler('give', give, pass_args = True)
dispatcher.add_handler(give_handler)
# play (with args)
play_handler = CommandHandler('play', play, pass_args = True)
dispatcher.add_handler(play_handler)
# start
print("Starting...")
updater.start_polling()
updater.idle()


