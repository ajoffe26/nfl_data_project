
-- Run to create tables

-- comment out for first time run
DROP TABLE TEAM CASCADE CONSTRAINTS;
DROP TABLE PLAYER CASCADE CONSTRAINTS;
DROP TABLE COACH CASCADE CONSTRAINTS;
DROP TABLE GAME CASCADE CONSTRAINTS;
DROP TABLE GAME_STATS CASCADE CONSTRAINTS;

DROP SEQUENCE seqTID;
DROP SEQUENCE seqPID;
DROP SEQUENCE seqCID;
DROP SEQUENCE seqGID;
-- end comment out for first time run

CREATE TABLE TEAM(
	TeamID			    Number			    NOT NULL,
	TeamName			Varchar(15)		    NOT NULL,
	City				Varchar(15)		    NOT NULL,
	Conference			Varchar(3)		    NOT NULL,
    Division            Varchar(1)		    NOT NULL,
	CONSTRAINT			TEAM_PK		        PRIMARY KEY(TeamID),
    CONSTRAINT          conference_ck       CHECK (Conference   IN ('AFC', 'NFC')),
    CONSTRAINT          division_ck         CHECK (Division     IN ('N', 'E', 'S', 'W'))
	);



CREATE TABLE PLAYER(
	PlayerID			Number			    NOT NULL,
	Fname			    Varchar(15)		    NOT NULL,
    Lname			    Varchar(15)		    NOT NULL,
	Position			Varchar(4)		    NOT NULL,
	TeamID			    Number			    NULL,
    CONSTRAINT			PLAYER_PK		    PRIMARY KEY(PlayerID),
	CONSTRAINT			PLAYER_TEAM_FK	    FOREIGN KEY (TeamID)
							REFERENCES TEAM(TeamID)
	);


CREATE TABLE COACH(
	CoachID			    Number			    NOT NULL,
	LName			    Varchar(15)		    NOT NULL,
	FName			    Varchar(15)		    NOT NULL,
	TeamID			    Number			    NULL,
	Role		        Varchar(15)		    NULL,
	CONSTRAINT		    COACH_PK		    PRIMARY KEY(CoachID),
    CONSTRAINT		    COACH_TEAM_FK	    FOREIGN KEY (TeamID)
                            REFERENCES TEAM(TeamID)
	);


CREATE TABLE GAME(
	GameID				Number			    NOT NULL,
	GameDate			Date			    NOT NULL,
    Week                Number			    NOT NULL,
	HomeTeamID			Number			    NOT NULL,
	AwayTeamID			Number			    NOT NULL,
	HomeTeamScore		Number			    NULL,
	AwayTeamScore		Number			    NULL,
	CONSTRAINT			GAME_PK 		    PRIMARY KEY(GameID),
	CONSTRAINT			GAME_HOME_TEAM_FK   FOREIGN KEY (HomeTeamID)
							REFERENCES TEAM(TeamID),
	CONSTRAINT			GAME_AWAY_TEAM_FK   FOREIGN KEY (AwayTeamID)
							REFERENCES TEAM(TeamID),
    CONSTRAINT          game_week_ck        CHECK (Week BETWEEN 1 AND 18),
    CONSTRAINT          game_teams_ck       CHECK (HomeTeamID <> AwayTeamID)
	);


CREATE TABLE GAME_STATS(
	GameID				Number				NOT NULL,
	PlayerID			Number				NOT NULL,
	Pass_yrd			Number				NULL,
	Rush_yrd			Number				NULL,
    Rec_yrd				Number				NULL,
    Touchdowns          Number              NULL,
    Tackles             Number              NULL,
    Interceptions       Number              NULL,
	CONSTRAINT			GAME_STATS_PK 		PRIMARY KEY(GameID, PlayerID),
	CONSTRAINT			GAME_STATS_GAME_FK  FOREIGN KEY (GameID)
							REFERENCES GAME(GameID),
	CONSTRAINT			GAME_STATS_PLAYER_FK FOREIGN KEY(PlayerID)
							REFERENCES PLAYER(PlayerID)
	);



