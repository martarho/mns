import sys, os
current_path = os.getcwd()
sys.path.append(current_path)

from cmn_classes import db, User, Session, Movie, Votes, IMDB
import datetime
from optparse import OptionParser
import sqlite3

def __main__():
    username = sys.argv[1]
    password = sys.argv[2]

    user = User.query.filter_by( username = username ).first()
    user.password = user.encrypt_string( password )
    db.session.commit()
       
if __name__ == __main__():
	main()
 
