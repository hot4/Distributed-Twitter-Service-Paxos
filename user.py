import socket
import time
import pickle

class User:
  
    def __init__(self, userId, peers, pickledWriteAheadLog, pickledCheckpoint):
        # Initiate private fields
        self.writeAheadLog = list()
        self.tweets = list()
        self.blockedUsers = list()
        self.userId = userId
        self.peers = peers
        self.accepted = list()
        self.index = 0
        self.commitAmt = 0

        # Check if pickledWriteAheadLog exists
        if(pickledWriteAheadLog != None):
            # Load writeAheadLog
            self.writeAheadLog = pickledWriteAheadLog['writeAheadLog']

        # Check if pickledCheckpoint exists
        if(pickledCheckpoint != None):
            # Load tweets
            self.tweets = pickledCheckpoint['tweets']
            # Load blockedUsers
            self.blockedUsers = pickledCheckpoint['blockedUsers']

        # Update index based on last proposal entry in writeAheadLog
        for proposal in self.writeAheadLog:
                if(not (proposal == None)):
                    self.index = self.index + 1

        # Update commitAmt based on how many commits are in writeAheadLog
        self.commitAmt = self.index % 5

        # Check if any proposals have been committed in writeAheadLog
        if(self.commitAmt > 0):
            # Get the disjoint betweent (writeAheadLog and tweets) and (writeAheadLog and blockedUsers)
            disjointTweets = [proposal for proposal in self.writeAheadLog if proposal not in self.tweets]
            disjointBlocks = [proposal for proposal in self.writeAheadLog if proposal not in self.blockedUsers]

            # Update tweets
            for proposal in disjointTweets:
            	if(proposal != None):
                	self.insertTweets(proposal)

            # Update blockedUsers
            for proposal in disjointBlocks:
            	if(proposal != None):
                	self.updateBlockedUsers(proposal)

    def pickleWriteAheadLog(self):
        pickleWriteAheadLog = {
            "writeAheadLog": self.writeAheadLog
        }
        pickle.dump(pickleWriteAheadLog, open("pickledWriteAheadLog" + str(self.userId) + ".p", "wb"))


    def pickleCheckpoint(self):
        pickleCheckpoint = {
            "tweets": self.tweets,
            "blockedUsers": self.blockedUsers
        }

        pickle.dump(pickleCheckpoint, open("pickledCheckpoint" + str(self.userId) + ".p", "wb"))
        
    """
    @param
        proposal: Proposal that was accepted by a majority of acceptors
    @effects
        Inserts proposal at it's index and may insert None values between last known index and proposal's index within writeAheadLog
        Increments index by 1 if proposal is not filling a hole
    @modifies
        writeAheadLog private field
    """
    def insertWriteAheadLog(self, proposal):
        # Check if last known empty index is less than or equal to proposal's index value
        if(self.index <= proposal[0]):
            # Temporarily store index
            i = self.index
            # Loop up until proposal's index
            while i < proposal[0]:
                # Insert None values into writeAheadLog
                self.writeAheadLog.append(None)
                i = i + 1
            # Insert proposal at end of writeAheadLog
            self.writeAheadLog.append(proposal)
            # Increment index
            self.index = self.index + 1
        # proposal is filling a hole in writeAheadLog
        else:
            # Insert proposal at index of proposal in writeAheadLog
            self.writeAheadLog[proposal[0]] = proposal

        # Update writeAheadLog
        self.pickleWriteAheadLog()
        
    """
    @param
        proposal: Proposal that was accepted by a majority of acceptors
    @effects
        Inserts proposal into tweets based on time
    @modifies
        tweets private field
    """
    def insertTweets(self, proposal):
        # proposal[3] -> (eventName, message, id, time)
        # Check if proposal is a tweet and originator of tweet is not blocking this User
        if (proposal[3][0] == "tweet" and not (self.isBlocked(proposal[3][2], self.userId))):
            # Check if tweets is empty
            if (not self.tweets):
                self.tweets.append(proposal)
            # Check if tweets contains one element
            elif(len(self.tweets) == 1):
                # Check if only element in tweets goes before proposal
                if(self.tweets[0][3][3] > proposal[3][3]):
                    # Insert proposal to end of tweets
                    self.tweets.append(proposal)
                else:
                    # Insert proposal to beginning of tweets
                    self.tweets.insert(0, proposal)
            # Figure out where to insert proposal into tweets
            else:
                # Temporary placeholder for index to insert proposal into writeAheadLog
                index = -1
                # tweets[i][[3] --> (eventName, message, id, time)
                for i in range(0, len(self.tweets)-1):
                    # Check if proposal index is between neighbor proposals
                    if(self.tweets[i][3][3] < proposal[3][3] and proposal[3][3] < self.tweets[i+1][3][3]):
                        # Store index
                        index = i
                        break
                # Check if index was found to insert proposal into tweets
                if(index > 0):
                    # Insert proposal into tweets at index
                    self.tweets.insert(index, proposal)
                else:
                    # Insert proposal to beginning of tweets
                    self.tweets.insert(0, proposal)

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
        # blockedUsers[i] --> (id, receiver)
        for i in range(0, len(self.blockedUsers)):
            # Check if there exists a blocked relationship where (id, receiver)
            if(self.blockedUsers[i][0] == id and self.blockedUsers[i][1] == receiver):
                return True
        return False

    def updateBlockedUsers(self, proposal):
        # proposal --> (index, maxPrepare, accNum, accVal)
        # proposal[3] --> (eventName, message, id, time)
        # Check if proposal is block
        if(proposal[3][0] == "block"):
            # Check if block does not exist already
            if(not (self.isBlocked(proposal[3][2], proposal[3][1]))):
                # Add block to blockedUsers
                self.blockedUsers.append((proposal[3][2], proposal[3][1]))

                # Check if recipient of block is this User
                if(proposal[3][1] == self.userId):
                    # tweets[i] --> (index, maxPrepare, accNum, accVal)
                    # tweets[i][3] --> (eventName, message, id, time)
                    i = 0
                    while i < len(self.tweets):
                        # Check if creator of tweet is creator of block
                        if(self.tweets[i][3][2] == proposal[3][2]):
                            # Delete originator's tweet from tweets
                            del self.tweets[i]
                        else:
                            i = i+1
        # Check if proposal is unblock
        elif(proposal[3][0] == "unblock"):
            # Check if block exists
            if(self.isBlocked(proposal[3][2], proposal[3][1])):
                # blockedUsers[i] --> (id, receiver)
                for i in range(0, len(self.blockedUsers)):
                    # Check if current block is the block
                    if(self.blockedUsers[i][0] == proposal[3][2] and self.blockedUsers[i][1] == proposal[3][1]):
                        del self.blockedUsers[i]
                        break

            # Check if receipient of unblock is this User
            if(proposal[3][1] == self.userId):
                # proposalItem --> (index, maxPrepare, accNum, accVal)
                # proposalItem[3] --> (eventName, message, id, time)
                for proposalItem in self.writeAheadLog:
                    # Check if creator of tweet is creator of unblock
                    if(proposalItem[3][2] == proposal[3][2]):
                        self.insertTweets(proposalItem)

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
        if(not self.tweets):
            print "No tweets are available to view"
        for tweet in self.tweets:
            print tweet

    """
    @effects 
        Prints all proposals in the writeAheadLog
    """
    def viewWriteAheadLog(self):
        if(not self.writeAheadLog):
            print "No proposals are stored in stable storage"
        for proposal in self.writeAheadLog:
            print proposal
            
    """
    @effects
        Prints all blocks in the dictionary
    """
    def viewDictionary(self):   
        if(not self.blockedUsers):
            print "No blocked relations are stored in the dictionary"
        for block in self.blockedUsers:
            print block

    """
    @param

        index: Index some proposer wishes to write a proposal to in writeAheadLog
        n: Proposal number from a proposer
    @effects
        Updates maxPrepare of accepted proposal if one exists at index
        Adds promise to accepted
    @modifies
        accepted private field
    @return
        (accNum, accVal) of proposal acceptor has accepted at index
        (None, None) if acceptor has not accepted any proposal at index
    """
    def prepare(self, index, n):
        # accepted[i] --> (index, maxPrepare, accNum, accVal)
        for i in range(0, len(self.accepted)):
            # Check if index are the same and n is greater than maxPrepare
            if(self.accepted[i][0] == index and self.accepted[i][1] < n):
                # Set maxPrepare equal to n
                self.accepted[i][1] = n
                # Return (accNum, accVal)
                return (self.accepted[i][2], self.accepted[i][3])

        # Acceptor has not accepted any value at index
        # Represents promise to proposer
        proposal = (index, n, None, None)
        # Add promise to accepted
        self.accepted.append(proposal)
        return (None, None)

    """
    @param
        proposals: Container of proposals accepted by a majority of acceptors
    @return
        Highest proposal value accepted by some acceptor if one exists, None otherwise
    """
    def filterProposals(self, proposals):
        maxAccNum = -1
        maxAccVal = None

        # proposal[i] --> (accNum, accVal)
        for i in range(0, len(proposals)):
            # Check if current proposal is greater than maxAccNum
            if(proposals[i][0] > maxAccNum):
                # Store accNum and accVal from proposal
                maxAccNum = proposals[i][0]
                maxAccVal = proposals[i][1]
        
        # Highest proposal value accepted by some acceptor if one exists, None otherwise
        return maxAccVal


    """
    @param
        index: Index some proposer wishes to write a proposal to in writeAheadLog
        n: Proposal number from a proposer
        v: Proposal value from a proposer
    @effects
        Updates maxPrepare, accNum, and accVal for proposal at index if one exists
        Inserts a new accepted proposal into accepted
    @modifies 
        accepted private field
    """
    def accept(self, index, n, v):
        # accepted[i] --> (index, maxPrepare, accNum, accval)
        for i in range(0, len(self.accepted)):
            # Check if index are the same and n is greater than or equal to maxPrepare
            if(accepted[i][0] == index and n >= accepted[i][1]):
                # Update accNum
                accepted[i][2] = n
                # Update accVal
                accepted[i][3] = v
                # Update maxPrepare
                accepted[i][1] = n

        # Temporary placeholder to verify proposal has been stored
        proposal = (index, n, n, v)
        # Check if proposal is in accepted
        if(not (proposal in self.accepted)):
            # Add propsal to accepted
            self.accepted.append(proposal)

    """
    @param
        proposal: proposal that accepted by a majority of acceptors
    @effects
        Adds proposal to writeAheadLog and (tweets or blockedUsers)
    @modifies 
        writeAheadLog, (tweets or blockedUsers), and checkpoint private field
    @return True if this User's proposal was committed, False otherwise
    """
    def commit(self, proposal):
    	print "Committing this proposal"
    	print proposal
        # proposal --> (index, maxPrepare, accNum, accVal)
        # proposal[3] --> (eventName, message, id, time)

        # Insert committed proposal to writeAheadLog
        self.insertWriteAheadLog(proposal)

        # Insert committed proposal to tweets
        self.insertTweets(proposal)

        # Update commited proposal to blockedUsers
        self.updateBlockedUsers(proposal)

        # Update index
        self.index = max(self.index, proposal[0] + 1)

        # Increment amount of proposals that have been committed
        self.commitAmt = self.commitAmt + 1
        
        # Check if commitAmt should occurr
        if(self.commitAmt == 5):
            # Update commitAmt
            self.pickleCheckpoint()
            # Reset commitAmt
            self.commitAmt = 0
        
        # accepted[i] --> (index, maxPrepare, accNum, accVal)
        # Remove proposal from accepted since it has been commited
        for i in range(0, len(self.accepted)):
            # Check if index are the same
            if(self.accepted[i][0] == proposal[0]):
                del self.accepted[i]
                break

        # Check if id's are the same
        if(proposal[3][2] == self.userId):
            # This User's proposal was committed
            return True
        else:
            # This User's proposal was not commited
            return False