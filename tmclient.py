import socket
import os
import pathlib

class CommandProcessor:
    def __init__(self,sock,uuid,command):
        self.sock=sock
        self.command=command.lower()
        self.uuid=uuid

    def processCommand(self):
        if self.command=="dir": self.processDIR()
        if self.command=="exit": self.processEXIT()
        if self.command=="download": self.processDOWNLOAD()
        if self.command=="logout": self.processLOGOUT()

    def processEXIT(self):
        self.sock.sendall(bytes("xyx123456abc".ljust(100),"utf-8"))
        isThreadActive=int(self.sock.recv(1).decode("utf-8"))
        if isThreadActive==1:
            killOrNot=input("The server is still busy. Force shut down?(Y/N)")
            if killOrNot.lower()=="y": self.sock.sendall(b'1')
            self.sock.sendall(b'0')
        self.sock.close()

    def processDIR(self):
        #receiving length of data files string
        dataFilesStrLength=int(self.sock.recv(100).decode("utf-8"))
        #receiving data files string
        dataFilesStr=self.sock.recv(dataFilesStrLength).decode("utf-8")
        if len(dataFilesStr)==dataFilesStrLength: self.sock.sendall(b'1')
        else: 
            self.sock.sendall(b'0')
            print("Problem receiving file names")
            return
        dataFiles=eval(dataFilesStr)
        print("Sr.No.".ljust(8),"File Name".ljust(50),"Size".ljust(10))
        i=1
        for dataFile in dataFiles:
            print(str(i).ljust(8), dataFile.ljust(50), str(dataFiles[dataFile]).ljust(10))
            i+=1

    def processDOWNLOAD(self):
        fileName=input("Enter file name: ")
        fileNameLength=len(fileName)
        a=self.uuid+str(fileNameLength)
        
        self.sock.sendall(bytes(a.ljust(100),"utf-8"))
        x=int(self.sock.recv(1).decode("utf-8"))
        if x!=1:
            print("Client is shutting down due to security purpose")
            self.sock.close()
            exit()
        self.sock.sendall(bytes(uuid+fileName,"utf-8"))
        x=int(self.sock.recv(1).decode("utf-8"))
        if x!=1:
            print("Client is shutting down due to security purpose")
            self.sock.close()
            exit()
        print("File name sent: ",fileName)
        x=int(self.sock.recv(1).decode("utf-8"))
        if x!=1:
            print("File not found")
            return
        #receiving length of file
        fileLength=int(str(self.sock.recv(100).decode("utf-8")).strip())
        #receiving file
        tmp=b''
        dataBytes=b''
        x=fileLength
        savingFileName=input("Save file as: ")
        savingPath=pathlib.Path(f'C:\\pythoneg\\pyapps\\networking\\tool1\\downloads\\{savingFileName}')
        file=open(savingPath,"wb")
        print("Waiting for file to download...")
        i=0
        while not x==0:
            a=b''
            i+=1
            if x>=4096:
                remainingBytes=4096
                while remainingBytes>0:
                    a+=self.sock.recv(remainingBytes)
                    remainingBytes=remainingBytes-len(a)
            else:
                remainingBytes=x
                while remainingBytes>0:
                    a+=self.sock.recv(remainingBytes)
                    remainingBytes=remainingBytes-len(a)        
            file.write(a)
            if i%50==0: print(x)
            x=x-len(a)
        file.close()
        if os.stat(savingPath).st_size==fileLength: print("File received successfully!")
        else: 
            print("Problem in receiving file", fileName)
            print("Required file length: ",fileLength,"\nFile length received: ",len(dataBytes))
            return

        print("File saved successfully")

    def processLOGOUT(self):
        x=int(self.sock.recv(1).decode("utf-8"))
        if x!=1: print("Problem logging out")
        else:
            self.sock.close() 
            print("Successfully logged out")
            exit()


ip=""
portNumber=0
cfgFileName="connection.cfg"
with open("connection.cfg","r") as cfgFile:
    ip=cfgFile.readline().strip()
    portNumber=int(cfgFile.readline().strip())

sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.connect((ip,portNumber))

username=input("Username: ")
password=input("Password: ")
sock.sendall(bytes(username.ljust(50),"utf-8"))
sock.sendall(bytes(password.ljust(50),"utf-8"))
uuid=""
usernameVerification=int(sock.recv(1).decode("utf-8"))
if usernameVerification!=1:
    print("Invalid username")
    sock.close()
    exit()
else: 
    passwordVerification=int(sock.recv(1).decode("utf-8"))
    if passwordVerification!=1:
        print("Invalid password")
        sock.close()
        exit()
    else:
        print("Welcome ",username)
        uuid=sock.recv(36).decode("utf-8")
        
while True:
    command=input("Enter your command: ").strip().lower()
    if not (command=="dir" or command=="exit" or command=="download" or command=="logout"):
        print("Invalid command...")
        continue
    commandLength=len(command)
    #sending length of command
    a=uuid+str(commandLength)
    sock.sendall(bytes(a.ljust(100),"utf-8"))
    x=int(sock.recv(1).decode("utf-8"))
    if x!=1:
        print("Client is shutting down due to security purpose")
        sock.close()
        break
    #sending command
    a=uuid+command
    sock.sendall(bytes(a,"utf-8"))
    x=int(sock.recv(1).decode("utf-8"))
    if x!=1:
        print("Client is shutting down due to security purpose")
        sock.close()
        break
    if command=="logout":
        x=int(sock.recv(1).decode("utf-8"))
        if x!=0: print("Problem logging out")
        else:
            sock.close() 
            print("Successfully logged out")
            exit()

    commandProcessor=CommandProcessor(sock,uuid,command)
    commandProcessor.processCommand()
    if command=="exit": break