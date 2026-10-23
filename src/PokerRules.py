import os
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import random
from random import shuffle
import operator
from stats import Persistent
from PokerHandList import get_rank

cards_52 = '2s3s4s5s6s7s8s9sTsJsQsKsAs' + '2h3h4h5h6h7h8h9hThJhQhKhAh' + \
           '2d3d4d5d6d7d8d9dTdJdQdKdAd' + '2c3c4c5c6c7c8c9cTcJcQcKcAc'
# this is Bicycle order for new playing cards. Aces on top and bottom with two kings in the middle
cards_52b = 'As2s3s4s5s6s7s8s9sTsJsQsKs' + 'Ad2d3d4d5d6d7d8d9dTdJdQdKd' + \
            'KcQcJcTc9c8c7c6c5c4c3c2cAc' + 'KhQhJhTh9h8h7h6h5h4h3h2hAh'  # <- top of deck
# order from top to bottom: A->K of Hearts, A->K of Clubs, K->A of Diamonds, K->A of Spades
#test decks are stacked for specific hands.  Need to set disable_random=True
cards_52s = '2s3s4s5sAd' '7s8sKd2h3h' '4h5h6h2d6c' '8c7d6sQhKh' 'Ah7c3d4d5d' '6d9c' + \
            'Ac7h8d9sTc' '5c8h9hThJh' '4c9dTdJdQd' '3cTsJsQsKs' '2cJcQcKcAs'
cards_52s1 ='2s3s'  '4s5sAd7s8s' 'Kd2h3h4h5h' '6h2d6c8c7d' '6sQhKhAh7c' '3d4d5d6d9c' + \
                    'Ac7h8d9sTc' '5c8h9hThJh' '4c9dTdJdQd' '3cTsJsQsKs' '2cJcQcKcAs'
    
cards_52s2 = '2s3s' '4s5sAd7s8s' 'Kd2h3h4h5h' '6h2d6c8c7d' '6sQhKhAh7c' '3d4d5d6d9c' + \
                    'Ac7h8d9sTc' '5c8h9hThJh' '4c9dTdJdQd' '3cTsJsQsKs' '2cJcQcKcAs'

cards_52s3 = 'As2s' '3s4s5s6s7s' '8s9sTsJsQs' 'KsAd2d3d4d' '5d6d7d8d9d' 'TdJdQdKdKc' + \
                    'QcJcTc9c8c' '7c6c5c4c3c' '2cAcKhQhJh' 'Th9h8h7h6h' '5h4h3h2hAh'  # <- top of deck

cards_52s4 = '2s3s' '4s5sAd7s8s' 'Kd2h3h4h5h' '6h2d6c8c7d' '6sQhKhAh7c' '3d4d5d6d9c' + \
                    'Ac7h8d9sTc' '5c8h9hThJh' '4c9dTdJdQd' '3cTsJsQsKs' '2cJcQcKcAs'


used_count = {  # this is exported to stats.json to track long term which cards are used the most
    'As': 0, '2s': 0, '3s': 0, '4s': 0, '5s': 0, '6s': 0, '7s': 0,
    '8s': 0, '9s': 0, 'Ts': 0, 'Js': 0, 'Qs': 0, 'Ks': 0,
    'Ad': 0, '2d': 0, '3d': 0, '4d': 0, '5d': 0, '6d': 0, '7d': 0,
    '8d': 0, '9d': 0, 'Td': 0, 'Jd': 0, 'Qd': 0, 'Kd': 0,
    'Ah': 0, '2h': 0, '3h': 0, '4h': 0, '5h': 0, '6h': 0, '7h': 0,
    '8h': 0, '9h': 0, 'Th': 0, 'Jh': 0, 'Qh': 0, 'Kh': 0,
    'Ac': 0, '2c': 0, '3c': 0, '4c': 0, '5c': 0, '6c': 0, '7c': 0,
    '8c': 0, '9c': 0, 'Tc': 0, 'Jc': 0, 'Qc': 0, 'Kc': 0
}

class D:
    LTIME = time.time_ns() >> 8  # 1722706309776316500 1725047351608597700
# LTIME = 1722706309776316500 #Ace-low Straight test with exchgprob=100
disable_random = False  # for testing
start_deck = cards_52s3  # cards_52s1  # cards_test1
exchangeProbability = 0  # 75% of shuffle exchanges that will complete


class W:
    logfile = None
    
    
class P:
    
    High_Card = 1
    One_Pair = 2
    Two_Pair = 3
    Three_of_a_Kind = 4
    Straight = 5
    Flush = 6
    Full_House = 7
    Four_of_a_Kind = 8
    Straight_Flush = 9
    Five_of_a_Kind = 10



def normalize(bigrank: int) -> int:
    rank = 0
    if 6186 <= bigrank <= 7462:
        rank = P.High_Card
    elif 3326 <= bigrank <= 6185:
        rank = P.One_Pair
    elif 2468 <= bigrank <= 3325:
        rank = P.Two_Pair
    elif 1610 <= bigrank <= 2467:
        rank = P.Three_of_a_Kind
    elif 1600 <= bigrank <= 1609:
        rank = P.Straight
    elif 323 <= bigrank <= 1599:
        rank = P.Flush
    elif 167 <= bigrank <= 322:
        rank = P.Full_House
    elif 11 <= bigrank <= 166:
        rank = P.Four_of_a_Kind
    elif 1 <= bigrank <= 10:
        rank = P.Straight_Flush
    return rank


singles = ['', 'ace', 'Deuce', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight',
             'Nine', 'Ten', 'Jack', 'Queen', 'King', 'Ace']
plurals = ['', 'aces', 'Deuces', 'Threes', 'Fours', 'Fives', 'Sixes', 'Sevens', 'Eights',
             'Nines', 'Tens', 'Jacks', 'Queens', 'Kings', 'Aces']


def get_poker_hand(handrank: int, cardrank: int, second=0)->str:
    si: int = cardrank
    sj: int = second
    nrank = normalize(handrank)
    match nrank:
        case P.High_Card:
            s = f"{singles[si]}-high"
        case P.One_Pair:
            s = f"Pair of {plurals[si]}"
        case P.Two_Pair:
            s = f"{plurals[si]} over {plurals[sj]}"
        case P.Three_of_a_Kind:
            s = f"Three {plurals[si]}"
        case P.Straight:
            if si == 14 and second == 5:
                s = f"{singles[si]}-low Straight"
                #G.aceslow controls if ace can count low
            else:
                s = f"{singles[si]}-high Straight"
        case P.Flush:
            s = f"{singles[si]}-high Flush"
        case P.Full_House:
            s = f"{plurals[si]} Full"
        case P.Four_of_a_Kind:
            s = f"Quad {plurals[si]}" #+ {singles[sj]}
        case P.Straight_Flush:
            if si == 14 and second == 5: #3:
                s = f"{singles[si]}-low Straight Flush"
                # G.aceslow controls if ace can count low
            elif second == 13:  #was 11 which made queen high SF a RF
                s = "Royal Flush" 
            else:
                s = f"{singles[si]}-high Straight Flush"
        case P.Five_of_a_Kind:
            s = f"Five {plurals[si]}"
        case _:
            s = "nothing"
    return s

def graphic_suit(cardName: str)->str:
    rsr: str = ''
    for index,letter in enumerate(cardName):
       if index & 1 == 1:
           rsr += Card.unicode_dict[letter]
       else:
           rsr += letter
    return rsr


class Card:
    rank_str = ' a23456789TJQKA'
    suit_str = ' shdc'
    RankOrder1 = ['', 'a', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suit_dict = {' ': 0, 's': 1, 'h': 2, 'd': 3, 'c': 4}
    suit_formal_names = ['', 'Spades', 'Hearts', 'Diamonds', 'Clubs']
    unicode_dict = {'s':'♠', 'h': '♥', 'd': '♦', 'c': '♣'}
    rankOrderD: dict = {'': 0, 'a': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
                        '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

    def __init__(self, card_name: str):
        self.name = card_name
        rc = self.name[0]
        sc = self.name[1]
        #print(f'rc={rc} sc={sc}')
        #self.rank: int = card_name.index(rc)
        self.rank: int = Card.rankOrderD[rc]
        self.suit: int = Card.suit_dict[sc]
        #print(f'{rc} {sc} {self.rank} {self.suit}')
        self.marked = False

    def __str__(self):

        return self.name
    
    def __getitem__(self, index):
        return self.name[index]

    def __int__(self):
        return self.rank
    
    
    def __lt__(self, other):
        return self.rank < other.rank
    
    
    def __le__(self, other):
        return self.rank <= other.rank
    
    
    def __gt__(self, other):
        return self.rank > other.rank
    
    
    def __ge__(self, other):
        return self.rank >= other.rank
    
    
    def is_face(self)->bool:
        return 11 <= self.rank <= 13
    
 
class Deck:
    
    _KEY = 1.27894657402

    def __init__(self, ucards=None):
       # if ucards is None:
        self.cards = populate_deck()
        # else:

        if ucards is not None:
            self.cards = ucards
        self._key = D.LTIME
        self.logdeck('New deck:') # top of the deck (with pop)
        self.usedcards = []
        self.discards: [Card] = []  # discards keep traded in for new cards separate to simulate manual mentods
        # self.discardedby: [int] = []
                    # so discards keep track of who discarded them
        self.replacing_cards: [Card] = []
        self.usedcardcount = used_count.copy()
        check_start_deck()

    def print_deck(self):
        print(f'card count={len(self.cards)}')
        for i, card in enumerate(self.cards):

            print(card.name[0]+Card.unicode_dict[card.name[1]], end=' ')
            if (i+1) % 13 == 0:
                print(' ',end='\n')

    def compile_card_used_stats(self):
        for card in self.usedcards:
            self.usedcardcount[card.name] += 1
            
    def logdeck(self, label: str):
        i: int = 0
        deck: str = label + '\n'
        for card in self.cards:
            deck += card.name + ', '
            i += 1
            if i % 13 == 0:
                deck += '\n'
        writelog([deck])


    def shuffledeck(self, exchangeProb: int, iterations: int):
        """Shuffles the given List in-place."""
        exchangedone = False
        while not exchangedone:
            for _ in range(iterations):
                for i in range(len(self.cards) - 1, 0, -1):
                    if random.randint(0, 100) < exchangeProb:
                        j = random.randint(0, i)
                        self.cards[i], self.cards[j] = self.cards[j], self.cards[i]
                        exchangedone = True

    def addtodeck(self, card: Card):
        if card not in self.cards:
            self.cards.append(card)


    def reshuffle_deck(self):
        self.compile_card_used_stats()
        for card in self.usedcards:
            self.addtodeck(card)
        for card in self.discards:
           self.addtodeck(card)
        if len(self.cards) != 52:
            writelog([f'reshuffle deck: is not 52 cards: {len(self.cards)}'])
            raise ValueError
        self.usedcards = []
        self.discards = []
        D.LTIME = time.time_ns() >> 8
        # print(f'\n{LTIME}\n')
        random.seed(D.LTIME)
        self.shuffledeck(exchangeProbability, 3000)
 
    def deal_a_card(self)->Card:
        if len(self.cards) == 0:
            writelog(['deck is empty'], printalso=True)
            exit(0)
            quit(2)
        topcard: [Card] = self.cards.pop()
        self.usedcards.append(topcard)
        return topcard


    def replace_cards(self, card: Card) -> Card:
        dealcard = self.deal_a_card()
        self.discards.append(card)
        return dealcard


# writelog(['random seed ='+ str(LTIME)], printalso=True)


def check_start_deck():
    ct = used_count.copy()
    for i in range(0, len(start_deck), 2):
        cardname = start_deck[i:i + 2]
        ct[cardname] += 1
    dstr1 = ''
    dstr2 = ''
    mx = max(ct.values())
    if mx > 1:
        dstr1 = 'Duplicate cards found in start deck: '
        for i,v in ct.items():
            if ct[i] > 1:
                dstr1 += f'{i}, '
    if 0 in ct:
        dstr2 = 'Cards missing in start_deck: '
        for i,v in ct.items():
            if ct[i] == 0:
                dstr2 += f'{i},'
    writelog([dstr1,dstr2], printalso=True)
    return


def populate_deck() -> [Card]:
    """ Generate full 52 card deck from str constants
    """
    cards: [Card] = []
    for i in range(0, len(start_deck), 2):
        cards.append(Card(start_deck[i:i+2]))
    if not disable_random:
        D.LTIME: int = time.time_ns() >> 4
        # print(f'\n{D.LTIME}\n')
        random.seed(D.LTIME, version=2)
        shuffle(cards)
    return cards


class Hand:
    
    rankCounter = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0,
                   8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0}
    suitCount = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    
    
    def __init__(self, card_list):
        """
        Initialize a Hand object which will hold all information about a poker hand.
        :param card_list: an iterator for five Card objects.
        self.cards = card_list
        self.sname = (short name) "AA2KK" for Aces over Kings, 2 pair
        self.name  :full name
        self.rankhand : 1 - 7462
        self.hand_type : 1 (high card) - 9 (straight flush)  see class P and normalize()
        self.hand_name : (text describing hand in poker slang 'trip kings'
        self.card_rank_groups : [(AA)(KK)Q] (list of lists containing cards grouped by hand type)
        self.is_flush : len(set(self.suits)) == 1
        self.suit_count : sorted number of suits in hand
        rank_count : sorted number of ranks in hand
        """
        self.card_str: str = ''
        self.cards: [Card] = []
        card_str: str = ''
        if len(card_list) == 0:
            # print("Empty list passed to Hand constructor.")
            self.sname = ''
            self.rankhand = 7462  # lowest hand rank
            return
        self.cards.extend(card_list)
        for card in card_list:
            newcard = Card(card.name)
            card_str += newcard.name  # rank_str[card.rank] #str(Card.rank_str.index(newcard.rank)) #card_str +=
            # card_str += Card.suit_str[newcard.suit]
        self.name = card_str
        rank_count = Hand.rankCounter.copy()
        suit_count = Hand.suitCount.copy()
        for card in self.cards:
            rank_count[card.rank] += 1
            suit_count[card.suit] += 1
        self.card_rank_groups = []
        tcardcount = {k: v for k, v in sorted(rank_count.items(),
                                              key=operator.itemgetter(1, 0), reverse=True)}
        sname = ''
        for v, c in tcardcount.items():
            # if v == 0: break
            if c > 0:
                self.card_rank_groups.append((v,c))
            for j in range(c):
               sname += Card.RankOrder1[v]
        self.sname = sname
        self.rankhand = get_rank(self.sname, self.name)
        self.hand_type = normalize(self.rankhand)
        # self.is_broadway = self.sname == 'AKQJT'
        # ranks = sorted([card.rank for card in self.cards], reverse=True)
        # print(ranks)
        self.suits = [card.suit for card in self.cards]
        # print(self.suits)
        self.is_flush = len(set(self.suits)) == 1
        gp = self.card_rank_groups
        si = gp[0][0] # highest card of first group (ex: A for (AAA)KK
        sj = gp[1][0] # highest card of second group (ex: K for AAA(KK)
        self.hand_name = get_poker_hand(self.rankhand, si,sj)
        # writelog([f'hand = {self.name}', f'{self.sname},',
        #          f' {self.hand_type}', f'rank={self.rankhand}', f'{self.hand_name}' ])
        self.suit_count = {k: v for k, v in sorted(rank_count.items(),
                                                   key=operator.itemgetter(1,0), reverse=True)}


# def dealcards(deck: Deck, num_hands: int, num_cards_each: int, turn: int):
#     """
#     :param deck:
#     :param num_hands:
#     :param num_cards_each:
#     :param turn: 0 - 4: identifies the player who is left of dealer
#     Simulate manual process of dealing cards by taking them from the randomly
#     shuffled deck, in order, and passing them out to each player one-at-a-time.
#    :return: a list of list of Card objects.
#     """
#     return_cards: [[Card]] = []
#     h0: [Card] = []
#     h1: [Card] = []
#     h2: [Card] = []
#     h3: [Card] = []
#     h4: [Card] = []
#     h5: [Card] = []
#     h6: [Card] = []
#     h7: [Card] = []
#     h8: [Card] = []
#     for i in range(num_cards_each):
#         for j in range(num_hands):
#             card = deck.deal_a_card()
#             match j:
#                 case 0, 1, 2, 3, 4, 5, 6, 7, 8:
#                     h0.append(card)
#                 case _:
#                     pass
#                     #logger.debug('dealcards: Exceeded supported number of players')
#     rc: [[Card]] = [h0, h1, h2, h3, h4, h5, h6, h7, h8]
#     for _ in range(turn):
#         hx = rc.pop(0)
#         rc.append(hx)
#     return_cards: [[Card]] = rc
#     returns = return_cards[:num_hands]
#     return returns


def writelog(lines:list, printalso=False):
    with open("gamelog.txt", "a") as W.logfile:
        #W.logfile.write("\n")
        for line in lines:
            W.logfile.write(line+"\n")
            if printalso:
                print(line)


def logstats(load=False):
    if load:
        Persistent.load()
    for k, v in used_count.items():
        Persistent.STATS[k] += v #random.randint(1, 15)
    Persistent.save()
    
# The 21 premutations of 7 cards into 5
C7 =[
    [1,2,3,4,5],
    [1,2,3,4,6],
    [1,2,3,4,7],
    [1,2,3,5,6],
    [1,2,3,5,7],
    [1,2,3,6,7],
    [1,2,4,5,6],
    [1,2,4,5,7],
    [1,2,4,6,7],
    [1,2,5,6,7],
    [1,3,4,5,6],
    [1,3,4,5,7],
    [1,3,4,6,7],
    [1,3,5,6,7],
    [1,4,5,6,7],
    [2,3,4,5,6],
    [2,3,4,5,7],
    [2,3,4,6,7],
    [2,3,5,6,7],
    [2,4,5,6,7],
    [3,4,5,6,7],
]
# The 6 premutations of 6 cards into 5
C6 =[
    [1,2,3,4,5],
    [1,2,3,4,6],
    [1,2,3,5,6],
    [1,2,4,5,6],
    [1,3,4,5,6],
    [2,3,4,5,6],
]

D5 =[
    [1,2,3,4,5],
    [1,2,3,4,5]
]


def best_hands(holecards: [Card], communitycards: [Card]) -> Hand:
    '''
    Create 21 temporary hands to determine highest scoring.
    :return top Hand for player
    '''
    #evalcards = [holecards,cards]   #
    #print(f'hole cards: {holecards[0]}, {holecards[1]}')
    #print(f'community cards: {communitycards[0]}, {communitycards[1]}, {communitycards[2]}')
    evalcards = []
    evalcards.extend(holecards)
    evalcards.extend(communitycards)
    wn = 0
    hands: [Hand] = []
    bestscore = 7462 #start with lowest possible score (highest number)
    pt: [int] = []
    if len(evalcards) == 7:
        pt = C7
    elif len(evalcards) == 6:
        pt = C6
    elif len(evalcards) == 5:
        pt = D5
    else:
        pt = []
    #print(pt)
    n = 0
    for i in range(0,len(pt)):
        elong = []
        for j in range(5):  #find the 5 best cards in each poker hand
            crd = evalcards[pt[i][j]-1]
            elong.append(Card(crd))
            # if type(crd) is str:
            #     elong.append(Card(crd))
            # elif type(crd) is Card:
            #     card = crd
            # elif type(crd) is list:
            #     print(f'type is list {crd[0]}')
            #     card = crd[0]
            # else:
            #     print(f'type is {type(crd)}')
            #     break
            # elong.append(card)
        hand = Hand(elong)
        hands.append(hand)
        score = hand.rankhand
        #print(f'\n score={score}')
        if score < bestscore: #(lower scores are better: think golf)
            bestscore = score
            wn = n
        n += 1
    winner = hands[wn]
    return winner

############################################################
if __name__ == "__main__":
    pass
    #pokerdeck = Deck()
    
