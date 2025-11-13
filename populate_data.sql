
-- Test data for data base

INSERT INTO TEAM (TeamID, TeamName, City, Conference, Division) VALUES (seqTID.NEXTVAL, 'Patriots', 'New England', 'AFC', 'E');
INSERT INTO TEAM (TeamID, TeamName, City, Conference, Division) VALUES (seqTID.NEXTVAL, 'Eagles', 'Philadelphia', 'NFC', 'E');
INSERT INTO TEAM (TeamID, TeamName, City, Conference, Division) VALUES (seqTID.NEXTVAL, 'Cowboys', 'Dallas', 'NFC', 'E');
INSERT INTO TEAM (TeamID, TeamName, City, Conference, Division) VALUES (seqTID.NEXTVAL, 'Packers', 'Green Bay', 'NFC', 'N');
INSERT INTO TEAM (TeamID, TeamName, City, Conference, Division) VALUES (seqTID.NEXTVAL, 'Colts', 'Indianapolis', 'AFC', 'S');
INSERT INTO TEAM (TeamID, TeamName, City, Conference, Division) VALUES (seqTID.NEXTVAL, 'Giants', 'New York', 'NFC', 'E');

INSERT INTO PLAYER (PlayerID, Fname, Lname, Position, TeamID) VALUES (seqPID.NEXTVAL, 'Tom', 'Brady', 'QB', 1);
INSERT INTO PLAYER (PlayerID, Fname, Lname, Position, TeamID) VALUES (seqPID.NEXTVAL, 'Ezekiel', 'Elliott', 'RB', 2);
INSERT INTO PLAYER (PlayerID, Fname, Lname, Position, TeamID) VALUES (seqPID.NEXTVAL, 'Jordan', 'Love', 'QB', 3);
INSERT INTO PLAYER (PlayerID, Fname, Lname, Position, TeamID) VALUES (seqPID.NEXTVAL, 'Sauce', 'Gardner', 'CB', 4);

INSERT INTO COACH (CoachID, LName, FName, TeamID, Role) VALUES (seqCID.NEXTVAL, 'Belichick', 'Bill', 1, 'Head Coach');
INSERT INTO COACH (CoachID, LName, FName, TeamID, Role) VALUES (seqCID.NEXTVAL, 'LaFleur', 'Matt', 3, 'Head Coach');

INSERT INTO GAME (GameID, GameDate, Week, HomeTeamID, AwayTeamID, HomeTeamScore, AwayTeamScore) VALUES (seqGID.NEXTVAL, TO_DATE('2025-11-9', 'YYYY-MM-DD'), 1, 1, 2, 24, 21);
INSERT INTO GAME (GameID, GameDate, Week, HomeTeamID, AwayTeamID, HomeTeamScore, AwayTeamScore) VALUES (seqGID.NEXTVAL, TO_DATE('2025-11-10', 'YYYY-MM-DD'), 2, 3, 4, 30, 27);

INSERT INTO GAME_STATS (GameID, PlayerID, Pass_yrd, Rush_yrd, Touchdowns, Interceptions) VALUES (1, 1, 300, 10, 3, 0);
INSERT INTO GAME_STATS (GameID, PlayerID, Rush_yrd, Rec_yrd, Touchdowns, Tackles) VALUES (1, 2, 120, 0, 1, 5);
INSERT INTO GAME_STATS (GameID, PlayerID, Pass_yrd, Rush_yrd, Touchdowns, Interceptions) VALUES (2, 3, 280, 5, 2, 1);
INSERT INTO GAME_STATS (GameID, PlayerID, Touchdowns, Tackles, Interceptions) VALUES (2, 4, 0, 8, 0);

