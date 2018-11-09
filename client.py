import threading
import grpc
import chatApp_pb2
import chatApp_pb2_grpc
from datetime import datetime
import time
from threading import Lock, Thread
import yaml
import sys
import base64
from cryptography.fernet import Fernet
from Crypto.Cipher import AES
# chnl = grpc.insecure_channel('localhost:3008')
# stub = chatApp_pb2_grpc.ExecuteExpressionStub(chnl)
#stub = chatApp_pb2_grpc.getMessageFromServerStreamStub(chnl)
ip = 'localhost'
port = 3008
portnumber = 0
max_call_per_30_seconds_per_user = 0
lock = Lock()
symmetric_key = ""

def padding(s):
    return s + ((16-len(s) % 16) * '~')

def yaml_load(filepath):
    with open(filepath, "r") as desc_file:
        data = yaml.load(desc_file)
        global portnumber
        global symmetric_key
        portnumber =  data.get('port')
        global max_call_per_30_seconds_per_user
        max_call_per_30_seconds_per_user = data.get('max_call_per_30_seconds_per_user')
        symmetric_key = data.get('key')
        symmetric_key = padding(symmetric_key)

yaml_load('config.yaml')

cipher = AES.new(symmetric_key)


def encrypt(plaint_text):
    global cipher
    return cipher.encrypt(padding(plaint_text))

def decrypt(ciphertext):
    global cipher
    dec = cipher.decrypt(ciphertext).decode()
    l = dec.count('~')
    return dec[:len(dec)-l]

class client:
    max_call_per_30_seconds_per_user = 0
    countOfMessages = 0
    rate_exceeded = False
    username=""
    key = ""

    def __init__(self, username, max_call, sym_key):
        channel = grpc.insecure_channel(ip+':'+str(portnumber))
        self.conn = chatApp_pb2_grpc.getMessageFromServerStreamStub(channel)
        self.username = username
        print("Channel Created")
        self.countOfMessages = 0
        self.rate_exceeded = False
        self.max_call_per_30_seconds_per_user = max_call
        #self.key = base64.urlsafe_b64encode(sym_key)
        #self.key = base64.urlsafe_b64encode(self.key)
        #print('SYm key ',self.key)
        #self.cipher_suite = Fernet(self.key)
        #self.encryption_suite = AES.new(self.key, AES.MODE_CBC, 'This is an IV456')

    # def rateLimiter(self):
    #     time.sleep(30)
    #     lock.acquire()
    #     self.countOfMessages = 0
    #     self.rate_exceeded = False
    #     lock.release()
        # if(self.countOfMessages > self.max_call_per_30_seconds_per_user):
        # #print("The accepted rate of messages is 1Message/sec, pls wait for 5sec")
        #     self.rate_exceeded = False
        #     self.countOfMessages = 0
        # else:
        #     self.rate_exceeded = True
        
        

    def listenOfflineMessages(self):
        clientDetails = chatApp_pb2.toClient(toClinetID = self.username)
        msgs = self.conn.getOfflineMessage(clientDetails)
        fromList = msgs.fromClient
        toList = msgs.toClient
        msgList = msgs.msg
        timeList = msgs.timestamp
        unique_from = uniqueUtil(fromList)
        if len(fromList):
            #print("Lenght of offline messages" + str(len(fromList)))
            print("[Spartan] You have offline messages from ",unique_from)
            #print("[Spartan] Do you wish to view them ? input yes to view, no to continue")
            viewoffline_msg = input("[Spartan] Do you wish to view them ? input yes to view, no to continue")
            if viewoffline_msg == 'Yes' or viewoffline_msg == 'yes' or viewoffline_msg == 'Y' or viewoffline_msg =='y':
                for i in range(len(fromList)):
                    #print('['+fromList[i]+'] '+self.cipher_suite.decrypt(msgList[i]).decode())   
                    print('['+fromList[i]+'] '+decrypt(msgList[i]))
        return

    def listenMessages(self):
        clientDetails = chatApp_pb2.toClient(toClinetID = self.username)
        while True:
            time.sleep(3)
            msgs = self.conn.getMessageStream(clientDetails)
            for message in msgs:
                #print('\n['+message.fromClient+'] '+self.cipher_suite.decrypt(message.msg).decode())
                print('\n['+message.fromClient+'] '+decrypt(message.msg))
           
                    

    def sendMessage(self, speakTo, message):
        msg = chatApp_pb2.sendMessage(fromClient = self.username, toClient= speakTo, msg= encrypt(message), timestamp= str(datetime.now()))
        response = self.conn.sendMessageService(encrypt(msg))
        #print(response.sentStatus)

    def authenticate(self, userName):
        authObj = chatApp_pb2.informServerOnlineStatus(clientID=userName,status="login")
        res = self.conn.notifyOnlineStatus(authObj)
        #print(res)
        return res.status
    
    def getOnlineUsers(self):
        oluser = self.conn.getOnlineUsers(chatApp_pb2.onlineUsers(clientID = ''))
        onlineUsers = '[Spartan] Online Users -:'
        for user in oluser:
            onlineUsers = onlineUsers+ user.clientID + ','
        print(onlineUsers)

class GroupChatClient:
    max_call_per_30_seconds_per_user = 0
    countOfMessages = 0
    rate_exceeded = False
    username = ""
    groupID = ""
    key = ""
    def __init__(self,username,max_call, sym_key):
        self.channel = grpc.insecure_channel(ip+':'+str(portnumber))
        self.connGroup = chatApp_pb2_grpc.groupChatServicerStub(self.channel)
        self.username = username
        print("Channel Created for group")
        self.countOfMessages = 0
        self.rate_exceeded = False
        self.max_call_per_30_seconds_per_user = max_call
        #self.key = sym_key
        #self.key = base64.urlsafe_b64encode(sym_key)
        # self.key = Fernet.generate_key()
        # self.cipher_suite = Fernet(self.key)
        #self.encryption_suite = AES.new(self.key, AES.MODE_CBC, 'This is an IV456')
        
    
    # def rateLimiter(self):
    #     time.sleep(30)
    #     lock.acquire()
    #     self.countOfMessages = 0
    #     self.rate_exceeded = False
    #     lock.release()

    def authenticate(self, username):
        authObj = chatApp_pb2.informServerOnlineStatus(clientID=username,status="login")
        res = self.connGroup.notifyOnlineStatus(authObj)
        print(res)
        self.groupID = res.status
        return res.status

    def getGroupMembers(self):
        groupList = chatApp_pb2.group_user(clientID = self.username, groupID = self.groupID)
        res = self.connGroup.getGroupMemebers(groupList)
        print(res.clientID)

    def sendMessageToGroup(self,message):
        #reqObj = chatApp_pb2.groupMessage(groupID = self.groupID, fromClient = self.username, msg = message, timestamp = str(datetime.now()) )
        #enc_msg = message.encode()
        #ciph_msg = self.cipher_suite.encrypt(enc_msg)
        enc_msg = encrypt(message)
        reqObj = chatApp_pb2.groupMessage(groupID = self.groupID, fromClient = self.username, msg = enc_msg, timestamp = str(datetime.now()) )
        res = self.connGroup.sendMessageToGroup(reqObj)
        return res

    def getOfflineMessage(self):
        req_obj = chatApp_pb2.group_user(groupID = self.groupID, clientID = self.username)
        res = self.connGroup.receiveOfflineMessageFromGroup(req_obj)
        fromList = res.fromClient
        toList = res.groupID
        msgList = res.msg
        timeList = res.timestamp
        if len(msgList)>0:
            viewOffline = input("You have offline messages, enter Y or yes to view them, n to resume chatting")
            if(viewOffline == 'Y' or viewOffline=='yes' or viewOffline == "Yes" or viewOffline=="y"):
                for i in range(len(msgList)):
                    ret_msg = msgList[i]
                    #print(ret_msg)
                    #dep_msg = self.cipher_suite.decrypt(ret_msg.encode())
                    dep_msg = decrypt(ret_msg)
                    print('['+fromList[i]+'] '+dep_msg)

    def receiveMessageStream(self):
        clientDetails = chatApp_pb2.toClient(toClinetID = self.username)
        while True:
            time.sleep(3)
            msgs = self.connGroup.receiveMessageFromGroup(clientDetails)
            for message in msgs:
                print('['+message.fromClient+'] '+decrypt(message.msg))

def uniqueUtil(x):
    x_set = set(x)
    x_list_unique = list(x_set)
    return x_list_unique

def run():
    
    
    address = sys.argv[1]
    #print(address)
    #address = input("Enter the username")
    #typeOfChat = input("Enter G for group Chat or enter to normal chat")
    typeOfChat = 'G'
    if typeOfChat == 'G' or typeOfChat == 'g':
        authGroup = GroupChatClient(address,max_call_per_30_seconds_per_user, symmetric_key)
        res = authGroup.authenticate(address)
        authGroup.getGroupMembers()
        authGroup.getOfflineMessage()
        threading.Thread(target=authGroup.receiveMessageStream, daemon=True).start()
        message = ""
        #threading.Thread(target=authGroup.rateLimiter, daemon=True).start()
        while message!="exit":
            # lock.acquire()
            # tempCount = authGroup.countOfMessages
            # lock.release()
            # if(tempCount < authGroup.max_call_per_30_seconds_per_user):
            #     message = input('['+authGroup.username+'] '+'> ')
            # else:
            #     message = input('['+authGroup.username+'] '+'> ')
            #     print('[Spartan] Maximum calls per 30 sec exceeded, please wait for 30 sec and try again')
            #     time.sleep(30)
            #     message = input('['+authGroup.username+'] '+'> ')
            # lock.acquire()
            # authGroup.countOfMessages = authGroup.countOfMessages+1
            # lock.release()
            message = input('['+authGroup.username+'] '+'> ')
            res_send = authGroup.sendMessageToGroup(message)
            if res_send.sentStatus != 'Success':
                print('It seems you have sent more than '+str(max_call_per_30_seconds_per_user)+' wait for few seconds')
                time.sleep(5)
    else:
        authRes = client(address, max_call_per_30_seconds_per_user, symmetric_key)
        res = authRes.authenticate(address)
        print(res)
        if res == "online":
            print('[Spartan] Connected to Spartan Server at port '+str(portnumber))
            #print("User logged in")
            authRes.listenOfflineMessages()
            authRes.getOnlineUsers()

            #print("Users Online ->")
            speakTo = input("Whom do you wish to speak to:")
            threading.Thread(target=authRes.listenMessages, daemon=True).start()
            print("Enter the message")

            message=""
            #countOfMessages = 0
            #threading.Thread(target=authRes.rateLimiter, daemon=True).start()
            while(message!="exit"):
                #print(authRes.username+'> ')
                # message = input('['+authRes.username+'] '+'> ')
                # if authRes.rate_exceeded == True:
                #     print('[Spartan] Maximum calls per 30 sec exceeded, please wait for 5 sec and try again')
                #     time.sleep(5)
                #     message = input('['+authRes.username+'] '+'> ')
                # countOfMessages = countOfMessages+1
                lock.acquire()
                tempCount = authRes.countOfMessages
                lock.release()
                if(tempCount < authRes.max_call_per_30_seconds_per_user):
                    message = input('['+authRes.username+'] '+'> ')
                else:
                    message = input('['+authRes.username+'] '+'> ')
                    print('[Spartan] Maximum calls per 30 sec exceeded, please wait for 30 sec and try again')
                    time.sleep(30)
                    message = input('['+authRes.username+'] '+'> ')
                lock.acquire()
                authRes.countOfMessages = authRes.countOfMessages+1
                lock.release()
                authRes.sendMessage(speakTo,message)
        else:
            print("auth issue")
    

if __name__ =='__main__':
    
    run()

# try:
#     # while(1):
#     #     x = input("Enter operand 1 for addition ")
#     #     if(x!=""):
#     #         y = input("Enter operand 2 for addition ")
#     #         expression = chatApp_pb2.Expression(operand1=float(x), operand2=float(y), operator='+')
#     #         response = stub.ExecExp(expression)
#     #         print('The result is ')
#     #         print(response.operand1)
#     #     else:
#     #         break
#     #while(1):
#     run
#     address = input("Enter the username")
        
#         # if x=="":
#         #     break
#         #authObj = chatApp_pb2.informSeverOnlineStatus(clientID=x,status="login")
#         #res = stub.notifyOnlineStatus(authObj)
    
# except KeyboardInterrupt:
#     exit()

