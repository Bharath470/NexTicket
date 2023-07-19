from flask import Flask, render_template, request, redirect , session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__) # initialization of app
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.sqlite3" # to configure the app

db = SQLAlchemy(app) #initialization of database
app.app_context().push() 
app.config['SECRET_KEY'] = "secretkeytomyapp" # for sesssions to work properly

class Venue(db.Model):
    venue_id = db.Column(db.Integer, primary_key = True)
    venue_name = db.Column(db.String, nullable = False)
    venue_place = db.Column(db.String, nullable = False)
    venue_cap =  db.Column(db.Integer, nullable = False)
    shows=db.relationship("Show")

class Show(db.Model):
    show_id = db.Column(db.Integer, primary_key = True)
    show_name = db.Column(db.String, nullable = False)
    show_rating = db.Column(db.String, nullable = False)
    show_tags =  db.Column(db.String, nullable = False)
    ticket_price = db.Column(db.Integer, nullable = False)
    venue_id=db.Column(db.Integer, db.ForeignKey(Venue.venue_id))
   # venues=db.relationship("Venue",backpopulates="shows")

# class Association(db.Model):
#     show_id=db.Column(db.Integer, db.ForeignKey("show.show_id"),primary_key=True)
#     venue_id=db.Column(db.Integer, db.ForeignKey("venue.venue_id"),primary_key=True)   

class User(db.Model):
    user_id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(20),unique= True, nullable= False)
    password=db.Column(db.String(80), nullable= False)
    bookings=db.relationship('Booking',backref='user')

class Admin(db.Model):
    admin_id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(20),unique= True, nullable= False)
    password=db.Column(db.String(80), nullable= False)    

class Booking(db.Model):
    booking_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.user_id'),nullable = False)
    show_id = db.Column(db.Integer,db.ForeignKey('show.show_id'),nullable = False)
    venue_id = db.Column(db.Integer,db.ForeignKey('venue.venue_id'),nullable = False)
    no_seats = db.Column(db.Integer, nullable = False)
    total_price = db.Column(db.Integer, nullable = False)




@app.route('/')
def login_page():
    return render_template('login.html')

# @app.route('/login', methods = ['POST','GET'])
# def login_page():
#     return render_template('login.html')

@app.route('/homeadmin')
def home_page():  # For CRUD operations
    return render_template('home.html')


@app.route('/adminlogin', methods = ['POST','GET'])
def adminlogin():
    if request.method == 'POST':
        uname = request.form['uname']
        pword = request.form['pword']
        admin=Admin.query.filter_by(username = uname).first()
        if (admin.username == uname ) and (admin.password == pword):
            session['username'] = uname
            # session['admin_id'] = admin.user_id
            return redirect('/homeadmin')
    return render_template('adminlogin.html')

@app.route('/userlogin', methods = ['POST','GET'])
def userlogin():
    if request.method == 'POST':
        uname = request.form['uname']
        pword = request.form['pword']
        user=User.query.filter_by(username = uname).first()
        if (user.username == uname ) and (user.password == pword):
            session['username'] = uname
            session['user_id'] = user.user_id
            return redirect('/userhome')    # to be filled
    return render_template('userlogin.html')

@app.route('/logout', methods = ['GET', 'POST'])
def logout():
    if 'username' in session:
        session.pop('username',None)
        return redirect('/')

@app.route('/userhome', methods =['post','get'])
def userhome():
    all=Venue.query.all()
    return render_template('userhome.html', all = all)

@app.route('/shows/view/<int:v_id>', methods=['get','post'])
def showsview(v_id):
    venue = Venue.query.get(v_id)
    shows = venue.shows
    return render_template('shows_view_user.html',venue = venue, shows=shows)

@app.route('/shows/book/<int:s_id>',methods=['get','post'])
def booktickets(s_id):
    show = Show.query.get(s_id)
    price = show.ticket_price
    ven_id = show.venue_id
    ven=Venue.query.get(ven_id)
    all_bookings_data = Booking.query.filter_by(venue_id=ven.venue_id).all()
    no_booked_seats = sum([booking.no_seats for booking in all_bookings_data])
    no_avail_seats = ven.venue_cap - no_booked_seats
    no_seats = 0
    total_price = no_seats * price
    if request.method=="POST":
        user_id = session['user_id']
        no_seats = int(request.form['no_seats'])
        if no_seats <= no_avail_seats:
            
            total_price = no_seats * price
            booking = Booking(user_id = user_id, show_id = s_id, venue_id = ven.venue_id, no_seats = no_seats, total_price=total_price)
            db.session.add(booking)
            db.session.commit()
            return render_template('confirmation.html',show = show,ven = ven,no_seats = no_seats,total_price = total_price,all_bookings_data = all_bookings_data)
    return render_template('booktickets.html',show=show, ven=ven, no_avail_seats=no_avail_seats , no_seats=no_seats)    

@app.route('/booked', methods = ['post','get'])
def booked():
    render_template('confirmation.html')

@app.route('/userbookings' , methods = ['POST' , 'GET'])
def showuserbookings():
    user_id=session['user_id']
    userbookings=Booking.query.filter_by(user_id = user_id).all()
    dict_shows={}
    dict_venues={}
    for booking in userbookings:
        ven=Venue.query.get(booking.venue_id)
        sho=Show.query.get(booking.show_id)
        dict_shows[booking.show_id]=sho.show_name
        dict_venues[booking.venue_id]=ven.venue_name
    return render_template('userbookings.html',userbookings = userbookings, dict_shows = dict_shows, dict_venues = dict_venues)    

@app.route('/searchvenue' , methods = ['POST' , 'GET'])
def searchvenue():
    if request.method == "POST":
        venue=request.form['search']    
        # vens=Venue.query.filter_by(venue_name=venue).all()
        vens = Venue.query.filter(Venue.venue_name.ilike(venue)).all()  # case insensitive results

        return render_template('userhome.html', all = vens) 

@app.route('/searchshows/<int:v_id>' , methods = ['POST' , 'GET'])
def searchshow(v_id):
    if request.method == "POST":
        sho=request.form['search']
        ven=Venue.query.get(v_id)
        # shows=Show.query.filter_by(show_name=sho).all()
        shows = Show.query.filter(Show.show_name.ilike(sho)).all()
        
        return render_template('shows_view_user.html', shows = shows , venue = ven) 
    
@app.route('/userregister', methods = ['POST','GET'])
def user_reg():
    if request.method == 'POST':
        uname = request.form['uname']
        pword = request.form['pword']
        user = User(username = uname , password = pword)
        db.session.add(user)
        db.session.commit()
        return redirect('/userlogin')
    return render_template('user_registration.html')

@app.route('/adminregister', methods = ['POST','GET'])
def admin_reg():
    if request.method == 'POST':
        uname = request.form['uname']
        pword = request.form['pword']
        admin = Admin(username = uname , password = pword)
        db.session.add(admin)
        db.session.commit()
        return redirect('/adminlogin')
    return render_template('admin_registration.html')

@app.route('/venue/create', methods = ['POST','GET'])
def venue_creation():
    if request.method == 'POST':
        v_name = request.form['v_name']
        v_place = request.form['v_place']
        v_cap = request.form['v_cap']
        venue1 = Venue(
            venue_name = v_name,
            venue_place = v_place,
            venue_cap = v_cap
        )
        db.session.add(venue1)
        db.session.commit()
        return redirect('/homeadmin')
    return render_template("venue.html")

@app.route('/venue/view')
def view_venue():
    all = Venue.query.all()
    return render_template("view_venue.html",all = all)

@app.route('/venue/update/<int:venue_id>', methods = ['POST','GET'])
def venue_updation(venue_id):
    if request.method == 'POST':
        venue=Venue.query.get(venue_id)
        venue.venue_name = request.form['v1_name']
        venue.venue_place = request.form['v1_place']
        venue.venue_cap = request.form['v1_cap']
        db.session.commit()
        return redirect('/venue/view')
    venue=Venue.query.get(venue_id)
    return render_template("editvenue.html",venue = venue)

@app.route('/venue/delete/<int:id>', methods=['GET','POST'])
def venue_deletion(id):
    venue = Venue.query.get(id)
    db.session.delete(venue)
    db.session.commit()
    return redirect('/venue/view')


@app.route('/show/create', methods = ['POST','GET'])
def show_creation():
    
    if request.method == 'POST':
        s_name = request.form['s_name']
        s_rating = request.form['s_rating']
        s_tags = request.form['s_tags']
        s_price = request.form['s_price']
        v_id = request.form['v_id']
        print(v_id,s_price)
        show1 = Show(
            show_name = s_name,
            show_rating = s_rating,
            show_tags = s_tags,
            ticket_price = s_price,
            venue_id=v_id
        )
        # ven=Venue.query.get(v_id)
        #print(show1.venue_id)
        db.session.add(show1)
        # ven.shows.append(show1)
        db.session.commit()
        return redirect('/homeadmin')
    vens = Venue.query.all()
    return render_template("show.html", vens = vens)

@app.route('/show/view/<int:venue_id>')
def view_show(venue_id):
    venue=Venue.query.get(venue_id)
    all = venue.shows
    return render_template("view_shows.html",all = all , venue_id=venue_id)

@app.route('/show/update/<int:show_id>', methods = ['POST','GET'])
def show_updation(show_id):
    
    if request.method == 'POST':
        show=Show.query.get(show_id)
        show.show_name = request.form['s1_name']
        show.show_rating = request.form['s1_rating']
        show.show_tags = request.form['s1_tags']
        show.ticket_price = request.form['s1_price']
        # v_id = request.form['v1_id']
        db.session.commit()
        return redirect(f'/show/view/{show.venue_id}')
    show=Show.query.get(show_id)
    return render_template("editshow.html", show = show)

@app.route('/show/delete/<int:id>', methods=['GET','POST'])
def show_deletion(id):
    show = Show.query.get(id)
    db.session.delete(show)
    db.session.commit()
    return redirect('/venue/view')



if(__name__== "__main__") :
    app.run(debug = True)
