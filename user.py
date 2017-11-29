import socket
import time
import pickle

class User:

    def __init__(self, userId, peers, pickle=None, pickledUser=None):
        if pickle:
            # Load User from pickle
            self.stableStorageLog = pickledUser['stableStorageLog']
            self.blockedUsers = pickledUser['blockedUsers']
            self.userId = ord(userId) - 65
            self.peers = peers

            # Add events to (paxosLog and tweets) or queue and store last known empty log entry in paxosLog
            self.paxosLog = list()
            self.queue = list()
            self.tweets = list()
            self.index = 0
            for event in self.stableStorageLog:
                # Check if event has been committed
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
            self.stableStorageLog = list()
            self.paxosLog = list()
            self.queue = list()
            self.index = 0
            self.tweets = list()
            self.blockedUsers = list()
            self.userId = ord(userId) - 65
            self.peers = peers

    def pickleSelf(self):
        pickleSelf = {
            "stableStorageLog": self.stableStorageLog,
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
        Adds new eventRecord to stableStorageLog if it does not exist in the stableStorageLog already
        Adds new eventRecord to (paxosLog or queue) if it does not exist already based on committed
        Adds tweets if eventName is tweet and this User is being blocked by creator of tweet and tweet is not in tweets already
    @modifies
        stableStorageLog, paxosLog, queue, and tweets private fields
    @return 
        Newly created event record
    """
    def insertEvent(self, eventName, committed, message, id, time, index, maxPrepare, accNum, accVal):
        eventRecord = (eventName, committed, message, id, time, index, maxPrepare, accNum, accVal)        
        
        # Add eventRecord to stableStorageLog
        if(not (eventRecord in self.stableStorageLog)):
            self.stableStorageLog.append(eventRecord)
        # Update eventRecord in stableStorageLog
        else:
            for i in range(0, len(self.stableStorageLog)):
                # Check if current event is the eventRecord
                if(self.stableStorageLog[i][5] == index):
                    # Update committed field
                    self.stableStorageLog[i][1] = committed
                    break
        
        # Add eventRecord to paxosLog or queue
        if(committed):
            if(not (eventRecord in self.paxosLog)):
                # Check if paxosLog is empty
                if(len(self.paxosLog) == 0):
                    # Add event to paxosLog
                    self.paxosLog.append(eventRecord)
                # Check if paxosLog contains one element
                elif(len(self.paxosLog) == 1):
                    # Insert event to end of paxosLog
                    if(self.paxosLog[0][5] < index):
                        self.paxosLog.append(eventRecord)
                    # Insert event to beginning of paxosLog
                    else:  
                        self.paxosLog.insert(0, eventRecord)
                # Figure out where to insert event into paxosLog
                else:
                    index = -1
                    for i in range(0, len(self.paxosLog)) - 1:
                        if(self.paxosLog[i][5] < index and self.paxosLog[i+1][5] > index):
                            index = i
                            break
                    # Check if index was found to insert event into paxosLog
                    if(index > 0):
                        # Insert event in paxosLog as specified index
                        self.paxosLog.insert(index, eventRecord)
                    # Insert event to end of paxosLog
                    else:
                        self.paxosLog.append(eventRecord)

                # Add event to tweets
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
        If event exists in tweets, update committed status
        Else add event to tweets
    @modifies
        tweets private field
    """
    def insertTweet(self, event):
        # Check if event is a tweet and originator of tweet is not blocking this User
        if (event[0] == "tweet" and not (self.isBlocked(event[3], self.userId))):
            for i in range(0, len(self.tweets)):
                # Check if current event is the event
                if(self.tweets[i][5] == event[5]):
                    # Update committed field
                    self.tweets[i][1] = event[1]
                    break

        # Insert event into tweets since it was not previously added
        if(not (event in self.tweets)):
            # self.tweets.append(event)
            # Check if tweets is empty
            if (len(self.tweets) == 0):
                self.tweets.append(event)
            # Check if tweets contains one element
            elif(len(self.tweets) == 1):
                # Insert event to end of tweets
                if(self.tweets[0][5] < event[5]):
                    self.tweets.append(event)
                # Insert event to beginning of tweets
                else:
                    self.tweets.insert(0, event)
            # Figure out where to insert event into tweets
            else:
                index = -1
                for i in range(0, len(self.tweets)) - 1:
                    if(self.tweets[i][5] < index and self.tweets[i+1][5] > index):
                        index = i
                        break
                # Check if index was found to insert event into tweets
                if(index > 0):
                    # Insert event in tweets at specified index
                    self.tweets.insert(index, eventRecord)
                # Insert event to end of tweets
                else:
                    self.tweets.append(eventRecord)


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
        for tweet in self.tweets:
            print tweet

    """
    @effects 
        Prints all events in the stableStorageLog
    """
    def viewstableStorageLog(self):
        for event in self.stableStorageLog:
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
        Adds tweet to stableStorageLog, (paxosLog or queue), and tweets private fields if unique
    @modifies 
        stableStorageLog, (paxosLog or queue), and tweets private fields
    @return 
        Tweet event record
    """
    def tweet(self, commmitted, message, id, time, index, maxPrepare, accNum, accVal):
        # Add event to stableStorageLog, paxosLog, queue, and tweets if unique
        return self.insertEvent("tweet", commmitted, message, id, time, index, maxPrepare, accNum, accVal)

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
            # Check if there exists a blocked relationship where (id, receiver)
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
        Adds event to stableStorageLog, (paxosLog or queue) if unique
        Adds block relationship to dictionary if one does not exist already
    @modifies 
        stableStorageLog, (paxosLog or queue), and blockedUsers private field
    @return
        Block event record
    """
    def block(self, commmitted, receiver, id, time, index, maxPrepare, accNum, accVal):
        # Add event to stableStorageLog and paxosLog if unique
        event = self.insertEvent("block", commmitted, receiver, id, time, index, maxPrepare, accNum, accVal)

        # Add block to dictionary if it does not exist already
        if(not (self.isBlocked(id, receiver))):
            self.blockedUsers.append((id, receiver))

            # Remove all tweets from this User's tweets if they have been revoked access to view
            if(receiver == self.userId):
                for i in range(0, len(self.tweets)):
                    # Check if tweet's creator equals id
                    if(self.tweets[i][3] == id):
                        # Delete tweet from tweets
                        del self.tweets[i]

        # Update dictionary
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
        Adds event to stableStorageLog and (paxosLog or queue) if unique
        Removes blocked relationship from dictionary if one exists
    @modifies
        stableStorageLog, (paxosLog or queue), and blockedUsers private fields
    @return
        Unblock event record
    """
    def unblock(self, commmitted, receiver, id, time, index, maxPrepare, accNum, accVal):
        # Add event to stableStorageLog and paxosLog if unique
        event = self.insertEvent("unblock", commmitted, receiver, id, time, index, maxPrepare, accNum, accVal)

        # Delete blocked relationship from dictionary if it exists
        if (self.isBlocked(id, receiver)):
            for i in range(0, len(self.blockedUsers)):
                # Check if there exists a blocked relationship (id, receiver)
                if(self.blockedUsers[i][0] == id and self.blockedUsers[i][1] == receiver):
                    # Delete blocked relationship from dictionary
                    del self.blockedUsers[i]
                    break

        # Set dictionary to new list if no blocked relationships exist
        if(len(self.blockedUsers) == 0):
            self.blockedUsers = list()

            # Add all tweets from this User's paxosLog if they have been given access to view
            if(receiver == self.userId):
                for event in self.paxosLog:
                    # Check if tweet's creator equals id and if event is a tweet
                    if(event[3] == id and event[0] == "tweet"):
                        # Add tweet to tweets
                        self.tweets.append(event)

        # Update dictionary
        self.pickleSelf()

        return event

    """
    @param
        index: Index some proposer wishes to write an event to in paxosLog
        n: Proposal number from a proposer
    @effects
        Checks if User has accepted some proposal with number and value based on index
    @modifies
        stableStorageLog and queue private fields
    @return
        If the User has accepted some number and value, that proposal will be returned given n is greater than maxPrepare
        Else (None, None)
    """
    def prepare(self, index, n):
        for i in range(0, len(self.queue)):
            # Check if event has been accepted and proposal number exceeds maxPrepare based on index
            if(self.queue[i][5] == index and n > self.queue[i][6]):
                # Update maxPrepare for proposal in stableStorageLog
                for i in range(0, len(self.stableStorageLog)):
                    # Check if current event is the event
                    if(self.stableStorageLog[i][5] == index):
                        # Update maxPrepare
                        self.stableStorageLog[i][6] = n
                        break

                # Update stable storage
                self.pickleSelf()

                # Update maxPrepare for proposal in queue
                for i in range(0, len(self.queue)):
                    # Check if current event is the event
                    if(self.queue[i][5] == index):
                        # Update maxPrepare
                        self.queue[i][6] = n
                        break

                # Highest proposal less than n that this User has accepted
                return (event[7], event[8])

        # This User has not accepted any proposal for such index
        return (None, None)

    """
    @param
        index: Index some proposer wishes to write an event to in paxosLog
        n: Proposal number from a proposer
        v: Proposal value from a proposer
    @effets
        Modifies proposal in stableStorageLog and queue with n and v based on index
    @modifies
        stableStorageLog and queue private fields
    """
    def accept(self, index, n, v):
        for i in range(0, len(self.stableStorageLog)):
            # Check if current event is the event
            if(self.stableStorageLog[i][5] == index):
                # Update accNum and accVal
                self.stableStorageLog[7] = n
                self.stableStorageLog[8] = v
                break

        # Update stable storage
        self.pickleSelf()

        for i in range(0, len(self.queue)):
            # Check if current event is the event
            if(self.queue[i][5] == index):
                # Update accNum and accVal
                self.queue[7] = n
                self.queue[8] = v
                break

        # Update dictionary
        self.pickleSelf()


    """
    @param
        event: Event that accepted by a majority of acceptors
    @effects
        Increments last known empty log entry in paxosLog
        Adds event to stableStorageLog and paxosLog
        Removes event from queue
        Adds tweet to tweets if
        Updates dictionary based on block and unblock events
    @modifies 
        index, stableStorageLog, paxosLog, queue, tweets, and dictionary private fields
    """
    def commit(self, event):
        # Add event to paxosLog, and (tweets or dictionary)
        # Update event in stableStorageLog
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