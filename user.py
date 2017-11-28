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

            # Add all committed (true attribute) events into paxosLog
            self.paxosLog = list()
            for event in self.timelineLog:
                if (event[1]):
                    self.paxosLog.append(event)

            self.tweets = list()
            for event in self.timelineLog:
                self.insertTweet(event)

        else:
            # Create User from scratch
            print "Creating user from scratch"
            self.timelineLog = list()
            self.paxosLog = list()
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
        message: The body of a tweet, or the username of who was blocked or unblocked
        id: User who created event
        time: UTC time
    @effects
        Adds new eventRecord to timelineLog if it does not exist in the timelineLog already
        Adds tweets if eventName is tweet and this User is being blocked by creator of tweet and tweet is not in tweets already
    @modifies
        timelineLog and tweets private fields
    @return 
        Newly created event record
    """
    def insertEvent(self, eventName, commmitted, message, id, time, index, maxPrepare, accNum, accVal):
        eventRecord = (eventName, commmitted, message, id, time, index, maxPrepare, accNum, accVal)
        
        if(not (eventRecord in self.timelineLog)):
            self.timelineLog.append(eventRecord)
        
        self.insertTweet(eventRecord)

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
        Private field timelineLog
    """
    def gettimelineLog(self):
        return self.timelineLog

    """
    @return 
        Private field peers
    """
    def getPorts(self):
        return self.peers

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
        Prints all blocks in the dictionary
    """
    def viewDictionary(self):   
        for block in self.blockedUsers:
            print block

    """
    @param
        committed: Boolean which indicated if the event was committed to paxosLog
        message: Body of tweet
        id: User who created the tweet
        time: UTC time
    @effects 
        Adds tweet to timelineLog and tweets private fields
    @modifies 
        timelineLog and tweets private fields
    @return 
        Tweet event record
    """
    def tweet(self, commmitted, message, id, time, index, maxPrepare, accNum, accVal):
        # Add event to timelineLog
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
        committed: Boolean which indicated if the event was committed to paxosLog
        receiver: User who is being blocked by id
        id: User who is blocking receiver
        time: UTC Time
    @effects 
        Adds event to timelineLog
        Adds block relationship to dictionary if one does not exist already
    @modifies 
        timelineLog and blockedUsers private field
    @return
        Block event record
    """
    def block(self, commmitted, receiver, id, time, index, maxPrepare, accNum, accVal):
        if(id == self.userId):
            print "Blocked User %d\n" % (receiver)

        # Add event to timelineLog
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
        committed: Boolean which indicated if the event was committed to paxosLog
        receiver: User who is being unblocked by id
        id: User who is unblocking receiver
        time: UTC Time
    @effects
        Adds event to timelineLog
        Removes blocked relationship from dictionary if one exists
    @modifies
        timelineLog and blockedUsers private fields
    @return
        Unblock event record
    """
    def unblock(self, commmitted, receiver, id, time, index, maxPrepare, accNum, accVal):
        if(id != self.userId):
            print "Unblocked User %d\n" % (receiver)

        # Add event to timelineLog
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

            # Add all tweets from this User's timelineLog if they have been given access to view
            if(receiver == self.userId):
                for event in self.timelineLog:
                    if(event[3] == id and event[0] == "tweet"):
                        self.tweets.append(event)

        self.pickleSelf()

        return event

    """
    @param
        event: Event that accepted by a majority of acceptors
    @effects
        Adds event to timelineLog if event does not exist already
        Adds tweet to tweets
        Updates dictionary based on block and unblock events
    @modifies 
        timelineLog, tweets, and dictionary private fields
    """
    def commit(self, event):
        # Update timelineLog, tweets, and dictionary private fields
        # Event: (eventName, commmitted, message, id, time, index, maxPrepare, accNum, accVal)
        if (event[0] == "tweet"):
            print "Committed tweet event!"
            # Add tweet to timelineLog and tweets
            self.tweet(True, event[2], event[3], event[4], event[5], event[6], event[7], event[8])
        if(event[0] == "block"):
            print "Committed block event!"
            # Add block to timelineLog and dictionary
            self.block(True, event[2], event[3], event[4], event[5], event[6], event[7], event[8])
        if(event[0] == "unblock"):
            print "Committed unblock event!"
            # Add unblock to timelineLog and remove from dictionary
            self.unblock(True, event[2], event[3], event[4], event[5], event[6], event[7], event[8])