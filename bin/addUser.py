import sys, os
current_path = os.getcwd()
sys.path.append(current_path)

from cmn_classes import db, User, Session, Movie, Votes, IMDB
import datetime
from optparse import OptionParser
import sqlite3
import time

# Start sessions table
def string_to_date(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d").date()

# Start users table

def __main__():
    parser = OptionParser()
    parser.add_option("-u", "--username",    		dest="username",    help="User",    metavar="USER", default=False)
    parser.add_option("-e", "--email",           dest="email",    help="User",    metavar="USER", default=False)
    parser.add_option("-p", "--password",   		dest="password",   help="PASS",   metavar="PASS", default=False)
    (opts, args) = parser.parse_args()

    check_user = User.query.filter_by( username = opts.username, email = opts.email  ).first()
    if check_user is None:
        u = User(opts.username, opts.email, opts.password, True)
        u.active = 1

        db.session.add(u)
        sys.stderr.write("# Adding new user " + opts.username + "\n")
        
        db.session.commit()
    
if __name__ == __main__():
	main()
 
