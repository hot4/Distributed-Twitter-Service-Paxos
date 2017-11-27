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
        else:
            # Create User from scratch
            print "Creating user from scratch"
            self.log = list()
            self.blockedUsers = list()
            self.userId = ord(userId) - 65
            self.peers = peers
            self.tweets = list()

    def pickleSelf(self):
        pickleSelf = {
            "log": self.log,
            "blockedUsers": self.blockedUsers
        }
        pickle.dump(pickleSelf, open("pickledUser.p", "wb"))

    """
    @param 
        eventName: Name of event 
        message: The body of a tweet, or an empty String for block or unblock
        time: UTC time
    @effects
        Adds new eventRecord to log. Adds to tweet only if eventName is a tweet
    @modifies
        log and tweets private fields
    """
    def insertion(self, eventName, message, time):
        eventRecord = (eventName, message, self.userId, time)
        self.log.append(eventRecord)
        if (eventName == "tweet"):
            self.tweets.append(eventRecord)
        self.pickleSelf()

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
    @param
        message: Body of tweet
        time: UTC time
    @effects 
        Adds tweet to log and tweets private fields
    @modifies 
        log and tweets private fields
    """
    def tweet(self, message, time):
        self.insertion("tweet", message, time)

    """
    @param
        time: UTC Time
        receiver: The site that will be blocked
    @effects 
        Adds event to log
        Adds block relationship to dictionary if one does not exist already
    @modifies 
        log and blockedUsers private field
    """
    def block(self, time, receiver):
        print "Blocked User %d\n" % (receiver)

        # Add event to log
        self.insertion("block", receiver, time)
        
        # Check if block already exists in dictionary
        blocked = False
        for i in range(0, len(self.blockedUsers)):
            if(self.blockedUsers[i][0] == self.userId and self.blockedUsers[i][1] == receiver):
                blocked = True

        # Add block to dictionary if it does not exist already
        if(not (blocked)):
            self.blockedUsers.append((self.userId, receiver))

        self.pickleSelf()

    """
    @param
        time: UTC Time
        receiver: The site that will be unblocked
    @effects
        Adds event to log
        Removes blocked relationship from dictionary if one exists
    @modifies
        log and blockedUsers private fields
    """
    def unblock(self, time, receiver):
        print "Unblocked User %d\n" % (receiver)

        # Add event to log
        self.insertion("unblock", receiver, time)

        # Delete blocked relationship from dictionary if it exists
        for i in range(0, len(self.blockedUsers)):
            if(self.blockedUsers[i][0] == self.userId and self.blockedUsers[i][1] == receiver):
                del self.blockedUsers[i]
                break

        # Set dictionary to new list if no blocked relationships exist
        if(len(self.blockedUsers) == 0):
            self.blockedUsers = list()

        self.pickleSelf()

    """
    @param
        recevivedLog: The senders log
    @effects
        Adds each tweet in receivedLog into tweets if it does not exist alraedy
        Adds each event in receivedLog into log if it does not exist already
    @modifies 
        log and tweets private fields
    """
    def receive(self, receivedLog):
        # Update log and tweets private fields
        for event in receivedLog:
            if (not (event in self.tweets) and event[0] == "tweet"):
                # Add tweet to tweets
                self.tweets.append(event)
            
            if(not (event in self.log)):
                # Add event to log
                self.log.append(event)