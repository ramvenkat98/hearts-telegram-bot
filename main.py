import telegram
from api_key import tok

from telegram.ext import Updater
updater = Updater(token = tok)

dispatcher = updater.dispatcher

import logging
logging.basicConfig(format = 
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

p1_cards = [2, 4, 6, 8]
p2_cards = [1, 3, 7, 9]
players = []
player_no = 1
game_started = False
existing_card = None
points = [0, 0]

from telegram.ext import CommandHandler

def start(bot, update):
    print("hi")
    print("Chat id is", update.message.chat_id)
    print("User id is ", update.message.from_user.id)
    bot.send_message(chat_id = update.message.chat_id,
        text = "Starting game, send /join to join")
start_handler = CommandHandler('start', start)

def join(bot, update):
    if game_started: return
    if len(players) < 2 and update.message.from_user.id not in players:
        players.append(update.message.from_user.id)
    bot.send_message(chat_id = update.message.chat_id,
        text = "Welcome to the game %s"%(
            update.message.from_user.first_name))
    if len(players) == 2:
        bot.send_message(chat_id = update.message.chat_id,
            text = "Starting game!")
        startGame(bot, update)
join_handler = CommandHandler('join', join)

def end(bot, update):
    global game_started, players, p1_cards, p2_cards, player_no
    global existing_card, points
    print("Players are", players)
    if update.message.from_user.id in players:
        p1_cards = [2, 4, 6, 8]
        p2_cards = [1, 3, 7, 9]
        players = []
        player_no = 1
        game_started = False
        existing_card = None
        points = [0, 0]
        bot.send_message(chat_id = update.message.chat_id,
        text = "Game over!")
end_handler = CommandHandler('end', end)

def destroy(bot, update):
    if update.message.from_user.last_name == "Venkat":
        updater.stop()
destroy_handler = CommandHandler('destroy', destroy)

def makeMove(bot, update, args):
    print("Entered make move")
    global existing_card, points, p1_cards, p2_cards, player_no
    print("Player no is %d"%player_no)
    if not (game_started
        and players[player_no-1] == update.message.from_user.id):
        print("GG")
        return
    try:
        card_no = int(args[0])
    except:
        return
    print("Card no is %d"%card_no)
    if ((player_no == 1 and card_no not in p1_cards) or
        (player_no == 2 and card_no not in p2_cards)):
        bot.send_message(chat_id = update.message.chat_id,
            text = "Eh, make legal move la dog")
        return
    print("So far so good")
    if player_no == 1: p1_cards.remove(card_no)
    else: p2_cards.remove(card_no)
    if existing_card == None:
        existing_card = card_no
    else:
        if card_no > existing_card:
            points[player_no-1] += (card_no - existing_card) ** 2
        else:
            points[2-player_no] += (card_no - existing_card) ** 2
        existing_card = None

    player_no = 3 - player_no
    bot.send_message(chat_id = update.message.chat_id,
        text = "Move made successfully")
    if len(p2_cards) == 0:
        bot.send_message(chat_id = update.message.chat_id,
            text = "Winner is player %d"%(
            points.index(max(points)))+1)
        end(bot, update)
        return

    return promptMove(bot, update)
makeMove_handler = CommandHandler('makeMove', makeMove, pass_args = True)

def startGame(bot, update):
    global game_started
    game_started = True
    promptMove(bot, update)
    return

def promptMove(bot, update):
    state = "Player 1 Cards:\n%s\nPlayer 2 Cards:\n%s"%(str(p1_cards),
    str(p2_cards))
    pts = "\nP1 Points: %d\nP2 Points: %d\n"%(points[0], points[1])
    bot.send_message(chat_id = update.message.chat_id, text = state+pts)
    nextPlayer = "Player %d make move by sending /makeMove [cardNo]"%player_no
    bot.send_message(chat_id = update.message.chat_id, text = nextPlayer)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(join_handler)
dispatcher.add_handler(end_handler)
dispatcher.add_handler(destroy_handler)
dispatcher.add_handler(makeMove_handler)

from telegram.ext import MessageHandler, Filters
def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
        text="Sorry, I didn't understand that command.")
unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

updater.start_polling()
