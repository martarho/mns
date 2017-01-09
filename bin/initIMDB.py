import sys, os
current_path = os.getcwd()
sys.path.append(current_path)

import sqlite3
import time
from optparse import OptionParser
from cmn_classes import db, IMDB


def load_imdb(f, db="imdb.db"):
	current_path = os.getcwd()
	db_path   =  os.path.join( os.getcwd(), "db", db)
	file_path =  os.path.join( os.getcwd(), f)
	conn = sqlite3.connect(db_path)
	c = conn.cursor()

	lines = 0
	lst = list()

	with open(file_path, "r") as myfile:
		for line in myfile:
			line = line.strip().split("\t")
			lst.append((line))
			lines += 1
	c.executemany("INSERT INTO imdb VALUES (?,?,?)", lst)

	conn.commit()
	conn.close()
	return lines


def __main__():
	parser = OptionParser()
	parser.add_option("-f", "--file", dest="f",help="file", metavar="ACT", default=False)
	(opts, args) = parser.parse_args()
	
	if opts.f: 
		start_time = time.clock()

		db.drop_all(bind = [ 'imdb' ])
		db.create_all(bind = [ 'imdb' ])
		lines = load_imdb(opts.f)

		elapsed_time = time.clock() - start_time
		print "Time elapsed: {} seconds".format(elapsed_time)
		print "Read {} lines".format(lines)

if __name__ == __main__():
	main()
 
