-- SQL queries

-- players with 250+ passing yards in a game
SELECT P.fname, P.lname, G.pass_yrd 
FROM PLAYER P
JOIN GAME_STATS G ON P.playerid = G.playerid
WHERE G.pass_yrd > 250
ORDER BY pass_yrd DESC, lname, fname;

-- total players per team
SELECT T.teamname, COUNT(P.playerid) AS player_count
FROM TEAM T
LEFT JOIN PLAYER P ON T.teamid = P.teamid
GROUP BY T.teamname
ORDER BY player_count DESC, teamname;

-- list all quarterbacks (QB) by team
SELECT P.fname, P.lname, P.position, T.teamname
FROM PLAYER P
LEFT JOIN TEAM T ON P.teamid = T.teamid
WHERE UPPER(P.position) = 'QB'
ORDER BY teamname, lname, fname;

-- games in a specific week with scores
SELECT G.week, HT.teamname AS home_team, G.hometeamscore,
       AT.teamname AS away_team, G.awayteamscore
FROM GAME G
JOIN TEAM HT ON G.hometeamid = HT.teamid
JOIN TEAM AT ON G.awayteamid = AT.teamid
WHERE G.week = 1
ORDER BY G.gamedate, home_team;

-- top rushing performances (100+ rush yards)
SELECT P.fname, P.lname, G.rush_yrd
FROM PLAYER P
JOIN GAME_STATS G ON P.playerid = G.playerid
WHERE G.rush_yrd >= 100
ORDER BY G.rush_yrd DESC, lname, fname;

-- average receiving yards by player
SELECT P.fname, P.lname, AVG(G.rec_yrd) AS avg_rec_yrd
FROM PLAYER P
JOIN GAME_STATS G ON P.playerid = G.playerid
GROUP BY P.fname, P.lname
HAVING AVG(G.rec_yrd) > 50
ORDER BY avg_rec_yrd DESC, lname, fname;

-- defensive standouts with interceptions recorded
SELECT P.fname, P.lname, G.interceptions, G.tackles
FROM PLAYER P
JOIN GAME_STATS G ON P.playerid = G.playerid
WHERE G.interceptions IS NOT NULL AND G.interceptions > 0
    AND G.tackles IS NOT NULL AND G.tackles > 2
ORDER BY G.interceptions DESC, lname, fname;


-- players above average rushing yards per game 
SELECT P.fname, P.lname, AVG(G.rush_yrd) AS avg_rush_yrd
FROM PLAYER P
JOIN GAME_STATS G ON P.playerid = G.playerid
GROUP BY P.fname, P.lname
HAVING AVG(G.rush_yrd) > (
    SELECT AVG(rush_yrd) FROM GAME_STATS
)
ORDER BY avg_rush_yrd DESC, lname, fname;

