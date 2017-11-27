import socket
import time
import pickle

class User:
    # eventLog = list()
    # eventCounter = 0;
    # blockedUsers = list()
    # maxtrixClock = list()
    # peers = list()
    # userId = 0


    """""
     This is the constructor for the User class. A User corresponds to a site.
     @param int,list[int],int
    """""
    def __init__(self, userId, peers, pickle=None, pickledUser=None):
        if pickle:
            # Load User from pickle
            self.eventLog = pickledUser['eventLog']
            self.eventCounter = pickledUser['eventCounter']
            self.blockedUsers = pickledUser['blockedUsers']
            self.matrixClock = pickledUser['matrixClock']
            self.peers = peers
            self.userId = ord(userId) - 65
        else:
            print 'creating user from scratch'
            # Create User from scratch
            self.eventLog = list()
            self.eventCounter = 0
            self.blockedUsers = list()
            self.matrixClock = list()
            self.peers = list()
            self.peers = peers
            self.userId = ord(userId) - 65

            #Initilize matrixClock to all zero values
            for i in range(0,len(self.peers)):
                newList = list()
                for j in range(0,len(self.peers)):
                    newList.append(0)
                self.matrixClock.append(newList)

    def printself(self):
        print self.eventLog, self.eventCounter, self.blockedUsers, self.matrixClock, self.peers, self.userId


    def pickleSelf(self):
        pickledSelf = {
            "eventLog": self.eventLog,
            "eventCounter": self.eventCounter,
            "blockedUsers": self.blockedUsers,
            "matrixClock": self.matrixClock
        }
        pickle.dump( pickledSelf, open( "pickledUser.p", "wb" ) )
        # self.printself()


    """
    Checks if a matrixClock contains a timestamp larger than what's in the eventRecord.
    @param tuple,int
        -eventRecord is a tuple containing eventName, message of event, timestamp, userId, and UTC time
    @return
        returns true or false depending on if the receiver has already been updated with the given event/
        If true is returned, then, the process knows the most recent event.
        If fals is returned the process does not know the most recent event
    """
    def hasRec(self,receivedClock,eventRecord,receiver):
        return receivedClock[receiver][eventRecord[3]] >= eventRecord[2]
        self.pickleSelf()


    """""
    @param String, String, int
        -eventName will either be "tweet","block","unblock"
        -message contains a String that consists of the body of a tweet, or an empty
        String for block or unblock
        -time contains the timestamp of the event to be stored
    @modifies
        eventCounter increases by one
        matrixClock is updated at the indices of the userId
        eventLog has a new eventRecord added to it
    @return
        returns a tuple containing :
        [0] -> eventName
        [1] -> message of event
        [2] -> timestamp
        [3] -> userId
        [4] -> UTC time
    """""
    def insertion(self,eventName,message,time):
        self.eventCounter += 1
        self.matrixClock[self.userId][self.userId] = self.eventCounter
        eventRecord = (eventName,message,self.eventCounter,self.userId,time)

        self.eventLog.append(eventRecord)
        self.pickleSelf()
        return eventRecord


    """"
    @param
        message: a message will come in form of a string
        time:  UTC time
    @modifies:
        Will modify matrixClock, eventLog. Will send out a message depending
        on what values are not in the blockedUsers list
    @return
        returns a list containg the following:
            [0] -> the sender's userID
            [1] -> the sender's matrixClock
            [2] -> a list containing all the eventRecords
    """
    def tweet(self,message,time):

        eventRecord = self.insertion("tweet",message,time)
        self.pickleSelf()
        return eventRecord

    def send(self,message,receiver):
        receiverId = (receiver/1111) - 1
        NP = list()
        for i in range(0,len(self.eventLog)):
            pastEvent = self.eventLog[i]
            mc = self.matrixClock
            checkReceived = self.hasRec(mc,pastEvent,receiverId)
            if(not (checkReceived)):
                NP.append(pastEvent)
        self.pickleSelf()
        # self.printself()
        return (message,self.matrixClock,NP)


    """"
    The block function will not allow the specificed receiver to recieve
    any tweets from this local User.
    @param
        time:  UTC time
        receiver: the site that will be blocked
    @modifies:
        Will modify matrixClock, eventLog since a new event will be occuring.
        Will also modify blockedIds and append a new block; unless that block already
        exists.
    @return
        returns nothing
    """
    def block(self,time,receiver):
        blocked = False
        eventRecord = self.insertion("block",receiver,time)
        ### add truncation code here for log
        for i in range(0,len(self.blockedUsers)):
            if(self.blockedUsers[i][0] == self.userId and self.blockedUsers[i][1] == receiver):
                blocked = True
        if(not (blocked)):
            self.blockedUsers.append((self.userId,receiver))
        
        self.pickleSelf()

    """"
    The unblock function will allow the specificed user to receive the local
    Users tweets.
    @param
        time:  UTC time
        receiver: the site that will be unblocked
    @modifies:
        Will modify matrixClock, eventLog since a new event will be occuring.
        Will also modify blockedIds and delete a block; unless that block does
        not exist
    @return
        returns nothing
    """
    def unblock(self,time,receiver):
        print "Unblocked User %d" % (receiver)
        for i in range(0,len(self.blockedUsers)):
            if(self.blockedUsers[i][0] == self.userId and self.blockedUsers[i][1] == receiver):
                del self.blockedUsers[i]
                break

        if(len(self.blockedUsers) == 0):
            self.blockedUsers = list()
        eventRecord = self.insertion("unblock",receiver,time)
        self.pickleSelf()


    def view(self):
        print "View command selected \n"
        acceptableTweets = list()
        for i in range(0,len(self.eventLog)):
            currentEvent = self.eventLog[i]
            eventType = currentEvent[0]
            eventCreator =  currentEvent[3]

            if(len(self.blockedUsers) > 0):
                if(eventType == "tweet"):
                    blocked = False
                    for j in range(0,len(self.blockedUsers)):
                        if(((self.blockedUsers[j][0] == eventCreator) and (self.blockedUsers[j][1] == self.userId))):
                            blocked = True
                            break
                    if not blocked:
                        acceptableTweets.append(currentEvent)
            else:
                if(eventType == "tweet"):
                    acceptableTweets.append(currentEvent)
        
        acceptableTweets = sorted(acceptableTweets, key=lambda event: event[4])
        for tweet in acceptableTweets:
            print tweet
        self.pickleSelf()

    def receive(self,message,receivedClock,receivedNP):
        #sentID = -1
        # for k in range(0,len(self.peers)):
        #     if(self.peers[k] == sendAddress):
        #         self.siteID = self.peers[k]
        NE = list()
        for i in range(0,len(receivedNP)):
            pastEvent = receivedNP[i]
            if(not (self.hasRec(self.matrixClock,pastEvent,self.userId))):
                NE.append(pastEvent)
        
        ##now we truncate the received log before moving forward to insert values into the dictionary
        #This loop updates the local dictionary depending on what was in the received dictionary
        allBlockingEvents = list()
        for i in range(0,len(NE)):
            blockEvent = NE[i][0]
            blockReceiver = NE[i][1]
            receiverId = NE[i][3]
            if(blockEvent == "block"):
                print "received block event!"
                self.blockedUsers.append((receiverId,blockReceiver))
            if(blockEvent == "unblock"):
                print "Received unblock event!"
                for j in range(0,len(self.blockedUsers)):
                    # print receiverId
                    # print blockReceiver
                    if(self.blockedUsers[j][0] == receiverId and self.blockedUsers[j][1] == blockReceiver):
                        print "Getting rid of blocked event!"
                        del self.blockedUsers[j]
                        break
        if(len(self.blockedUsers) == 0):
            self.blockedUsers = list()


        #The first item in the received message contains the ID of the sender
        sender = message[3]
        fullUnion = self.eventLog + NE
        # print self.matrixClock
        for k in range(0,len(self.peers)):
            if self.matrixClock[self.userId][k] > receivedClock[sender][k]:
                # print "redundant"
                self.matrixClock[self.userId][k] = self.matrixClock[self.userId][k]
            else:
                # print "extra"
                # print receivedClock
                # print sender
                self.matrixClock[self.userId][k] = receivedClock[sender][k]

        clearedLog = list()
        #the combination of k and l will correctly update the matrixClock
        for k in range(0,len(self.peers)):
            for l in range(0,len(self.peers)):
                self.matrixClock[k][l] = max(self.matrixClock[k][l],receivedClock[k][l])


        #the m loop goes through the fullUnion of the partialLog and eventRecord
        #the loop checks for all relevant partialLog options


        for m in range(0,len(fullUnion)):
            currentRecord = fullUnion[m]
            for k in range(0,len(self.peers)):
                if(not self.hasRec(self.matrixClock,currentRecord,k)):
                    clearedLog.append(currentRecord)
                    break


        #the eventLog changes to this filled once clearedLog
        self.eventLog = clearedLog
        self.pickleSelf()

    def nonBlockedPorts(self):
        nonBlocked = set()
        for i in range(0,len(self.peers)):
            nonBlocked.add(i)

        blocked = set()
        for i in range(0,len(self.blockedUsers)):

            for j in range(0,len(self.peers)):
                if self.blockedUsers[i][0] == self.userId and self.blockedUsers[i][1] == j:
                    blocked.add(j)
        nonBlocked = nonBlocked - blocked
        self.pickleSelf()
        return nonBlocked

    def viewMatrixClock(self):
        for i in range(0,len(self.matrixClock)):
            print self.matrixClock[i]

    def viewPartialLog(self):
        for i in range(0,len(self.eventLog)):
            print self.eventLog[i]

    def viewDictonary(self):
        for i in range(0,len(self.blockedUsers)):
            print self.blockedUsers[i]

