from flask import Flask, render_template, redirect, request, session, flash
from flask_bcrypt import Bcrypt
from mysqlconnection import connectToMySQL
import re

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "thisissecretkey"

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
   
    is_valid = True
    if len(request.form['first_name'])<2:
        flash('First name must be longer than 2 characters.')
        is_valid = False
    if len(request.form['last_name'])<2:
        flash('Last name must be longer than 2 characters.')
        is_valid = False
    if not re.match(EMAIL_REGEX, request.form['email']):
        flash('Email address is not valid.')
        is_valid = False
    if len(request.form['password'])<8:
        flash('Password must be at least 8 characters long')
        is_valid = False
    if request.form['password'] != request.form['confirm_password']:
        flash('Passwords do not match.')
        is_valid = False

    if is_valid == False:
        return redirect('/')    
    
    else:
        password = bcrypt.generate_password_hash(request.form['password'])
        mysql = connectToMySQL('trips_buddy')
        query = 'INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES(%(first)s, %(last)s, %(em)s, %(pw)s, NOW(), NOW());'
        data = {
            'first': request.form['first_name'],
            'last': request.form['last_name'],
            'em': request.form['email'],
            'pw': password
        }
        user_id = mysql.query_db(query, data)
        session['id'] = user_id
        session['greeting'] = request.form['first_name']
        return redirect('/dashboard')

@app.route('/login', methods=['POST'])
def login():
    mysql = connectToMySQL('trips_buddy')
    query = "SELECT * FROM users WHERE email = %(em)s;"
    data = {
        'em': request.form['email']
    }
    matching_users = mysql.query_db(query, data)
    if matching_users:
        user = matching_users[0]
        if bcrypt.check_password_hash(user['password'], request.form['password']):
            session['id'] = user['id']
            session['greeting'] = user['first_name']
            return redirect('/dashboard')

    flash("Email or password invalid")
    return redirect('/')

@app.route('/dashboard')
def trip_app():
    if not 'id' in session:
        return redirect('/')
    else:
        mysql = connectToMySQL('trips_buddy')
        trips = mysql.query_db('SELECT * FROM trips;') #WHERE id=%(id)s

#        mysql = connectToMySQL('trips_buddy')
#        joined = mysql.query_db('SELECT trips.destination, users.first_name, trips.start_date, trips.end_date FROM trips JOIN users ON trips.traveler = users.id WHERE joined_trip IS NOT NULL;')
        print(trips)
        return render_template('trips.html', all_trips=trips)

@app.route('/trips/new')
def new_trip():
    return render_template('new.html')

@app.route('/page', methods =['POST'])
def add_trip():
    is_valid = True

    if  len(request.form['destination'])<3:
        flash("A trip Destination must be at least 3 characters.")
        is_valid = False
    if  len(request.form['start_date'])<3:
        flash("Start date must be filled.")
        is_valid = False
    if  len(request.form['end_date'])<3:
        flash("End date must be filled")
        is_valid = False
    if len(request.form['plan']) < 10:
        flash("A plan must be provided.")
        is_valid = False
    
    if is_valid == False:
        return redirect('/trips/new')
    else:
        mysql = connectToMySQL('trips_buddy')
        print(request.form)
        query = "INSERT INTO trips (destination, start_date, end_date, plan, created_at, updated_at, traveler) VALUES(%(des)s, %(std)s, %(end)s, %(pl)s, NOW(), NOW(), %(tl)s);"
        data = {
            "des" : request.form['destination'],
            "std" : request.form['start_date'],
            "end" : request.form['end_date'],
            "pl" : request.form['plan'],
            "tl" : session['id']
        }
        new_trip = mysql.query_db(query, data)
        return redirect('/dashboard')

@app.route('/trips/<id>')
def triped(id):
    mysql = connectToMySQL('trips_buddy')
    query = "UPDATE trips SET cal_trips=NOW() WHERE id=%(tl)s;" #fix this either by creating new field, in trips table
    data = {
        'tl': id
    }
    mysql.query_db(query,data)

    return redirect(f'/dashboard')
    
@app.route('/trips/edit/<id>')
def edit(id):
    mysql = connectToMySQL('trips_buddy')
    query = "SELECT * FROM trips WHERE id = %(id)s;"
    data = {
        'id' : id
    }
    trip = mysql.query_db(query, data)
    return render_template('edit.html', trip=trip[0])

@app.route('/trips/<id>/update', methods=['POST'])
def update(id):
    is_valid = True

    if  len(request.form['destination'])<3:
        flash("A trip Destination must be at least 3 characters.")
        is_valid = False
    if  len(request.form['start_date'])<3:
        flash("Start date must be filled.")
        is_valid = False
    if  len(request.form['end_date'])<3:
        flash("End date must be filled")
        is_valid = False
    if len(request.form['plan']) < 10:
        flash("A plan must be provided.")
        is_valid = False
    
    if is_valid == False:
        return redirect('/dashboard')
    
    else:
        mysql = connectToMySQL('trips_buddy')
        query = "UPDATE trips SET destination=%(des)s, start_date=%(std)s, end_date=%(end)s, plan=%(pl)s, updated_at=NOW() WHERE id=%(id)s"
        data = {
            "des" : request.form['destination'],
            "std" : request.form['start_date'],
            "end" : request.form['end_date'],
            "pl" : request.form['plan'],
            "id" : id
        }
        mysql.query_db(query, data)
        flash('Your Information has been updated')
    return redirect('/dashboard') #end here

@app.route('/trips/<id>/show')
def show_one(id):
    mysql = connectToMySQL('trips_buddy')
    query = "SELECT * FROM trips WHERE id = %(id)s;"
    data = {
        'id' : id
    }
    trip = mysql.query_db(query, data)
    print(trip)
    return render_template('show.html', trip=trip[0])

@app.route('/delete/<id>')
def delete(id):
    mysql = connectToMySQL('trips_buddy')
    query = 'DELETE FROM trips WHERE id = %(id)s;'
    data = {
        'id' : int(id)
    }
    mysql.query_db(query, data)
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)