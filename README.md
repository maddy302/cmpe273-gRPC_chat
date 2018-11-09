Building a messenger using gRPC andpython 3

Features Implemented - 

__Level 1__ - :star:

1. 	P2P chat, the P2P section requires a user prompt to enter into it.

2. 	Group Chat, the user is logged into group chat by default. If the user is present in any of the groups (as specified in the yaml), he will be allowed to chat, else a AUTH Error will be displayed.

3. 	LRU Cahce, LRU Cahche has been maintained to be able to store the message for user when he is offline, the limit of messages that can be store can be changed in the config.yaml file.
	As soon as the user logs in, a prompt will be shown if user wishes to see the offline message, accept to view, reject to delete them and continue to the chat.
	
4. 	Ratelimiting - A rate limiting feature has been implemeted, preventing users from requesting the server very often. The limit of requests is set in the config.yaml

__Level 2__ - :star::star:

5.	End to End Encryption - Based on the key defined in the config.yaml file, the key will and message will be padded to a multiple of 16bits - a constaint by the libraries. A symmetric key encryption 
   	has been used. The message leaves encypted from the one client, to server and decrypted at the other client. Please check the server console, the encrypted data will be displayed from the  payload,
	Library used - pycrypto
	
__Level 3__ - :star::star::star:

6. 	Group chat has been implemeted, allowing multiple users to be able to chat in a group, all the user list and group list are loaded dynamicalling, changing the number of groups is possible by editing the 
	config.yaml
	
7.	All the features described above (P2P, LRU Cache, Rate Limting, End to End Ecryption have been extended to group chat)


In case of any issues, please mail the same to madhukar.battepatisrihari@sjsu.edu
