import numpy as np
from enum import Enum
import itertools
import random
import operator

class VotingScheme(Enum):
    plurality = 1
    bi_plurality = 2
    anti_plurality = 3
    borda = 4

useGeneratedVoters = False

votingScheme = VotingScheme.anti_plurality
#options
m = 7
#voters
n = 10

votersEx = np.array([
    [3, 2, 1],
    [1, 3, 2],
    [2, 1, 3],
    [1, 2, 3],
    [2, 3, 1],
    [3, 1, 2]
    ])

votingVector = None
voting_results = None
voters = votersEx
voter_happiness = None


def inputVoters():
    global voters, m, n
    print("Set the voter preferences. Candidates are numbered 1,2,3,... etc.")
    print("Please ensure that all numbers occur only once per voter preference.")
    print("The format is 'x y ... z'. Spaces go beween numbers.")
    print("Once the first voter preference is set, all following preferences must use the same number of candidates.")
    print("Press enter on an empty field to finish.")
    votersRun = True
    voter = ""
    voters = []
    numVoters = 0
    printError = "This preference is not valid. Please re-enter.";
    while votersRun:
        voter = [int(x) for x in input("Please set voter {}'s preferences:".format(numVoters)).split()]
        if numVoters > 0 and len(voter) == 0:
            votersRun = False
            break
        elif validVoterPreference(voter):
            if numVoters == 0:
                m = len(voter)
            if validPreferenceLength(voter, m):
                numVoters += 1
                voters = voters + [voter]
            else:
                print(printError)
        else:
            print(printError)
    n = len(voters)
    voters = np.array(voters)

def validVoterPreference(preference):
    if len(preference) > 1:
        comparingList = list(range(1,len(preference)+1))
        if comparingList == sorted(preference):
            return True
        return False

def validPreferenceLength(preference, m):
    return (len(preference) == m)
    

def inputScheme():
    global votingScheme
    scheme = input("Please choose between the voting schemes \n(1) Plurality \n(2) Bi-plurality (voting for two) \n(3) Anti-Plurality \n(4) Borda\n")
    if(scheme == "" or int(scheme) <= 0 or int(scheme) >= 5):
        print("Default voting [Plurality] is chosen.")
        scheme = 1
    print("Using voting scheme "+VotingScheme(int(scheme)).name)
    setVotingScheme(VotingScheme(int(scheme)))
    

def generateVoters():
    global m, n, voters
    perms = [x for x in itertools.permutations(range(1,m+1))]
    voters = np.array(random.choices(perms, k=n))    


def setVotingScheme(scheme):
    global votingScheme, votingVector, m
    votingScheme = scheme
    if(votingScheme == VotingScheme.plurality):
        votingVector = np.array([1 if i==0 else 0 for i in range(m)])
    elif(votingScheme == VotingScheme.bi_plurality):
        votingVector = np.array([1 if i in [0,1] else 0 for i in range(m)])
    elif(votingScheme == VotingScheme.anti_plurality):
        votingVector = np.array([0 if i == (m-1) else 1 for i in range(m)])
    elif(votingScheme == VotingScheme.borda):
        votingVector = np.array([m-i for i in range(1,m+1)])

def countVotes():
    global votingVector, voters, m, n, voting_results
    print(votingVector)
    voting_results = {key:0 for key in range(1,m+1)}
    for i in range(n):
        for j in range(m):
            voting_results[voters[i,j]] += votingVector[j]

def getSortedVotingResult():
    global voting_results
    return sorted(voting_results.items(), key=lambda kv: (-kv[1], kv[0]))

def getWinner():
    global voting_results
    return max(voting_results, key=voting_results.get)

def calculateVoterHappiness():
    global voters, m, voting_results, voter_happiness
    winner = getWinner()
    voter_happiness = np.array([m-(v.tolist().index(winner)+1) for v in voters])

def getUnhappyVoters():
    global voter_happiness, m
    return [i for (i,v) in enumerate(voter_happiness) if v < m-1]

def findDeceptions(voter):
    global voters, voting_results, voter_happiness
    print("voter "+str(voter))
    voterPreference = voters[voter,:]
    happiness = voter_happiness[voter]
    favorite = voterPreference[0]
    winner = getWinner()  
    
    sorted_voting_result = getSortedVotingResult()
    if favorite is not winner:
        rankFavorite = m - happiness
        pointsFavorite = sorted_voting_result[rankFavorite-1][1]
        pointsWinner = sorted_voting_result[0][1]
        pointDifference = pointsWinner - pointsFavorite
        if favorite < winner: #if favorite has a lower id, one less point suffices to catch up
            pointDifference -= 1
        print(pointDifference)
        #voterPreference
    

def countVotesWithDeception(voter, deceptivePreference):
    global votingVector, voters, m, n
    newVoters = voters
    newVoters[voter] = deceptivePreference
    voting_results = {key:0 for key in range(1,m+1)}
    for i in range(n):
        for j in range(m):
            voting_results[newVoters[i,j]] += votingVector[j]
    return voting_results


if useGeneratedVoters:
    generateVoters()
    setVotingScheme(votingScheme)
else:
    inputVoters()
    inputScheme()
    

countVotes()
calculateVoterHappiness()

print("Voting vector: "+str(votingVector))
print(voters)
print(voting_results)
print("The winner is option "+str(getWinner()))
print("Voter happiness is "+str(voter_happiness))
print("Overall happiness is "+str(np.sum(voter_happiness)))
print("Voters "+str(getUnhappyVoters()) + " are unsatisfied with the result.")

print()
findDeceptions(getUnhappyVoters()[0])














