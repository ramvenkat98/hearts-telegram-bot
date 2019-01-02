def initDict():
	with open('dictfile.txt', 'w') as f:
		f.write('{}')

def loadDict():
	with open('dictfile.txt', 'r') as f:
		s = f.read()
	exec("d = " + s)
	return d

global_dict = loadDict()

class UserInfo(object):
	def __init__(self, indiv_chat_id):
		self.indiv_chat_id = indiv_chat_id
		self.active_group = None




def getIndividualChatId(user_id):
	if user_id in global_dict:
		return global_dict[user_id].indiv_chat_id
	else:
		print("GG")
		return 1/0

def setActiveGroup(user_id, active_grop_chat_id):
	if user_id in global_dict:
		global_dict[user_id].active_group = active_group_chat_id
	else:
		print("GG")
		return 1/0
