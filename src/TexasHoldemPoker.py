import os
import sys
import random
from random import shuffle
import time
from pathlib import Path
import pygame
from pygame import Color, Rect, Surface, display, image, font, mouse, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from pygame import QUIT, KEYDOWN, K_ESCAPE, K_SPACE, KEYUP, KMOD_SHIFT
from pygame.transform import smoothscale_by
from PokerRules import Card, Hand, Carddeck, best_hands, logstats, writelog
import json
from PokerHandList import handrankdict
os.environ['SDL_VIDEO_CENTERED'] = '1'  # center screen
os.environ['PYGAME_FORCE_SCALE'] = 'photo'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'
pygame.init()

NUMPLAYERS = 9
HDH = 1920  # 1600 #1440
HDV = 1080  # 900

SIM = False
maxspeed = False
OVERRIDE = False
if len(sys.argv) > 1:
    OVERRIDE = '-o' in sys.argv
if OVERRIDE:
    FULLSCREEN_MODE = False
else:
    FULLSCREEN_MODE = True
SHOWALLHOLECARDS = '-s' in sys.argv

Community_cards = ["cc_Flop1.png", "cc_Flop2.png",
                   "cc_Flop3.png", "cc_Turn.png", "cc_River.png"]
DealerButtons = [[1297, 274], [1492, 525], [1485, 765], [1219, 880], [840, 845],
                 [621, 810], [375, 681], [330, 472], [420, 274]]  # going cw starting with you
ARDPREFIX = 'cp_'
main_dir = os.path.split(os.path.abspath(__file__))[0]


# ------------------------ POKER STUFF---------------------
ANTE = 5
SMALLBET = 10
BIGBET = 20
RAISES_CAP = 3


class HOLDEM:
    LIMIT = 0
    pot_limit = 1
    no_limit = 2
    GAME = 0
    
    
class A:
    pay_small_blind = 0
    pay_big_blind = 1
    fold_initial_round = 2
    call_big_blind = 3
    raise_double_big_blind = 4
    call_big_minus_small = 5
    pay_ante = 6
    straddle = 7
    all_in = 8


class Attitude:
    PassiveAggressive = 0
    StrategicAggressive = 1
    BerzerkerAggressive = 2


class H:
    playerAggression = []
    turn = 0
    pot = 0
    pottext = ''
    bet = 0
    initialStake = 6000
    PlayerStakes = [initialStake, initialStake, initialStake, initialStake,
                    initialStake, initialStake, initialStake, initialStake, initialStake]
    ante = 5
    smallblind = 10
    bigblind = 15
    smallbet = 20
    bigbet = 40
    minbet = bigblind
    current = bigblind
    increment = smallbet
    ibot = 0
    raisecount = 0
    raises = {}


# -----------------------Player record ------------------------


class PokerPlayer:

    name = None

    def __init__(self, name: str, stake: int, tude: Attitude):
        self.name: str = name
        self.inhand: bool = True
        self.stack: int = stake
        self.personality: Attitude = tude


# -----------------------GAME stuff ------------------------


class R:
    PlayerTurn: int = 1
    PlayerList: list = [PokerPlayer]
    ActionPlayer: PokerPlayer  # the betting action's is on you
    layerData = {}  # : [dict]
    card_image_d = {}
    CARDPREFIX = "cp_"
    deck = Carddeck("")
    cccard = 0
    ncc = 3
    step = -1
    the_button: int = 0  # 1
    the_small_blind: int = 1
    the_big_blind: int = 2
    under_the_gun: int = 3
    last_player_to_raise = ''
    PlayerCardPos = {}
    messageq: [str] = []
    HoleCardRecord1 = {}
    HoleCardRecord2 = {}
    playercards = {}
    PlayerHoleCardName1 = {}
    PlayerHoleCardName2 = {}
    CommunityCards = []
    PlayerOrder = {'you': 0, 'Ian': 1, 'Ben': 2, 'Jax': 3, 'Max': 4,
                    'Pam': 5, 'Ray': 6, 'Sal': 7, 'Zak': 8}
    PLAYERNAMES = ['you', 'Ian', 'Ben', 'Jax', 'Max', 'Pam', 'Ray', 'Sal', 'Zak']
    PLAYERCARDXY = {'you': [1249, 356], 'Ian': [1412, 399],
                    'Ben': [1384, 582], 'Jax': [1220, 728],
                    'Max': [928, 728], 'Pam': [636, 728],
                    'Ray': [471, 584], 'Sal': [474, 393], 'Zak': [651, 358]}
    COMMUNITYCARDSXY = [[845, 488], [922, 488], [998, 488], [1071, 488], [1148, 488]]
    CARDWIDTH = 76
    PlayerBestHands = []
    playerscore = {'you': 0, 'Ian': 0, 'Ben': 0, 'Jax': 0, 'Max': 0, 'Pam': 0, 'Ray': 0, 'Sal': 0, 'Zak': 0}
    BOTIMAGES = []
    main_font = pygame.font.SysFont("times", 28)
    ante = False  # set to False if no ante desired
    bets = 0
    waitingonante = False
    cardsdealt = 0
    num_players_in_hand = NUMPLAYERS
    flaglist = []


def next_ActionPlayer():
    limit = NUMPLAYERS
    while limit > 0:
        RO.PlayerTurn = (RO.PlayerTurn + 1) % NUMPLAYERS
        RO.ActionPlayer = RO.PlayerList[RO.PlayerTurn]
        if RO.ActionPlayer.inhand:
            break
        else:
            limit -= 1

def initialization(name: str):
    # takes the place of dozens of separate flags to
    # determine if something has been done yet
    #print("order of deal:",RO.reordered_names)
    if name not in RO.flaglist:
        RO.flaglist.append(name)
        print(f'initialiation {name}')
        return True
    else:
        return False
    

# text_box_rect = pygame.Rect(410, 20, 415 ,435)

def player_relative_to_dealer(orderindeal: int) -> int:
    order = RO.the_button
    for i in range(orderindeal):
        order = (order + 1) % NUMPLAYERS
    return order


RO: R = R()



class LayeredImage:
    loaded: dict
    
    def __init__(self):
        pass

    @classmethod
    def save(cls):
        json_object = json.dumps(LayeredImage.loaded, indent=4)
        with open("lay_out.json", "w") as outfile:
            if outfile.writable():
                outfile.write(json_object)
            else:
                print('lay_out.json file is not writeable.')

    @classmethod
    def load(cls):
        filepath = Path(main_dir, 'assets', 'image', 'blayers', '9 player table.json')
        with open(filepath, 'r') as openfile:
            LayeredImage.loaded = json.load(openfile)
 

LayeredImage.load()

screen: pygame.Surface = pygame.display.set_mode([HDH, HDV], 0, 32)

backgnd = image.load(Path(main_dir, 'assets', 'image', 'Background.png')).convert_alpha()
SCREEN_SIZE = backgnd.get_size()  # (HDH,HDV)
if FULLSCREEN_MODE:
    screen = display.set_mode([HDH, HDV])  # [screenInfo.current_w, screenInfo.current_h], flags=pygame.FULLSCREEN)
    large_window = True  # [HDH, HDV])
else:
    # SCREEN_SIZE = (1600, 900)
    large_window = False
    screen: pygame.Surface = pygame.display.set_mode([1600, 900], 0, 32)
screenInfo = display.Info()
if FULLSCREEN_MODE:
    screen = display.set_mode([screenInfo.current_w, screenInfo.current_h], flags=pygame.FULLSCREEN)  # , vsync=1)
else:
    screen: pygame.Surface = pygame.display.set_mode(SCREEN_SIZE, 0, 32)

SCREEN_SIZE = (screenInfo.current_w, screenInfo.current_h)
print(f'screen size = {screenInfo.current_w}, {screenInfo.current_h}')
SCREENRECT = Rect(0, 0, SCREEN_SIZE[0], SCREEN_SIZE[1])
CENTERBOTTOM = [SCREENRECT.centerx, SCREENRECT.bottom]
WIDTH, HEIGHT = SCREENRECT.size
XCENTER = WIDTH // 2
YCENTER = HEIGHT // 2
isize = [display.Info().current_w, display.Info().current_h]  # backgnd.get_size()]
SCALEH: float = WIDTH / isize[0]  # .82
SCALEV: float = HEIGHT / isize[1]
print(f'WIDTH={WIDTH} SCALEH={SCALEH}')

# backgnd = image.load(Path(maindir, 'assets', 'image', 'Background.png')).convert_alpha()
dealerbutton = image.load(Path(main_dir, 'assets', 'image', 'dbutton.png')).convert_alpha()
winimage = image.load(Path(main_dir, 'assets', 'image', 'win.png')).convert_alpha()
tieimage = image.load(Path(main_dir, 'assets', 'image', 'tie.png')).convert_alpha()
# chipimage = image.load(Path(main_dir, 'assets', 'image', 'blayers','4chips.png')).convert_alpha()
chip5image = image.load(Path(main_dir, 'assets', 'image', 'blayers', 'c5.png')).convert_alpha()
chip10image = image.load(Path(main_dir, 'assets', 'image', 'blayers', 'c10.png')).convert_alpha()
chip100image = image.load(Path(main_dir, 'assets', 'image', 'blayers', 'c100.png')).convert_alpha()
chip500image = image.load(Path(main_dir, 'assets', 'image', 'blayers', 'c500.png')).convert_alpha()
# size = chipimage.get_size()
# chipimage = pygame.transform.smoothscale_by(chipimage, .5)
chip5image = pygame.transform.smoothscale_by(chip5image, .375)
chip10image = pygame.transform.smoothscale_by(chip10image, .375)
chip100image = pygame.transform.smoothscale_by(chip100image, .375)
chip500image = pygame.transform.smoothscale_by(chip500image, .375)
# betimage = pygame.transform.smoothscale_by(betimage0, .5)
# betimagez = pygame.transform.smoothscale_by(betimage, .5)
# betimage1 = image.load(Path(main_dir,'assets', 'image', 'blayers','PlacebetZ.png')).convert_alpha()
background = pygame.transform.smoothscale(backgnd, (WIDTH, HEIGHT))
buttonBlank1 = image.load(Path(main_dir, 'assets', 'image', 'buttonBlank.png')).convert_alpha()
buttonBlank = pygame.transform.smoothscale_by(buttonBlank1, .5) 
buttonQuit1 = image.load(Path(main_dir, 'assets', 'image', 'Quit.png')).convert_alpha()
buttonQuit = pygame.transform.smoothscale_by(buttonQuit1, .5) 
buttonDeal1 = image.load(Path(main_dir, 'assets', 'image', 'Deal.png')).convert_alpha()
buttonDeal = pygame.transform.smoothscale_by(buttonDeal1, .5) 
DownButton = image.load(Path(main_dir, 'assets', 'image', 'Down.png')).convert_alpha()
DownButton = pygame.transform.smoothscale_by(DownButton, .5)
ChipDownButton = image.load(Path(main_dir, 'assets', 'image', 'blayers', 'chipdown.png')).convert_alpha()
ChipDownButton = pygame.transform.smoothscale_by(ChipDownButton, .375)
buttonFold = image.load(Path(main_dir, 'assets', 'image', 'Fold.png')).convert_alpha()
buttonFold = pygame.transform.smoothscale_by(buttonFold, .5) 
buttonCall = image.load(Path(main_dir, 'assets', 'image', 'Call.png')).convert_alpha()
buttonCall = pygame.transform.smoothscale_by(buttonCall, .5) 
buttonRaise = image.load(Path(main_dir, main_dir, 'assets', 'image', 'Raise.png')).convert_alpha()
buttonRaise = pygame.transform.smoothscale_by(buttonRaise, .5) 
buttonBet = image.load(Path(main_dir, 'assets', 'image', 'Bet.png')).convert_alpha()
buttonBet = pygame.transform.smoothscale_by(buttonBet, .5) 
buttonCheck = image.load(Path(main_dir, 'assets', 'image', 'Check.png')).convert_alpha()
buttonCheck = pygame.transform.smoothscale_by(buttonCheck, .5)


Green = Color(38, 155, 46)
dark = Color(55, 10, 25)
darktran = Color(55, 10, 25, 104)
Red = Color(207, 86, 25)


# -------------------------BETS-------------------------------#

# bets before the flop
betbig = 1      # bet the maximum or 3/4 the limit
betave = 2      # bet the average or 1/2 the limit
betsmall = 3    # bet the big blind or 1/4 the limit
betcall = 4     # don't raise, call the minimum, or 1/10 the maximum
betfold = 0     # if not found in dictionary then fold unless a bluff is indicated


foldcallraise = {
    'AA': betbig, 'KK': betbig, 'QQ': betbig, 'JJ': betbig, 'AKs': betbig,
    'AQs': betbig, 'TT': betbig, 'AK': betbig, 'AJs': betbig, 'KQs': betbig, 
    '99': betave, 'ATs': betave, 'AQ': betave, 'KJs': betave, '88': betave, 
    'QJs': betave, 'KTs': betave, 'AJ': betave, 'A9s': betave, 'QTs': betave, 
    'KQ': betsmall, '77': betsmall, 'JTs': betsmall, 'A8s': betsmall, 
    'K9s': betsmall, 'AT': betsmall, 'A7s': betsmall, 'A5s': betsmall, 
    'KJ': betsmall, '66': betsmall, 'Q9s': betsmall, 'A4s': betsmall, 
    'T9s': betcall, 'J9s': betcall, 'QJ': betcall, 'A6s': betcall, '55': betcall, 'A3s': betcall, 
}
traphands = ['AT', 'AJ', 'KQ', 'KJ', 'KT', 'QJ', 'QT']
diceodds = {2: 2.778, 3: 5.556, 4: 8.333, 5: 11.111, 6: 13.889, 7: 16.667,  # dice roll : odds percent
            8: 13.889, 9: 11.111, 10: 8.333, 11: 5.556, 12: 2.778}


def fold_call_or_raise(holecards: str) -> int:
    if holecards in foldcallraise:
        e = foldcallraise[holecards]
        if not (e == betbig | e == betave | e == betsmall | e == betcall):
            return betfold
        else:
            return e
    return betfold


def diceroll() -> int:
    die1 = random.randint(1, 6)
    die2 = random.randint(1, 6)
    return die1 + die2
 

# --------------------All about Cards-------------------------#

cards_52s1 = '2s3s'  '4s5sAd7s8s' 'Kd2h3h4h5h' '6h2d6c8c7d' '6sQhKhAh7c' '3d4d5d6d9c' + \
                    'Ac7h8d9sTc' '5c8h9hThJh' '4c9dTdJdQd' '3cTsJsQsKs' '2cJcQcKcAs'


def read_mini_cards() -> {}:
    """
    load all the minicard images
    """
    sprite_sheet_image = image.load(Path(main_dir, 'assets', 'image', 'cardsheet75x107.png'))
    sprite_sheet_image.convert_alpha()  #screen)
    w, h = sprite_sheet_image.get_size()
    rows = 4
    columns = 13
    rowsize = h // rows
    columnsize = w // columns
    x1, y1 = 0, 0
    imagedict = {}
    ranklist: [str] = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    for suit in ['h', 's', 'c', 'd']:
        for rank in ranklist:
            cardname = rank + suit
            # cardpath = Path(main_dir,'assets', 'image','75', cardname + '.png')
            # cimage: Surface = pygame.image.load(cardpath)
            cimage = Surface((columnsize, rowsize))  # create surfact to blit to
            # blit(source, dest, area=None, special_flags=0) -> Rect
            # Draws a source Surface onto this Surface (the one left of the dot).
            # The draw can be positioned with the dest argument.
            # The dest argument   pair of oordinates representing the position
            # of the upper left corner of the blit. A rect is optional instead, but useless.
            # An optional area rectangle can be passed as well. This represents a
            # smaller portion of the source Surface to draw.
            # !!! It seems simpler to use subsurface, but it may be buggy
            cimage.blit(sprite_sheet_image, (0, 0), area=Rect(x1, y1, columnsize, rowsize))
            # sprite_sheet_image.blit(cimage, (0, 0))
            imagedict[cardname] = cimage.copy().convert_alpha()  #screen)
            x1 += columnsize
        x1 = 0
        y1 += rowsize
        # imagedict[cardname] = cimage.convert_alpha(screen)
    backb = image.load(Path(main_dir, 'assets', 'image', 'backblue75.png'))
    imagedict['bk'] = backb
    return imagedict


testdeck = '2s2c3h3c3s4s4h5c5h6h6c6d7d' \
    '3d4d4c5dAdTs7hAhJc8d8h2h7s2dJs9c6s5sJhKdAcQd9s' \
    '7h7c8c8d9h9dAhAcJdKhKcKsQhQsQc3d4d4c'
#                                      ^ first card dealt


def populate_deck3():
 
    """ Generate test deck from str constant
    """
    cards: [str] = []
    for i in range(0, len(testdeck), 2):
        cards.append(testdeck[i:i+2])
    RO.deck = Carddeck(cards)
 
 
def preloadcards():
    # populate_deck3() #FOR TESTING
    # populate_deck2(cards_52s1)
    RO.deck = Carddeck(cards_52s1)
    RO.card_image_d = read_mini_cards()
 

def pick_a_card() -> (str, image):
    try:
        card = RO.deck.deal_a_card()
    except IndexError:
        print('Out of cards in deck.')
        return None, None
    return card.name, RO.card_image_d[card.name]
 


def scalept(pt: [int, int]) -> [int, int]:
    if SCALEH == SCALEV == 1.0:
        return pt
    return [int(pt[0]*SCALEH), int(pt[1]*SCALEV)]


def scalerect(r: Rect) -> Rect:
    if SCALEH == SCALEV == 1.0:
        return r
    pt = r.topleft
    return Rect(int(pt[0]*SCALEH), int(pt[1]*SCALEV),
                int(r.width*SCALEH), int(r.height*SCALEV))


def scaleblit(image1: image, pos, refit=1.0, scalepos=True):
    if SCALEH == SCALEV == 1.0 and refit == 1.0:
        screen.blit(image1, pos)
        return
    image3 = smoothscale_by(image1, (SCALEH, SCALEV))
    if scalepos:
        spos = [pos[0]*SCALEH, pos[1]*SCALEV]
        screen.blit(image3, spos)
    else:
        screen.blit(image3, pos)


def openimage(layername: str) -> image:
    try:
        if layername[-4:] != '.png':
            layername += '.png'
        layerimage = image.load(Path('assets', 'image', 'blayers', layername))
        # print(f'layername = {layername}')
    except FileNotFoundError:
        print(f"Error: The file {layername} was not found.")
        return None
    return layerimage


def draw_poker_table():
    mainimage = LayeredImage.loaded.get('image')
    layers = mainimage['layers']
    for layer in reversed(layers):
        layername = layer.get("name")
        layerimage = openimage(layername)
        if layerimage is None:
            print(f'    layer {layername} missing.')
        else:
            visible: bool = layer.get("visible")
            offsets: [int] = layer.get("offsets")
            layerimage = layerimage.convert_alpha()  #screen)
            RO.layerData[layername] = [offsets, layerimage, visible]


def CountPlayersinHand() -> int:
    n: int = 0
    for p in RO.PlayerList:
        if p.inhand:
            n += 1
    return n

def inc_deal():
    RO.the_button = (RO.the_button + 1) % NUMPLAYERS
    RO.the_small_blind = (RO.the_small_blind + 1) % NUMPLAYERS
    RO.the_big_blind = (RO.the_big_blind + 1) % NUMPLAYERS
    RO.under_the_gun = (RO.under_the_gun + 1) % NUMPLAYERS


def calc_winner() -> int:
    RO.playercards = {}
    for player in RO.PlayerList:
        offsets, deck_cardname1, diskcardimage = RO.HoleCardRecord1[player.name]
        offsets, deck_cardname2, diskcardimage = RO.HoleCardRecord2[player.name]
        RO.playercards[player.name] = [Card(deck_cardname1), Card(deck_cardname2)]
        print(f'player={RO.playercards[player.name]}')
    RO.PlayerBestHands = []
    for player in RO.PlayerList:
        besthand = best_hands(RO.playercards[player.name], RO.CommunityCards)
        RO.PlayerBestHands.append(besthand)
    wn = 0
    # RO.playerscore = {'you': 0, 'Ian': 0, 'Ben': 0, 'Jax': 0, 'Max': 0, 'Pam': 0, 'Ray': 0, 'Sal': 0, 'Zak': 0}
    scores = []
    bestscore = 7462  # start with lowest possible score (highest number)
    for player, n in enumerate(RO.PlayerList):
        besthands()
        hand: [Hand] = RO.PlayerBestHands[n]  # .hand_name
        score = hand.rankhand  # get_rank(hand.sname,  hand.name)
        scores.append(score)
        writelog([f'{player.name}:{hand.name}:{hand.sname}'])
        if score < bestscore:  # (lower scores are better: think golf)
            bestscore = score
            wn = n
    pos = DealerButtons[wn]  # RO.PLAYERNAMES[
    scaleblit(winimage, pos)
    # print(f'pos= {pos} wn={wn}')
    winners = []
    if scores.count(bestscore) > 1:
        for i, score in enumerate(scores):
            if score == bestscore:
                pos = DealerButtons[i]
                scaleblit(tieimage, pos)
                winners.append(RO.PlayerList[i].name)
        splitpot(winners)
    print(f'winners: {winners}')
    return wn


def splitpot(winnernames: []):
    scount = len(winnernames)
    # wn = -1
    potdiv = H.pot // scount
    for name in winnernames:
        i = RO.PLAYERNAMES.index(name)
        H.PlayerStakes[i] += potdiv
    
    
def besthands():
    RO.PlayerBestHands = []
    # for playernum in range(NUMPLAYERS): #RO.PLAYERS
    for player in RO.PlayerList:
        if player.inhand:
            holecards = [RO.HoleCardRecord1[player.name][1], RO.HoleCardRecord2[player.name][1]]
            besthand = best_hands(holecards, RO.CommunityCards)
            RO.PlayerBestHands.append(besthand)
    return RO.PlayerBestHands


def set_card_offsets_simple():
    RO.PlayerCardPos = {}
    for player in RO.PlayerList:
        RO.PlayerCardPos[player.name] = scalept(RO.PLAYERCARDXY[player.name])


# def set_card_offsets():
#     RO.PlayerCardPos = {}
#     for player in RO.PlayerList:
#         layername = RO.CARDPREFIX+player.name+'.png'
#         offsets, layerimage, visible = RO.layerData[layername]
#         RO.PlayerCardPos[player] = scalept(offsets)


def dealholecard(ang: int, second: bool, initc=False):
    if initc:
        if second:
            RO.HoleCardRecord2 = {}
        else:
            RO.HoleCardRecord1 = {}
    offsets = RO.PlayerCardPos[RO.ActionPlayer.name]
    pos = offsets.copy()
    deck_cardname, deck_cardimage = pick_a_card()
    diskcardimage = RO.card_image_d[deck_cardname]
    if second:
        RO.HoleCardRecord2[RO.ActionPlayer.name] = (offsets, deck_cardname, diskcardimage)
    else:
        RO.HoleCardRecord1[RO.ActionPlayer.name] = (offsets, deck_cardname, diskcardimage)
    backx = RO.card_image_d['bk']
    card1 = diskcardimage
    showyou = SHOWALLHOLECARDS or RO.ActionPlayer.name == 'you'
    if showyou:
        a1 = 0.
        if second:
            pos[0] += 75
    else:
        if second:
            pos[0] += 10
            a1 = -ang
        else:
            a1 = ang
    spindeal(pos, backx, card1, screen, WIDTH // 2, angle=a1, showcard=showyou)


def dealholecards(ang: int, second: bool):
    if second:
        RO.HoleCardRecord2 = {}
    else:
        RO.HoleCardRecord1 = {}
    for player in RO.PlayerList:
        offsets = RO.PlayerCardPos[player.name]
        pos = offsets.copy()
        deck_cardname, deck_cardimage = pick_a_card()
        diskcardimage = RO.card_image_d[deck_cardname]
        if second:
            RO.HoleCardRecord2[player] = (offsets, deck_cardname, diskcardimage)
        else:
            RO.HoleCardRecord1[player] = (offsets, deck_cardname, diskcardimage)
        backx = RO.card_image_d['bk']
        card1 = diskcardimage
        showyou = player.name == 'you'
        if showyou:
            a1 = 0.
            if second:
                pos[0] += 75
        else:
            if second:
                pos[0] += 10
                a1 = -ang
            else:
                a1 = ang
        spindeal(pos, backx, card1, screen, WIDTH//2, angle=a1, showcard=showyou)
    RO.PlayerTurn = RO.the_button  # RO.under_the_gun


def showholecards():
    playernum = 0
    for player in RO.reordered_names:
        showholecard(playernum)
        playernum += 1


def showholecard(playernum: int):
    playername = RO.reordered_names[playernum]
    offsets, cardname, cardimage = RO.HoleCardRecord1[playername]
    #print(f'hole cards = {RO.HoleCardRecord2}')
    offsets2, cardname2, cardimage2 = RO.HoleCardRecord2[playername]
    cardsize = cardimage.get_size()
    x1 = offsets[0] - 10
    y1 = offsets[1] #- 10
    x2 = offsets[0]- 10 + cardsize[0] + 2
    y2 = offsets[1] #- 10
    cardrect = Rect(offsets[0] - 10, offsets[1] - 10, cardsize[0]*2+2, cardsize[1]+8)
    pygame.draw.rect(screen, Color(207, 86, 25), cardrect, width=0)
    scaleblit(cardimage, [x1, y1])
    scaleblit(cardimage2, [x2, y2])


class CardAnimate:
    cardhand: [Surface] = []
    cardloc: [int, int] = []
    CLOCK = pygame.time.Clock()



def spinmovescaleblit(surf: Surface, dest: Surface, xmove: int, ymove: int,
                      degrees: float, scale: float):
    sr = surf.get_rect()
    surf.get_rect().move_ip(xmove, ymove)
    snew: Surface = pygame.transform.rotozoom(surf, degrees, scale)
    dest.blit(snew, snew.get_rect(center=(sr.centerx + xmove, sr.centery + ymove)))


def spindeal(tpos: [int, int], back: Surface, card: Surface, window: Surface,
             swidth, angle=0., showcard=False):
    run = True
    cx = swidth // 2 + 360
    cy = back.get_height()+28  # HEIGHT
    cx, cy = scalept([cx, cy])
    angle1: float = angle
    if showcard:
        rot_card = card
    else:
        rot_card = back
    fps = 120
    pygame.event.set_blocked(pygame.MOUSEMOTION)
    # Create a new surface with the same size as the screen
    screen_copy = pygame.Surface(window.get_size()) 
    # Blit the screen onto the new surface
    screen_copy.blit(window, (0, 0)) 
    t: float = 0.
    dt: float = 0.022222222222222
    bx = 0
    by = 1.
    cs = 0
    while run:
        CardAnimate.CLOCK.tick(fps)
        window.blit(screen_copy, (0, 0))
        screen_copy.blit(window, (0, 0))
        cs = max(.25, t) * SCALEH
        bx = int(cx * (1.-t) + tpos[0] * t)
        by = int(cy * (1.-t) + tpos[1] * t)
        angle1 += 2
        spinmovescaleblit(rot_card, window, bx, by, angle1, cs)
        cardrect = Rect(bx, by, rot_card.get_width(), rot_card.get_height())
        pygame.display.update(cardrect)
        t += dt
        run = t <= 1.
    window.blit(screen_copy, (0, 0))
    screen_copy.blit(window, (0, 0))
    spinmovescaleblit(rot_card, window, bx, by, angle, cs)
    pygame.display.flip()


def dealflop():
    dealcommunitycards()  # RO.cccard)
    RO.cccard = (RO.cccard + 1)  # % 5
    dealcommunitycards()  # RO.cccard)
    RO.cccard = (RO.cccard + 1)  # % 5
    dealcommunitycards()  # RO.cccard)
    RO.cccard = (RO.cccard + 1)  # % 5


def dealturn():
    dealcommunitycards()  # RO.cccard)
    RO.cccard = (RO.cccard + 1) % 5


def dealriver():
    dealcommunitycards()  # RO.cccard)
    RO.cccard = (RO.cccard + 1) % 5

    
def dealcommunitycards():
    ccnum = RO.cccard
    deck_cardname, deck_cardimage = pick_a_card()
    card: Card = Card(deck_cardname)
    RO.CommunityCards.append(card)
    diskcardimage = RO.card_image_d[deck_cardname]
    rcard = Community_cards[ccnum]
    offsets = RO.COMMUNITYCARDSXY[ccnum]
    offsets = scalept(offsets)
    backx = RO.card_image_d['bk']
    card1 = diskcardimage
    coff = [offsets[0], offsets[1] + 6]
    spindeal(coff, backx, card1, screen, WIDTH//2, angle=0, showcard=True)


def drawlayers():
    screen.fill(Green)
    for layername, layerdata in RO.layerData.items():
        offsets, layerimage, visible = layerdata
        if visible:
            scaleblit(layerimage, offsets)


def draw_text_labels(bottexts: [str]):
    i = -1
    RO.BOTIMAGES = []
    for index, bot_name in enumerate(bottexts):
        i += 1
        pos = DealerButtons[index]
        # info = bot_name  # + ': $'+str(stack[i])
        imagelabel = labelimage(RO.PLAYERNAMES[index], pos, Color(4, 24, 5), shadow=Color(250, 252,  23))
        RO.BOTIMAGES.append(imagelabel)
        scaleblit(imagelabel, pos)
    return


def drawbotlabels():
    for n in range(len(RO.PlayerList)):
        pos = DealerButtons[n]
        txt = RO.PlayerList[n].name
        print(pos, n, txt)
        draw_labels(pos, n, txt)


def draw_labels(pos: [int, int], player_num: int, info: str) -> image:
    q = RO.PlayerBestHands[player_num]
    stack = H.PlayerStakes[player_num]
    handkey = [k for k, v in handrankdict.items() if v == q.rankhand][0]
    infoline = f'{info}:${stack} :{handkey}:{q.hand_name}'  # {q.rankhand}'
    writelog([infoline], printalso=True)
    textimage = labelimage(infoline, pos, Color(4, 24, 5), shadow=Color(250, 252, 23))
    return textimage


def labelimage(caption: str, pos: [int, int],
               uicolor: Color, shadow=Color(5, 23, 25)) -> image:
    # uicolor = Color(240,235,255)
    uifontsize = 28
    uifontnum: font.Font = pygame.font.SysFont("Times", uifontsize)
    csize = uifontnum.size(caption)
    pygame.draw.rect(screen, shadow, Rect(pos[0], pos[1], csize[0], csize[1]))
    textimage = uifontnum.render(caption, True, Color(125, 124, 15)).convert_alpha()
    scaleblit(textimage, pos)
    textimage2 = uifontnum.render(caption, True, uicolor).convert_alpha()
    scaleblit(textimage2, [pos[0]-1, pos[1]-1])
    return textimage
 
 
def refresh_display():
    display.flip()


def drawdealerbutton():
    pos = DealerButtons[RO.the_button]
    scaleblit(dealerbutton, pos)


#  ---------------------stack/pot math--------------------------------#
    # the "ready bet" area is a spot that accumulates a potential bet
    # by clicking on the chips in the upper right corner
def ready_bet(amount):
    H.bet += amount
    H.current = amount
    labelimage(f'Bet: {H.bet}', K.placetext.topleft,
               Color(250, 205, 25), shadow=Color(5, 23, 25))


def placebet(action: str):
    match action:
        case "Fold":
            H.bet = 0  # sit out the rest of the hand
            RO.ActionPlayer.inhand = False
            return
        case "Call":
            # find the current bet amount and call it
            H.bet = H.current
        case "Raise":
            # find the amount of the maximum raise and bet it
            H.bet = H.minbet
            H.raises[RO.ActionPlayer.name] = H.bet
            RO.last_player_to_raise = RO.ActionPlayer

        case "Bet":
            if RO.ActionPlayer.name == 'you':  # call, raise, or fold as appropriate
                H.bet = H.current
        case "Bet":
            if RO.ActionPlayer.name == 'you':  # call, raise, or fold as appropriate
                H.bet = H.current
        case "Check":
            if RO.ActionPlayer.name == 'you':  # call, raise, or fold as appropriate
                H.bet = 0
        case _:
            H.bet = 0
    # pygame.event.pump()
    RO.ActionPlayer.stack -= H.bet
    H.pottext += f'+${H.bet}'
    H.pot += H.bet
    H.bet = 0
    labelimage(f'              ', K.placetext.topleft,
               Color(250, 205, 25), shadow=Color(5, 23, 25))
    potimage = RO.main_font.render(f'${H.pot}', True, Color(5, 23, 25)).convert_alpha()
    potimage2 = RO.main_font.render(H.pottext, True, Color(5, 23, 25)).convert_alpha()
    pygame.draw.rect(screen, Red, K.potrect, width=0)
    pygame.draw.rect(screen, dark, K.potrect, width=3)
    screen.set_clip(K.potrect)
    scaleblit(potimage, K.potrect.topleft)
    scaleblit(potimage2, [K.potrect.left, K.potrect.top+28])
    screen.set_clip(None)
    # pygame.event.pump()
    
    
# ----------------------SCROLL LIST--------------------------#
class K:
    textrect = scalerect(Rect(819, 20, 415, 378))
    text_surf_list = []  
    wsurface = screen.subsurface(textrect) 
    potrect = scalerect(Rect(819, textrect.bottom+1, 415, 90))
    # backgroundx = pygame.Surface(textrect.size)
    pclock = pygame.time.Clock()
    # shrink = 0.75
    si = 60
    startx = 1565
    starty = 0
    text_y = 0
    # startx, starty = [startx, starty]
    placetext: Rect = Rect(startx, 200, 200, 35)
    bet500Rect: Rect = Rect(startx, starty + 20, si, si)
    bet100Rect: Rect = Rect(startx+55, starty + 48, si, si)
    bet10Rect: Rect = Rect(startx+112, starty + 80, si, si)
    bet5Rect: Rect = Rect(startx+171, starty + 105, si, si)
    placebetPos = [placetext.left - 8, placetext.top - 58]
    # placebetRect = Rect(placebetPos[0], placebetPos[1],76,23)


def whichclicked(rectlist: [Rect], pos: [int, int]) -> int:
    # spos = scalept(pos)
    for i, r in enumerate(rectlist):
        r2 = scalerect(r)
        if r2.collidepoint(pos):
            return i
    return -1


def setupui():
    drawlayers()
    drawdealerbutton()
    RO.PLAYERIN = [True, True,  True,  True, True, True,  True, True, True]

    #for i in range(0, NUMPLAYERS):
    #    RO.inhand.append(True)
    # pos = [1550, 5]
    pygame.event.set_blocked(pygame.MOUSEMOTION)
    K.wsurface.fill(Color(0, 0, 0), rect=K.textrect, special_flags=0)
    pygame.draw.rect(screen, dark, K.potrect, width=3)
    

def there_are_messages() -> bool:
    return len(RO.messageq) > 0


def messages() -> str:
    if len(RO.messageq) > 0:
        return RO.messageq.pop(0)
    else:
        return ''


def foldplayer():
    postmessage(f'{RO.ActionPlayer.name} {"fold" if RO.ActionPlayer.name == "you" else "folds"}')
    RO.ActionPlayer.inhand = False



def chooseverb(pluralverb: str, singularverb: str):
    return f' {singularverb if RO.ActionPlayer.name == "you" else pluralverb}'


def bet(bettype: int):
    if bettype == A.fold_initial_round:
        RO.ActionPlayer.inhand = False
    if bettype == A.call_big_blind:
        RO.ActionPlayer.stack -= H.bigblind
        H.pot += H.bigblind
        postmessage(f'{RO.ActionPlayer.name} {chooseverb("calls", "call")}')
    if bettype == A.pay_ante:
        RO.ActionPlayer.stack -= H.ante
        H.pot += H.ante
        postmessage(f'{RO.ActionPlayer.name} {"pays ante" if RO.PlayerOrder[RO.ActionPlayer.name] > 0 else "pay ante"}')
    if bettype == A.raise_double_big_blind:
        RO.ActionPlayer.stack -= H.bigblind * 2
        H.raiseamount = H.bigblind * 2
        H.pot += H.raiseamount
        postmessage(f'{RO.ActionPlayer.name} {chooseverb("raises", "raise")} {H.raiseamount}')
    if bettype == A.call_big_minus_small:
        RO.ActionPlayer.stack -= (H.bigblind - H.smallblind)
        H.pot += (H.bigblind - H.smallblind)
        postmessage(f'{RO.ActionPlayer.name} {chooseverb("calls", "call")} ')

    

def preflop_betting():
    dealto = RO.PlayerTurn
    card1: str = RO.HoleCardRecord1[RO.ActionPlayer.name][1]
    card2: str = RO.HoleCardRecord2[RO.ActionPlayer.name][1]
    rank1: int = Card.rankOrderD[card1[0]]
    rank2: int = Card.rankOrderD[card2[0]]
    if card1[1] == card2[1]:
        suited = 's'
    else:
        suited = ''
    if rank1 < rank2:
        holecards = card2[0]+card1[0]+suited
    else:
        holecards = card1[0] + card2[0] + suited
    if fold_call_or_raise(holecards) == betfold and dealto == 8:
        if CountPlayersinHand() == 1:  # you are the big  blind and only one left in
            bet(A.pay_big_blind)
        else:
            bet(A.fold_initial_round)
        postmessage(f'{RO.ActionPlayer.name} folds pre-flop: {holecards}')
        return
    if dealto == 1:
        verb = chooseverb("pays", "pay")
        postmessage(f'{dealto}:{RO.ActionPlayer.name} {verb} the small blind: {holecards}')
        bet(A.pay_small_blind)
    elif dealto == 2:
        verb = chooseverb("pays", "pay")
        postmessage(f'{dealto}:{RO.ActionPlayer.name}  {verb}  the big blind: {holecards}')
        bet(A.pay_big_blind)
    elif dealto == 3 and fold_call_or_raise(holecards) == betfold:
        if RO.ActionPlayer.personality == G.BerzerkerAggressive and diceroll() == 7:  # 17% chance
            verb = chooseverb("raises", "raise")
            postmessage(f'{dealto}:{RO.ActionPlayer.name} {verb} by double the big blind: {holecards}')
            bet(A.raise_double_big_blind)
        else:
            verb = chooseverb("folds", "fold")
            postmessage(f'{RO.ActionPlayer}  {verb}  preflop: {holecards}')
            bet(A.fold_initial_round)
    elif dealto == 3 and fold_call_or_raise(holecards) == betbig:
        verb = chooseverb("raises", "raise")
        print(f'{dealto}:{RO.ActionPlayer} {verb} by double the big blind: {holecards}')
        bet(A.raise_double_big_blind)
    elif 2 < dealto < 8 and fold_call_or_raise(holecards) <= betave:
        verb = chooseverb("calls", "call")
        postmessage(f'{dealto}:{RO.ActionPlayer} {verb} the big blind: {holecards}')
        bet(A.call_big_blind)
    elif dealto == 1 and fold_call_or_raise(holecards) <= betave:
        verb = chooseverb("calls", "call")
        postmessage(f'{dealto}:{RO.ActionPlayer.name} {verb} the big blind: {holecards}')
        bet(A.call_big_minus_small)


# TODO: Finish
def post_flop_betting(dealto: int):
    better = RO.reordered_names[dealto]
    return better  # just for now
    # playernum = RO.PLAYERS[better]


def next_card(init=False):
    if init:
        RO.PlayerTurn = RO.the_button
        RO.cardsdealt = 0
    next_turn()
    RO.cardsdealt += 1
    return

def next_turn(init = False):
    if init:
        RO.PlayerTurn = RO.the_button
    else:
        RO.PlayerTurn = (RO.PlayerTurn + 1) % NUMPLAYERS
    RO.ActionPlayer = RO.PlayerList[RO.PlayerTurn]


def next_bet(init=False, preholecards=False) -> bool:
    next_turn()
    if init:
        RO.bets = 0
        #RO.PlayerTurn = RO.the_button
        #RO.ActionPlayer = RO.PlayerList[RO.PlayerTurn]
        if preholecards:
            bet(H.bigblind)
            RO.bets += 1
        else:
             RO.bets += 2
    else:
        #next_turn()
        RO.bets += 1


def postmessage(message: str):
    RO.messageq.append(message)
    # print(message)


def messageswaiting() -> bool:
    return len(RO.messageq) > 0


def showmessage(message: str):
    # return
    if len(message) > 0:
        postmessage(message)
    if len(RO.messageq) > 0:
        message = RO.messageq.pop(0)
    K.text_surf = RO.main_font.render(message, True, Color(15, 100, 255))
    # K.text_surf_list.append(K.text_surf)
    h = RO.main_font.get_height()
    K.text_y = K.textrect.bottom - h - 10
    scaleblit(K.text_surf, (K.textrect.left + 10, K.text_y))
    K.wsurface.scroll(0, -h)
    display.update(K.textrect)
    pygame.time.wait(200)


def getline() -> [str]:  #this is temporary to debug scrolling message system
    H.ibot = (H.ibot + 1) % NUMPLAYERS  # 9
    bot = RO.PLAYERNAMES[H.ibot]
    if bot == 'you':
        names = ['you fold.', 'you call big blind',
                 'you raise 2 x big blind', 'you bet 20', 'you bet 40']
    else:
        names = [f'{bot} folds.', f'{bot} calls big blind',
                 f'{bot} raises 2 x big blind', f'{bot} bets', f'{bot} bets 20', f'{bot} bets 40']
    return names


def sequencer() -> bool:
    # the sequencer makes things happen in a specific
    # order consistent with the rules of hold'em.
    # Actions by bots will happen in a short time window,
    # but actions by 'you' will wait for an event.
    # 1. the first action is for the blinds to be collected.
    # 2. then betting proceeds to the player clockwise from the big blind.
    # 3. if the game is limit holdem, bets are made in increments
    #  of the small bet and the big bet.
    #  They may fold, call, or raise, but they must, at least,
    #  deposit chips matching the big blind.
    #
    # Before the flop and after the flop you bet in increments of the small bet.
    # After the turn and river, players bet in increments of the big bet.
    # The SMALLBET is 10 and the BIGBET is 20.
    #
    # The rules are different for Pot Limit Holdem and no limit Holdem.
    # Check-raise is permitted in all games, except in certain forms of lowball.
    # In no-limit and pot-limit games, unlimited raising is allowed.
    #
    # In limit poker, for a pot involving three or more players who are not all-in,
    # there is a maximum of a bet and three raises all owed.
    # Unlimited raising for money games is allowed in heads-up play. This applies any
    # time the action becomes heads-up before the raising has been capped. Once the
    # raising is capped on a betting round, it cannot be uncapped by a subsequent
    # fold that leaves two players heads-up. For tournament play, the three raise
    # maximum for limit poker applies when heads-up as well.

    # In limit play, an all-in wager of less than half a bet does not reopen the
    # betting for any player who has already acted and is in the pot for all previous bets.
    #
    # A player facing less than half a bet can fold, call, or complete the wager.
    # An all-in wager of a half a bet or more is treated as a full bet, and a player may
    # fold, call, or make a full raise. (An example of a full raise is on a $20 betting
    # round,raising a $15 all-in bet to $35).
    # Any wager must be at least the size of the previous bet or raise in that round,
    # unless a player is going all-in.
    #
    # A player putting on a straddle makes a blind bet, before the cards are dealt, that
    # is at least double the big blind amount. The straddle takes the place of the big blind,
    # as all subsequent players must call or raise based on the straddle amount.

    setupui()
    # drawlayers()
    blankpos = [K.bet5Rect.right + 10, K.bet5Rect.top - 100]
    quitrect = Rect(blankpos[0], blankpos[1], 82, 42)
    dealrect = Rect(blankpos[0], blankpos[1] + 45, 82, 42)
    dealmouserect = Rect(dealrect.topleft, dealrect.size)
    scaleblit(buttonQuit, blankpos)
    scaleblit(buttonDeal, dealrect.topleft)
    area2pos = [blankpos[0], blankpos[1] + 100]  # [100,100]
    foldrect = Rect(area2pos[0], area2pos[1], 82, 42)
    callrect = Rect(area2pos[0], area2pos[1] + 45, 82, 42)
    raiserect = Rect(area2pos[0], area2pos[1] + 45 * 2, 82, 42)
    betrect = Rect(area2pos[0], area2pos[1] + 45 * 3, 82, 42)
    checkrect = Rect(area2pos[0], area2pos[1] + 45 * 4, 82, 42)
    scaleblit(buttonFold, foldrect.topleft)
    scaleblit(buttonCall, callrect.topleft)
    scaleblit(buttonRaise, raiserect.topleft)
    scaleblit(buttonBet,  betrect.topleft)
    scaleblit(buttonCheck,  checkrect.topleft)
    quitflag = False
    resetflag = True
    # shiftkey = False
    timer_event = pygame.event.custom_type()
    # card_event = pygame.event.custom_type()
    betplaced = False
    if maxspeed:
        vardelay = 40
    else:
        vardelay = 150
    scroll_timer = True
    # show_cards = False
    # !!!
    yscroll = 0
    if HOLDEM.GAME == HOLDEM.LIMIT:
        H.increment = SMALLBET
    K.wsurface.fill(Color(0, 0, 0), rect=K.textrect, special_flags=0)
    startx = 1575
    starty = 0
    si = 60
    rtxt = ''
    placetext: Rect = Rect(startx, 200, 200, 35)
    K.bet500Rect = Rect(startx, starty + 20, si, si)
    K.bet100Rect = Rect(startx + 55, starty + 48, si, si)
    K.bet10Rect = Rect(startx + 112, starty + 80, si, si)
    K.bet5Rect = Rect(startx + 171, starty + 105, si, si)
    K.PlaceBetPos = [placetext.left - 8, placetext.top - 58]
    scaleblit(chip5image, K.bet5Rect)
    scaleblit(chip10image, K.bet10Rect)
    scaleblit(chip100image, K.bet100Rect)
    scaleblit(chip500image, K.bet500Rect)

    buttonrects = [K.bet5Rect, K.bet10Rect, K.bet100Rect, K.bet500Rect, quitrect, dealmouserect,
                   foldrect, callrect, raiserect, betrect, checkrect]
    buttonimages = [chip5image, chip10image, chip100image, chip500image, buttonQuit, buttonDeal,
                    buttonFold, buttonCall, buttonRaise, buttonBet, buttonCheck]
    buttonindex = -1
    # upbuttonindex = 0
    # targetrect: Rect = Rect(0, 0, 0, 0)  # K.bet5Rect
    # targetimage: image = buttonimages[0]
    delayed_sequence = False
    shiftkey = False
    RO.flaglist = []
    # stepinit = True
    firstrun = True
    # duration = 0
    RO.step = -1
    pygame.time.set_timer(timer_event, 1800)
    running = True
    # ---------------start event loop ------------------#
    while running:
        for ev in pygame.event.get():
            # writelog([f'ev.type={ev.type} ev.dict={ev.dict}'])
            if ev.type == QUIT:
                running = False
                quitflag = True
                break
            elif ev.type == timer_event:
                # print('timer event')
                if scroll_timer:
                    pygame.time.set_timer(timer_event, 200)
                    K.wsurface.scroll(0, yscroll)
                    staterect = Rect(K.textrect.left - 100, K.text_y, 85, 25)
                    pygame.draw.rect(screen, Color(207, 86, 25), staterect, width=0)
                    screen.blit(K.text_surf, staterect)
                    K.pclock.tick_busy_loop(30)
                    # print('scroll_timer event RESET to 200ms')
                # continue
                if firstrun:
                    firstrun = False
                    RO.step = 0
                # write commentary to scrolling list
                if SIM:
                    names = getline()
                    rtxt = random.choice(names)
                else:
                    if scroll_timer:
                        rtxt = messages()
                        writelog([rtxt], printalso=True)
                K.text_surf = RO.main_font.render(rtxt, True, Color(15, 100, 255))
                K.text_y = K.textrect.bottom - RO.main_font.get_height() - 10
                scaleblit(K.text_surf, (K.textrect.left + 10, K.text_y))
                scroll_timer = True
                #pygame.time.set_timer(timer_event, vardelay)
                pygame.time.set_timer(timer_event, vardelay if scroll_timer else 0)
                if maxspeed:
                    vardelay = 4
                else:
                    vardelay = random.randint(350, 500)
                yscroll = (-1 if scroll_timer else 0)

            elif ev.type == KEYDOWN:
                mod = pygame.key.get_mods()
                shiftkey = mod & KMOD_SHIFT
                # controlkey = mod & KMOD_CTRL
                if ev.key == K_ESCAPE:
                    running = False
                    quitflag = True
                    break
                elif ev.key == K_SPACE:
                    running = False
                    break

            elif ev.type == KEYUP:
                shiftkey = False

            elif ev.type == MOUSEBUTTONDOWN and ev.button == 1:  # left mouse buton:
                mousepos = mouse.get_pos()
                buttonindex = whichclicked(buttonrects, mousepos)
                if buttonindex > 3:
                    targetrect = buttonrects[buttonindex]
                    targetimage = DownButton
                    scaleblit(targetimage, targetrect)
                    display.update(targetrect)
                elif 0 <= buttonindex <= 3:
                    targetrect = buttonrects[buttonindex]
                    targetimage = ChipDownButton
                    scaleblit(targetimage, targetrect)
                    display.update(targetrect)

            elif ev.type == MOUSEBUTTONUP and ev.button == 1:  # left mouse buton:
                mousepos = mouse.get_pos()
                upbuttonindex = whichclicked(buttonrects, mousepos)
                if upbuttonindex > -1:  # and buttonindex == upbuttonindex
                    targetrect = buttonrects[upbuttonindex]
                    targetimage = buttonimages[upbuttonindex]
                    scaleblit(targetimage, targetrect)
                    display.update(targetrect)  # targetimage.get_rect())
                elif buttonindex > -1:
                    targetrect = buttonrects[buttonindex]
                    targetimage = buttonimages[buttonindex]
                    scaleblit(targetimage, targetrect)
                if upbuttonindex != -1 and buttonindex == upbuttonindex:
                    m = -1 if shiftkey else 1
                    match upbuttonindex:
                        case 0:  # K.bet5Rect
                            ready_bet(5 * m)
                        case 1:  # K.bet10Rect
                            ready_bet(10 * m)
                        case 2:  # K.bet100Rect
                            ready_bet(100 * m)
                        case 3:  # K.bet500Rect
                            ready_bet(500 * m)
                        case 4:  # quitrect
                            running = False
                            quitflag = True
                            break
                        case 5:  # dealmouserect
                            running = False
                            quitflag = False
                            resetflag = True
                            break
                        case 6:  # foldrect
                            placebet('Fold')
                            betplaced = True
                        case 7:  # callrect
                            placebet('Call')
                            betplaced = True
                        case 8:  # raiserect
                            placebet('Raise')
                            betplaced = True
                        case 9:  # betrect
                            placebet('Bet')
                            betplaced = True
                        case 10:  # checkrect
                            placebet('Check')
                            betplaced = True
                        case _:  # no button clicked
                            pass
                    if betplaced:
                        print('bet placed')
                        betplaced = False
                        delayed_sequence = False
            K.text_surf = RO.main_font.render('state:' + str(RO.step), True, Color(15, 100, 255))  # Color('white'))
            K.text_y = K.textrect.bottom - RO.main_font.get_height() + 100
            staterect = Rect(K.textrect.left - 100, K.text_y, 85, 25)
            pygame.draw.rect(screen, Color(207, 86, 25), staterect, width=0)
            screen.blit(K.text_surf, staterect)
            K.pclock.tick_busy_loop(30)
            if delayed_sequence:  # or messageswaiting()
                # print('delayed_sequence')
                continue

        # if maxspeed:
        #     K.wsurface.scroll(0,yscroll)
        #     display.flip()
        #     K.clock.tick(230)
        # else:
        yscroll = (-1 if scroll_timer else 0)
        K.wsurface.scroll(0, yscroll)
        display.flip()
        # display.update()
        K.pclock.tick(60)
        if delayed_sequence:  # or messageswaiting()
            # print('delayed_sequence')
            continue
        match RO.step:
            case 0:  # optional ante
                RO.PlayerTurn = RO.the_button
                RO.ActionPlayer = RO.PlayerList[RO.PlayerTurn]
                print(f'case: 0')
                #(init=True, preholecards=True)
                # if RO.ante:
                #     bet(A.pay_ante)
                #     msg = f'{RO.ActionPlayer.name} posts ante'
                #     postmessage(msg)
                #else:
                next_turn()
                bet(A.pay_big_blind)
                msg = f"{RO.ActionPlayer.name} is in"
                postmessage(msg)
                # if RO.bets >= NUMPLAYERS:
                #     if RO.ante:
                #         postmessage('all players post ante')
                #     else:
                #         postmessage('All players are in')
                RO.step = 1

            case 1:  # small blind
                print(f'case: 1')
                #RO.PlayerTurn = RO.the_button
                next_turn()
                bet(A.pay_small_blind)
                postmessage(f'{RO.ActionPlayer.name} {chooseverb("posts", "post")} the small blind')
                RO.step = 2

            case  2:  # big blind
                if initialization('big blind'):
                    next_bet()
                    bet(A.pay_big_blind)
                    postmessage(f'{RO.ActionPlayer.name} {chooseverb("posts", "post")} the big blind')
                    RO.step = 3

            case 3:  # deal the first hole card
                if initialization('holecard1'):
                    next_card(init=True)
                    dealholecard(10, False, initc= True)
                    continue
                else:
                    next_card(init=False)
                # player = RO.reordered_names[RO.deal_target]
                #print(f'#{RO.cardsdealt} card to {RO.deal_target_name} num_players_in_hand: {RO.num_players_in_hand}')
                dealholecard(10, False)
                print(f' Players in hand {CountPlayersinHand()}')
                if RO.cardsdealt >= CountPlayersinHand():
                    RO.step = 4
                    # pygame.time.set_timer(card_event, 1800)

            case 4:
                if initialization('holecard2'):
                    next_card(init=True)
                    #print(f'#{RO.cardsdealt} card to {RO.deal_target_name}')
                    dealholecard(10, True, initc=True)
                    postmessage("Dealing second hole card")
                    continue
                else:
                    next_card()
                print(f' {RO.cardsdealt} card to {RO.ActionPlayer.name}')
                dealholecard(10, True)
                if RO.cardsdealt >= NUMPLAYERS:
                    K.wsurface.fill(Red)
                    RO.step += 1
                    # pygame.time.set_timer(card_event, 1800)

            case 5:
                if initialization('preflop_betting'):
                    if RO.ActionPlayer.name == 'you':
                        delayed_sequence = True
                    else:
                        preflop_betting()
                else:
                    if next_turn():
                        preflop_betting()

                if RO.ActionPlayer.name == 'you':
                    postmessage("Your bet")
                    delayed_sequence = True  # continue
                if delayed_sequence is False or RO.bets >= CountPlayersinHand():
                    RO.step += 1

            case 6:  # flop
                dealflop()
                RO.step += 1

            case 7:  #
                if initialization('post_flop_betting'):
                    delayed_sequence = True
                    if next_turn(init=True):
                        bet(RO.bet_target_name, A.raise_double_big_blind)
                else:
                    if next_turn():
                        bet(RO.bet_target_name, A.raise_double_big_blind)
                    if RO.bet_target_name == 'you':
                        delayed_sequence = True
                        postmessage("Your bet")
                        continue
                #print(f'{RO.bet_target_name} is bet #{RO.bets}')
                if RO.bets >= NUMPLAYERS:
                    RO.step += 1

            case 8:  # turn
                dealturn()
                RO.step += 1

            case 9:  # post_turn_betting
                if initialization('post_turn_betting'):
                    delayed_sequence = True
                    if next_turn(init=True):
                        bet(RO.bet_target_name, A.raise_double_big_blind)
                else:
                    next_turn()
                    bet(RO.bet_target_name, A.call_big_blind)
                if RO.bets >= NUMPLAYERS:
                    RO.step += 1
            case 10:  # river
                if initialization('post_river_betting'):
                    dealriver()
                next_turn()
                bet(RO.bet_target_name, A.call_big_blind)
                if RO.bets >= NUMPLAYERS:
                    RO.step += 1
            case 11:  # showdown
                RO.step += 1
                # if initialization('post_turn_betting'):
                #     if next_bet(init=True):
                #         bet(RO.bet_target_name, A.raise_double_big_blind)
                #         # show_cards = True
                # else:
                #     next_bet()
                # RO.playernum = RO.PLAYERS[RO.bet_target_name]
                #
                # if RO.bets >= NUMPLAYERS:  #RO.playernum == 0:
                #     RO.step += 1

            case 12:
                showholecards()
                if initialization('showdown'):
                    print(f'#{RO.cardsdealt} card to {RO.deal_target_name}')
                    #showholecard(RO.deal_target)
                #else:
                    if RO.bets >= CountPlayersinHand(): #NUMPLAYERS:
                        RO.step += 1

            case 13:
                wn = calc_winner()
                print(f'winner is {RO.PLAYERNAMES[wn]}')
                refresh_display()
                drawbotlabels()
                RO.step += 1
                pygame.time.set_timer(timer_event, vardelay)
            case _:
                pass

    if quitflag:
        logstats()
        pygame.quit()
        sys.exit()
    return resetflag


# ---------------end event loop ------------------#


def onetimeinit():
    #RO = R()
    RO.PlayerList: [PokerPlayer] = []
    RO.PlayerList.append(PokerPlayer("you", H.initialStake, Attitude.PassiveAggressive))
    RO.PlayerList.append(PokerPlayer("Ian", H.initialStake, Attitude.StrategicAggressive))
    RO.PlayerList.append(PokerPlayer("Ben", H.initialStake, Attitude.PassiveAggressive))
    RO.PlayerList.append(PokerPlayer("Jax", H.initialStake, Attitude.PassiveAggressive))
    RO.PlayerList.append(PokerPlayer("Max", H.initialStake, Attitude.PassiveAggressive))
    RO.PlayerList.append(PokerPlayer("Pam", H.initialStake, Attitude.PassiveAggressive))
    RO.PlayerList.append(PokerPlayer("Ray", H.initialStake, Attitude.PassiveAggressive))
    RO.PlayerList.append(PokerPlayer("Sal", H.initialStake, Attitude.PassiveAggressive))
    RO.PlayerList.append(PokerPlayer("Zak", H.initialStake, Attitude.BerzerkerAggressive))
    RO.PlayerTurn = RO.the_button
    RO.ActionPlayer = RO.PlayerList[RO.PlayerTurn]
   # whose_turn_is_it(start=True)


def main():
    preloadcards()
    onetimeinit()
    logstats(load=True)
    print(f'RO.PlayerTurn = {RO.PlayerTurn}')
    print(f'{RO.PlayerList[RO.PlayerTurn]}')
    set_card_offsets_simple()
    looping = True
    while looping:
        draw_poker_table()
        RO.PlayerTurn = RO.the_button
        looping = sequencer()
        RO.num_players_in_hand = CountPlayersinHand()
        inc_deal()
        RO.cccard = 0
        RO.deck = Carddeck(cards_52s1)


if __name__ == '__main__':
    main()
