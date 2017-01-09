from cmn_classes import db, Schedule, User
import datetime
from optparse import OptionParser
import sqlite3
import time
import sys

fh = open(sys.argv[1], "r")
for line in fh.readlines():
	l = line.rstrip().split("\t")
	sid, username, calendar, date = l
	user = User.query.filter_by( username = username ).first()
	s = Schedule(user.id,sid,calendar, attending=False, attended=False, date=date)
	db.session.add(s)
db.session.commit()
fh.close()
