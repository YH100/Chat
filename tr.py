1 #####################################################
2 # db.py #
3 #####################################################
4
5 import os.path
6 import pickle
7 import threading
8 import time
9 class DB:
10
11 def __init__(self, path):
12 self.path=path
13 self.d = {}
14 my_file= path
15 if os.path.isfile(self.path):
16 f=open(self.path,"rb")
17 self.d=pickle.load(f)
18 f.close()
19 def read(self):
20 return self.d
21 def addentry(self,key,value):
22 self.d[key]=value
23 def removeentry(self,key):
24 self.d.pop(key,None)
25 def finish(self):
26 f=open(self.path,"wb")
27 pickle.dump(self.d,f)
28 f.close()
29
30
31 class SDB:
32 def __init__(self,path):#create the database object
33 self.sem=threading.Semaphore(10)
34 self.db=DB(path)
35 def readdb(self):#read the database
36 self.sem.acquire()
37 #while not self.sem.acquire(False):
38 #print('access not granted')
39 #time.sleep(1)
40 #print('access granted')
41 #time.sleep(3)
42 self.sem.release()
43 #print('disconnected')
44 return self.db.read()
45 def wrtdb(self,key,value):#write into the database
46 for i in range(10):
47 while not self.sem.acquire(False):
48 self.sem.acquire(False)
49 self.db.addentry(key,value)
50 self.db.finish()
51 for i in range(10):
52 self.sem.release()
53 def removekey(self,key):#remove a key from the database
54 for i in range(10):
55 while not self.sem.acquire(False):
56 self.sem.acquire(False)
57 self.db.removeentry(key)
58 self.db.finish()
59 for i in range(10):
60 self.sem.release()
61

1 #####################################################
2 # server.py #
3 #####################################################
4
5 import socket
6 import select
7 import time
8 import db
9 import os
10 import glob
11 import threading
12 import shutil
13 import hashlib
14
15 from Crypto.PublicKey import RSA
16 from Crypto import Random
17 from Crypto.Cipher import PKCS1_OAEP
18 from cryptography.fernet import Fernet
19
20 server_socket=socket.socket()
21 server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
22 server_socket.bind(('0.0.0.0',23))
23 server_socket.listen(5)
24 open_client_sockets=[]
25 waiting_messages=[]
26 messages_to_send=[]
27
28
29 #get the location of the server file in the computer
30 dirname, filename = os.path.split(os.path.abspath(__file__))
31
32 #create/read the server databases
33 clients={}
34 clientspath=os.path.join(dirname,'clients.txt')
35 clientnames=db.SDB(clientspath)
36 current_clients=clientnames.readdb()
37 clientsdatapath=os.path.join(dirname,'clients_data.txt')
38 clientdata=db.SDB(clientsdatapath)
39 client_data=clientdata.readdb()
40 chatspath=os.path.join(dirname,'chats.txt')
41 chats=db.SDB(chatspath)
42 print (clientnames.readdb())
43
44 file_sem=threading.Semaphore()
45
46 keys={}
47
48
49 #create the assymetric key(for the key exchange)
50 random_generator = Random.new().read
51 key = RSA.generate(1024, random_generator)
52 public_key = key.publickey()
53 server_cipher = PKCS1_OAEP.new(key)
54
55 #maximum size(in bytes) that a file can have and be sent in one piece, and the size
of each piece
56 FILEMAX=1048576 #1MB = 1024*1024 B
57 CHUNK_SIZE=1048576 #1MB = 1024*1024 B
58
59 #make sure there is a folder for the uploaded files
60 if not os.path.exists(os.path.join(dirname,'uploadedfiles')):
61 os.makedirs(os.path.join(dirname,'uploadedfiles'))
62
63 #receive a message and decrypt
64 def enc_recv(sock):
65 rlist,wlist,xlist=select.select([sock],[],[],0.1)
66 try:
67 data=sock.recv(1024)
68 rlist,wlist,xlist=select.select([sock],[],[],0.1)
69 while sock in rlist: #continues receiving until the whole message has been

received

70 data+=sock.recv(1024)

71 rlist,wlist,xlist=select.select([sock],[],[],0.1)
72 sock.send(b'datadone')
73 key=keys[sock]
74 cipher=Fernet(key)
75 data=cipher.decrypt(data)
76 return data
77 except Exception:
78 pass
79
80 #encrypt a message and send
81 def enc_send(sock,data):
82 key=keys[sock]
83 cipher=Fernet(key)
84 data=cipher.encrypt(data)
85 sendmes(sock,data)
86
87 #encode a string(if needed)
88 def stren(string):
89 try:
90 string=string.encode()
91 except Exception:
92 pass
93 return string
94
95 #decode a string(if needed)
96 def strde(string):
97 try:
98 string=string.decode()
99 except Exception:
100 pass
101
102 #check if a client exists(is registered)
103 def clientexist(client_number):
104 clients=clientnames.readdb()
105 for i in clients.keys():
106 if clients[i][2]==client_number:
107 return True
108 return False
109
110 #send a message
111 def sendmes(cli_socket,mes):
112 rlist,wlist,xlist=select.select([cli_socket],[],[],0.1) #waits for the socket to

be free

113 while len(rlist)>0:
114 rlist,wlist,xlist=select.select([cli_socket],[],[],0.1)
115 open_client_sockets.remove(cli_socket)
116 cli_socket.send(mes)
117 cli_socket.recv(1024)
118 open_client_sockets.append(cli_socket)
119
120 #create a file in the folder specified for the chat it was sent in
121 def uploadfile(chatid,uploader,filename,filedata):
122 if not os.path.exists(os.path.join(dirname,'uploadedfiles',chatid)):
123 os.makedirs(os.path.join(dirname,'uploadedfiles',chatid))
124 chatfiles=db.SDB(os.path.join(dirname,'uploadedfiles',chatid,'__files.txt'))
125 n=1
126 fname=filename
127 while os.path.exists(os.path.join(dirname,'uploadedfiles',chatid,filename)):
#changes the name of the file(add a number) if a file with the given name
already exists

128 filename_parts=fname.split('.')
129 filename=''
130 for i in filename_parts[:-1]:
131 filename=filename+i+'.'
132 filename=filename[:-1]
133 filename=filename+'('+str(n)+').'+filename_parts[-1]
134 n+=1
135 newfile=open(os.path.join(dirname,'uploadedfiles',chatid,filename),"wb")
136 newfile.write(filedata)
137 newfile.close()
138 chatfiles.wrtdb(filename,[time.time(),uploader])
139 print (b'file upload finished'.decode())

140
141 #check the files every m minutes
142 def tcheckfiles(m):
143 t=60*m #60 seconds*m=m minutes
144 while True:
145 print(b'checking files'.decode())
146 check_files()
147 time.sleep(t)
148
149 #check if any files are older than 24 hours
150 def check_files():
151 chat_directories=os.listdir(os.path.join(dirname,'uploadedfiles'))
152 file_sem.acquire()
153 for i in chat_directories: #checks all the chat folders
154 if os.path.exists(os.path.join(dirname,'uploadedfiles',i,'__files.txt')):
155 chatfiles=db.SDB(os.path.join(dirname,'uploadedfiles',i,'__files.txt'))
156 chatfiles2=chatfiles.readdb()
157 if len(chatfiles2.keys())>0:
158 k=list(chatfiles2.keys())
159 for j in k:
160 upload_time=chatfiles2[j][0]
161 if check24h(upload_time): #checks how long ago the file was

uploaded

162 if os.path.exists(os.path.join(dirname,'uploadedfiles',i,j)):
163 print(os.path.join(dirname,'uploadedfiles',i,j),end=' ')
164 print(b'was older than 24 hours'.decode())
165 os.remove(os.path.join(dirname,'uploadedfiles',i,j))
166 chatfiles.removekey(j)
167
168 chats2=chats.readdb()
169 chat_participants=chats2[i][2].split(',')
170 sendchatfilelist(i,chat_participants)
171 else:
172

shutil.rmtree(os.path.join(dirname,'uploadedfiles',i),ignore_errors=Tr
ue)
173 file_sem.release()
174
175 #get the names of all the files uploaded to a chat
176 def getchatfilesnames(chatid):
177 path=os.path.join(dirname,'uploadedfiles',chatid,'*.*') #checks all the files in

the folder

178 files=glob.glob(path)
179 filenames=''
180 for i in files:
181 if i.split('\\')[-1]=='__files.txt':
182 files.remove(i)
183 for i in files:
184 filenames+=i.split('\\')[-1]+','
185 return filenames[:-1]
186
187 #send the list of files uploaded to a chat
188 def sendchatfilelist(chatid,cur_client):
189 files=getchatfilesnames(chatid)
190 message='8/r/n'+chatid+'/r/n'+files+'/r/n//mesend'
191 waiting_messages.append([message,cur_client])
192
193 #send a file to a client
194 def tsendfile(sock,chatid,filename,cli):
195 adress=sock.getpeername()
196 (ip,port)=adress
197 print(b'sending '.decode(),end='')
198 print(filename,end=' ')
199 print(b'to: '.decode(),end='')
200 print(cli)
201 path=os.path.join(dirname,'uploadedfiles',chatid,filename)
202 file_data=getfile(path)
203 file_size=len(file_data)
204 s=socket.socket()
205 s.connect((ip,24)) #connect to the client
206 s.recv(1024)
207 if file_data==b'filenotfound': #the wanted file was not found

208 s.send(b'nofile')
209 s.recv(1024)
210 print(b'file not found'.decode())
211 else:
212 if file_size <= FILEMAX: #the file is small enough to be sent in one

chunk(smaller than 1MB)
213 s.send(b'small')
214 s.recv(1024)
215 key=keys[sock]
216 cipher=Fernet(key)
217 data=cipher.encrypt(file_data)
218 s.send(data)
219 s.recv(1024)
220 s.send(b'done')
221 else: #the file is large and need to be sent in multiple chunks(bigger than

1MB)

222 key=keys[sock]
223 cipher=Fernet(key)
224 s.send(b'big')
225 s.recv(1024)
226 s.send((str(file_size)).encode('utf-8'))
227 s.recv(1024)
228 piece=file_data[:CHUNK_SIZE]
229 enc_piece=cipher.encrypt(piece)
230 s.send(enc_piece)
231 s.recv(1024)
232 for i in range(CHUNK_SIZE,file_size,CHUNK_SIZE): #send each chunk

seperately

233 s.send(b'pieces left')
234 piece=file_data[i:i+CHUNK_SIZE]
235 enc_piece=cipher.encrypt(piece)
236 s.send(enc_piece)
237 s.recv(1024)
238 print(b'file sent'.decode())
239 s.close()
240
241
242 #read the data of a file
243 def getfile(path):
244 file_sem.acquire()
245 if os.path.exists(path): #if the file exists read the file
246 f=open(path,"rb")
247 l=f.read()
248 f.close()
249 print(b'file size: '.decode(),end='')
250 print((len(l)/1024),end=' ')
251 print(b'KB'.decode())
252 else:
253 l=b'filenotfound' #if the file doesn't exist, let the client know
254 file_sem.release()
255 return l
256
257 #remove a client from a chat
258 def remove_client(clientid,chatid,data):
259 client_data=clientdata.readdb()
260 if chatid in client_data[clientid][1]:
261 client_data[clientid][1].remove(chatid)
262 clientdata.wrtdb(clientid,client_data[clientid])
263 chats2=chats.readdb()
264 participants=chats2[chatid][2]
265 split_par=participants.split(',')
266 if clientid in split_par:
267 split_par.remove(clientid)
268 participants=''
269 for i in split_par:
270 participants=participants+i+','
271 participants=participants[:-1]
272 chats2[chatid][2]=participants
273 chats2[chatid][4]+=data
274 chats.wrtdb(chatid,chats2[chatid])
275
276 #check if 24 hours have past since a time

277 def check24h(timetocheck):
278 cur_time=time.time()
279 timetocheck=float(timetocheck)
280 time_diff=cur_time-timetocheck
281 if int(time.strftime('%d',time.gmtime(time_diff)))-1 >0:
282 #print('file is older than 24h')
283 return True
284 return False
285
286 #receive a file from a client
287 #this function is called after the server has received a 'upload' request from the
client
288 #the server responds by TCP connection to the client and upload begins
289 def trecvfile(sock,chatid,uploader,filename):
290 adress=sock.getpeername()
291 (ip,port)=adress
292 print(b'receiving '.decode(),end='')
293 print(filename,end=' ')
294 print(b'from: '.decode(),end='')
295 print(uploader)
296 s=socket.socket()
297 s.connect((ip,24)) #conncect to the client
298 rlist,wlist,xlist=select.select([s],[],[],10)
299 filedata=b''
300 down_type=s.recv(1024)
301 if down_type==b'small': #file is smaller than one chunk (1MB)
302 s.send(b'ready')
303 filedata=s.recv(1024)
304 rlist,wlist,xlist=select.select([s],[],[],0.1)
305 while s in rlist:
306 filedata+=s.recv(1024)
307 rlist,wlist,xlist=select.select([s],[],[],0.1)
308 s.send(b'done')
309 s.close()
310 key=keys[sock]
311 cipher=Fernet(key)
312 data=cipher.decrypt(filedata)
313 elif down_type==b'big': #file will be uploaded in multiple chunks
314 s.send(b'ready')
315 key=keys[sock]
316 filedata=piecerec(s,key)
317 s.send(b'piece recvd')
318 filedone=s.recv(1024)
319 while filedone == b'pieces left': #receive each chunk seperatley
320 filedata+=piecerec(s,key)
321 s.send(b'piece recvd')
322 filedone=s.recv(1024)
323 uploadfile(chatid,uploader,filename,filedata)
324 chats2=chats.readdb()
325 chat_participants=chats2[chatid][2].split(',')
326 sendchatfilelist(chatid,chat_participants)
327
328 #receive a piece of a file from a client
329 def piecerec(sock,key):
330 enc_piece=sock.recv(1024)
331 rlist,wlist,xlist=select.select([sock],[],[],0.1)
332 while len(rlist)>0:
333 while len(rlist)>0:
334 enc_piece+=sock.recv(1024)
335 rlist,wlist,xlist=select.select([sock],[],[],0.01)
336 rlist,wlist,xlist=select.select([sock],[],[],3)
337 cipher=Fernet(key)
338 rlist,wlist,xlist=select.select([sock],[],[],1)
339 piece=cipher.decrypt(enc_piece)
340 return piece
341
342 #send a client their chats
343 def sendclientchats(client_number):
344 chats2=chats.readdb()
345 client_data=clientdata.readdb()
346 chatsid=client_data[client_number][1]
347 for i in chatsid:

348 message='3/r/n'+i+'/r/n'+chats2[i][1]+'/r/n'+chats2[i][2]+'/r/n//mesend'
349 chat_participants=chats2[i][2].split(',')
350 waiting_messages.append([message,[client_number]])
351
352 #send a client their contacts
353 def sendclientcontacts(client_number):
354 client_data=clientdata.readdb()
355 client_contacts=client_data[client_number][0]
356 for i in client_contacts.keys():
357 contact_number=i
358 contact_name=client_contacts[i]
359 message='7/r/n'+contact_name+'/r/n'+contact_number+'/r/n//mesend'
360 waiting_messages.append([message,[client_number]])
361
362 #append the waiting messages with the destination port instead of the number
363 def append_waiting_messages(waiting_messages):
364 for i in waiting_messages:
365 for j in i[1]:
366 if j in clients.keys():
367 messages_to_send.append(([clients[j]],i[0]))
368 if len(i[1]) == 1:
369 waiting_messages.remove(i)
370 else:
371 i[1].remove(j)
372
373 #send the messages waiting to be sent
374 def send_waiting_messages(wlist):
375 for message in messages_to_send:
376 (client_sockets,data)=message #deconstruct the message into the data and the

socket

377 for current_socket in client_sockets:
378 if current_socket in wlist:
379 try:
380 data=data.encode()
381 except Exception:
382 pass
383 if data.split(b'/r/n')[0]=='5'.encode():
384

messages=data.split(b'//chatstart')[1].split(b'//chatend')[0].spli
t(b'//mesend')[:-1]

385 conv=data.split(b'//chatstart')[1].split(b'//chatend')[0]
386 enc_send(current_socket,b'5/r/n//chatstart')
387 mes=b''
388 for i in messages:
389 mess=i+b'//mesend'
390 mes+=mess
391 enc_send(current_socket,conv)
392 else:
393 enc_send(current_socket,data)
394 client_sockets.remove(current_socket)
395 if len(client_sockets)==0:
396 messages_to_send.remove(message)
397
398 threading.Thread(target=tcheckfiles,args=(10,)).start() #check the files every 10
minutes
399
400 #main part of the server
401 while True:
402

rlist,wlist,xlist=select.select([server_socket]+open_client_sockets,open_client_so
ckets,[],0.1)#check which clients are trying to send messages

403 for current_socket in rlist:
404 if current_socket is server_socket:
405 #establish a connection with the client
406 (new_socket,address)=server_socket.accept()
407 open_client_sockets.append(new_socket)
408 recvd=new_socket.recv(1024)
409
410 try:
411 recvd=recvd.encode()
412 except Exception:
413 pass

414
415 #start the key exchange with the client
416 (ip,port)=address
417 print(b'exchanging keys with client at ip: '.decode(),end='')
418 print(ip)
419 if recvd == b'GET_PUBLIC_KEY':
420 new_socket.send(public_key.exportKey())
421 new_key=new_socket.recv(1024)
422 new_key=server_cipher.decrypt(new_key)
423 keys[new_socket]=new_key
424 else:
425

rlist,wlist,xlist=select.select([current_socket],open_client_sockets,[],0.
1)

426 if current_socket in rlist:
427 data=enc_recv(current_socket)#receive a message from a client
428 dataen=data
429 #create an encoded and a decoded version of the message
430 try:
431 dataen=data.encode()
432 except Exception:
433 pass
434 try:
435 data=data.decode()
436 except Exception:
437 pass
438 if type(data)==type(''):
439 data2=data.split('/r/n')
440 if data2[0]=='1':#handle a type 1 message(login)
441 returnans='notregistered'
442 cid=data2[1]
443 md5id=hashlib.sha224(cid.encode()).hexdigest() #hash the

clients login info

444 for i in current_clients.keys():
445 if i == md5id:
446 cur_client_number=current_clients[i][2]
447 returnans=cur_client_number+','+current_clients[i][1]
448 clients[cur_client_number]=current_socket
449 print(cur_client_number,end='')
450 print(b' signed in'.decode())
451 enc_send(current_socket,returnans.encode())
452 if returnans!='notregistered':
453 enc_recv(current_socket)
454 clients[cur_client_number]=current_socket
455 sendclientcontacts(cur_client_number)
456 sendclientchats(cur_client_number)
457 elif data2[0]=='2':#handle a type 2 message(register)
458 cid=data2[1]
459 md5id=hashlib.sha224(cid.encode()).hexdigest()
460 registered=False
461 for i in current_clients.keys():
462 if i == md5id:
463 registered=True
464 if registered == False:
465 client_number=str(int(float(str(time.time()))*100))

#create a client id for the new client
466 clients[client_number]=current_socket
467 username=data2[2]
468 name=data2[3]
469 client_chats=[]
470 client_contacts={}
471 clientnames.wrtdb(md5id,[username,name,client_number])

#add the new client to the client database
472 current_clients=clientnames.readdb()
473 retans=client_number+','+name
474 enc_send(current_socket,retans.encode())
475 clients[client_number]=current_socket
476

clientdata.wrtdb(client_number,[client_contacts,client_cha
ts])

477 print(client_number,end=' ')
478 print(b'registered'.decode())

479 else:
480 enc_send(current_socket,b'userregistered') #let the
client know the information he enterd is already used
and therefore invalid

481 elif data2[0]=='0':#handle a type 0 message(logout)
482 enc_send(current_socket,b'logout')
483 open_client_sockets.remove(current_socket) #remove the

client's socket from the active client list

484 keys.pop(current_socket,None)
485 current_socket.close()
486 elif data2[0]=='3':#handle a type 3 message(create chat)
487 chatid=str(int(float(str(time.time())[2:])*100)) #create a

chat id
488 conversation=''
489 chatday = time.strftime("%a, %d/%m/%y",time.gmtime())
490

chats.wrtdb(chatid,[data2[1],data2[2],data2[3],chatday,convers
ation]) #add the chat to the chat database

491

message='3/r/n'+chatid+'/r/n'+data2[2]+'/r/n'+data2[3]+'/r/n//
mesend'

492 chat_participants=data2[3].split(',')
493 for i in chat_participants:
494 client_data=clientdata.readdb()
495 client_data[i][1].append(chatid)
496 clientdata.wrtdb(i,client_data[i])
497 waiting_messages.append([message,chat_participants]) #send
all the participants a message about the creation of the chat

498

message='4/r/n'+chatid+'/r/n'+'SERVER'+'/r/n'+'CREATEDATE'+'/r
/n'+chatday+'/r/n//mesend'
499 chats2=chats.readdb()
500 chats2[chatid][4]+=message
501 chats.wrtdb(chatid,chats2[chatid])
502

message='4/r/n'+chatid+'/r/n'+'SERVER'+'/r/n'+'/r/n'+'/r/n//me
send'

503 chats2[chatid][4]+=message
504 chats.wrtdb(chatid,chats2[chatid])
505 elif data2[0]=='4':#handle a type 4 message(message in a chat)
506 chat=data2[1]
507 chats2=chats.readdb()
508 cur_date=time.strftime("%a, %d/%m/%y",time.gmtime())
509 if cur_date != chats2[chat][3]:
510 chat_participants=chats2[chat][2].split(',')
511

message='4/r/n'+chat+'/r/n'+'SERVER'+'/r/n'+'DATE'+'/r/n'+
cur_date+'/r/n//mesend'
512 chats2[chat][4]+=message
513 chats2[chat][3]=cur_date
514 chats.wrtdb(chat,chats2[chat])
515 waiting_messages.append([message,chat_participants])
516 chat_participants=chats2[chat][2].split(',')
517 chats2[chat][4]+=data #add the message to the conversation
518 chats.wrtdb(chat,chats2[chat])
519 waiting_messages.append([data,chat_participants])
520 elif data2[0]=='5':#handle a type 5 message(chat conversation

request)

521 chat=data2[1]
522 chats2=chats.readdb()
523 conversation=chats2[chat][4]
524 message='5/r/n//chatstart'+conversation+'//chatend'
525 waiting_messages.append(([message,[data2[2]]]))
526 sendchatfilelist(chat,[data2[2]])
527 elif data2[0]=='6':#handle a type 6 message(add participants to

a chat)

528 chatid=data2[1]
529 par_to_add=data2[2]
530 adder=data2[3]
531 chats2=chats.readdb()
532 chats2[chatid][2]=chats2[chatid][2]+','+par_to_add #add the
participants to the chat participants in the database

533 chats2[chatid][4]+=data
534 chats.wrtdb(chatid,chats2[chatid])
535 client_data=clientdata.readdb()
536 for i in par_to_add.split(','):
537 client_data[i][1].append(chatid)
538 clientdata.wrtdb(i,client_data[i])
539

waiting_messages.append(['3/r/n'+chatid+'/r/n'+chats2[chat
id][1]+'/r/n'+chats2[chatid][2]+'/r/n//mesend',par_to_add.
split(',')])

540 waiting_messages.append([data,chats2[chatid][2].split(',')])
541 elif data2[0]=='7':#handle a type 7 message(client adding a

contact)

542 client_data=clientdata.readdb()
543 client_number=data2[1]
544 contact_name=data2[2]
545 contact_number=data2[3]
546 if clientexist(contact_number): #add the contact to the

client's contacts

547 enc_send(current_socket,stren(client_number))
548 client_data[client_number][0][contact_number]=contact_name
549 clientdata.wrtdb(client_number,client_data[client_number])
550 else:
551 enc_send(current_socket,b'noclient') #let the client

know the number he entered doesn't exist

552 elif data2[0]=='8':#handle a type 8 message(chat file list

request)

553 chat=data2[1]
554 client_number=data2[2]
555 sendchatfilelist(chat,[client_number])
556 elif data2[0]=='9':#handle a type 9 message(file upload reqest)
557 uploader=data2[1]
558 chatid=data2[2]
559 filename=data2[3]
560

threading.Thread(target=trecvfile,args=(current_socket,chatid,
uploader,filename,)).start()

561 elif data2[0]=='10':#handle a type 10 message(file download

request)

562 cur_client=data2[1]
563 chatid=data2[2]
564 filename=data2[3]
565

threading.Thread(target=tsendfile,args=(current_socket,chatid,
filename,cur_client,)).start()

566 elif data2[0]=='11':#handle a type 11 message(client leaving a

chat)

567 clientid=data2[1]
568 chatid=data2[2]
569 remove_client(clientid,chatid,data)
570 chats2=chats.readdb()
571 chat_participants=chats2[chatid][2].split(',')
572 waiting_messages.append([data,chat_participants])
573 #handle and send the messages waiting to be sent
574 if len(open_client_sockets)>0:
575

rlist,wlist,xlist=select.select(open_client_sockets,open_client_sockets,[],0.1
)

576 append_waiting_messages(waiting_messages)
577 send_waiting_messages(wlist)
578

1 #####################################################
2 # client.py #
3 #####################################################
4
5 import socket
6 import select
7 import threading
8 import time
9 import md5
10 import db
11 import os
12 import Queue
13 import shutil
14 from cryptography.fernet import Fernet
15 from Crypto.Cipher import PKCS1_OAEP
16 from Crypto.PublicKey import RSA
17
18 server_adress=('192.168.1.13',23)
19
20 key=Fernet.generate_key()
21 client_cipher=Fernet(key)
22
23
24 CHUNK_SIZE=1048576
25 FILEMAX=1048576
26
27 #receive a message and decrypt
28 def enc_recv():
29 socksem.acquire()
30 data=my_socket.recv(1024)
31 rlist,wlist,xlist=select.select([my_socket],[],[],0.1)
32 time.sleep(0.1)
33 rlist,wlist,xlist=select.select([my_socket],[],[],0.1)
34 if my_socket in rlist: #continues receiving until the whole message was received
35 while my_socket in rlist:
36 data+=my_socket.recv(1024)
37 rlist,wlist,xlist=select.select([my_socket],[],[],0.1)
38 my_socket.send('datadone')
39 socksem.release()
40 data=client_cipher.decrypt(data)
41 return data
42
43 #encrypt a message and send
44 def enc_send(data):
45 try:
46 data=data.encode()
47 except Exception:
48 pass
49 data=client_cipher.encrypt(data)
50 socksem.acquire()
51 my_socket.send(data)
52 my_socket.recv(1024)
53 socksem.release()
54
55 #establish a connection with the server
56 my_socket=socket.socket()
57 my_socket.connect(server_adress)
58 date=time.strftime("%a, %d %b %Y",time.gmtime())
59
60
61 #start the key exchange
62 print(b'exchanging keys'.decode())
63 my_socket.send('GET_PUBLIC_KEY')
64 public_key=my_socket.recv(1024)
65 public_key=RSA.importKey(public_key)
66
67 cipher = PKCS1_OAEP.new(public_key)
68 enc_key=cipher.encrypt(key)
69
70 my_socket.send(enc_key)
71
72 #get the location of the client file in the computer

73 dirname, filename = os.path.split(os.path.abspath(__file__))
74
75
76 #erase existing databases if last client didn't log out properly
77 chatspath=os.path.join(dirname,'mychats.txt')
78
79 if os.path.exists(chatspath):
80 os.remove(chatspath)
81
82 chats=db.SDB(chatspath)
83 chats2=chats.readdb()
84
85 contactspath=os.path.join(dirname,'contacts.txt')
86
87 if os.path.exists(contactspath):
88 os.remove(contactspath)
89
90 contacts=db.SDB(contactspath)
91 contacts2=contacts.readdb()
92
93 if os.path.isdir(os.path.join(dirname,'downloadedfiles')):
94 shutil.rmtree(os.path.join(dirname,'downloadedfiles'), ignore_errors=True)
95
96 my_number='0'
97 socksem=threading.Semaphore()
98 file_sem=threading.Semaphore()
99 up_sem=threading.Semaphore()
100
101 #leave a group
102 def leavegroup(my_num,groupid):
103 message='11/r/n'+my_num+'/r/n'+groupid+'/r/n//mesend'
104 enc_send(message)
105 chats.removekey(groupid)
106
107 #download a file from the server
108 def downloadfile(my_num,chatid,filename):
109 file_sem.acquire()
110 ## print(b'downloading '.decode(),end='')
111 ## print(filename)
112 print('downloading '+filename)
113 message='10/r/n'+my_num+'/r/n'+chatid+'/r/n'+filename+'/r/n//mesend'
114 enc_send(message)
115 file_sock=socket.socket()
116 file_sock.bind(('0.0.0.0',24))
117 file_sock.listen(1) #wait for the server to conect in order to download the file
118 (ser_file_sock,adress)=file_sock.accept()
119 file_data=b''
120 ser_file_sock.send('start')
121 down_type=ser_file_sock.recv(1024)
122 ser_file_sock.send(b'ok')
123 if down_type==b'nofile': #if the file was not found cancel the download
124 print(' file not found')
125 elif down_type == b'small': #if the file is smaller than 1MB it will be received

in one chunk

126 file_data=ser_file_sock.recv(1024)
127 rlist,wlist,xlist=select.select([ser_file_sock],[],[],0.1)
128 while ser_file_sock in rlist:
129 file_data+=ser_file_sock.recv(1024)
130 rlist,wlist,xlist=select.select([ser_file_sock],[],[],0.1)
131 try:
132 filedata=client_cipher.decrypt(file_data)
133 except Exception:
134 file_sem.release()
135 ser_file_sock.send(b'finished')
136 ser_file_sock.recv(1024)
137 ser_file_sock.close()
138 print('download failed')
139 elif down_type==b'big': #if the file is bigger than 1MB it will be received in

multiple chunks

140 file_size=ser_file_sock.recv(1024)
141 ser_file_sock.send(b'ready')
142 try: #in case of a failure in the download(decryption failure,

disconnection,..) the client will be able to download files again

143 file_data=piecerecv(ser_file_sock)
144 ser_file_sock.send(b'piece recvd')
145 filedone=ser_file_sock.recv(1024)
146 except Exception:
147 file_sem.release()
148 ser_file_sock.send(b'finished')
149 ser_file_sock.recv(1024)
150 ser_file_sock.close()
151 print('download failed')
152 while filedone == b'pieces left': #receive each chunk seperatley
153 prog=((float(len(file_data))/float(file_size))*100)
154 print(prog)
155 try: #in case of a failure in the download(decryption failure,
disconnection,..) the client will be able to download files again

156 file_data+=piecerecv(ser_file_sock)
157 ser_file_sock.send(b'piece recvd')
158 filedone=ser_file_sock.recv(1024)
159 except Exception:
160 file_sem.release()
161 ser_file_sock.send(b'finished')
162 ser_file_sock.recv(1024)
163 ser_file_sock.close()
164 print('download failed')
165 createfile(chatid,filename,file_data,my_num)
166 ser_file_sock.send(b'finished')
167 ser_file_sock.recv(1024)
168 ser_file_sock.close()
169 file_sock.close()
170 print(b'download finished'.decode())
171 file_sem.release()
172
173 #receive a chunk of the file
174 def piecerecv(ser_file_sock):
175 enc_piece=ser_file_sock.recv(1024)
176 rlist,wlist,xlist=select.select([ser_file_sock],[],[],0.1)
177 while len(rlist)>0:
178 while len(rlist)>0:
179 enc_piece+=ser_file_sock.recv(1024)
180 rlist,wlist,xlist=select.select([ser_file_sock],[],[],0.1)
181 rlist,wlist,xlist=select.select([ser_file_sock],[],[],1)
182 piece=client_cipher.decrypt(enc_piece)
183 return piece
184
185 def tupload(path,chatid,my_number):
186 file_name=path.split('\\')[-1]
187 up_sem.acquire()
188 ## print(b'uploading '.decode(),end='')
189 ## print(file_name)
190 print('uploading '+file_name)
191
192 message=b'9/r/n'+my_number+b'/r/n'+chatid+b'/r/n'+file_name+b'/r/n//mesend'
193
194 try:
195 my_number=my_number.encode('utf-8')
196 except Exception:
197 pass
198
199 try:
200 chatid=chatid.encode('utf-8')
201 except Exception:
202 pass
203
204
205 try:
206 message=message.encode('utf-8')
207 except Exception:
208 pass
209
210 enc_send(message)
211 file_data=getfile(path)
212 file_size = len(file_data)

213 up_sock=socket.socket()
214 up_sock.bind(('0.0.0.0',24))
215 up_sock.listen(1)
216 (ser_up_sock,adress)=up_sock.accept()
217 rlist,wlist,xlist=select.select([],[ser_up_sock],[])
218 if file_size <= FILEMAX:
219 ser_up_sock.send(b'small')
220 ser_up_sock.recv(1024)
221 try: #in case of a failure in the upload(decryption failure,
disconnection,..) the client will be able to upload files again

222 enc_file=client_cipher.encrypt(file_data)
223 ser_up_sock.send(enc_file)
224 ser_up_sock.recv(1024)
225 except Exception:
226 ser_up_sock.close()
227 up_sock.close()
228 up_sem.release()
229 print('file upload failed')
230 else:
231 ser_up_sock.send(b'big')
232 ser_up_sock.recv(1024)
233 piece=file_data[:CHUNK_SIZE]
234 try: #in case of a failure in the upload(decryption failure,
disconnection,..) the client will be able to upload files again

235 enc_piece=client_cipher.encrypt(piece)
236 ser_up_sock.send(enc_piece)
237 ser_up_sock.recv(1024)
238 for i in range(CHUNK_SIZE,file_size,CHUNK_SIZE):
239 prog=((float(i)/float(len(file_data)))*100)
240 print(prog)
241 ser_up_sock.send(b'pieces left')
242 piece=file_data[i:i+CHUNK_SIZE]
243 enc_piece=client_cipher.encrypt(piece)
244 ser_up_sock.send(enc_piece)
245 ser_up_sock.recv(1024)
246 ser_up_sock.send(b'done')
247 except Exception:
248 ser_up_sock.close()
249 up_sock.close()
250 up_sem.release()
251 print('file upload failed')
252 ser_up_sock.close()
253 up_sock.close()
254 up_sem.release()
255 print(b'upload finished'.decode())
256
257
258 #check if a file has already been downloaded
259 def checkifexists(chatid,filename):
260 return

os.path.exists(os.path.join(dirname,'downloadedfiles',findchatbyid(chatid)+'('+cha
tid+')',filename))

261
262 #read the data of a file
263 def getfile(path):
264 f=open(path,"rb")
265 l=f.read()
266 f.close()
267 return l
268
269 #save a file downloaded from the server
270 def createfile(chatid,filename,filedata,mynum):
271 if not

os.path.exists(os.path.join(dirname,'downloadedfiles',findchatbyid(chatid)+'('+cha
tid+')')):

272

os.makedirs(os.path.join(dirname,'downloadedfiles',findchatbyid(chatid)+'('+ch
atid+')'))

273 n=1
274 fname=filename
275 while

os.path.exists(os.path.join(dirname,'downloadedfiles',findchatbyid(chatid)+'('+cha

tid+')',filename)): #change the name of a file(adds a number) if a file with the
given name already exists

276 filename_parts=fname.split('.')
277 filename=filename_parts[0]+'('+str(n)+').'+filename_parts[1]
278 n+=1
279

newfile=open(os.path.join(dirname,'downloadedfiles',findchatbyid(chatid)+'('+chati
d+')',filename),"wb")
280 newfile.write(filedata)
281 newfile.close()
282 message='8/r/n'+chatid+'/r/n'+mynum+'/r/n//mesend'
283 enc_send(message)
284 ## print(filename,end=' ')
285 ## print(b'saved'.decode())
286 print(filename+' saved')
287
288 #let the server know you want to log out and delete data(contacts,chats,files
downloaded
289 def logout():
290 if os.path.exists(chatspath):
291 os.remove(chatspath)
292 if os.path.exists(contactspath):
293 os.remove(contactspath)
294 if os.path.isdir(os.path.join(dirname,'downloadedfiles')):
295 shutil.rmtree(os.path.join(dirname,'downloadedfiles'), ignore_errors=True)
296 enc_send('0/r/n')
297 print(b'loging out'.decode())
298 enc_recv()
299 my_socket.close()
300
301
302 #ask the server to check if the information is correct in order to log in
303 def checkregistered(usrnamepassward):
304 message='1/r/n'+usrnamepassward+'/r/n//mesend'
305 enc_send(message)
306 ans=enc_recv()
307 if ans == 'notregistered':
308 return False #let the gui know the login failed
309 my_number=ans.split(',')[0]
310 enc_send('signin')
311 print(b'signin successful'.decode())
312 return ans #give the gui the client number and name
313
314 #ask the server to register as a new client
315 def register(usernamepassward,username,name):
316 message='2/r/n'+usernamepassward+'/r/n'+username+'/r/n'+name+'/r/n//mesend'
317 enc_send(message)
318 ans=enc_recv()
319 if ans == b'userregistered':
320 return False #let the gui know the registration failed
321 my_number=ans.split(',')[0]
322 print(b'register successful'.decode())
323 return ans #give the gui the client number and name
324
325 #add a contact
326 def addcontact(mynum,name,number):
327 message='7/r/n'+mynum+'/r/n'+name+'/r/n'+number+'/r/n//mesend'
328 enc_send(message)
329 conans=enc_recv()
330 if conans=='noclient':
331 return False #let the gui know the client number given doesn't exist
332 else:
333 writecontact(number,name) #add the contact to the database
334 ## print(name,end=' ')
335 ## print(b'added as a contact'.decode())
336 print(name+' added as a contact')
337 return True #let the gui know the contact has been added successfully
338
339 #write a contact's information in the database
340 def writecontact(number,name):
341 contacts2=contacts.readdb()
342 if number not in contacts2.keys():

343 contacts.wrtdb(number,name)
344 contacts2=contacts.readdb()
345
346 #return the user's contacts
347 def getcontactlist():
348 contacts2=contacts.readdb()
349 return contacts2
350
351
352 #return the user's chats
353 def getchatlist():
354 chats2=chats.readdb()
355 return chats2
356
357 #create a chat and tell the server
358 def createchat(chatcreator,chatname,participants):
359 participantnumbers=''
360 for i in participants:
361 participantnumbers=participantnumbers+i+','
362 participantnumbers=participantnumbers[:-1]
363

message='3/r/n'+chatcreator+'/r/n'+chatname+'/r/n'+participantnumbers+'/r/n//mesen
d'

364 enc_send(message)
365
366 #send a message to a group
367 def snd(chatid,sender,mess):
368 if chatid in getchatlist().keys():
369

message='4/r/n'+chatid+'/r/n'+sender+'/r/n'+time.strftime("%H:%M:%S",time.gmti
me())+'/r/n'+mess+'/r/n//mesend'

370 enc_send(message)
371
372 #check for messages waiting to be received(and receive if needed)
373 def recvmes(mynum):
374 rlist,wlist,xlist=select.select([my_socket],[],[],0.1)
375 for current_socket in rlist:
376 data=enc_recv()
377 data2=data.split('/r/n')
378 if data2[0]=='3':#message indicating a creation of a group
379 chatid=data2[1]
380 chatname=data2[2]
381 participants=data2[3]
382 unread='0'
383 chats.wrtdb(chatid,[chatname,participants,unread]) #add the chat to the

database

384 chats2=chats.readdb()
385 if not

os.path.exists(os.path.join(dirname,'downloadedfiles',chatname+'('+chatid+
')')):

386

os.makedirs(os.path.join(dirname,'downloadedfiles',chatname+'('+chatid
+')'))

387 ## print(b'chat: '.decode(),end='')
388 ## print(chatname,end=' ')
389 ## print(b'created'.decode())
390 print('chat: '+chatname+' created')
391 return data
392 elif data2[0]=='4':#message in a group
393 return data
394 elif data2[0]=='5':#message containing the entire conversation of a group
395 recvd=''
396 convs=[]
397 conv=enc_recv()
398 return '5/r/n//chatstart'+conv+'//chatend'
399 elif data2[0]=='6':#message indicating a member has been added to a group
400 chatid=data2[1]
401 par_to_add=data2[2]
402 adder=data2[3]
403 chats2=chats.readdb()
404 chatname=findchatbyid(chatid)
405 if chatid in chats2.keys():

406 chats2[chatid][1]=chats2[chatid][1]+','+par_to_add
407 chats.wrtdb(chatid,chats2[chatid])
408 return data
409 elif data2[0]=='7':#message containing the information of a contact to be

added

410 contact_name=data2[1]
411 contact_number=data2[2]
412 writecontact(contact_number,contact_name)
413 elif data2[0]=='8':#message containing the names of the files in a group
414 return data
415 elif data2[0]=='11':#a message indicating a member left a chat
416 return data
417
418 #return the name of a chat with a known id
419 def findchatbyid(chatid):
420 chats2=chats.readdb()
421 if chatid in chats2.keys():
422 return chats2[chatid][0]
423 return 'NONE'
424
425 #ask the server for the whole conversation of a chat
426 def getchat(chatid,num):
427 chats2=chats.readdb()
428 chatname=findchatbyid(chatid)
429 chats2[chatid][2]='0'
430 chats.wrtdb(chatid,chats2[chatid])
431 message='5/r/n'+chatid+'/r/n'+num+'/r/n//mesend'
432 enc_send(message)
433
434 #get the number of unread messages in each chat
435 def getunreadstats():
436 chats2=chats.readdb()
437 unreadchat={}
438 for i in chats2.keys():
439 unreadchat[i]=int(chats2[i][2])
440 return unreadchat
441
442 #indicate an unread message in a chat
443 def unreadmessage(chatid):
444 if chatid in chats.readdb().keys():
445 chatname=findchatbyid(chatid)
446 chats2=chats.readdb()
447 chats2[chatid][2]=str(int(chats2[chatid][2])+1)
448 chats.wrtdb(chatid,chats2[chatid])
449
450 #get the numbers of the participants in a chat
451 def getchatparticipants(chatid):
452 chats2=chats.readdb()
453 return chats2[chatid][1].split(',')
454
455 #removes a client from the list of participants in the database
456 def removechatparticipant(chatid,part):
457 chats2=chats.readdb()
458 participants=chats2[chatid][1].split(',')
459 if part in participants:
460 participants.remove(part)
461 participants2=b''
462 for i in participants:
463 participants2=participants2+i+','
464 participants2=participants2[:-1]
465 chats2[chatid][1]=participants2
466 chats.wrtdb(chatid,chats2[chatid])
467
468 #add a participant to a chat
469 def addparticipant(chat,participantnum,addernum):
470 par_nums=''
471 for i in participantnum:
472 par_nums=par_nums+i+','
473 par_nums=par_nums[:-1]
474 message='6/r/n'+chat+'/r/n'+par_nums+'/r/n'+addernum+'/r/n//mesend'
475 enc_send(message)
476

1 #####################################################
2 # clientgui.py #
3 #####################################################
4
5 import wx
6 import md5
7 import client
8 import time
9 import threading
10 import os
11
12
13 class windowClass(wx.Frame):
14 def __init__(self,*args,**kwargs):
15 super(windowClass,self).__init__(*args,**kwargs)
16
17 self.login()
18
19 self.Center()
20 #load the login window
21 def login(self):
22
23 LoginDialog(self)
24
25 #load the chat window
26 def basicGUI(self,client_number,client_name):
27
28 self.chat_names=[]
29
30 self.currentchat=b''
31
32 self.sem=threading.Semaphore()
33
34 self.mynum=client_number
35
36 panel=wx.Panel(self)
37
38 menuBar=wx.MenuBar()
39
40 fileButton=wx.Menu()
41 editButton=wx.Menu()
42
43 exitItem=fileButton.Append(wx.ID_EXIT, 'EXIT','STATUS MESSAGE')
44
45 menuBar.Append(fileButton, 'File')
46 menuBar.Append(editButton,'Edit')
47
48

self.txtinpt=wx.TextCtrl(panel,pos=(125,530),size=(400,60),style=wx.TE_PROCESS
_ENTER|wx.TE_MULTILINE)

49

self.txtout=wx.TextCtrl(panel,pos=(125,70),size=(460,450),style=wx.TE_MULTILIN
E|wx.TE_READONLY|wx.HSCROLL|wx.TE_RICH)

50
51 clt=''
52 for i in client.getchatlist().keys():
53 clt+=i+'\n'
54

self.chatlisttxt=wx.TextCtrl(panel,-1,clt,pos=(10,160),size=(105,220),style=wx
.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL|wx.TE_RICH)
55 self.chatlisttxt.Bind(wx.EVT_LEFT_DCLICK, self.on_left)
56
57

self.chatfiles=wx.TextCtrl(panel,-1,clt,pos=(10,390),size=(105,170),style=wx.T
E_MULTILINE|wx.TE_READONLY|wx.HSCROLL|wx.TE_RICH)
58 self.chatfiles.Bind(wx.EVT_LEFT_DCLICK, self.getfile)
59
60

self.toptxt=wx.TextCtrl(panel,pos=(125,40),size=(350,20),style=wx.TE_READONLY|
wx.TE_RICH)

61 self.toptxt.ChangeValue('CHAT')
62

63 self.SetMenuBar(menuBar)
64
65 self.addcontacts= wx.Button(panel, id=-1,label='ADD CONTACTS',pos=(10, 40),

size = (105,20))

66 self.addcontacts.Bind(wx.EVT_BUTTON,self.addcontact)
67
68 self.createchat= wx.Button(panel, id=-1,label='CREATE CHAT',pos=(10, 70),

size = (105,20))

69 self.createchat.Bind(wx.EVT_BUTTON,self.createChat)
70
71 self.addpart=wx.Button(panel,id=-1,label='ADD
PARTICIPANT',pos=(10,100),size=(105,20))
72 self.addpart.Bind(wx.EVT_BUTTON,self.addPart)
73
74 self.uploadfile= wx.Button(panel, id=-1,label='UPLOAD FILE',pos=(10, 130),

size = (105,20))

75 self.uploadfile.Bind(wx.EVT_BUTTON,self.uploadFile)
76
77 self.logOut=wx.Button(panel,id=-1,label='LOG OUT',pos=(10,570),size=(105,20))
78 self.logOut.Bind(wx.EVT_BUTTON,self.logout)
79
80 self.leavegroup= wx.Button(panel, id=-1,label='LEAVE GROUP',pos=(480, 40),

size = (105,20))

81 self.leavegroup.Bind(wx.EVT_BUTTON,self.leave)
82
83 self.SEND= wx.Button(panel, id=-1,label='SEND',pos=(530, 530), size = (55,60))
84 self.SEND.Bind(wx.EVT_BUTTON,self.sendto)
85
86 t1=threading.Thread(target=self.recvmes)
87 t1.start()
88
89 self.SetTitle(client_name+': '+client_number)
90
91

self.clientinfo=wx.TextCtrl(panel,pos=(10,10),size=(575,20),style=wx.TE_READON
LY|wx.TE_RICH)

92 self.clientinfo.ChangeValue(client_name+': '+client_number)
93
94 self.lastsentfrom=''
95
96 self.Show(True)
97
98 #leave the current chat
99 def leave(self,evt):
100 chat_names2=self.chat_names
101 for i in chat_names2:
102 if self.currentchat == i.split('//number')[1]:
103 client.leavegroup(self.mynum,self.currentchat)
104 self.chat_names.remove(i)
105 if len(self.chat_names)>0:
106 self.bringlinetotop2(0)
107 else:
108 self.chatlisttxt.ChangeValue('')
109 self.txtout.SetDefaultStyle(wx.TextAttr(wx.YELLOW,wx.WHITE))
110 self.txtout.AppendText('you left the group')
111 self.txtout.SetDefaultStyle(wx.TextAttr(wx.BLACK,wx.WHITE))
112
113 #upload a file to the current chat
114 def uploadFile(self,evt):
115 desktoppath=os.path.join(os.path.join(os.environ['USERPROFILE']),'Desktop')
116 openFileDialog = wx.FileDialog(None, "Open", desktoppath, "", "", wx.FD_OPEN

| wx.FD_FILE_MUST_EXIST)

117
118 openFileDialog.ShowModal()
119 path = openFileDialog.GetPath()
120 openFileDialog.Destroy()
121

threading.Thread(target=client.tupload,args=(path,self.currentchat,self.mynum,
)).start()

122
123 #download a file
124 def getfile(self,evt):

125 position = evt.GetPosition()
126 (x,y,z) = self.chatfiles.HitTest(position)
127 filename = self.chatfiles.GetLineText(z)
128 if filename!='':
129

threading.Thread(target=client.downloadfile,args=(self.mynum,self.currentc
hat,filename,)).start()

130
131 #choose a chat from the list
132 def on_left(self, evt):
133 position = evt.GetPosition()
134 (x,y,z) = self.chatlisttxt.HitTest(position)
135 cht=self.chat_names[z]
136 self.choosechatwithtxt(cht)
137 self.bringlinetotop2(z)
138
139 #change the order of the chats in the list according to the last message sent
140 def bringlinetotop2(self,z):
141 if int(z) < len(self.chat_names):
142 chats_reorder=[]
143 z=int(z)
144 the_line = self.chatlisttxt.GetLineText(z)
145 unreadmess=client.getunreadstats()
146 chats_reorder.append(self.chat_names[z])
147 for i in range(z):
148 chats_reorder.append(self.chat_names[i])
149 for i in range(z+1,len(self.chat_names)):
150 chats_reorder.append(self.chat_names[i])
151 self.chatlisttxt.ChangeValue('')
152 self.chat_names=chats_reorder
153 for i in self.chat_names:
154 chatname=i.split('//number')[0]
155 chatnumber=i.split('//number')[1]
156 if chatnumber == self.currentchat:
157 self.chatlisttxt.SetDefaultStyle(wx.TextAttr(wx.RED,wx.WHITE))
158 self.chatlisttxt.AppendText(chatname+'\n')
159 elif chatnumber in unreadmess.keys():
160 if int(unreadmess[chatnumber])==0:
161 self.chatlisttxt.SetDefaultStyle(wx.TextAttr(wx.BLACK,wx.WHITE))
162 self.chatlisttxt.AppendText(chatname+'\n')
163 else:
164 self.chatlisttxt.SetDefaultStyle(wx.TextAttr(wx.GREEN,wx.WHITE))
165 self.chatlisttxt.AppendText(chatname+'\n')
166
167 #send a message
168 def sendto(self,EVT):
169 text=self.txtinpt.GetValue()
170 client.snd(self.currentchat,self.mynum,text)
171 self.txtinpt.ChangeValue('')
172
173 #add text to the conversation window
174 def addtoout(self,sendtime,sentfrom,message):
175 #chooses the color according to the type of message
176 self.text=''
177 if sentfrom=='SERVER':
178 if sendtime=='DATE':
179 self.text=self.text+'\n'+'DATE: '+message+'\n\n'
180 elif sendtime=='CREATEDATE':
181 self.text=self.text+'CREATED ON: '+message+'\n\n'
182 self.txtout.SetDefaultStyle(wx.TextAttr(wx.BLUE))
183 self.txtout.AppendText(self.text)
184 self.lastsentfrom='SERVER'
185 elif sendtime=='ADD':
186 self.text=self.text+'\n'+sentfrom+' added '+message+' to the group'+'\n\n'
187 self.txtout.SetDefaultStyle(wx.TextAttr(wx.BLUE))
188 self.txtout.AppendText(self.text)
189 self.lastsentfrom='ADD'
190 elif sendtime=='LEFT':
191 self.txtout.SetDefaultStyle(wx.TextAttr(wx.YELLOW,wx.WHITE))
192 self.txtout.AppendText('\n'+sentfrom+' left the group\n\n')
193 elif sentfrom=='YOU':
194 self.txtout.SetDefaultStyle(wx.TextAttr(wx.GREEN))

195 if self.lastsentfrom!='YOU':
196 self.txtout.AppendText('YOU:\n')
197 self.txtout.SetDefaultStyle(wx.TextAttr(wx.BLACK))
198 splitmes=message.split('\n')
199 self.txtout.AppendText(sendtime+' '+splitmes[0]+'\n')
200 for i in splitmes[1:]:
201 self.txtout.AppendText(' '+i+'\n')
202 self.lastsentfrom='YOU'
203 else:
204 self.txtout.SetDefaultStyle(wx.TextAttr(wx.RED))
205 if self.lastsentfrom!=sentfrom:
206 self.txtout.AppendText(sentfrom+':\n')
207 self.txtout.SetDefaultStyle(wx.TextAttr(wx.BLACK))
208 self.txtout.AppendText(sendtime+' '+message+'\n')
209 self.lastsentfrom=sentfrom
210
211 #load the window for adding contacts
212 def addcontact(self,event):
213 AddContactDialog(self)
214
215 #create a new chat
216 def createChat(self,event):
217 self.contactslist=client.getcontactlist()
218 self.contact_options=[]
219 self.contact_numbers=[]
220 for i in self.contactslist.keys():
221 self.contact_options.append(self.contactslist[i]+' ('+i+')')
222 self.contact_numbers.append(i)
223 self.mult=wx.MultiChoiceDialog(None, 'CREATE CHAT', 'CHOOSE PARTICIPANTS',

self.contact_options)
224 self.mult.Show(True)
225 if self.mult.ShowModal()==wx.ID_OK:
226 c = self.mult.GetSelections()
227 self.numbers=[self.mynum]
228 for i in c:
229 self.numbers.append(self.contact_numbers[i])
230 self.chatname=wx.TextEntryDialog(None,'CREATE GROUP','ENTER GROUP

NAME','group1')

231 if self.chatname.ShowModal()==wx.ID_OK:
232 name=self.chatname.GetValue()
233 client.createchat(self.mynum,name,self.numbers)
234
235 #log out of the app
236 def logout(self,evt):
237 yesnoBox=wx.MessageDialog(None,'ARE YOU SURE YOU WANT TO LOG

OUT?','LOGOUT',wx.YES_NO)
238 yesnoAnswer=yesnoBox.ShowModal()
239 yesnoBox.Destroy()
240 if yesnoAnswer==wx.ID_YES:
241 client.logout()
242 self.Destroy()
243
244 #choose the current chat(which will be shown in the conversation window
245 def choosechatwithtxt(self,cht):
246 self.chats=client.getchatlist()
247 chatnames=[]
248 chatname=cht.split('//number')[0]
249 chatnumber=cht.split('//number')[1]
250 for i in self.chats.keys():
251 chatnames.append(self.chats[i][0])
252 if chatnumber in self.chats.keys():
253 self.toptxt.ChangeValue(chatname)
254 self.currentchat=str(chatnumber)
255 self.txtout.ChangeValue('')
256 client.getchat(self.currentchat,self.mynum)
257
258 #check for messages that need to be received
259 def recvmes(self):
260 while True:
261 self.sem.acquire()
262 recvd=client.recvmes(self.mynum)
263 self.sem.release()

264 if recvd != None:
265 recvd2=recvd.split('/r/n')
266 if recvd2[0]=='3': #add the new chat to the list of chat names in

order for it to show

267 t=client.findchatbyid(recvd2[1])+'//number'+recvd2[1]
268 self.chat_names.append(t)
269 self.chatlisttxt.AppendText(t.split('//number')[0])
270 self.bringlinetotop2(0)
271 if recvd2[0]=='4':
272 self.recvmes4(recvd)
273 elif recvd2[0]=='5': #split the conversation into the seperate

messages and handle each one seperately

274

self.currentchat_conversation=recvd.split('//chatstart')[1].split(
'//chatend')[0].split('//mesend')[:-1]
275 for i in self.currentchat_conversation:
276 if i.split('/r/n')[0]=='4':
277 self.recvmes4(i)
278 elif i.split('/r/n')[0]=='6':
279 self.recvmes6(i)
280 elif i.split('/r/n')[0]=='11':
281 self.recvmes11(i)
282 elif recvd2[0]=='6':
283 self.recvmes6(recvd)
284 elif recvd2[0]=='8':
285 self.recvmes8(recvd)
286 elif recvd2[0]=='11':
287 self.recvmes11(recvd)
288 time.sleep(0.1)
289
290 #handle a type 4 message(message in a chat)
291 def recvmes4(self,recvd):
292 recvd2=recvd.split('/r/n')
293 if str(recvd2[1])==self.currentchat:
294 self.addtoout(recvd2[3],self.returncontact(recvd2[2]),recvd2[4])
295 else:
296 client.unreadmessage(recvd2[1])
297 unreadmess=client.getunreadstats()
298 z=0
299 for i in range(len(self.chat_names)):
300 if self.chat_names[i].split('//number')[1]==recvd2[1]:
301 z=i
302 self.bringlinetotop2(z)
303 #handle a type 6 message(add participants to a chat)
304 def recvmes6(self,recvd):
305 recvd2=recvd.split('/r/n')
306 par_to_add=recvd2[2].split(',')
307 toadd=''
308 if str(recvd2[1])==self.currentchat:
309 for i in par_to_add:
310 toadd+=self.returncontact(i)
311 toadd+=','
312 toadd=toadd[:-1]
313 adder=self.returncontact(recvd2[3])
314 self.addtoout('ADD',adder,toadd)
315 else:
316 client.unreadmessage(recvd2[1])
317 unreadmess=client.getunreadstats()
318 z=0
319 for i in range(len(self.chat_names)):
320 if self.chat_names[i].split('//number')[1]==recvd2[1]:
321 z=i
322 self.bringlinetotop2(z)
323
324 #handle a type 8 message(chat file list)
325 def recvmes8(self,recvd):
326 recvd2=recvd.split('/r/n')
327 if str(recvd2[1])==self.currentchat:
328 self.chatfiles.ChangeValue('')
329 files=recvd2[2].split(',')
330 for filename in files: #add the file name to the file list and choose

the color according to wether it has been downloaded already

331 if client.checkifexists(self.currentchat,filename):
332 self.chatfiles.SetDefaultStyle(wx.TextAttr(wx.BLACK))
333 self.chatfiles.AppendText(filename+'\n')
334 else:
335 self.chatfiles.SetDefaultStyle(wx.TextAttr(wx.BLUE))
336 self.chatfiles.AppendText(filename+'\n')
337
338 #handle a type 11 messgae(a participant left a group)
339 def recvmes11(self,recvd):
340 recvd2=recvd.split('/r/n')
341 client=recvd2[1]
342 chatid=recvd2[2]
343 if chatid==self.currentchat:
344 self.addtoout('LEFT',self.returncontact(client),chatid)
345
346 #return the name of a contact whose number is known(if he is a saved conatct)
347 def returncontact(self,number):
348 self.contactslist=client.getcontactlist()
349 if number==self.mynum:
350 return 'YOU'
351 elif number in self.contactslist.keys():
352 return self.contactslist[number]
353 else:
354 return number
355
356 #return a dictionary of contacts where the keys are the names(instead of the

numbers)

357 def createcountercontacts(self):
358 countercontacts={}
359 self.contactslist=client.getcontactlist()
360 for i in self.contactslist.keys():
361 countercontacts[self.contactslist[i]]=i
362 return countercontacts
363
364 #add a participant to a chat
365 def addPart(self,evt):
366 chat_part=client.getchatparticipants(self.currentchat)
367 self.contactslist=client.getcontactlist()
368 self.contact_options=[]
369 self.contactop_names=[]
370 for i in self.contactslist.keys(): #add only the contacts who are not

already in the chat
371 if i not in chat_part:
372 self.contact_options.append(self.contactslist[i]+' ('+i+')')
373 self.contactop_names.append(self.contactslist[i])
374 if len(self.contact_options)>0:
375 self.mult=wx.MultiChoiceDialog(None, 'ADD PARTICIPANT(S)', 'CHOOSE

PARTICIPANT(S)', self.contact_options)

376 self.mult.Show(True)
377 if self.mult.ShowModal()==wx.ID_OK:
378 c = self.mult.GetSelections()
379 self.numbers=[]
380 for i in c:
381

self.numbers.append(self.createcountercontacts()[self.contactop_na
mes[i]])

382 client.addparticipant(self.currentchat,self.numbers,self.mynum)
383 else:
384 wx.MessageBox('no contacts to add to this group', 'Info', wx.OK |

wx.ICON_INFORMATION) #if all the user's contacts are already in the chat
a message is displayed

385
386 class LoginDialog(wx.Dialog):
387 def __init__(self,chatwindow):
388 self.chatwindow=chatwindow
389 wx.Dialog.__init__(self, None, title="Login",size=(200,200))
390 # user info
391 user_sizer = wx.BoxSizer(wx.HORIZONTAL)
392 user_lbl = wx.StaticText(self, label="Username:")
393 user_sizer.Add(user_lbl, 0, wx.ALL|wx.CENTER, 5)
394 self.user = wx.TextCtrl(self)
395 user_sizer.Add(self.user, 0, wx.ALL, 5)

396 # pass info
397 p_sizer = wx.BoxSizer(wx.HORIZONTAL)
398 p_lbl = wx.StaticText(self, label="Password:")
399 p_sizer.Add(p_lbl, 0, wx.ALL|wx.CENTER, 5)
400 self.password = wx.TextCtrl(self,
style=wx.TE_PASSWORD|wx.TE_PROCESS_ENTER)
401 p_sizer.Add(self.password, 0, wx.ALL, 5)
402
403 main_sizer = wx.BoxSizer(wx.VERTICAL)
404 main_sizer.Add(user_sizer, 0, wx.ALL, 5)
405 main_sizer.Add(p_sizer, 0, wx.ALL, 5)
406
407 btn = wx.Button(self, label="Login",pos=(100,100),size=(80,30))
408 btn.Bind(wx.EVT_BUTTON, self.onLogin)
409
410 btn = wx.Button(self, label="Register",pos=(20,100),size=(80,30))
411 btn.Bind(wx.EVT_BUTTON, self.onRegister)
412
413 self.SetSizer(main_sizer)
414 self.Show()
415
416 #try to login using the information entered
417 def onLogin(self,event):
418 username=self.user.GetValue()
419 password=self.password.GetValue()
420 m=md5.new()
421 m.update(username+password)
422 myid=m.hexdigest()
423 logans = client.checkregistered(username+password)
424 if logans == False:
425 wx.MessageBox('username or password incorrect', 'Info', wx.OK |
wx.ICON_INFORMATION) #if the information is not correct a
message is displayed

426 self.password.ChangeValue('')
427 else:
428 self.Destroy()
429 client_number=logans.split(',')[0]
430 client_name=logans.split(',')[1]
431 self.chatwindow.basicGUI(client_number,client_name)
432
433 #load the register window
434 def onRegister(self,event):
435 self.Destroy()
436 RegisterDialog(self.chatwindow)
437
438 class RegisterDialog(wx.Dialog):
439 def __init__(self,chatwindow):
440 self.chatwindow=chatwindow
441 wx.Dialog.__init__(self, None, title="Register",size=(200,200))
442 # user nickname
443 name_sizer = wx.BoxSizer(wx.HORIZONTAL)
444 name_lbl = wx.StaticText(self, label="Name: ")
445 name_sizer.Add(name_lbl, 0, wx.ALL|wx.CENTER, 5)
446 self.name = wx.TextCtrl(self)
447 name_sizer.Add(self.name, 0, wx.ALL, 5)
448 # user info
449 user_sizer = wx.BoxSizer(wx.HORIZONTAL)
450 user_lbl = wx.StaticText(self, label="Username:")
451 user_sizer.Add(user_lbl, 0, wx.ALL|wx.CENTER, 5)
452 self.user = wx.TextCtrl(self)
453 user_sizer.Add(self.user, 0, wx.ALL, 5)
454 # pass info
455 p_sizer = wx.BoxSizer(wx.HORIZONTAL)
456 p_lbl = wx.StaticText(self, label="Password: ")
457 p_sizer.Add(p_lbl, 0, wx.ALL|wx.CENTER, 5)
458 self.password = wx.TextCtrl(self,
style=wx.TE_PASSWORD|wx.TE_PROCESS_ENTER)
459 p_sizer.Add(self.password, 0, wx.ALL, 5)
460
461 main_sizer = wx.BoxSizer(wx.VERTICAL)
462 main_sizer.Add(name_sizer, 0, wx.ALL, 5)
463 main_sizer.Add(user_sizer, 0, wx.ALL, 5)

464 main_sizer.Add(p_sizer, 0, wx.ALL, 5)
465
466 btn = wx.Button(self, label="Register",size=(80,30),pos=(60,130))
467 btn.Bind(wx.EVT_BUTTON, self.onRegister)
468
469 self.SetSizer(main_sizer)
470 self.Show()
471
472 #try to register using the information entered
473 def onRegister(self,event):
474 name=self.name.GetValue()
475 username=self.user.GetValue()
476 password=self.password.GetValue()
477 m=md5.new()
478 m.update(username+password)
479 myid=m.hexdigest()
480 regans =

client.register(username+password,username,name)#client.register(myid,
username,name)
481 if regans == False:
482 wx.MessageBox('invalid information, already used', 'Info', wx.OK
| wx.ICON_INFORMATION) #if the information the client enterd a
is already in use a message is displayed

483 self.Destroy()
484 RegisterDialog(self.chatwindow)
485 else:
486 self.Destroy()
487 client_number=regans.split(',')[0]
488 client_name=regans.split(',')[1]
489 self.chatwindow.basicGUI(client_number,client_name)
490
491
492 class AddContactDialog(wx.Dialog):
493 def __init__(self,chatwindow):
494 self.chatwindow=chatwindow
495 wx.Dialog.__init__(self, None, title="ADD CONTACT",size=(200,200))
496 # name
497 name_sizer = wx.BoxSizer(wx.HORIZONTAL)
498 name_lbl = wx.StaticText(self, label="Name:")
499 name_sizer.Add(name_lbl, 0, wx.ALL|wx.CENTER, 5)
500 self.name = wx.TextCtrl(self)
501 name_sizer.Add(self.name, 0, wx.ALL, 5)
502 # number
503 num_sizer = wx.BoxSizer(wx.HORIZONTAL)
504 num_lbl = wx.StaticText(self, label="Number:")
505 num_sizer.Add(num_lbl, 0, wx.ALL|wx.CENTER, 5)
506 self.num = wx.TextCtrl(self)
507 num_sizer.Add(self.num, 0, wx.ALL, 5)
508
509 main_sizer = wx.BoxSizer(wx.VERTICAL)
510 main_sizer.Add(name_sizer, 0, wx.ALL, 5)
511 main_sizer.Add(num_sizer, 0, wx.ALL, 5)
512
513 btn = wx.Button(self, label="ADD",pos=(100,100),size=(80,30))
514 btn.Bind(wx.EVT_BUTTON, self.onadd)
515
516 btn = wx.Button(self, label="CANCEL",pos=(20,100),size=(80,30))
517 btn.Bind(wx.EVT_BUTTON, self.oncancel)
518
519 self.SetSizer(main_sizer)
520 self.Show()
521
522 #Adds a contact
523 def onadd(self,event):
524 name=self.name.GetValue()
525 number=self.num.GetValue()
526 if not client.addcontact(self.chatwindow.mynum,name,number):
527 wx.MessageBox('could not add a client that does not exist',
'Info', wx.OK | wx.ICON_INFORMATION) #if a non existing number
is entered a message is displayed

528 self.Destroy()

#closes the addcontact window
def oncancel(self,event):
self.Destroy()

def main():
app=wx.App()
windowClass(None,size=(600,700),style=wx.SYSTEM_MENU | wx.CAPTION |

wx.CLIP_CHILDREN)


 app.MainLoop()
 main()