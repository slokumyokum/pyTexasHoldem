This is a graphical simulation of Texas Hold'em poker for nine players - 
one person and 8 bots using Python and Pygame.  The code is broken into three main 
files: PokerRules.py, TexasHoldemPoker.py, and PokerHandList.py.

PokerRules implements Card, Deck, and Hand objects for Poker. It
goes to a lot of trouble to ensure that the distribution of cards is similar to 
that of the real world, which is not totally random but is impacted by how they are 
gathered up, shuffled, and cut. If desired, it can implement a stacked deck for testing.

PokerHandList is basically a lookup table of hand ranking. This makes it possible 
to visually verify that hands are ranked correctly. 

TexasHoldemPoker has all of the code to implement the game actions, however it is not finished.  
It includes code and graphics to handle the main overhead of dealing, betting, showdown, and distribution of winnings. It simulates a dealer that deals the hole cards. It had some
code to allow for customizing to due to bot personality.
It has a real-time event loop that is still not working without issues.  It attempts to 
allow all players to participate in simulated real-time with messages scrolling up in a 
designated area.  It currently does not have speech or sound effects, but can support 
those without too much effort.




