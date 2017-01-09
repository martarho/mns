from flask import Flask, render_template,flash,redirect, url_for, abort, request, session,g, jsonify
from flask.ext.wtf import Form
from wtforms import TextField, PasswordField, BooleanField, validators, HiddenField, DateField, RadioField
from wtforms.validators import Required, Length, EqualTo, Regexp, Email
from flask_wtf.csrf import CsrfProtect
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func, cast
from sqlalchemy import Date

from flask.ext.login import LoginManager, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta, datetime, time
from sqlalchemy.dialects.sqlite import DATE
import re



d = DATE(
        storage_format="%04d-%02d-%02d",
        regexp=re.compile("(\d+)-(\d+)-(\d+)")
    )

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/cmn.db'
app.config['SQLALCHEMY_BINDS'] = { 'imdb': 'sqlite:///db/imdb.db' }
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'super-secret'

db    = SQLAlchemy(app)
CsrfProtect(app)

# Set up LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Set up loaders for user sessions
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user


# --- --- --- --- Classes --- --- --- --- #


def str2date(s):
    if s is None or s == "ND":
        return s
    
    return datetime.strptime(s, "%Y-%m-%d").date()

def str2datetime(s):
    if s is None or s == "ND":
        return s
    
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f").date()

def get_next_monday(day=None):
    s = Session.query.order_by(Session.week.desc()).first()
    if day is None and s is not None:
        last_session_date = s.week
        dt = str2date(last_session_date)
        nextmonday = dt + timedelta(days=(7 - dt.weekday()))
        return nextmonday
    elif s is not None:
        nextmonday = day + timedelta(days=(7 - day.weekday()))
        return nextmonday
     
    return None

def check_days_difference(d1,d2,diff=7):
	d = d1 - d2
	return d.days <= diff
	

def openNewSession(day=None):
    nextmonday = get_next_monday(day=day)    
    # week, date=None, movieid=None, status=1
    session = Session(str(nextmonday), "ND", 0, 1)
    db.session.add(session)
    db.session.commit()


def query_imdb(s):
    from urllib2 import urlopen
    from re import sub 
    import json
    
    a = re.compile("^(tt\d{7})$")
    if a.match(s):
        omdb = [json.loads(urlopen("http://www.omdbapi.com/?i=" + s).read())]
        
    elif s == "":
        omdb = False
    else:
        movie_name = sub(" ","%20", s)
        omdb = json.loads(urlopen("http://www.omdbapi.com/?s=" + movie_name).read())
        
        if "Search" in omdb.keys():
            omdb = [ x for x in omdb["Search"] if x["Type"] == "movie" ]
            omdb = [dict(t) for t in set([tuple(d.items()) for d in omdb])]

        else:
            omdb = False
            
    return omdb


class User(db.Model):
    __tablename__ = 'users'
    id        = db.Column(db.Integer, primary_key=True)
    username  = db.Column(db.String(80), unique=True)
    password  = db.Column(db.String(80))
    email     = db.Column(db.String(120))
    date      = db.Column(db.String(25))
    active    = db.Column(db.Boolean())
    admin     = db.Column(db.Boolean())
    votes     = db.relationship('Votes', backref='user')
    
    def __init__(self, username, email, password, date=False, active=True, admin=False, encrypt=True):
        self.username = username
        passw = self.encrypt_string(password) if encrypt else password
        self.password = passw
        self.email    = email
        self.date     = datetime.now() if date is False else date
        self.active   = active
        self.admin    = admin

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.username)

    def check_password(self, s):
        return check_password_hash(self.password, s)
    
    def check_email(self, s, encrypted=True):
        if encrypted:
            return check_password_hash(self.email, s)
        else:
            return self.email == s
    
    def encrypt_string(self, s):
        return generate_password_hash(s)

    def last_voted_session(self):
        return self.votes[-1].sessionid

    def voted_in_session(self,sid):
        for vote in self.votes:
            if vote.sessionid == sid:
                return True
        return False
    
    def proposed_movies_watched(self):
        mlist = sum([ m.times_seen() for m in Movie.query.filter_by(id = self.id) ])
        return mlist
    
    
class Movie(db.Model):
    __tablename__ = "movies"
    id        = db.Column(db.Integer, primary_key=True)
    title     = db.Column(db.String(120))
    date      = db.Column(db.String(10))
    imdbid    = db.Column(db.String(12))
    userid    = db.Column(db.Integer)
    votes     = db.relationship('Votes', backref='movie', lazy='dynamic')
    choosen   = db.relationship('Session', backref='movie', lazy='dynamic')
    votes_counted = None    

    def __init__(self, title, userid, imdbid, day=None):
        self.title  = title
        self.userid = userid
        self.imdbid = imdbid
        self.date   = date.today() if day is None else day
        
    def get_username(self):
        u =  User.query.filter_by(id=self.userid).first()
        return u.username
    
    def times_seen(self):
        return self.choosen.count()
    
    def last_time_seen(self):
        # Session when it was choosen
        c = self.choosen.first()
        # If there is a session when it was choosen, assign date / week
        if c is not None:
            if c.date == "ND":
                return str2date(c.week)
            else:
                return str2date(c.date)
        
        # if not, assign None
        else:
            return None #str2date(self.date)
        
        
        return None
    
    def count_votes(self,sid=None):
        # Check last time the movie was seen, count votes from that day on
        lts = self.last_time_seen()

        if lts is None:
            v = self.votes.count()	
        else:
            v = self.votes #.filter( cast(Votes.date, Date) > lts).count()
            cv = 0
        
            for vo in v:
                t = str2datetime(vo.date)
                print t, lts, cv, self.title
                if t >= lts:
                    cv += 1

            v = cv + (self.times_seen() * -10)
        print self.title, v
        self.votes_counted = v
        return v
    
class Votes(db.Model):
    __tablename__ = "votes"
    id          = db.Column(db.Integer, primary_key=True)
    userid      = db.Column(db.Integer, db.ForeignKey('users.id'))
    movieid     = db.Column(db.Integer, db.ForeignKey('movies.id'))
    sessionid   = db.Column(db.Integer)
    date        = db.Column(db.String(30))
     
    def __init__(self, userid, movieid, sessionid, day=None):
        self.userid     = userid
        self.movieid    = movieid
        self.sessionid  = sessionid
        self.date       = day if day is not None else datetime.now()
    
#class Role(db.Model):
    #__tablename__ = "roles"
    #id = db.Column(db.Integer(), primary_key=True)
    #name = db.Column(db.String(80), unique=True)
    #description = db.Column(db.String(255))
    
class Session(db.Model):
    __tablename__ = "sessions"
    id          = db.Column(db.Integer, primary_key=True)
    week        = db.Column(db.String(10))
    date        = db.Column(db.String(10))
    movieid     = db.Column(db.Integer, db.ForeignKey('movies.id'))
    status      = db.Column(db.Boolean())

    def __init__(self, week, date=None, movieid=None, status=1):
        self.date    = date if date is not None else "ND"
        self.week    = week
        self.movieid = 0 if movieid is None else movieid
        self.status  = status
    
    def get_movie_title(self):
        if self.movieid > 0:
            m = Movie.query.filter_by(id = self.movieid).first()
            return m.title
        
        return "ND"

    def choose_movie(self):
		# Get votes by movie discarding the votes previous 
		# to that movie being watched if that applies
		
		from operator import itemgetter
		# l = ID, TITLE, COUNT, DATE, USERID
		l = [ (m.id, str(m.title), m.count_votes(sid=self.id), str2date(m.date), m.userid) for m in Movie.query.all() ]
		m = max(l, key=itemgetter(2))[2]
		max_votes = [ x for x in l if x[2] == m ]
		
		if len(max_votes) == 1:
			return max_votes[0]
		
		else:
			# If there is a tie between movies, 
			# choose the ones proposed most recently
			last_proposed_time = sorted(max_votes, key=itemgetter(3), reverse=True)[0][3]
			recent_movies = [ x for x in max_votes if x[3] == last_proposed_time ]
						
			if len(recent_movies) == 1:
				return recent_movies[0]
			
			else:
				# Get proposers of movies left and count how many movies 
				# proposed by them have been watched and get min
				# (user with less)
				for i,u in enumerate(recent_movies):
					prop = sum([ m.times_seen() for m in Movie.query.filter_by(userid = u[4]) ])
					recent_movies[i] += (prop,)
					
				min_proposed_movies_choosen = sorted( recent_movies, key=lambda x: x[5])[0][5]

				least_choosen_proposed = [ x for x in recent_movies if x[5] == min_proposed_movies_choosen ]
				if len(least_choosen_proposed) == 1:
					
					return least_choosen_proposed[0]
				else:
					from random import choice				
					# If there's a tie, then select randomly and fuck it all
					randmovie = choice(least_choosen_proposed)
					return randmovie

    def define_movie(self):
        movie = self.choose_movie()
        self.movieid = movie[0]
        db.session.commit()
        return movie
	
    def close(self):
        # Close Session
        self.status = 0
        db.session.commit()


        
class IMDB(db.Model):
    __bind_key__ = 'imdb'
    id       = db.Column(db.String(12), primary_key=True)
    title    = db.Column(db.String(100))
    year     = db.Column(db.String(4))
   
    def __init__(self,a):
        iid, title,year, genre = a
        self.id      = iid
        self.title   = title
        self.year    = year
       

class Schedule(db.Model):
	__tablename__ = 'schedule'
	id           = db.Column(db.Integer, primary_key=True)
	userid       = db.Column(db.Integer, db.ForeignKey('users.id'))
	sessionid    = db.Column(db.Integer, db.ForeignKey('sessions.id'))
	availability = db.Column(db.String(7))
	attending    = db.Column(db.Boolean())
	attended     = db.Column(db.Boolean())
	date        = db.Column(db.String(30))

	def __init__(self,userid,sessionid,availability, attending=False, attended=False, date=False):		
		self.userid = userid
		self.sessionid = sessionid
		self.availability = availability
		self.attending = attending
		self.attendend = attended
		self.date     = datetime.now() if date is False else date
		
	def get_username(self):
		u =  User.query.filter_by(id=self.userid).first()
		return u.username

# ---- FORMS ----- #

class LoginForm(Form):
    username    = TextField('Username', validators = [Required(), Length(min=4, max=25)])
    password    = PasswordField('Password', validators = [Required(), Length(min=8, max=25, message = "Password too short"), EqualTo('confirm', message='Passwords must match')])
   
    remember_me = BooleanField('Remember Me', default = False)
    
    def validate(self):
        valid_user = User.query.filter_by(
            username=self.username.data,
            active=True).first()
        
        if valid_user is None:
            return False
        
        if valid_user.check_password(self.password.data) is False:
            return False

        self.user = valid_user
        return True

class RegistrationForm(Form):
    # User Registration form
    username    = TextField('Username', validators = [Required(), Length(min=4, max=25)])
    email       = TextField('Email Address', [Length(min=6, max=40, message="Email is too short..."), Email(message="Email format is not valid")])	
    password    = PasswordField('Password', validators = [Required(), Length(min=8, max=25, message = "Password too short..."), EqualTo('confirm', message='Passwords must match')])
    confirm     = PasswordField('Repeat Password')

class ChangePassword(Form):
	# User change password form
	oldpassword = PasswordField('Old Password', validators = [Required()])
	password = PasswordField('Password', validators = [Required(), Length(min=8, max=25), EqualTo('confirm', message='Passwords must match')])
	confirm  = PasswordField('Repeat Password')
	
class UpdateEmail(Form):
	# Email update form
	oldemail = TextField('Current Email address', validators = [Required(), Email(message = "Email format is not valid")])
	email    = TextField('New Email address', validators = [Required(), Email(message = "Email format is not valid")])

		
class AddSessionForm(Form):
	# Form to add new movie sessions
	regex = re.compile('^(\d{4}-\d{2}-\d{2})$')


	# Require value + formatted as YYYY-MM-DD through regex
	week  = DateField('', format = "%Y-%m-%d", validators = [Required()], default="")



	def validate(self):
		# Validate requirements to open a new session
		boolflag = False

		# Is there any session open?
		open_session = Session.query.filter_by(status = 1).count() == 0
		not_an_empty_string = self.week.data != ""
		# Get last session monday date
		s = Session.query.order_by(Session.date.desc()).first()
		if s is not None and not_an_empty_string:
			last_session_date = str2date(s.week)
			# Check if new session is 1 week or more after the last one
			# and if it is monday (id of session is ALWAYS monday!)
			# and if there is no other session open
			boolflag = ((self.week.data - last_session_date) >= timedelta(days=7))# and ( self.week.data.isoweekday() == 1 and open_session)			
		
		return boolflag

class SearchMovie(Form):
    search = TextField('Search', validators = [Required(message = "Empty search not allowed!")])

class AddMovie(Form):
    title  = HiddenField('Title', validators = [Required()])
    imdbid = HiddenField('imdbID', validators = [Required()])

class VoteForm(Form):
     mid = HiddenField("MID", validators= [Required()])

def create_schedule_table(sid):
	from string import maketrans
	import re
	transtab =  {'-': 0, '?': 0.5, 'Y': 1, 'N': 0}
	sched = Schedule.query.filter_by(sessionid = sid).all()
	users_query = User.query.filter_by(active = 1)
	users = dict([ ((u.username,u.id), ["-","-","-","-","-","-","-"]) for u in users_query ])
	users_update = dict([ ((u.username,u.id), "ND") for u in users_query ])
	
	total = [0,0,0,0,0,0,0]

	for s in sched:
		u = (s.get_username(),s.userid)
		users[ u ] = list(s.availability)
		users_update[ u ] = re.sub(r'\..*$', '', s.date)
		
		preencoded = [ transtab[x] for x in list(str(s.availability))]

		total = map(lambda (x,y): float(x)+float(y), zip(total,preencoded))

	m = max(total)
	return (users,users_update,total,m)



class Calendar(Form):
	Mon = RadioField('Monday', choices=[('Y','Yes'),('N','No'),('?','?')])
	Tue = RadioField('Tuesday', choices=[('Y','Yes'),('N','No'),('?','?')])
	Wed = RadioField('Wednesday', choices=[('Y','Yes'),('N','No'),('?','?')])
	Thu = RadioField('Thursday', choices=[('Y','Yes'),('N','No'),('?','?')])
	Fri = RadioField('Friday', choices=[('Y','Yes'),('N','No'),('?','?')])
	Sat = RadioField('Saturday', choices=[('Y','Yes'),('N','No'),('?','?')])
	Sun = RadioField('Sundary', choices=[('Y','Yes'),('N','No'),('?','?')])

	def return_encoded_string(self):
		s = []
		days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
		for day in days:
			a = getattr(self, day)
			s.append(a.data)
		
		#s = "".join(s).translate(trantab)
		return "".join(s)	

