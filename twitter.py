"""
Create command_input client thread
				^V^
Create server thread
	has clients to all other sites



for each other site
	create new socket connection

"""


import threading
import signal
import time
import sys
import asyncore
import socket
import dill
import pickle
import datetime
from user import User

names_ = [line.rstrip('\n').split(' ')[0] for line in open('EC2-peers.txt')]
ec2ips_ = [line.rstrip('\n').split(' ')[1] for line in open('EC2-peers.txt')]
peers_ = [int((line.rstrip('\n')).split(' ')[2])
          for line in open('EC2-peers.txt')]


class Client(asyncore.dispatcher_with_send):
    def __init__(self, host, port, message):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.connect((host, port))
        self.out_buffer = message
        self.message = message

    def handle_close(self):
        self.close()

    # def handle_read(self):
    # 	print 'Received', self.recv(1024)
    # 	self.close()

    # def handle_write(self):
    # 	self.getLog(self.message)
    # 	self.close()
    # 	pass

    def handle_error(self):
        # print "Can't connect to peer at %s:%s" % (self.host, self.port)
        print

class EchoHandler(asyncore.dispatcher_with_send):

	def handle_read(self):
		data = self.recv(16384)
		if data:
			serializedMessage = dill.loads(data)

			# Check if prepare
			if(serializedMessage[0] == "prepare"):
				# serializedMessage --> (flagString, IP|PORT, proposal)
				# proposal --> (index, n, event)
				print "Recevied prepare message ", serializedMessage[2], " from ", serializedMessage[1]
				promise = site.prepare(serializedMessage[2][0], serializedMessage[2][1])

				# promise --> (index, accNum, accVal)
				# Check if promise is None
				if(promise == None):
					print serializedMessage[2][1], " does not exceed maxPrepare value. ", site.getId(), " cannot promise."
				else:
					dilledMessage = dill.dumps(("promise", serializedMessage[1], serializedMessage[2], promise))
					for index, peerPort in enumerate(site.getPorts()):
			    			c = Client("", peerPort, dilledMessage)
			    			asyncore.loop(timeout=5, count=1)

			if(serializedMessage[0] == "promise"):
				# serializedMessage --> (flagString, IP|POR, proposal, promise)
				print "Received promise message ", serializedMessage[3]
				site.addPromise(serializedMessage[3])
				
				print site.getPromises()
				print "Total: ", site.getAmtSites()

            # FILTER RECEIVES
            # Commit proposal to writeAheadLog
            # site.commit(serializedMessage)

class Server(asyncore.dispatcher_with_send):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)
        print "Server listening at", host, port

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            sender = 0
            for index, ip in enumerate(ec2ips_):
                if ip == repr(addr)[0]:
                    sender = index
            # print 'Recieved message from %s' % names_[sender]
            handler = EchoHandler(sock)

    # def handle_read(self):
    # 	data = self.recv(8192)
    # 	print "Messaged received"
    # 	if data:
    # 		self.getLog(data)
    # 		# self.close()


# Main thread wrapper class
class myThread (threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        # The shutdown_flag is a threading.Event object that indicates whether the thread should be terminated.
        self.shutdown_flag = False
        self.name = name
        # self.peers = [int(line.rstrip('\n')) for line in open('peers.txt')]
        # self.names = [line.rstrip('\n') for line in open('names.txt')]

        self.peers = [int((line.rstrip('\n')).split(' ')[2])
                      for line in open('EC2-peers.txt')]
        self.names = [line.rstrip('\n').split(' ')[0]
                      for line in open('EC2-peers.txt')]
        self.ec2ips = [line.rstrip('\n').split(' ')[1]
                       for line in open('EC2-peers.txt')]

    def run(self):
        # Update this User's IP and port private field
        for index, peerPort in enumerate(self.peers):
        	if(peerPort == int(sys.argv[1])):
        		site.updateIPPort(self.ec2ips[index], peerPort)

        # Enter while loop accepting the following commands
        if self.name == 'commandThread':
            while 1:
                time.sleep(0.2)
                command = raw_input("\nPlease enter a command:\n")
                if command[:6] == "tweet ":
                    messageBody = command[6:]
                    utcDatetime = datetime.datetime.utcnow()
                    utcTime = utcDatetime.strftime("%Y-%m-%d %H:%M:%S")

                    proposal = (site.getIndex(),
                                ("tweet", command[6:], site.getId(), utcTime))
                    self.prepare(proposal)
                elif command == "view":
                    site.view()
                elif command == "quit":
                    self.shutdown_flag = True
                    raise KeyboardInterrupt
                    self.shutdown_flag = True
                elif command[:8] == "unblock ":
                    name = command[8:]
                    siteName = sys.argv[2]

                    utc_datetime = datetime.datetime.utcnow()
                    utcTime = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")

                    print "Unblocking User: " + command[8:]
                    proposal = (site.getIndex(), ("unblock", ord(
                        name[0]) - 65, site.getId(), utcTime))
                    self.prepare(proposal)
                elif command[:6] == "block ":
                    name = command[6:]
                    siteName = sys.argv[2]

                    utc_datetime = datetime.datetime.utcnow()
                    utcTime = utc_datetime.strftime("%Y-%m-%d %H:%M:%S")

                    print "Blocking User: " + command[6:]
                    proposal = (site.getIndex(), ("block", ord(
                        name[0]) - 65, site.getId(), utcTime))
                    self.prepare(proposal)
                elif command == "View Log":
                    site.viewWriteAheadLog()
                elif command == "View Dictionary":
                    site.viewDictionary()
                else:
                    print "Unknown command %s :(. Try again." % (command)

        # Start the server the listening for incoming connections
        elif self.name == 'serverThread':
            server = Server('0.0.0.0', int(sys.argv[1]))
            if self.shutdown_flag != True:
                asyncore.loop()

    def prepare(self, proposal):
    	print site.getId(), " is proposing ", proposal, " to be committed at index ", proposal[0]
        # RUN SYNOD ALGORITHM RATHER THAN JUST COMMITTING
        # proposal --> (index, accVal)
        maxPrepare = -1
        accNum = site.getId()
        # self.commit((proposal[0], maxPrepare, accNum, proposal[1]))

        # Broadcast to all sites
        for index, peerPort in enumerate(self.peers):
        	dilledMessage = dill.dumps(("prepare", (site.getIP(), site.getPort()), (proposal[0], maxPrepare, accNum, proposal[1])))
        	c = Client("", peerPort, dilledMessage)
        	asyncore.loop(timeout=5, count=1)

    # Connect to all peers send them <msg>
    def commit(self, proposal):
        # avoid connecting to self
        for index, peerPort in enumerate(self.peers):

            # if peerPort != int(sys.argv[1]) and len(site.getPorts()) == len(self.peers):
                # print "### Sending", msg, "to", peerPort
            dilledMessage = dill.dumps(proposal)
            # c = Client(self.ec2ips[index], peerPort, dilledMessage) # send <msg> to localhost at port 5555
            c = Client("", peerPort, dilledMessage)
            asyncore.loop(timeout=10,  count=1)
            # else:
            # 	nonBlockedPorts = site.getPorts()
            # 	check = (index in nonBlockedPorts)
            # 	if peerPort != int(sys.argv[1]) and len(nonBlockedPorts) > 0 and check:
            #		dilledMessage = dill.dumps(event)
            # 		c = Client(self.ec2ips[index], peerPort, dilledMessage) # send <msg> to localhost at port <peerPort>
            # 		asyncore.loop(timeout =5, count = 1)


class ServiceExit(Exception):
    """
    Custom exception which is used to trigger the clean exit
    of all running threads and the main program.
    """
    pass


def service_shutdown(signum, frame):
    print('Caught signal %d' % signum)
    raise ServiceExit


if __name__ == "__main__":

    """
    program usage:				-change to->
            arg 0: twitter.py (duh)							--> twitter.py
            arg 1: local port										--> local port
            arg 2: name													--> 'Alice'

            local port needs to match port of current EC2 instance
    """

    # Register the signal handlers
    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)

    # Create new threads
    # takes in raw_inputs and sends tweets to peers
    commandThread = myThread("commandThread")
    commandThread.setDaemon(True)
    # handles incoming connections from peers
    serverThread = myThread("serverThread")
    serverThread.setDaemon(True)

    # Try loading from pickle file
    allIds = None
    site = None
    # try:
    # 	# Create user from pickle
    # 	pickledWriteAheadLog = pickle.load( open( "pickledWriteAheadLog.p", "rb" ) )

    # 	print "pickledWriteAheadLog.p exists, loading into User"
    # 	allIds = commandThread.peers
    # 	site = User(sys.argv[2][0], allIds, pickledWriteAheadLog)
    # except IOError:
    # 	print "Site pickle doesn't exist. Creating user from scratch."
    # 	allIds = commandThread.peers
    # 	site = User(sys.argv[2][0], allIds, False, None)
    userId = ord(sys.argv[2][0]) - 65
    port = int(sys.argv[1])
    fileExt = str(userId) + ".p"
    pickledWriteAheadLog = None
    pickledCheckpoint = None

    try:
        # Try opening pickledWriteAheadLog file
        fileName = "pickledWriteAheadLog" + fileExt
        pickledWriteAheadLog = pickle.load(open(fileName, "rb"))
    except IOError:
        print "pickledWriteAheadLog file does not exist"

    try:
        # Try opening pickledCheckpoint file
        fileName = "pickledCheckpoint" + fileExt
        pickledCheckpoint = pickle.load(open(fileName, "rb"))
    except IOError:
        print "pickledCheckpoint file does not exist"

    allIds = commandThread.peers
    site = User(userId, allIds, pickledWriteAheadLog, pickledCheckpoint)

    # # Start new Threads
    commandThread.start()
    serverThread.start()

    # keep main thread alive
    while True:
        # print threading.activeCount()
        time.sleep(3)
