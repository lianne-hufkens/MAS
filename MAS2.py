import random
from tabulate import tabulate

# Number of item types M
# Number of sellers K
# Number of buyers N
# Number of auction rounds R
# Universal maximum starting price Smax
# Penalty factor E
# Indication whether “pure” of leveled commitment auctioning is used PureCommitment
# other...

roundCount = 1
auctionCount = 1
epsilon=0.3

class Buyer:
    bidFactors = None
    bid = None
    lastWin = None
    profit = 0.0

    def __init__(self, ID):
        self.ID = ID
        self.bidFactors = [random.uniform(1, 5) for t in range(M)]  # a seperate factor for each item type

    def setBid(self, startPrice, itemType):
        self.bid = self.bidFactors[itemType] * startPrice


class Seller:
    itemType = None
    startPrice = None
    lastWin = None
    profit= 0.0



    def __init__(self, ID):
        self.ID = ID

    def setStartingPrice(self):
        self.startPrice = random.randint(1, Smax)  # maybe turn this into float?

    def setItemType(self):
        global M
        self.itemType = random.randint(0, M - 1)


def askInput(message, lowBound=None, highBound=None):
    if lowBound is None:
        lowBound = 0
    if highBound is None:
        highBound = 100
    while True:
        a = input(message)
        if a is not "":
            if a.isdigit() and int(a) > lowBound and int(a) <= highBound:
                return int(a)


def askBool(message):
    while True:
        a = input(message)
        if a is not "":
            if a.lower() in ["y", "yes", "t", "tr", "true", "1"]:
                return True
            else:
                return False


def createAllObjects():  # create all buyers and sellers
    global buyers, sellers
    buyers = [Buyer(b) for b in range(N)]
    sellers = [Seller(s) for s in range(K)]


def sortBidders(bidders):
    return sorted(bidders, key=lambda x: x.bid, reverse=True)


def getWinnerAndPrice(bidders, marketPrice):  # get the winning bidder and the price they must pay
    biddersLeft = [b for b in bidders if b.bid < marketPrice]
    biddersLeft = sortBidders(biddersLeft)
    if len(biddersLeft) > 1:
        return biddersLeft[0], biddersLeft[1].bid
    elif len(biddersLeft) == 1:
        return biddersLeft[0], biddersLeft[0].bid
    else:
        return None, None

def runAllRoundsLevelCommitment():
    for r in range(R):
        runRoundLevelCommitement()
        levelCommitment()

    printProfit()

def levelCommitment():
    global buyers, sellers
    a = input("Do you want to refund more item?(y\n)")
    while (a=="y"):
        buyerNumber = int(input("Please provide ur Buyer Numnber: "))
        sellerNumber = int(input("Please provide ur Seller Numnber: "))
        price = float(input("Please provide ur Bidding Price: "))
        penaltyFee=epsilon*price

        profitSeller = [n for n in range(len(sellers))]
        for s in profitSeller:
            if sellerNumber==int(sellers[s].ID):
                    sellers[s].profit=sellers[s].profit-price+penaltyFee

        profitBuyer = [n for n in range(len(buyers))]
        for s in profitBuyer:
            if int(buyers[s].ID)==buyerNumber:
                buyers[s].profit=buyers[s].profit+price-penaltyFee
        a = input("Do you want to refund more item?(y\n)")
        if a == "n":
            break




def runRoundLevelCommitement():
    global buyers, sellers, roundCount, auctionCount
    for s in sellers:
        s.setItemType()  # sellers pick their item type
    roundOrder = [n for n in range(len(sellers))]
    random.shuffle(roundOrder)  # to get the turn order for the sellers
    participatingBuyers = [b for b in buyers]  # all buyers participate at first
    for o in roundOrder:
        participatingBuyers = runAuction(sellers[o], participatingBuyers)  # run an auction
    auctionCount = 1
    roundCount += 1


def printProfit():
    global buyers, sellers

    print()
    print()
    profitDisplaySeller = [n for n in range(len(sellers))]
    for s in profitDisplaySeller:
        print("Profit price for", sellers[s].ID, " seller ", sellers[s].profit)
    print()
    print()
    profitDisplayBuyer = [n for n in range(len(buyers))]
    for s in profitDisplayBuyer:
        print("Profit price for", buyers[s].ID, " buyer ", buyers[s].profit)


def runAllRounds():
    for r in range(R):
        runRound()

    printProfit()

def runRound():
    global buyers, sellers, roundCount, auctionCount
    for s in sellers:
        s.setItemType()  # sellers pick their item type
    roundOrder = [n for n in range(len(sellers))]
    random.shuffle(roundOrder)  # to get the turn order for the sellers
    participatingBuyers = [b for b in buyers]  # all buyers participate at first
    for o in roundOrder:
        participatingBuyers = runAuction(sellers[o], participatingBuyers)  # run an auction
    auctionCount = 1
    roundCount += 1


def runAuction(seller, bidders):
    global auctionCount

    if len(bidders) > 1:  # at least two bidders are present
        win = False
        seller.setStartingPrice()  # set starting price
        for b in buyers:
            b.setBid(seller.startPrice, seller.itemType)  # make all bids
        marketPrice = sum(b.bid for b in bidders) / len(bidders)  # calculate market price
        winner, winPrice = getWinnerAndPrice(bidders, marketPrice)  # get the winning buyer and what they need to pay
        if winner is not None:  # if there's a winner, record the price
            winner.lastWin = winPrice
            seller.lastWin = winPrice
            win = True
        printAuctionResults(bidders, seller, marketPrice, win,winPrice)  # print the results for this auction
        seller.profit +=winPrice
        winner.profit +=marketPrice - winPrice

        auctionCount += 1
        if win:
            return [b for b in bidders if b is not winner]  # winner is removed from list
        else:
            return bidders


def printAuctionResults(bidders, seller, marketPrice, win,winPrice):
    s1 = "Round {} auction {}".format(roundCount, auctionCount)
    s2 = "Seller {} auctioned item type {} with starting price {}".format(seller.ID, seller.itemType, seller.startPrice)
    bidders = sortBidders(bidders)
    bids = [b.bid for b in bidders]
    bids.append(marketPrice)
    bids.sort(reverse=True)
    mpIndex = bids.index(marketPrice)
    biddersID = [b.ID for b in bidders]
    biddersID.insert(mpIndex, "Market Price")
    data = [biddersID, bids]
    data = list(map(list, zip(*data)))  # transpose list of lists
    print()
    print(s1)
    print(s2)
    print(tabulate(data, headers=['Buyer #', 'Bid value'], tablefmt="fancy_grid", stralign="center"))
    if not win:
        print("This auction had no winner.")
    #print("Profit price for", seller.ID, " seller ", winPrice)

# start of program run

M = askInput("How many item types? ")
K = askInput("How many sellers? ")
N = askInput("How many buyers? ", K)
R = askInput("How many auction rounds? ")
E = askInput("What is the penalty factor? ", 0, 1)

Smax = askInput("What is the universal maximum starting price? ")

if askBool("Is pure commitment used? ")== True:
    createAllObjects()
    runAllRounds()
else:
    createAllObjects()
    runAllRoundsLevelCommitment()
