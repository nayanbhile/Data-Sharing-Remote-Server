import socket
import os
import pathlib
import threading
from uuid import uuid1

activeThreads=0

class Model:
    def __init__(self):
        self.dataFiles=self.readDataFiles()
        self.semaphores=self.addSemaphores()
        self.userIDs=self.getUserIDs()
        self.activeUsers=dict()
        
    def readDataFiles(self):
        path=pathlib.Path("C:\\pythoneg\\pyapps\\networking\\tool1\\store")
        pathstr="C:\\pythoneg\\pyapps\\networking\\tool1\\store\\"
        dir=os.listdir(path)
        dataFiles=dict()
        for fileName in dir:
            filePath=pathlib.Path(pathstr+fileName)
            fileSize=os.stat(filePath).st_size
            dataFiles[f'{fileName}']=fileSize
        return dataFiles

    def getUserIDs(self):
        file=open("userID.txt","r")
        a=eval(file.read())
        return a

    def addActiveUser(self,uuid,username):
        self.activeUsers[uuid]=username

    def removeActiveUser(self,uuid):
        return self.activeUsers.pop(uuid)

    def addSemaphores(self):
        fileNames=list(self.dataFiles.keys())
        semaphores=dict()
        for fileName in fileNames:
            semaphore=threading.Semaphore(5)
            semaphores[fileName]=semaphore            
        return semaphores

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
        global activeThreads
        toReceive=100
        tmp=b''
        while toReceive>0:
            a=self.sock.recv(toReceive)
            tmp+=a
            toReceive-=len(a)
        request=str(tmp.decode()).strip()
        if request=="xyx123456abc":
            if activeThreads!=1:
                self.sock.sendall(bytes(str(1),"utf-8"))
                forceClose=int(self.sock.recv(1))
                if forceClose!=1: sys.exit() 
            self.sock.sendall(bytes(str(0),"utf-8"))
            print("Server shutting down")
            serverSocket.close()
            os._exit(0)

    def processDIR(self):
        global model
        dataFiles=model.dataFiles
        dataFilesStr=str(dataFiles)
        dataFilesStrLength=len(dataFilesStr)
        #sending length of dataFilesStr
        self.sock.sendall(bytes(str(dataFilesStrLength).ljust(100),"utf-8"))
        #sending dataFilesStr
        self.sock.sendall(bytes(dataFilesStr,"utf-8"))
        response=int(self.sock.recv(1).decode("utf-8"))
        if response==1: print("List of data files sent")
        else: print("Problem sending list of data files")

    def processDOWNLOAD(self):
        global model
        #receiving length of file name
        a=str(self.sock.recv(100).decode("utf-8")).strip()
        b=a[36:]
        if self.uuid!=a[:36]:
            self.sock.sendall(b'0')
            self.sock.close()
            return "0"
        else: 
            self.sock.sendall(b'1')
        fileNameLength=int(b)
        #receiving file name
        a=str(self.sock.recv(fileNameLength+36).decode("utf-8"))
        if self.uuid!=a[:36]:
            self.sock.sendall(b'0')
            self.sock.close()
            return "0"
        else: 
            self.sock.sendall(b'1')
        fileName=a[36:].strip()
        if fileName not in model.dataFiles:
            print("Action terminated: File not found") 
            self.sock.sendall(b'0')
            return
        else: self.sock.sendall(b'1')
        a="C:\\pythoneg\\pyapps\\networking\\tool1\\store\\"
        b=a+fileName
        path=pathlib.Path(b)
        file=open(path,"rb")
        fileLength=os.stat(path).st_size
        self.sock.sendall(bytes(str(fileLength).ljust(100),"utf-8"))
        print("File length sent: ",fileLength)
        model.semaphores[fileName].acquire()
        print("Sending file...")
        tmp=fileLength
        while not tmp==0:
            if tmp>=4096: self.sock.sendall(file.read(4096))
            else: 
                self.sock.sendall(file.read(tmp))
                break
            tmp=tmp-4096
        print("File sent successfully!")
        model.semaphores[fileName].release()        

    def processLOGOUT(self):
        self.sock.sendall(b'1')
        self.sock.close()


class TaskManagerThread(threading.Thread, CommandProcessor):
    command=""
    def __init__(self,sock,uuid):
        global activeThreads
        threading.Thread.__init__(self)
        self.sock=sock
        self.uuid=uuid
        activeThreads+=1
        self.start()
    def getCommand(self):
        global activeThreads
        a=str(self.sock.recv(100).decode("utf-8")).strip()
        b=a[36:]
        if self.uuid!=a[:36]:
            self.sock.sendall(b'0')
            self.sock.close()
            return "0"
        else: 
            self.sock.sendall(b'1')
        commandLength=int(b)
        
        a=str(self.sock.recv(commandLength+36).decode("utf-8"))
        if self.uuid!=a[:36]:
            self.sock.sendall(b'0')
            self.sock.close()
            return "0"
        else: 
            self.sock.sendall(b'1')
        command=a[36:].strip()
        print("Command received: ",command)
        if command=="logout": 
            self.sock.sendall(b'0')
            self.sock.close()
            print("User logged out: ",model.activeUsers[self.uuid])
            model.removeActiveUser(self.uuid)
            return "0"
        return command
    def run(self):
        global activeThreads
        while True:
            self.command=self.getCommand()
            if self.command=="0": break
            self.commandProcessor=CommandProcessor(self.sock,self.uuid,self.command)
            self.commandProcessor.processCommand()
            
        activeThreads-=1
        
ip=""
portNumber=0
cfgFileName="connection.cfg"
with open("connection.cfg","r") as cfgFile:
    ip=cfgFile.readline().strip()
    portNumber=int(cfgFile.readline().strip())

model=Model()
serverSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
serverSocket.bind((ip,portNumber))
serverSocket.listen()

while True:
    print("-"*75)
    print("Server is listening on port: ",portNumber)
    sock,sockName=serverSocket.accept()
    username=sock.recv(50).decode("utf-8").strip()
    password=sock.recv(50).decode("utf-8").strip()
    if username not in model.userIDs:
        sock.sendall(b'0')
        sock.close()
        continue
    else:
        sock.sendall(b'1')
        if model.userIDs[username]!=password:
            sock.sendall(b'0')
            sock.close()
            continue
        else: 
            sock.sendall(b'1')
            uuid=str(uuid1())
            sock.sendall(bytes(uuid,"utf-8"))
            model.addActiveUser(uuid,username)
    print(username," logged in")
    t=TaskManagerThread(sock,uuid)
    