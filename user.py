import socket
import time
import pickle

class User:

    def __init__(self, userId, peers, pickle=None, pickledUser=None):
        if pickle:
            # Load User from pickle
            self.log = pickledUser['log']
            self.blockedUsers = pickledUser['blockedUsers']
            self.userId = ord(userId) - 65
            self.peers = peers
            self.tweets = list()
            for event in self.log:
                self.insertTweet(event)
        else:
            # Create User from scratch
            print "Creating user from scratch"
            self.log = list()
            self.tweets = list()
            self.blockedUsers = list()
            self.userId = ord(userId) - 65
            self.peers = peers

    def pickleSelf(self):
        pickleSelf = {
            "log": self.log,
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
        Adds new eventRecord to log if it does not exist in the log already
        Adds tweets if eventName is tweet and this User is being blocked by creator of tweet and tweet is not in tweets already
    @modifies
        log and tweets private fields
    """
    def insertEvent(self, eventName, message, id, time):
        eventRecord = (eventName, message, id, time)
        
        if(not (eventRecord in self.log)):
            self.log.append(eventRecord)
        
        self.insertTweet(eventRecord)

        self.pickleSelf()

    """
    @param
        event: Event that has occurred by some User
    @effects
        Adds event to tweets if eventName is tweet and this User is being blocked by creator of tweet and tweet is not in tweets already
    """
    def insertTweet(self, event):
        if (event[0] == "tweet" and not (self.isBlocked(event[2], self.userId)) and not (event in self.tweets)):
            self.tweets.append(event)

    """
    @return
        Private field log
    """
    def getLog(self):
        return self.log

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
        Prints all events in the log
    """
    def viewLog(self):
        for event in self.log:
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
        time: UTC time
        id: User who created the tweet
        message: Body of tweet
    @effects 
        Adds tweet to log and tweets private fields
    @modifies 
        log and tweets private fields
    """
    def tweet(self, time, id, message):
        # Add event to log
        self.insertEvent("tweet", message, id, time)

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
        time: UTC Time
        id: User who is blocking receiver
        receiver: User who is being blocked by id
    @effects 
        Adds event to log
        Adds block relationship to dictionary if one does not exist already
    @modifies 
        log and blockedUsers private field
    """
    def block(self, time, id, receiver):
        if(id == self.userId):
            print "Blocked User %d\n" % (receiver)

        # Add event to log
        self.insertEvent("block", receiver, id, time)

        # Add block to dictionary if it does not exist already
        if(not (self.isBlocked(id, receiver))):
            self.blockedUsers.append((id, receiver))

            # Remove all tweets from this User's tweets if they have been revoked access to view
            if(receiver == self.userId):
                for i in range(0, len(self.tweets)):
                    if(self.tweets[i][2] == id):
                        del self.tweets[i]

        self.pickleSelf()

    """
    @param
        time: UTC Time
        id: User who is unblocking receiver
        receiver: User who is being unblocked by id
    @effects
        Adds event to log
        Removes blocked relationship from dictionary if one exists
    @modifies
        log and blockedUsers private fields
    """
    def unblock(self, time, id, receiver):
        if(id != self.userId):
            print "Unblocked User %d\n" % (receiver)

        # Add event to log
        self.insertEvent("unblock", receiver, id, time)

        # Delete blocked relationship from dictionary if it exists
        if (self.isBlocked(id, receiver)):
            for i in range(0, len(self.blockedUsers)):
                if(self.blockedUsers[i][0] == id and self.blockedUsers[i][1] == receiver):
                    del self.blockedUsers[i]
                    break

        # Set dictionary to new list if no blocked relationships exist
        if(len(self.blockedUsers) == 0):
            self.blockedUsers = list()

            # Add all tweets from this User's log if they have been given access to view
            if(receiver == self.userId):
                for event in self.log:
                    if(event[2] == id and event[0] == "tweet"):
                        self.tweets.append(event)

        self.pickleSelf()

    """
    @param
        recevivedLog: The senders log
    @effects
        Adds event to log if event does not exist already
        Adds tweet to tweets
        Updates dictionary based on block and unblock events
    @modifies 
        log, tweets, and dictionary private fields
    """
    def receive(self, receivedLog):
        print receivedLog
        # Update log, tweets, and dictionary private fields
        for event in receivedLog:
            if (event[0] == "tweet"):
                print "Recevived tweet event!"
                # Add tweet to log and tweets
                self.tweet(event[3], event[2], event[1])
            if(event[0] == "block"):
                print "Received block event!"
                # Add block to log and dictionary
                self.block(event[3], event[2], event[1])
            if(event[0] == "unblock"):
                print "Received unblock event!"
                # Add unblock to log and remove from dictionary
                self.unblock(event[3], event[2], event[1])