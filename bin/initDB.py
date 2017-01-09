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

def load_users(f, e):
    current_path = os.getcwd()
    file_path =  os.path.join( os.getcwd(), f)
    fh = open(file_path, "r")
    for line in fh.readlines():
        username,email,password = line.rstrip().split("\t")
        check_user = User.query.filter_by( username = username, email = email  ).first()
        if check_user is None:
            u = User(username, email, password, e)
            u.active = 1

            if u.username in ["Marta","Marcel"]:
                u.admin = 1
            db.session.add(u)
            sys.stderr.write("# Adding new user " + username + "\n")
            
    db.session.commit()
    fh.close()


def load_movies(f):
	fh = open(f, "r")
	for line in fh.readlines():
		day, user, imdbid, title = line.rstrip().split("\t")
		check_movie = Movie.query.filter_by( title = title, imdbid = imdbid).first()
		if check_movie is None:
			u = User.query.filter_by(username=user).first()			
			m = Movie(title,u.id,imdbid, day)
			db.session.add(m)
			sys.stderr.write("# Adding new movie\n")
	db.session.commit()
	fh.close()


def load_sessions(f):
	fh = open(f, "r")
	for line in fh.readlines():
		week, date, movie = line.rstrip().split("\t")
		week_date = string_to_date(week)
		check_session = Session.query.filter_by( week = week ).first()
		
		if check_session is None:
				date_date = "ND" if date == "ND" else string_to_date(date)
				m = Movie.query.filter_by(title=movie).first()
			
				if m is not None:
					m = m.id
					s = 0
				else:
					m = 0
					s = 1
				s = Session(week_date, date_date, m, s)
				db.session.add(s)
				sys.stderr.write("# Adding new session\n")
		
	db.session.commit()
	fh.close()

def load_votes(f):
	fh = open(f, "r")
	for line in fh.readlines():
		# userid, movieid, sessionid, date=None
		sessionid,username,date,movie = line.rstrip().split("\t")
		
		m = Movie.query.filter_by(title=movie).first()
		u = User.query.filter_by(username=username).first()
		check_votes = Votes.query.filter_by( userid = u.id , movieid = m.id , sessionid = sessionid  ).first()
		if check_votes is None:
			v = Votes(u.id, m.id, sessionid, date)
			db.session.add(v)
			sys.stderr.write("# Adding new vote\n")

	db.session.commit()
	fh.close()

def __main__():
    parser = OptionParser()
    parser.add_option("-v", "--votes",    		dest="votes",    help="Votes",    metavar="ANN", default="data/votes.tbl")
    parser.add_option("-m", "--movies",   		dest="movies",   help="Movies",   metavar="MOV", default="data/movies.tbl")
    parser.add_option("-s", "--sessions", 		dest="sessions", help="Sessions", metavar="ANN", default="data/sessions.tbl")
    parser.add_option("-u", "--users",     dest="users",     help="Users", metavar="ANN", default="data/users.tbl")
    parser.add_option("-d", "--drop",           dest="drop",     help="Drop",     metavar="ACT", default=False, action='store_true')

    parser.add_option("-e", "--encrypt",    dest="encrypt", help="Encrypt", metavar="ACT", default=True, action='store_false')
    
    (opts, args) = parser.parse_args()

    if opts.drop:
        db.metadata.drop_all(db.engine, tables = [ User.__table__ ])
        db.metadata.create_all(db.engine, tables = [ User.__table__ ])
    
    load_users(opts.users, opts.encrypt)
    
    if opts.drop: 
        db.metadata.drop_all(db.engine, tables = [ Movie.__table__, Session.__table__, Votes.__table__ ])
        db.metadata.create_all(db.engine, tables = [ Movie.__table__, Session.__table__, Votes.__table__ ])
    

    load_movies(os.path.join( os.getcwd(), opts.movies))
    load_sessions(os.path.join( os.getcwd(), opts.sessions))
    load_votes(os.path.join( os.getcwd(), opts.votes))


if __name__ == __main__():
	main()
 
