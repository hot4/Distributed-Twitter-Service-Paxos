import socket
import time
import pickle

class User:

    def __init__(self, userId, peers, pickle=None, pickledUser=None):
        if pickle:
            # Load User from pickle
            self.timelineLog = pickledUser['timelineLog']
            self.blockedUsers = pickledUser['blockedUsers']
            self.userId = ord(userId) - 65
            self.peers = peers

            # Add events to (paxosLog and tweets) or queue and store last known empty log entry in paxosLog
            self.paxosLog = list()
            self.queue = list()
            self.tweets = list()
            self.index = 0
            for event in self.timelineLog:
                if (event[1]):
                    # Add events to paxosLog and tweets
                    self.paxosLog.append(event)
                    self.insertTweet(event)

                    # Store the max index being stored in paxosLog
                    self.index = max(self.index, event[5])
                else:
                    self.queue.append(event)

            # Increment index to signal last known empty log entry in paxosLog
            self.index = self.index+1

        else:
            # Create User from scratch
            print "Creating user from scratch"
            self.timelineLog = list()
            self.paxosLog = list()
            self.queue = list()
            self.index = 0
            self.tweets = list()
            self.blockedUsers = list()
            self.userId = ord(userId) - 65
            self.peers = peers

    def pickleSelf(self):
        pickleSelf = {
            "timelineLog": self.timelineLog,
            "blockedUsers": self.blockedUsers
        }
        pickle.dump(pickleSelf, open("pickledUser.p", "wb"))

    """
    @param 
        eventName: Name of event 
        committed: Boolean which indicated if the event was committed to paxosLog
        message: The body of a tweet, or the username of who was blocked or unblocked
        id: User who created event
        time: UTC time
        index: Index where event is added to paxosLog
        maxPrepare: Max prepare value User promised to not respond to lower values
        accNum: Accepted number for event
        accVal: Accepted value for event
    @effects
        Adds new eventRecord to timelineLog if it does not exist in the timelineLog already
        Adds new eventRecord to (paxosLog or queue) if it does not exist already based on committed
        Adds tweets if eventName is tweet and this User is being blocked by creator of tweet and tweet is not in tweets already
    @modifies
        timelineLog, paxosLog, queue, and tweets private fields
    @return 
        Newly created event record
    """
    def insertEvent(self, eventName, committed, message, id, time, index, maxPrepare, accNum, accVal):
        eventRecord = (eventName, committed, message, id, time, index, maxPrepare, accNum, accVal)        
        
        # Add eventRecord to timelineLog
        if(not (eventRecord in self.timelineLog)):
            self.timelineLog.append(eventRecord)
        # Update eventRecord in timelineLog
        else:
            for i in range(0, len(self.timelineLog)):
                if(self.timelineLog[i][5] == index):
                    self.timelineLog[i][1] = committed
        
        # Add eventRecord to paxosLog or queue
        if(committed):
            if(not (eventRecord in self.paxosLog)):
                # Add event to paxosLog and tweets
                self.paxosLog.append(eventRecord)
                self.insertTweet(eventRecord)
        else:
            if(not (eventRecord in self.queue)):
                # Add event to queue
                self.queue.append(eventRecord)
        

        self.pickleSelf()

        return eventRecord

    """
    @param
        event: Event that has occurred by some User
    @effects
        Adds event to tweets if eventName is tweet and this User is being blocked by creator of tweet and tweet is not in tweets already
    """
    def insertTweet(self, event):
        if (event[0] == "tweet" and not (self.isBlocked(event[3], self.userId)) and not (event in self.tweets)):
            self.tweets.append(event)

    """
    @return
        Private field index
    """
    def getIndex(self):
        return self.index

    """
    @return 
        Private field peers
    """
    def getPorts(self):
        return self.peers

    """
    @return
        Private field userId
    """
    def getId(self):
        return self.userId

    """
    @effects 
        Prints all tweets in tweets
    """
    def view(self):
        print "View command was selected\n"
        for tweet in self.tweets:
            print tweet

    """
    @effects 
        Prints all events in the timelineLog
    """
    def viewTimelineLog(self):
        for event in self.timelineLog:
            print event

    """
    @effects
        Prints all events in the paxosLog
    """
    def viewPaxosLog(self):
        for event in self.paxosLog:
            print event

    """
    @effects
        Prints all blocks in the dictionary
    """
    def viewDictionary(self):   
        for block in self.blockedUsers:
            print block

    """
    @param
        eventName: Name of event 
        committed: Boolean which indicated if the event was committed to paxosLog
        message: The body of a tweet
        id: User who created event
        time: UTC time
        index: Index where event is added to paxosLog
        maxPrepare: Max prepare value User promised to not respond to lower values
        accNum: Accepted number for event
        accVal: Accepted value for event
    @effects 
        Adds tweet to timelineLog, (paxosLog or queue), and tweets private fields if unique
    @modifies 
        timelineLog, (paxosLog or queue), and tweets private fields
    @return 
        Tweet event record
    """
    def tweet(self, commmitted, message, id, time, index, maxPrepare, accNum, accVal):
        # Add event to timelineLog, paxosLog, queue, and tweets if unique
        event = self.insertEvent("tweet", commmitted, message, id, time, index, maxPrepare, accNum, accVal)
        return event

    """
    @param
        id: User who blocked receiver
        receiver: User who is being blocked by id
    @effects 
        Checks whether a block exists between id and receiver
    @return
        True if a block exists between id and receiver, false otherwise
    """
    def isBlocked(self, id, receiver):
        for i in range(0, len(self.blockedUsers)):
            if(self.blockedUsers[i][0] == id and self.blockedUsers[i][1] == receiver):
                return True
        return False

    """
    @param
        eventName: Name of event 
        committed: Boolean which indicated if the event was committed to paxosLog
        receiver: The username of who was blocked or unblocked
        id: User who created event
        time: UTC time
        index: Index where event is added to paxosLog
        maxPrepare: Max prepare value User promised to not respond to lower values
        accNum: Accepted number for event
        accVal: Accepted value for event
    @effects 
        Adds event to timelineLog, (paxosLog or queue) if unique
        Adds block relationship to dictionary if one does not exist already
    @modifies 
        timelineLog, (paxosLog or queue), and blockedUsers private field
    @return
        Block event record
    """
    def block(self, commmitted, receiver, id, time, index, maxPrepare, accNum, accVal):
        # Add event to timelineLog and paxosLog if unique
        event = self.insertEvent("block", commmitted, receiver, id, time, index, maxPrepare, accNum, accVal)

        # Add block to dictionary if it does not exist already
        if(not (self.isBlocked(id, receiver))):
            self.blockedUsers.append((id, receiver))

            # Remove all tweets from this User's tweets if they have been revoked access to view
            if(receiver == self.userId):
                for i in range(0, len(self.tweets)):
                    if(self.tweets[i][3] == id):
                        del self.tweets[i]

        self.pickleSelf()

        return event

    """
    @param
        eventName: Name of event 
        committed: Boolean which indicated if the event was committed to paxosLog
        receiver: The body of a tweet, or the username of who was blocked or unblocked
        id: User who created event
        time: UTC time
        index: Index where event is added to paxosLog
        maxPrepare: Max prepare value User promised to not respond to lower values
        accNum: Accepted number for event
        accVal: Accepted value for event
    @effects
        Adds event to timelineLog and (paxosLog or queue) if unique
        Removes blocked relationship from dictionary if one exists
    @modifies
        timelineLog, (paxosLog or queue), and blockedUsers private fields
    @return
        Unblock event record
    """
    def unblock(self, commmitted, receiver, id, time, index, maxPrepare, accNum, accVal):
        # Add event to timelineLog and paxosLog if unique
        event = self.insertEvent("unblock", commmitted, receiver, id, time, index, maxPrepare, accNum, accVal)

        # Delete blocked relationship from dictionary if it exists
        if (self.isBlocked(id, receiver)):
            for i in range(0, len(self.blockedUsers)):
                if(self.blockedUsers[i][0] == id and self.blockedUsers[i][1] == receiver):
                    del self.blockedUsers[i]
                    break

        # Set dictionary to new list if no blocked relationships exist
        if(len(self.blockedUsers) == 0):
            self.blockedUsers = list()

            # Add all tweets from this User's paxosLog if they have been given access to view
            if(receiver == self.userId):
                for event in self.paxosLog:
                    if(event[3] == id and event[0] == "tweet"):
                        self.tweets.append(event)

        self.pickleSelf()

        return event

    """
    @param
        index: Index some proposer wishes to write an event to in paxosLog
        n: Proposal number from a proposer
        v: Proposal value from a proposer
        container: Container of events
    @effects
        Modifies proposal in list with n and v based on index
    """
    def updateProposal(self, index, n, v, container):
        for i in range(0, len(container)):
            # Check if event should be updated with (n, v) if n is greater than or equal to maxPrepare of proposal based on index
            if(container[i][5] == index and n >= container[6]):
                # Update maxPrepare of proposal
                container[i][6] = n
                # Update accNum of proposal
                container[i][7] = n
                # Update accVal of proposal
                if(not (v == None)):
                    container[i][8] = v

    """
    @param
        index: Index some proposer wishes to write an event to in paxosLog
        n: Proposal number from a proposer
    @effects
        Checks if User has accepted some proposal with number and value based on index
    @return
        If the User has accepted some number and value, that proposal will be returned given n is greater than maxPrepare
        Else (None, None)
    """
    def prepare(self, index, n):
        for i in range(0, len(self.queue)):
            # Check if event has been accepted and proposal number exceeds maxPrepare based on index
            if(self.queue[i][5] == index and n > self.queue[i][6]):
                # Update maxPrepare for proposal
                self.updateProposal(index, n, None, self.timelineLog)
                self.updateProposal(index, n,  None, self.queue)
                return (event[7], event[8])
        return (None, None)

    """
    @param
        index: Index some proposer wishes to write an event to in paxosLog
        n: Proposal number from a proposer
        v: Proposal value from a proposer
    @effets
        Modifies proposal in timelineLog and queue with n and v based on index
    @modifies
        timelineLog and queue private fields
    """
    def accept(self, index, n, v):
        self.updateProposal(index, n, v, self.timelineLog)
        self.updateProposal(index, n, v, self.queue)

    """
    @param
        event: Event that accepted by a majority of acceptors
    @effects
        Increments last known empty log entry in paxosLog
        Adds event to timelineLog and paxosLog
        Removes event from queue
        Adds tweet to tweets if
        Updates dictionary based on block and unblock events
    @modifies 
        index, timelineLog, paxosLog, queue, tweets, and dictionary private fields
    """
    def commit(self, event):
        # Add event to paxosLog, and (tweets or dictionary)
        # Update event in timelineLog
        # Event: (eventName, commmitted, message, id, time, index, maxPrepare, accNum, accVal)
        if (event[0] == "tweet"):
            print "Committed tweet event!"
            # Add tweet to paxosLog, and tweets
            self.tweet(True, event[2], event[3], event[4], event[5], event[6], event[7], event[8])
        if(event[0] == "block"):
            print "Committed block event!"
            # Add block to paxosLog, and dictionary
            self.block(True, event[2], event[3], event[4], event[5], event[6], event[7], event[8])
        if(event[0] == "unblock"):
            print "Committed unblock event!"
            # Add unblock to paxosLog, and remove from dictionary
            self.unblock(True, event[2], event[3], event[4], event[5], event[6], event[7], event[8])

        # Index is either the increment of this User's index or event's index value
        self.index = max(self.index+1, event[5]+1)

        # Delete event from queue since it has been stored in paxosLog
        for i in range(0, len(self.queue)):
            if(self.queue[i][5] == event[5]):
                del self.queue[i]