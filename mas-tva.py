import numpy as np
from enum import Enum
import itertools
import random
import operator
import copy
from tabulate import tabulate

class VotingScheme(Enum):
    plurality = 1
    bi_plurality = 2
    anti_plurality = 3
    borda = 4

useGeneratedVoters = False

votingScheme = None
#options
m = 5
#voters
n = 7

votingVector = None
voting_results = None
voters = None
voter_happiness = None
tactical_voting_options = []

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
    print()

def inputSettings():
    global m, n
    m = input("Please choose the number of candidates(m):")
    if m == "" or int(m) <= 1:
        print("m has defaulted to 3.")
        m = 3
    m = int(m)
    n = input("Please choose the number of voters(n):")
    if n == "" or int(n) <= 1:
        print("n has defaulted to 5.")
        n = 5
    n = int(n)

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

def countVotes(voters):
    global votingVector, m, n
    voting_results = {key:0 for key in range(1,m+1)}
    for i in range(n):
        for j in range(m):
            voting_results[voters[i,j]] += votingVector[j]
    return voting_results

def countVotesWithDeception(voter, deceptivePreference):
    return countVotes(getVotersWithDeception(voter, deceptivePreference))

def getVotersWithDeception(voter, deceptivePreference):
    global voters
    newVoters = copy.deepcopy(voters)
    newVoters[voter] = deceptivePreference
    return newVoters

def getSortedVotingResult(voting_results):
    return sorted(voting_results.items(), key=lambda kv: (-kv[1], kv[0]))

def getWinner(voting_results):
    return max(voting_results, key=voting_results.get)

def calculateHappiness(m, voterPreference, winner):
    return (m-(voterPreference.tolist().index(winner)+1))

def calculateAllHappiness(m, voters, voting_results):
    winner = getWinner(voting_results)
    return np.array([calculateHappiness(m, v, winner) for v in voters])

def getUnhappyVoters():
    global voter_happiness, m
    return [i for (i,v) in enumerate(voter_happiness) if v < m-1]

def identifyDeception(truePreference, newPreference, trueWinner, newWinner):
    trueWinIndex = list(truePreference).index(trueWinner)
    trueNewIndex = list(truePreference).index(newWinner)
    newWinIndex = list(newPreference).index(trueWinner)
    newNewIndex = list(newPreference).index(newWinner)
    #if the new winner has been ranked higher in the preferences
    if trueNewIndex > newNewIndex: 
        return "compromising"
    elif trueWinIndex < newWinIndex:
        return "burying"
    else:
        return None

def findDeceptions(voterList):
    global voters, voting_results, voter_happiness
    sorted_voting_result = getSortedVotingResult(voting_results)
    deceptions = []
    count = 0
    for voter in voterList:
        voterPreference = voters[voter,:]
        happiness = voter_happiness[voter]
        favorite = voterPreference[0]
        winner = getWinner(voting_results)    
        if favorite is not winner:
            rankFavorite = m - happiness
            pointsFavorite = sorted_voting_result[rankFavorite-1][1]
            pointsWinner = sorted_voting_result[0][1]
            #(v,Õ,~H,z)
            for newPreference in itertools.permutations(voterPreference):
                newResults = countVotesWithDeception(voter, newPreference)
                newWinner = getWinner(newResults)
                newHappiness = calculateHappiness(m, voterPreference, newWinner)
                
                if newHappiness > happiness:
                    newVoters = getVotersWithDeception(voter, newPreference)
                    deceptions.append((count, voter, newPreference, newResults,
                                       np.sum(calculateAllHappiness(m, getVotersWithDeception(voter, newPreference), newResults)),
                                       identifyDeception(voterPreference, newPreference, winner, newWinner)))
                    count += 1
    return deceptions

def printVoterPreferences(voters):    
    headers = ["Voter \n"+str(v) for v in range(len(voters))]
    voterList = copy.deepcopy(voters)
    print(tabulate(voterList.T, headers, numalign="center"))
    print()

def printResults(voting_results):
    sorted_voting_results = getSortedVotingResult(voting_results)
    headers = ["Candidate","Points"]
    print(tabulate(sorted_voting_results, headers, numalign="center"))
    print()

def printDeceptions(deceptions):
    if len(deceptions) > 0:
        headers=['ID','Voter', 'Tactical preference', 'New voting outcome', 'New happiness', 'Tactic']
        print(tabulate(deceptions, headers, numalign="center"))
        print()

def printScenario(scene):
    global voting_results, m, voters, voter_happiness
    voter = scene[1]
    print()
    print("Showing scenario "+str(scene[0])+" in detail:")
    SVR = getSortedVotingResult(voting_results)
    SSR = getSortedVotingResult(scene[3])
    print()
    headers = ["Candidate", r"Original Score", "Candidate", "New Score"]
    merged_list = [(SVR[i][0], SVR[i][1], SSR[i][0], SSR[i][1]) for i in range(m)]
    print(tabulate(merged_list, headers, numalign="center"))
    orgVoterPref = copy.deepcopy(voters[voter].tolist())
    newVoterPref = np.array(copy.deepcopy(scene[2]))
    print()
    headers = ["True preference", "Tactical preference"]
    merged_pref = [(orgVoterPref[j], newVoterPref[j]) for j in range(m)]
    print(tabulate(merged_pref, headers, numalign="center"))
    print()
    print("Overall happiness went up from "+str(np.sum(voter_happiness))+" to "+str(scene[4])+".")
    print("Voter #"+str(voter)+" used "+str(scene[5])+" for this result.")
    print()
    
def calculateTacticalRisk(tactical_voting_options):
    global n
    return len(tactical_voting_options)/n

run = True
while run:
    if useGeneratedVoters:
        inputSettings()
        generateVoters()
        inputScheme()
    else:
        inputVoters()
        inputScheme()

    voting_results = countVotes(voters)
    voter_happiness = calculateAllHappiness(m, voters, voting_results)

    print("Voting vector: "+str(votingVector))
    print("Voter preferences are as follows: ")
    printVoterPreferences(voters)
    print("The results are: ")
    printResults(voting_results)
    print("The winner is candidate #"+str(getWinner(voting_results)))
    print("Voter happiness is "+str(voter_happiness))
    print("Overall happiness is "+str(np.sum(voter_happiness)))
    print("Voters "+str(' '.join("#"+str(u) for u in getUnhappyVoters())) + " are unsatisfied with the result.")

    print()
    if len(getUnhappyVoters()) > 0:
        tactical_voting_options = findDeceptions(getUnhappyVoters())
        printDeceptions(tactical_voting_options)
        if len(tactical_voting_options) == 0:
            print("There are no voting manipulation tactics possible in this situation.")
        
    print("The overall risk for tactical voting is "+str(calculateTacticalRisk(tactical_voting_options)))
    
    loop = (len(tactical_voting_options) > 0)
    while loop:
        scene = input("\nShow details of a scenario with tactical voting('no' to decline): ")
        if scene == "" or scene.lower() == "n" or scene.lower() == "no":
            loop = False
        elif int(scene) >= 0 and int(scene) < len(tactical_voting_options):
            printScenario(tactical_voting_options[int(scene)])

    scenario = input("\nRun another voting scenario(y/n)?")
    if scenario != "" and scenario.lower() != "y" and scenario.lower() != "yes":
        run = False
