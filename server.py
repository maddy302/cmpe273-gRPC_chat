import chatApp_pb2
import chatApp_pb2_grpc
import calculator
import grpc
from concurrent import futures
import time
import yaml
import threading
from threading import Thread, Lock
#users = ['alice','bob','charlie','eve','foo','bar','baz','qux','Maddy','Chinnu','Sri']
users = []
group1 = []
group2 = []
portnumber = 0
max_num_messages_per_user_g = 0
message_dict_offline = {}
group_memb_online_temp = {}
group_memb_dict_temp = {}
message_dict_group_temp = {}
max_call_per_30_seconds_per_user_g = 0
symmetric_key = ''
msg_count_list_grp_temp = {}
msg_count_list_temp = {}
lock = Lock()
# message_dict_offline = {
#     "alice" : [],
#     "bob" : [],
#     "charlie" : [],
#     "eve"   :[],
#     "foo"   :[],
#     "bar"   :[],
#     "baz"   :[],
#     "qax"   :[],
#     "Maddy" :[],
#     "Chinnu":[],
#     "Sri"   :[]
# }


friends_list = {
        "alice" : list(),
    "bob" : list(),
    "charlie" : list(),
    "eve"   :list(),
    "foo"   :list(),
    "bar"   :list(),
    "baz"   :list(),
    "qax"   :list(),
    "Maddy" :list(),
    "Chinnu":list(),
    "Sri"   :list()
}

onlineUsers = list()
onlineUsers_group = {}
# onlineUsers_group = {
#     "group1" : [],
#     "group2" : []
# }
messageList = list()
messageList_group = list()
class ChatMessage(object):
    clientFrom=""
    clientTo=""
    msg=""
    timestamp=""

    def __init__(self,clientFrom, clientTo, msg, timestamp):
        self.clientFrom = clientFrom
        self.clientTo = self.clientTo
        self.msg = msg
        self.timestamp = timestamp

class ExecuteExpressionServicer(chatApp_pb2_grpc.ExecuteExpressionServicer):
    def ExecExp(self, request, context):
        response = chatApp_pb2.Expression()
        response.operand1 = calculator.add(request.operand1,request.operand2)
        return response

# class getMessageStreamServicer(chatApp_pb2_grpc.getMessageStreamServicer):
#     def putMessagesInStream(self, request, context):
#         response = chatApp_pb2.toClient()
#         response.
class getMessageStreamServicer(chatApp_pb2_grpc.getMessageFromServerStreamServicer):
    
    def __init__(self, msg_count_list_temp):
        self.msg_count_list = msg_count_list_temp
        threading.Thread(target=self.rateLimiter, daemon=True).start()

    def rateLimiter(self):
        time.sleep(30)
        lock.acquire()
        # self.countOfMessages = 0
        # self.rate_exceeded = False
        self.msg_count_list = {x : 0 for x in self.msg_count_list}
        lock.release()
        
    def notifyOnlineStatus(self, request, response):
        #response = chatApp_pb2.informServerOnlineStatus()
        #response.clientID = request.clientID
        #print("Client ID: "+request.clientID)
        if users.count(request.clientID)<1:
            #response.status = "User Not found"
            return chatApp_pb2.informServerOnlineStatus(clientID = request.clientID,status = "User Not found" )

        if request.status =="logout" :
            onlineUsers.remove(request.clientID)
            #response.status = "offline"
            return chatApp_pb2.informServerOnlineStatus(clientID = request.clientID, status = 'offline')
        else:
            onlineUsers.append(request.clientID)
            #printOnlineUsers()
            #onlineUsers.append(request.clientID)
            return chatApp_pb2.informServerOnlineStatus(clientID = request.clientID, status = 'online')
            #response.status = "online"
        
        # return response

    def getMessageStream(self, request, context):
        #while True:
        indx = 0
        for message in messageList:
            
            if request.toClinetID == message.toClient:
                print(message.fromClient + message.toClient + message.msg)
                sendMsg = chatApp_pb2.sendMessage(fromClient=message.fromClient,toClient = message.toClient,msg= message.msg, timestamp= message.timestamp)
                messageList.pop(indx)
                indx = indx-1
                #message_dict.update({request.toClinetID:message_dict.get(request.toClinetID)-1})
                yield message
            indx = indx + 1
        # message_send_pop = message_dict.get(request.toClinetID)
        # #print(message_send_pop)
        # for message in message_send_pop:
        #     print(message.fromClient + message.toClient + message.msg)
        #     sendMsg = chatApp_pb2.sendMessage(fromClient=message.fromClient,toClient = message.toClient,msg= message.msg, timestamp= message.timestamp)
        #     (message_dict.get(request.toClinetID)).pop(indx)
        #     yield message
        #     indx = indx + 1

    def sendMessageService(self, request, response):
        # messageList.append(request)
        # print("length of messages as oon as msg is received " + str(len(messageList)))
        # #response.sentStatus = "Success"
        # response = chatApp_pb2.sentConfirmation(clientID = request.toClient,sentStatus= "Success")
        # return response
        if request.toClient in onlineUsers:
            lock.acquire()
            temp_msg_count = self.msg_count_list[request.fromClient]
            lock.release()
            if temp_msg_count < max_call_per_30_seconds_per_user_g:
                messageList.append(request)
                temp_msg_count = temp_msg_count + 1
                
                lock.acquire()
                self.msg_count_list[request.fromClient] = temp_msg_count
                lock.release()
                
                response = chatApp_pb2.sentConfirmation(clientID = request.toClient,sentStatus= "Success")
            else:
                response = chatApp_pb2.sentConfirmation(clientID = request.toClient, sentStaus= "Limit Exceeded")
            return response
        else:
            print(request.toClient + ' is offline')
            tempList = message_dict_offline.get(request.toClient)
            numberOfMessages = len(tempList)
            if(numberOfMessages<10):
            #messageList.append(request)
                tempList.append(request)
                message_dict_offline[request.toClient] = tempList
                #print(message_dict_offline[request.toClient] )
                response = chatApp_pb2.sentConfirmation(clientID = request.toClient,sentStatus= "Success")
                return response
            else:
                response = chatApp_pb2.sentConfirmation(clientID = request.toClient,sentStatus= "Queue full")
                return response


    def getOnlineUsers(self,request,context):
        for user in onlineUsers:
            yield chatApp_pb2.onlineUsers(clientID = user)

    def getOfflineMessage(self, request,response):
        indx = 0
        fromList = list()
        toList = list()
        msgList = list()
        timeList = list()
        msgOfflineList = message_dict_offline[request.toClinetID]
        for message in msgOfflineList:
            #print(len(msgOfflineList))
            if request.toClinetID == message.toClient:
                print(message.fromClient + message.toClient + message.msg)
                
                #message_dictmessage_dict.update({request.toClinetID:message_dict.get(request.toClinetID)-1})
                fromList.append(message.fromClient)
                toList.append(message.toClient)
                msgList.append(message.msg)
                timeList.append(message.timestamp)
                #msgOfflineList.pop(0)
                
            #indx = indx + 
        message_dict_offline[request.toClinetID] = []
        response = chatApp_pb2.sendMessageRepeated(fromClient=fromList,toClient = toList,msg= msgList, timestamp= timeList)
        return response
# def loadSampleMessages():
#     for i in range(5):
#         messageList.append(ChatMessage("Maddy","Chinnu","Hi this is no. "+str(i)))

class GroupChatServicer(chatApp_pb2_grpc.groupChatServicerServicer):
    
    group1 = []
    group2 = []
    group_memb_online = {}
    group_memb_dict = {}
    message_dict_group = {}
    max_call_per_30_seconds_per_user = 3
    max_num_messages_per_user = 5
    key = ''
    msg_count_list_grp = {}

    def __init__(self,group_memb_online_temp,group_memb_dict_temp,message_dict_group_temp, max_call_per_30_seconds_per_user_g, max_num_messages_per_user_g, symmetric_key, msg_count_list_grp_temp):
        # self.group1 = ['alice','bob','charlie','eve','Maddy','Chinnu','Shri']
        # self.group2 = ['foo','bar','baz','qux']
        # self.group_memb_online = {
        #     "group1" : [],
        #     "group2" : []
        # }
        self.max_call_per_30_seconds_per_user = max_call_per_30_seconds_per_user_g
        self.max_num_messages_per_user = max_num_messages_per_user_g
        self.key = symmetric_key
        self.group_memb_online = group_memb_online_temp
        # self.group_memb_dict = {
        # "group1" : self.group1,
        # "group2" : self.group2
        # }
        self.group_memb_dict = group_memb_dict_temp
        self.message_dict_group = message_dict_group_temp
        self.msg_count_list_grp = msg_count_list_grp_temp
        # self.message_dict_group = {
        # "alice" : [],
        # "bob" : [],
        # "charlie" : [],
        # "eve"   :[],
        # "foo"   :[],
        # "bar"   :[],
        # "baz"   :[],
        # "qux"   :[],
        # "Maddy" :[],
        # "Chinnu":[],
        # "Sri"   :[]
        # }
        threading.Thread(target=self.rateLimiter, daemon=True).start()
    
    def rateLimiter(self):
        time.sleep(30)
        lock.acquire()
        # self.countOfMessages = 0
        # self.rate_exceeded = False
        self.msg_count_list_grp = {x : 0 for x in self.msg_count_list_grp}
        lock.release()
#====================================================================================================================================#    
    def notifyOnlineStatus(self, request, response):
        #print("Inside notifyOnlineStatus")
        # if users.count(request.clientID)<1:
        #     #response.status = "User Not found"
        #     return chatApp_pb2.informServerOnlineStatus(clientID = request.clientID,status = "User Not found" )

        # if request.status =="logout" :
        #     onlineUsers.remove(request.clientID)
        #     #response.status = "offline"
        #     return chatApp_pb2.informServerOnlineStatus(clientID = request.clientID, status = 'offline')
        # else:
        #     onlineUsers.append(request.clientID)
        #     #printOnlineUsers()
        #     onlineUsers.append(request.clientID)
        #     return chatApp_pb2.informServerOnlineStatus(clientID = request.clientID, status = 'online')
        userFound = False
        #print("list of groups",list(self.group_memb_dict))
        #tempGroupList = list(self.group_memb_dict)
        for groupKey in list(self.group_memb_dict):
            #print("In loop "+groupKey)
            if((self.group_memb_dict.get(groupKey)).count(request.clientID) < 1):
                #return chatApp_pb2.informServerOnlineStatus(clientID = request.clientID,status = "User Not found")
                #print(self.group_memb_dict.get(groupKey))
                userFound = False
            else:
                userFound = True
                tempList = self.group_memb_online.get(groupKey)
                tempList.append(request.clientID)
                self.group_memb_online[groupKey] = tempList
                break
        if userFound:
            return chatApp_pb2.informServerOnlineStatus(clientID = request.clientID, status = groupKey)
        else :
            return chatApp_pb2.informServerOnlineStatus(clientID = request.clientID,status = "User Not found")

#==============================================================================================================================================#
    
    def getGroupMemebers(self, request, response):
        print("Inside getGroupMemebers")
        member_list = []
        for user in self.group_memb_dict[request.groupID]:
            member_list.append(user)
        return chatApp_pb2.group_list(clientID = member_list)
            
#==============================================================================================================================================#

    def sendMessageToGroup(self, request, response):
        print("Inside sendMessagetoGroup")
        lock.acquire()
        count_msg = self.msg_count_list_grp[request.fromClient]
        lock.release()
        if count_msg < self.max_call_per_30_seconds_per_user:
            for user in self.group_memb_dict[request.groupID]:
                if user!=request.fromClient:
                    tempList = self.message_dict_group.get(user)
                    numberOfMessages = len(tempList)
                    if(numberOfMessages<self.max_num_messages_per_user):
                    #messageList.append(request)
                        tempList.append(request)
                        self.message_dict_group[user] = tempList
                        print(self.message_dict_group[user] )
                #response = chatApp_pb2.sentConfirmation(clientID = request.toClient,sentStatus= "Success")
                #return response
                    else:
                        #tempList = message_dict_offline.get(user)
                        tempList.pop(0)
                        tempList.append(request)
                        self.message_dict_group[user] = tempList
                        print("After poping a value",self.message_dict_group[user])
                        #response = chatApp_pb2.sentConfirmation(clientID = request.toClient,sentStatus= "Queue full")
            count_msg = count_msg + 1
            lock.acquire()
            self.msg_count_list_grp[request.fromClient] = count_msg
            lock.release()
            return chatApp_pb2.sentConfirmation(clientID = request.groupID,sentStatus= "Success")
        else:
            return chatApp_pb2.sentConfirmation(clientID = request.groupID,sentStatus= "Limit Exceeded")
        #return chatApp_pb2.Empty()
#==============================================================================================================================================#

    def receiveMessageFromGroup(self, request, response):
        #print("Inside receiveMessageFromGroup")
        indx = 0
        messageListRcv = self.message_dict_group[request.clientID]
        for message in messageListRcv:
            #print("server will send this message back",message)
            #if request.groupID == message.groupID:
                #print(message.fromClient + message.toClient + message.msg)
            #sendMsg = chatApp_pb2.groupMessage(fromClient=message.fromClient,groupID = message.groupID,msg= message.msg, timestamp= message.timestamp)
            messageListRcv.pop()
            self.message_dict_group[request.clientID] = messageListRcv
            #indx = indx-1
                #message_dict.update({request.toClinetID:message_dict.get(request.toClinetID)-1})
            yield message
            #indx = indx + 1

#==============================================================================================================================================#


    def receiveOfflineMessageFromGroup(self, request, response):
        #print("Inside receiveofflinemessagefromgroup")
        indx = 0
        fromList = list()
        groupIDList = list()
        msgList = list()
        timeList = list()
        msgOfflineList = self.message_dict_group[request.clientID]
        for message in msgOfflineList:
            #print(len(msgOfflineList))
            if request.groupID == message.groupID:
                #print(message.fromClient + message.toClient + message.msg)
                
                #message_dictmessage_dict.update({request.toClinetID:message_dict.get(request.toClinetID)-1})
                fromList.append(message.fromClient)
                groupIDList.append(message.groupID)
                msgList.append(message.msg)
                timeList.append(message.timestamp)
                #msgOfflineList.pop(0)
                
            #indx = indx + 
        self.message_dict_group[request.clientID] = []
        response = chatApp_pb2.groupMessageRepeated(fromClient=fromList,groupID = groupIDList,msg= msgList, timestamp= timeList)
        return response
#==============================================================================================================================================#









def loadSampleUsersOnline():
    users.append("Maddy")
    users.append("Chinnu")
    users.append("Sri")

def printOnlineUsers():
    for i in range(len(onlineUsers)):
        print(onlineUsers[i])
#==============================================================================================================================================#

def yaml_load(filepath):
    with open(filepath, "r") as desc_file:
        data = yaml.load(desc_file)
        global portnumber
        portnumber =  data.get('port')
        global users
        users = data.get('users')
        global group_memb_online_temp
        global group_memb_dict_temp
        global message_dict_offline
        global max_num_messages_per_user_g
        global message_dict_group_temp
        global max_call_per_30_seconds_per_user_g
        global msg_count_list_grp_temp
        global msg_count_list_temp
        global symmetric_key
        max_call_per_30_seconds_per_user_g = data.get('max_call_per_30_seconds_per_user')
        max_num_messages_per_user_g = data.get('max_num_messages_per_user')
        
        symmetric_key = data.get('key')
        message_dict_offline = {}
        for i in range(len(users)):
            message_dict_offline[users[i]] = []
            msg_count_list_temp[users[i]] = 0
            #message_dict_group_temp[users[i]] = []

        groups = data.get('groups')
        #print(groups)
        
        group_memb_dict_temp = groups
        for grp in list(groups):
            group_memb_online_temp[grp] = []
            for usr in groups[grp]:
                message_dict_group_temp[usr] = []
                msg_count_list_grp_temp[usr] = 0

        #print(group_memb_online_temp)
        #print(message_dict_offline,group_memb_online_temp,group_memb_dict_temp,max_num_messages_per_user,message_dict_group_temp,max_call_per_30_seconds_per_user,symmetric_key)
        print("yaml loading completed, below are the new values")
#==============================================================================================================================================#

#loadSampleMessages()
yaml_load('config.yaml')
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
#chatApp_pb2_grc.add_ExecuteExpressionServicer_to_server(ExecuteExpressionServicer(),server)
chatApp_pb2_grpc.add_getMessageFromServerStreamServicer_to_server(getMessageStreamServicer(msg_count_list_temp),server)
chatApp_pb2_grpc.add_groupChatServicerServicer_to_server(GroupChatServicer(group_memb_online_temp,group_memb_dict_temp,message_dict_group_temp, max_call_per_30_seconds_per_user_g, max_num_messages_per_user_g, symmetric_key, msg_count_list_grp_temp),server)
print('server listing on port ',portnumber)
port_server = '[::]:'+str(portnumber)
server.add_insecure_port(port_server)
server.start()

try:
    while True:
        time.sleep(86400)
except KeyboardInterrupt:
    server.stop(0)