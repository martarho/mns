import sys, os
binpath = os.path.dirname(__file__)
libpath = os.path.join(binpath,"../")
sys.path.append(libpath)
from datetime import date, datetime
from cmn_classes import Session, openNewSession, check_days_difference, str2date

# Monday == 0
args = dict(zip(["cmd","day"],sys.argv))

if "day" not in args.keys():
	args["day"] = 0

if datetime.today().weekday() == int(args["day"]):
	print "# It's Monday!! Updating system"

	# Recover open session
	s = Session.query.filter_by( status = 1).first()

	# If there's an open session, choose a movie for it and close it
	if s is not None:# and check_days_difference(str2date(s.week), date.today(), 7):
			
		# Choose movie
		#print s.choose_movie()
		movie = s.define_movie()
		print movie
		# Close session
		s.close()
	
		# Open new session with blank movie, session date and editable

		openNewSession(day=None)
        print "# System update succesfully"
	
