import sys, os
current_path = os.getcwd()
sys.path.append(current_path)

from cmn_classes import db, User, Session, Movie, Votes, IMDB
import datetime
from optparse import OptionParser
import sqlite3
import time

# Dump Users
print "USERS"
users = User.query.all()
for u in users:
	print "\t".join(map(str, [ u.id, u.username, u.email, u.password, u.date, u.active, u.admin ]))

# Dump Movies
print "MOVIES"
movies = Movie.query.all()
for m in movies:
	print "\t".join(map(str, [ m.id, m.title, m.date, m.imdbid, m.userid ]))

# Dump Sessions
print "SESSIONS"
sessions = Session.query.all()
for s in sessions:
	print "\t".join(map(str, [ s.id, s.week, s.date, s.movieid, s.status ]))

# Dump Votes
print "VOTES"
votes = Votes.query.all()
for v in votes:
	print "\t".join(map(str, [ v.id, v.userid, v.movieid, v.sessionid, v.date ]))
