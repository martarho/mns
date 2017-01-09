from cmn_classes import *



# --------------- Views --------------- #

# --- Home --- #

@app.route('/', methods=["GET", "POST"])
@app.route('/index', methods=["GET", "POST"])
@login_required
def index():
    form = AddSessionForm()
    #if request.method == "POST" and form.validate_on_submit() and form.validate():
        #openNewSession(form)
        #flash('Session added')
        #return redirect(url_for('index'))
        

    sessions = Session.query.order_by(Session.id.desc()).all()
    return render_template('home.html', 
                           pagetitle="- CMC - Home", 
                           sessions = sessions,
                           form=form,
                           u = g.user)

# --- Session --- #

@app.route('/session/<int:sid>/', methods=["GET","POST"])
@login_required
def session(sid):
    
    # -- VARS --
    # Can user vote?
    #can_vote = False if g.user.last_voted_session() >= sid else True
    
    can_vote = True
    if g.user.voted_in_session(sid):
        can_vote = False
    
    
    # Set up forms
    form     = VoteForm()
    sform    = SearchMovie()
    aform    = AddMovie()
    
    # Get Session data
    session  = Session.query.filter_by(id = sid).first()
    
    if session.status is False:
        return redirect(url_for('index'))
    
    # Set up default omdb search flag
    omdb     = False
    
    #
    # Check Forms
    #
    if request.method == "POST":
        
        # If User clicked Search, query OMDB, return data in list format
        if request.form['btn'] == "Search":            
            
            # omdb = query_imdb(sform.search.data)            
            a = re.compile("^(tt\d{7})$")
            if a.match(sform.search.data):
                # Search by id
                pass
            elif sform.search.data == "":
                pass
            else:
                # Search title
                omdb = IMDB.query.filter(IMDB.title.ilike("%" + sform.search.data + "%")).all()

        
        elif request.form['btn'] == "Clear":
            omdb = False
            
        # If User clicked Add, check if movie is not already listed and add
        elif request.form['btn'] == "Add" and can_vote:
            is_movie = Movie.query.filter_by( imdbid = aform.imdbid.data ).count()
            
            if is_movie == 0: 
                movie = Movie(aform.title.data, g.user.id, aform.imdbid.data )
                db.session.add(movie)
                db.session.commit()
            
                movie = Movie.query.filter_by( title = movie.title).first()
                vote = Votes(g.user.id, movie.id, sid)
                db.session.add(vote)
                db.session.commit()
                can_vote = False
            


        # If the User is voting and is allowed to do so, add the vote
        elif request.form['btn'] == "Vote" and can_vote:
            # Get Votes object, insert and commit
            vote = Votes(g.user.id, form.mid.data, sid)
            db.session.add(vote)
            db.session.commit()
            can_vote = False     # now he can't
    
    #
    # Query movies in DB, display them
    #
    movies  = Movie.query.all()

    for i in range(0,len(movies)):
        movies[i].count_votes(sid) 
    
    return render_template('session.html', 
                        pagetitle = " - CMC - Session", 
                        session = session, 
                        movies=movies,
                        u=g.user,
                        vote=can_vote, 
                        vform=form,
                        sform=sform,
                        aform=aform,
                        omdb=omdb)

@app.route('/addmoar/', methods=["GET","POST"])
@login_required
def addmoar():
    sid = 0
    # -- VARS --
    # Can user vote?
    can_vote = True
    
    # Set up forms
    form     = VoteForm()
    sform    = SearchMovie()
    aform    = AddMovie()

    canweaddmoar = True
    #whichdate = "0000-01-01"
    
    if canweaddmoar is False:
        return redirect(url_for('index'))
    
    # Set up default omdb search flag
    omdb     = False
    #
    # Check Forms
    #
    if request.method == "POST":
        
        # If User clicked Search, query OMDB, return data in list format
        if request.form['btn'] == "Search":            
            
            # omdb = query_imdb(sform.search.data)            
            a = re.compile("^(tt\d{7})$")
            if a.match(sform.search.data):
                # Search by id
                pass
            elif sform.search.data == "":
                pass
            else:
                # Search title
                omdb = IMDB.query.filter(IMDB.title.ilike("%" + sform.search.data + "%")).all()

        
        elif request.form['btn'] == "Clear":
            omdb = False
            
        # If User clicked Add, check if movie is not already listed and add
        elif request.form['btn'] == "Add" and can_vote:
            is_movie = Movie.query.filter_by( imdbid = aform.imdbid.data ).count()
            
            if is_movie == 0: 
                #movie = Movie(aform.title.data, g.user.id, aform.imdbid.data, whichdate)
                movie = Movie(aform.title.data, g.user.id, aform.imdbid.data)
                db.session.add(movie)
                db.session.commit()
            
                movie = Movie.query.filter_by( title = movie.title).first()

    #
    # Query movies in DB, display them
    #
    movies  = Movie.query.order_by(Movie.title, Movie.date.desc()).all()    
    return render_template('addmovie.html', 
                        pagetitle = " - CMC - Add more movies", 
                        session = session, 
                        movies=movies,
                        u=g.user,
                        vform=form,
                        sform=sform,
                        aform=aform,
                        omdb=omdb)


# --- Login --- #

@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    # Get form 
    form = LoginForm()
    if form.validate_on_submit() and form.validate():
        flash(u'Succesfully logged in as %s' % form.user.username)
        #session['remember_me'] = form.remember_me.data
        login_user(form.user, remember = form.remember_me.data)
        return redirect(request.args.get('next') or url_for('index'))
        
    return render_template('login.html', 
                           pagetitle="- CMC - login", 
                           form=form)

# --- Logout --- #

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index')) 
    
# --- Register --- #

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm(request.form)
    if request.method == "POST" and form.validate():
        user = User(form.username.data, form.email.data, form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Thanks for registering')
        return redirect(url_for('login'))
    return render_template('register.html', 
                           form = form)


# --- Edit --- #

@app.route('/edit/<int:sid>/')
@login_required
def edit(sid):
    return render_template('edit.html',
                            pagetitle = "- CMC - Edit Session",
                            u = g.user)


# --- Schedule --- #
@app.route('/schedule/<int:sid>/', methods=["GET","POST"])
@login_required
def schedule(sid):
    # Set dictionary to pass through **kwargs and set form default values
    
    s = ""
    if request.method == "POST":
        calendar_form = Calendar()
        if calendar_form.validate_on_submit():
            s = calendar_form.return_encoded_string()
            previous_entry = Schedule.query.filter_by(userid = g.user.id, sessionid = sid).first()
            
            if previous_entry:
                previous_entry.availability = s
                previous_entry.date = datetime.now()
            
            else:
                schdl = Schedule(g.user.id, sid, s)
                db.session.add(schdl)
            
            db.session.commit()


    
    # Get calendars for active users (dict of lists, list, int)
    weekdaynames = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

    users,users_update,total,maxs = create_schedule_table(sid)
    
    myuser = dict(zip(weekdaynames,users[(g.user.username, g.user.id)]))
    calendar_form = Calendar(**myuser)

    session_week = str2date(Session.query.filter_by(id = sid).first().week)
    weekdays = [ str(session_week + timedelta(days=i)) for i in range(0,7)]
    weekdays = [ (i) for i in zip(weekdaynames,weekdays)]
    
    # Is session without a date...?
    dayOfToday = date.today()
    
    editflag = True
    if session_week <= dayOfToday:
        editflag = False
    
    # Sort users by last update
    import operator
    users_update = sorted(users_update.items(), key=operator.itemgetter(1))

    return render_template('schedule.html',
                            pagetitle = "- CMC - Schedule Session",
                            users = users, total=total, users_update = users_update,
                            maxs=maxs, calendar=calendar_form, u=g.user, weekdays=weekdays, editflag = editflag)

# --- Me --- #

@app.route('/me', methods=["GET","POST"])
@login_required
def me():
    pform = ChangePassword()
    eform = UpdateEmail()
    #
    # Check Forms
    #
    errmsg = ""
    
    if request.method == "POST":
        u = User.query.filter_by( id = g.user.id ).first()
        # If User clicked Search, query OMDB, return data in list format
        if request.form['btn'] == "Update email" and eform.validate_on_submit() and u.check_email(eform.oldemail.data, encrypted=False):            
            #u.email = u.encrypt_string( eform.email.data)
            u.email = eform.email.data
            db.session.commit()
            errmsg = "Email updated succesfully!"
        
        # If User clicked Add, check if movie is not already listed and add
        elif request.form['btn'] == "Update password" and pform.validate_on_submit() and u.check_password(pform.oldpassword.data):
            u.password = u.encrypt_string( pform.password.data )
            db.session.commit()
            errmsg = "Password updated succesfully!"
            
        else:
            errmsg = "Update failed"
            
    return render_template('me.html', pagetitle = "- CMC - Me", pform = pform, eform = eform, u=g.user, errmsg = errmsg)


# --- Stats --- #

@app.route('/stats')
@login_required
def stats():
    return render_template('stats.html',
                            pagetitle = "- CMC - Statistics")
# --- FAQ --- #

@app.route('/faq')
@login_required
def FAQ():
    return render_template('faq.html',
                            pagetitle = "- CMC - Statistics")




# --- MAIN() --- #

if __name__ == '__main__':
    app.run(debug=True)
