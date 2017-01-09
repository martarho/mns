import sys, os
current_path = os.getcwd()
sys.path.append(current_path)

from cmn_classes import db, User, Session, Movie, Votes, IMDB
import datetime
from optparse import OptionParser


for line in sys.stdin.readlines():
	pass
