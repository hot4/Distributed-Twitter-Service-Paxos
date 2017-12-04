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
import select
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

			# serializedMessage --> (flagString, id|IP|PORT, proposal)
			# Check if prepare
			if(serializedMessage[0] == "prepare"):
				self.prepare(serializedMessage)
				

			# serializedMessage --> (flagString, id|IP|PORT, proposal, promise)
			# promise --> (index, accNum, accVal)
			# Check if promise
			if(serializedMessage[0] == "promise" and site.getId() == serializedMessage[1][0]):
				self.promise(serializedMessage)


			# serializedMessage --> (flagString, id|IP|PORT, proposal)
			# Check if accept
			if(serializedMessage[0] == "accept"):
				self.accept(serializedMessage)

			# serializedMessage --> (flagString, id|IP|PORT, proposal)
			# Check if ack
			if(serializedMessage[0] == "ack"):
				self.ack(serializedMessage)

			# serializedMessage --> (flagString, id|IP|PORT, proposal)
			# Check if commit
			if(serializedMessage[0] == "commit"):
				self.commit(serializedMessage)

	"""
    @effects
    	Creates a string timestamp
    @return
		timestamp
    """
	def timeStamp(self):
		utcDatetime = datetime.datetime.utcnow()
		return utcDatetime.strftime(site.getFormat())

	def prepare(self, serializedMessage):
    	# serializedMessage --> (flagString, id|IP|PORT, proposal)
		# proposal --> (index, n, event)
		# print "Recevied prepare message ", serializedMessage[2], " from ", serializedMessage[1]
		promise = site.prepare(serializedMessage[2][0], serializedMessage[2][1])

		# promise --> (index, accNum, accVal)
		# Check if promise is None
		if(promise == None):
			print serializedMessage[2][1], " does not exceed maxPrepare value. ", site.getId(), " cannot promise."
		else:
			# Send to proposer
			dilledMessage = dill.dumps(("promise", serializedMessage[1], serializedMessage[2], promise))
			for index, peerPort in enumerate(site.getPorts()):
				# Check if peerPort matches the sender
				if(peerPort == serializedMessage[1][2]):
					c = Client(ec2ips_[index], peerPort, dilledMessage)
					asyncore.loop(timeout=5, count=1)

	def promise(self, serializedMessage):
		# serializedMessage --> (flagString, id|IP|PORT, proposal, promise)
		# proposal --> (index, n, event)
		print "Received promise message ", serializedMessage[3]

		# Check if a majority already exists for index
		if(site.checkPromiseMajority(serializedMessage[3][0])):
			print "Majority of promises have already been recevied at ", serializedMessage[3][0]
		else:
			# Add promise for index
			site.addPromise(serializedMessage[3])

			# Check if a majority has been reached
			if(site.checkPromiseMajority(serializedMessage[3][0])):
				print "Majority of promises have been received at ", serializedMessage[3][0]
				
				# Get the subset of promises at index
				promised = site.removePromises(serializedMessage[3][0])

				# Get highest accepted proposal at index
				highVal = site.filterPromises(promised)

				# highVal --> accVal
				# Check if highVal is None
				if(highVal == None):
					# This User can propose it's own value
					highVal = serializedMessage[2][2]
				
				proposal = (serializedMessage[2][0], serializedMessage[2][1], highVal)

				# Set new timeout timestamp
				timeStamp = self.timeStamp()
				site.setProposeTimeout((timeStamp, (proposal[0], proposal[1], proposal[2])))

				# Broadcast to all sites
				dilledMessage = dill.dumps(("accept", serializedMessage[1], proposal))
				for index, peerPort in enumerate(site.getPorts()):
					c = Client(ec2ips_[index], peerPort, dilledMessage)
					asyncore.loop(timeout=5, count=1)

	def accept(self, serializedMessage):
		# serializedMessage --> (flagString, id|IP|PORT, proposal)
		# proposal --> (index, n, accVal)
		print "Received accept message ", serializedMessage[2], " from ", serializedMessage[1]
		ack = site.accept(serializedMessage[2][0], serializedMessage[2][1], serializedMessage[2][2])

		# ack --> (index, accNum, accVal)
		# Check if ack is None
		if(ack == None):
			print serializedMessage[2][1], " does not exceed maxPrepare value. ", site.getId(), " cannot accept."
		else:
			# Send to proposer
			dilledMessage = dill.dumps(("ack", serializedMessage[1], ack))
			for index, peerPort in enumerate(site.getPorts()):
				# Check if peerPort matches the sender
				if(peerPort == serializedMessage[1][2]):
					c = Client(ec2ips_[index], peerPort, dilledMessage)
					asyncore.loop(timeout=5, count=1)

	def ack(self, serializedMessage):
		# serializedMessage --> (flagString, id|IP|PORT, proposal)
		# proposal --> (index, n, accVal)
		print "Received ack message ", serializedMessage[2]

		# Check if a majority already exists for index
		if(site.checkAckMajority(serializedMessage[2][0])):
			print "Majority of ack have already been recevied at ", serializedMessage[2][0]
		else:
            # Adding ack
			site.addAck(serializedMessage[2])

			# Check if a majority has been reached
			if(site.checkAckMajority(serializedMessage[2][0])):
				print "Majority of ack have been received at ", serializedMessage[2][0]

				site.removeAcks(serializedMessage[2][0])

				proposal = (serializedMessage[2][0], serializedMessage[2][2])

				# Broadcast to all sites
				dilledMessage = dill.dumps(("commit", serializedMessage[1], proposal))
				for index, peerPort in enumerate(site.getPorts()):
					c = Client(ec2ips_[index], peerPort, dilledMessage)
					asyncore.loop(timeout=5, count=1)

	def commit(self, serializedMessage):
		# serializedMessage --> (flagString, id|IP|PORT, proposal)
		# proposal --> (index, accVal)
		print "Received commit message ", serializedMessage[2]

		site.commit(serializedMessage[2])


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
        	prompt = False
        	# print "\nPlesase enter a command: "
        	while 1:
        		# Check if this User has already been prompted
        		if(not prompt):
        			print "\nPlesase enter a command: "
        			prompt = True

        		# Read from standard input
        		while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
        			prompt = False
        			command = sys.stdin.readline()
    				if(command[:5] == "tweet"):
    					print "Message: ", command[6:]
    					timeStamp = self.timeStamp()
    					proposal = (site.getIndex(), ("tweet", command[6:], site.getId(), timeStamp))
    					self.prepare(site.getId(), timeStamp, proposal)
    				elif(command[:5] == "block"):
    					print "Blocked: ", command[6:]
    					timeStamp = self.timeStamp()
    					proposal = (site.getIndex(), ("block", ord(command[6]) - 64, site.getId(), timeStamp))
    					self.prepare(site.getId(), timeStamp, proposal)
    				elif(command[:7] == "unblock"):
    					print "Unblocked: ", command[8:]
    					timeStamp =  self.timeStamp()
    					proposal = (site.getIndex(), ("unblock", ord(command[8]) - 64, site.getId(), timeStamp))
    					self.prepare(site.getId(), timeStamp, proposal)
    				elif(command[:4] == "View"):
    					site.view()
    				elif(command[:3] == "Log"):
    					site.viewWriteAheadLog()
    				elif(command[:10] == "Dictionary"):
    					site.viewDictionary()
    				elif(command[:4] == quit):
    					self.shutdown_flag = True
    					raise KeyboardInterrupt
    					self.shutdown_flag = True
    				else:
    					print "Unknown command %s:( Try again." % (command)

        		if(len(site.getProposeTimeout()) != 0):
        			# proposeTimeout[i] --> (time, proposal)
        			# proposal --> (index, n, event)
        			proposeTimeout = site.getProposeTimeout()
        			timeStamp = self.timeStamp()
        			for i in range(0, len(proposeTimeout)):
        				# Check if proposal has been timedout
        				if(self.amountSeconds(self.stringToTimeStamp(timeStamp), self.stringToTimeStamp(proposeTimeout[i][0])) > 5):
        					# Check if a majority has not been received
        					if (not (site.checkPromiseMajority(proposeTimeout[i][1][0]) or site.checkAckMajority(proposeTimeout[i][1][0]))):
        						# Clear out promises/ack that have been received at index
        						site.removePromises(proposeTimeout[i][1][0])
        						site.removeAcks(proposeTimeout[i][1][0])

	        					self.prepare(proposeTimeout[i][1][1]+len(site.getPorts()), timeStamp, (proposeTimeout[i][1][0], proposeTimeout[i][1][2]))

        # Start the server the listening for incoming connections
        elif self.name == 'serverThread':
            server = Server('0.0.0.0', int(sys.argv[1]))
            if self.shutdown_flag != True:
                asyncore.loop()

    """
    @effects
    	Creates a string timestamp
    @return
		timestamp
    """
    def timeStamp(self):
    	utcDatetime = datetime.datetime.utcnow()
    	return utcDatetime.strftime(site.getFormat())
    	
    """
    @effects
    	Converts string timestamp into datetime
    @return
    	datetime timestamp
    """
    def stringToTimeStamp(self, time):
    	return datetime.datetime.strptime(time, site.getFormat())

    """
    @param
    	current: Current timestamp
    	past: Previous timestamp
    @effects
    	Calculates the amount of seconds between current and past
    @return
    	Amount of seconds between current and past
    """
    def amountSeconds(self, current, past):
		return datetime.timedelta.total_seconds(current - past)    	

    def prepare(self, n, timestamp, proposal):
    	# proposal --> (index, event)
        # event --> (eventName, message, id, time)
    	print site.getId(), " is proposing ", proposal, " to be committed at index ", proposal[0], " with n = ", n

    	# Begin timeout
        site.setProposeTimeout((timestamp, (proposal[0], n, proposal[1])))

        # Broadcast to all sites
        for index, peerPort in enumerate(self.peers):
        	dilledMessage = dill.dumps(("prepare", (site.getId(), site.getIP(), site.getPort()), (proposal[0], n, proposal[1])))
        	c = Client(ec2ips_[index], peerPort, dilledMessage)
        	asyncore.loop(timeout=5, count=1)

    # # Connect to all peers send them <msg>
    # def commit(self, proposal):
    #     # avoid connecting to self
    #     for index, peerPort in enumerate(self.peers):

    #         # if peerPort != int(sys.argv[1]) and len(site.getPorts()) == len(self.peers):
    #             # print "### Sending", msg, "to", peerPort
    #         dilledMessage = dill.dumps(proposal)
    #         # c = Client(self.ec2ips_[index], peerPort, dilledMessage) # send <msg> to localhost at port 5555
    #         c = Client(self.ec2ips_[index], peerPort, dilledMessage)
    #         asyncore.loop(timeout=10,  count=1)
    #         # else:
    #         # 	nonBlockedPorts = site.getPorts()
    #         # 	check = (index in nonBlockedPorts)
    #         # 	if peerPort != int(sys.argv[1]) and len(nonBlockedPorts) > 0 and check:
    #         #		dilledMessage = dill.dumps(event)
    #         # 		c = Client(self.ec2ips_[index], peerPort, dilledMessage) # send <msg> to localhost at port <peerPort>
    #         # 		asyncore.loop(timeout =5, count = 1)


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
    userId = ord(sys.argv[2][0]) - 64
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
