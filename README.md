*************************************
FINAL PROJECT PRINCIPLES OF DATABASES
    Andrew Joffe, Jack Covino
          NFL DATABASE
*************************************

SCHEMA:

TEAM
teamid*  teamname    city    conference  division


PLAYER
playerid*   teamid^  fname   lname   position    


COACH
coachid*   teamid^    fname     lname   role 


GAME
gameid*     week    homeid^     awayid^     homepts     awaypts   


GAME_STATS
gameid^*    playerid^*      pass_yrd    rush_yrd    rec_yrd     touchdowns      tackles     interceptions

__________
p-key = *
f-key = ^