import random, re
from tabulate import tabulate
import seaborn
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

#Number of item types M
#Number of sellers K
#Number of buyers N
#Number of auction rounds R
#Universal maximum starting price Smax
#Penalty factor E
#Indication whether “pure” of leveled commitment auctioning is used PureCommitment
#other...

roundCount = 1
auctionCount = 1
records = []

class Buyer:
    def __init__(self, ID):
        self.bid = None
        self.bidFactors = [random.uniform(Bmin,Bmax) for t in range(K)] #a seperate factor for each seller
        self.bidFactorHistory = []
        self.profit = []
        self.auctionCount = 0
        self.auctionWin = 0
        self.auctionCancel = 0
        self.ID = ID
        self.auctionsWonInThisRound = []
        self.Dup = random.uniform(DUmin, DUmax)
        self.Ddown = random.uniform(DDmin, DDmax)
    def setBid(self, startPrice, sellerID):
        self.bid = self.bidFactors[sellerID] * startPrice
    def recordWin(self, record):
        self.auctionCount += 1
        self.bidFactorHistory.append(self.bidFactors)
        self.bidFactors[record.seller.ID] *= self.Ddown #regardless of strategy used
        self.profit.append(record.getProfit())
        self.auctionWin += 1
        if not PureCommit:
            self.auctionsWonInThisRound.append(record)
            if len(self.auctionsWonInThisRound) == 2:
                self.cancelLeastProfitableBuy()
    def cancelLeastProfitableBuy(self):
        if self.auctionsWonInThisRound[0].getProfit() > self.auctionsWonInThisRound[1].getProfit():
            self.cancelBuy(1) #to cancel
        else:
            self.cancelBuy(0)
    def cancelBuy(self, index):
        global E
        self.auctionCancel += 1
        self.auctionWin -= 1
        #buy to cancel
        record = self.auctionsWonInThisRound[index]
        seller = record.seller
        profit = record.getProfit()
        price = record.winPrice
        penaltyFee = price * E
        seller.cancelSell(penaltyFee) #pay fee
        self.profit[self.profit.index(profit)] = -penaltyFee #mark fee payment as loss
        record.setCancelled() #mark this buy as cancelled
        self.auctionsWonInThisRound.remove(record) #remove from list
    def recordLoss(self, record):
        self.auctionCount += 1
        self.profit.append(0)
        self.bidFactorHistory.append(self.bidFactors)
        if not newStrategy or (record.marketPrice - self.bid) > 0: #if the bid was below market price or using the old strategy
            self.bidFactors[record.seller.ID] *= self.Dup
        else:
            self.bidFactors[record.seller.ID] *= self.Ddown
            
    def resetForRound(self):
        self.auctionsWonInThisRound = []

class Seller:
    def __init__(self, ID):
        self.itemType = None
        self.startPrice = None
        self.profit = []
        self.auctionCount = 0
        self.auctionSell = 0
        self.auctionCancel = 0
        self.ID = ID
    def setStartingPrice(self):
        self.startPrice = round(random.uniform(1, Smax), 2) #float with 2 decimals
    def setItemType(self):
        global M
        self.itemType = random.randint(0, M-1)
    def recordSell(self, record):
        self.auctionCount += 1
        self.profit.append(record.winPrice)
        self.auctionSell += 1
    def recordUnsold(self):
        self.auctionCount += 1
        self.profit.append(0)
    def cancelSell(self, fee):
        self.profit[-1] = fee #change last buy to fee
        self.auctionCancel += 1
        self.auctionSell -= 1

class AuctionRecord:
    def __init__(self, roundN, auctionN, marketPrice, winPrice, bidders, seller, winner):
        self.round = roundN
        self.auction = auctionN
        self.cancelled = False
        self.winner = winner
        self.win = (self.winner is not None)
        self.winPrice = winPrice
        self.seller = seller
        self.startPrice = seller.startPrice
        self.marketPrice = marketPrice
        #create list (table) of information
        self.data = [(b.ID, b.bid) for b in sortBidders(bidders)]
        self.data.append(("Market Price", marketPrice))
        self.data.sort(key=lambda x: x[1], reverse=True)
    def setCancelled(self):
        self.cancelled = True
    def getBidOf(self, buyerID):
        found = [row[1] for row in self.data if row[0] == buyerID]
        if len(found) == 1:
            return found
        elif len(found) == 0:
            return 0
        else:
            print("ERROR: multiple buyers found in list!")
    def getProfit(self):
        if self.win:
            return self.marketPrice - self.winPrice
        else:
            return 0
    def getBidders(self):
        return [row[0] for row in self.data if isinstance(row[0], int)]
    def printData(self):
        s1 = "Round {} auction {}".format(self.round, self.auction)
        s2 = "Seller {} auctioned item type {} with starting price {}".format(self.seller.ID, self.seller.itemType, self.startPrice)
        print()
        print(s1)
        print(s2)
        print(tabulate(self.data, headers=['Buyer #', 'Bid value'], tablefmt="fancy_grid", stralign="center"))
        if self.winner is None:
            print("This auction had no winner.")
        elif self.cancelled:
            print("Buyer {} cancelled their purchase.".format(self.winner.ID))
        else:
            print("Bidder {} won the auction and paid {}.".format(self.winner.ID, self.winPrice))

def askInput(message, lowBound=None, highBound=None):
    if lowBound is None:
        lowBound = 0
    if highBound is None:
        highBound = 100
    while True:
        a = input(message)
        if a is not "" and re.match("^[0-9]+\.?[0-9]?$", a): #check for int or float
            if isinstance(lowBound, int) and float(a) > lowBound and float(a) <= highBound:
                return round(float(a))
            elif isinstance(lowBound, float) and float(a) > lowBound and float(a) <= highBound:
                return float(a)
            
def askBool(message):
    a = input(message)
    if a is not "":
        if a.lower() in ["y", "yes", "t", "tr", "true", "1"]:
            return True
    return False
    
def askRange(message, minN=None, maxN=None):
    if minN is None:
        minN = False
    if maxN is None:
        maxN = False
    while True:
        a = input(message)
        if a is not "":
            p = list(re.split('[ ,]',a)) #split into input numbers, then check if they are valid floats/integers
            if len(p) == 2 and p[0] != p[1] and re.match("^[0-9]*\.?[0-9]+?$", str(p[0])) and re.match("^[0-9]*\.?[0-9]+?$", str(p[1])):
                p[0] = float(p[0])
                p[1] = float(p[1])
                if p[0] > p[1]: #biggest value in back
                    t = p[0]
                    p[0] = p[1]
                    p[1] = t
                if not minN and not maxN: #no constrains means all is good
                    break
                elif minN and not maxN and p[1] >= minN: #the range must be above the minimum
                    break
                elif not minN and maxN and p[0] <= maxN: #the range must be below the maximum
                    break
                elif minN and maxN and p[1] >= minN and p[0] <= maxN: #the range must fall within the boundaries
                    break
    return p[0], p[1] #output min, max

def createAllObjects(): #create all buyers and sellers
    global buyers, sellers
    buyers = [Buyer(b) for b in range(N)]
    sellers = [Seller(s) for s in range(K)]
    for s in sellers: #sellers pick their item type
        s.setItemType() 

def sortBidders(bidders):
    return sorted(bidders, key=lambda x: x.bid, reverse=True)
    
def getWinnerAndPrice(bidders, marketPrice): #get the winning bidder and the price they must pay
    biddersLeft = [b for b in bidders if b.bid < marketPrice]
    biddersLeft = sortBidders(biddersLeft)
    if len(biddersLeft) > 1: #if at least two bids are below market price
        return biddersLeft[0], biddersLeft[1].bid #second bid becomes price
    elif len(biddersLeft) == 1: #else
        return biddersLeft[0], biddersLeft[0].bid #winning bid becomes price
    else:
        return None, None

def runAllRounds():
    for r in range(R):
        runRound()
        if not PureCommit:
            for b in buyers:
                b.resetForRound()

def runRound():
    global buyers, sellers, roundCount, auctionCount
    roundOrder = [n for n in range(len(sellers))] 
    random.shuffle(roundOrder) #to get the turn order for the sellers
    participatingBuyers = [b for b in buyers] #all buyers participate at first
    for o in roundOrder:
        participatingBuyers = runAuction(sellers[o], participatingBuyers) #run an auction
    auctionCount = 1
    roundCount += 1

def runAuction(seller, bidders):
    global auctionCount, records
    if len(bidders) > 1: #at least two bidders are present
        win = False
        seller.setStartingPrice() #set starting price
        for b in buyers:
            b.setBid(seller.startPrice, seller.ID) #make all bids
        marketPrice = sum(b.bid for b in bidders) / len(bidders) #calculate market price
        winner, winPrice = getWinnerAndPrice(bidders, marketPrice) #get the winning buyer and what they need to pay
        records.append(AuctionRecord(roundCount, auctionCount, marketPrice, winPrice, bidders, seller, winner)) #record the results for this auction
        recordParticipation(records[-1])
        auctionCount += 1
        if winner is not None and PureCommit:
            return [b for b in bidders if b is not winner] #winner is removed from list
        else: #leveled commit has all buyers participate again
            return bidders
        
def recordParticipation(record):#bidders, seller, marketPrice, winner=None, winPrice=None):
    global buyers
    #deal with seller
    record.seller.auctionCount += 1
    if record.win:
         record.seller.recordSell(record)
    else: #the item goes unsold
        record.seller.recordUnsold()
    #deal with buyers
    for b in buyers: 
        if b in record.getBidders():
            b.auctionCount += 1 
        if b is record.winner: #if there's a winner, record the profits
            b.recordWin(record)
        else:
            b.recordLoss(record)

def printAuctionResults():#bidders, seller, marketPrice, win):
    global records
    for r in records:
        r.printData() #print the results for the auctions

def plotBar():
    global sellers, buyers

    #prepare base palettes
    sellerPalette = seaborn.husl_palette(len(sellers), l=.5)
    buyerPalette = seaborn.husl_palette(len(buyers), h=.3, l=0.7)

    #prepare tick labels
    xTickLabelsBuyer = ["Buyer{}".format(int(a % N) + 1) for a in range(N)]
    xTickLabelsSeller = ["Seller{}".format(int(a % K) + 1) for a in range(K)]
    barWidth = 0.5
    
    plt.subplot(1, 2, 1)
    plt.title("Items bought")
    #prepare data
    x = range(len(buyers))
    y1 = np.array([b.auctionWin for b in buyers])
    if not PureCommit:
        y2 = np.array([b.auctionCancel for b in buyers])
        bottomColor = buyerPalette[0]
        topColor = buyerPalette[1]
    else:
        bottomColor = buyerPalette        
    #plot graph
    p1 = plt.bar(x, y1, color=bottomColor, edgecolor='white', width=barWidth)
    if not PureCommit:
        p2 = plt.bar(x, y2, bottom=y1, color=topColor, edgecolor='white', width=barWidth)
    #configure axes ticks and labels
    plt.ylabel('Number of items')
    plt.xticks(x, xTickLabelsBuyer, fontsize=6, rotation=30)
    if not PureCommit:
        plt.legend((p1[0], p2[0]), ('Bought', 'Cancelled' ))

    plt.subplot(1, 2, 2)
    plt.title("Items sold")
    #prepare data
    x = range(len(sellers))
    y1 = np.array([s.auctionSell for s in sellers])
    if not PureCommit:
        y2 = np.array([s.auctionCount - s.auctionSell for s in sellers])
        bottomColor = sellerPalette[0]
        topColor = sellerPalette[1]
    else:
        bottomColor = sellerPalette
    #plot graph
    p1 = plt.bar(x, y1, color=bottomColor, edgecolor='white', width=barWidth)
    if not PureCommit:
        p2 = plt.bar(x, y2,bottom=y1, color=topColor, edgecolor='white', width=barWidth)
    #configure axes ticks and labels
    plt.ylabel('Number of items')
    plt.xticks(x, xTickLabelsSeller, fontsize=6, rotation=30)
    if not PureCommit:
        plt.legend((p1[0], p2[0]), ('Sold', 'Cancelled' ))

    plt.show()    

def plotProfits():
    global sellers, buyers, records
    #create the data structures
    sd = np.array([[p for p in s.profit] for s in sellers]).T
    sc = np.array([np.cumsum(s.profit, dtype=float) for s in sellers]).T
    bd = np.array([[q for q in b.profit] for b in buyers]).T
    bc = np.array([np.cumsum(b.profit, dtype=float) for b in buyers]).T

    #prepare base palettes
    sellerPalette = seaborn.husl_palette(len(sellers), l=.5)
    buyerPalette = seaborn.husl_palette(len(buyers), h=.3, l=0.7)

    #add market price to data
    marketPricePerAu = np.array([[r.marketPrice for r in records]])
    marketPricePerRound = np.array([np.mean(marketPricePerAu.reshape(-1, K), axis=1)]).T
    sd = np.c_[sd, marketPricePerRound] 
    bd = np.c_[bd, marketPricePerAu.T]
    sellerPaletteM = sellerPalette + ["#000000"] #add black for market price line
    buyerPaletteM = buyerPalette + ["#000000"]

    #custom labels
    xTickRangeS = [_ for _ in range(R)]
    xTickLabelsS = [_ for _ in range(1,R+1)]
    xTickRangeB = [_ for _ in range(R*K)]
    #xTickLabelsB = ["R{}\nA{}".format(int(a/K)+1, (a%K)+1) for a in range(R*K)]
    xTickLabelsB = ["R{}".format(i) for i in range(1,R+1)]

    #custom major tick locations
    bPos = [i for i in range(R*K) if i%K == 0]
    
    plt.style.use("seaborn-darkgrid")
    seaborn.set(rc={"xtick.bottom" : True, "xtick.major.size": 4, "xtick.minor.size": 2})#, "ytick.left" : True})
    plt.subplots_adjust(hspace = 0.4)
    
    #create main title with parameter info
    if PureCommit:
        c = "Pure"
    else:
        c = "E:"+str(E)+", Leveled"
    if newStrategy:
        s = "New"
    else:
        s = "Old"
    plt.suptitle("M:{}, K:{}, N:{}, R:{}, {} Commitment, Dup:({},{}), Ddown:({},{}), Bfactor:({},{}), {} Strategy".format(M,K,N,R,c,DUmin,DUmax,DDmin,DDmax,Bmin,Bmax,s))

    #start of graph plotting (rendering)
    
    plt.subplot(2,2,1)
    plt.title("Seller profits per round", weight='semibold')
    ax = seaborn.lineplot(data=sd, dashes=False, palette=sellerPaletteM)
    #configure ticks
    plt.xticks(xTickRangeS)
    ax.set_xticklabels(xTickLabelsS)
    #modify legend
    handles, labels = ax.get_legend_handles_labels()
    labels[-1] = "AVG Market Price"
    ax.legend(handles, labels)
    #add axes labels
    plt.xlabel('Rounds')
    plt.ylabel('Profits')
    
    plt.subplot(2,2,2)
    plt.title("Seller profits cumulative", weight='semibold')
    ax = seaborn.lineplot(data=sc, dashes=False, palette=sellerPalette)
    #configure ticks
    plt.xticks(xTickRangeS)
    ax.set_xticklabels(xTickLabelsS)
    #add axes labels
    plt.xlabel('Rounds')
    plt.ylabel('Profits')
    
    plt.subplot(2,2,3)
    plt.title("Buyer profits per auction", weight='semibold')
    ax = seaborn.lineplot(data=bd, dashes=False, palette=buyerPaletteM)
    #configure ticks
    plt.xticks(xTickRangeB)
    ax.get_xaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
    ax.get_xaxis().set_major_locator(mpl.ticker.FixedLocator(bPos))
    ax.set_xticklabels(xTickLabelsB)
    #modify legend
    handles, labels = ax.get_legend_handles_labels()
    labels[-1] = "Market Price"
    ax.legend(handles, labels)
    #add axes labels
    plt.xlabel('Auctions')
    plt.ylabel('Profits')

    plt.subplot(2,2,4)
    plt.title("Buyer profits cumulative", weight='semibold')
    ax = seaborn.lineplot(data=bc, dashes=False, palette=buyerPalette)
    #configure ticks
    plt.xticks(xTickRangeB)
    ax.get_xaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
    ax.get_xaxis().set_major_locator(mpl.ticker.FixedLocator(bPos))
    ax.set_xticklabels(xTickLabelsB)
    #add axes labels
    plt.xlabel('Auctions')
    plt.ylabel('Profits')
    
    plt.show()

#start of program run

debug = True
if not debug:
    M = askInput("How many item types? [x > 1] ", 1)
    K = askInput("How many sellers? [x > 1] ")
    N = askInput("How many buyers? [x > sellers] ", K)
    R = askInput("How many auction rounds? [x > 0] ")
    Smax = askInput("What is the universal maximum starting price? [x > 0] ", 0.0, 1000)
    PureCommit = askBool("Is pure commitment used? [default: no] ")
    if not PureCommit:
        E = askInput("What is the penalty factor? [0 < x <= 1] ", 0.0, 1.0)
    DUmin, DUmax = askRange("Enter the Delta Up range, separated by a space or comma [x >= 1]: ", minN=1)
    DDmin, DDmax = askRange("Enter the Delta Down range, separated by a space or comma [0 < x <= 1]: ", minN=0, maxN=1)
    Bmin, Bmax = askRange("Enter the Bidding Factor range, separated by a space or comma [x > 0]: ", minN=0)
    newStrategy = askBool("Is the new bidding strategy used? [default: no] ")
else:
    M = 15
    K = 4
    N = 5
    R = 15
    Smax = 10
    PureCommit = False
    E = 0.9
    DUmin = 2
    DUmax = 3
    DDmin = 0.3
    DDmax = 0.5
    Bmin = 1
    Bmax = 5
    newStrategy = True

createAllObjects()
runAllRounds()
printAuctionResults()
plotProfits()
plotBar()
