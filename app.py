from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/')
@app.route('/catalog/')
def indexCatalog():
    categories = session.query(Category).all()
    return render_template('index.html', categories = categories)

# Category CRUD Routes
@app.route('/catalog/new/', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        urlSlug = request.form['name'].replace(" ", "")
        newCategory = Category(name=request.form['name'],slug=urlSlug,user_id=login_session['user_id'])
        if session.query(Category).filter_by(slug=urlSlug).count() < 1:
            session.add(newCategory)
            session.commit()
        return redirect(url_for('indexCatalog'))
    else:
        return render_template('category_new.html')

@app.route('/catalog/<category_slug>/')
def showCategory(category_slug):
    category = session.query(Category).filter_by(slug=category_slug).one()
    items = session.query(Item).filter_by(category_id=category.id).all()
    return render_template('category_show.html', items=items, category=category)

@app.route('/catalog/<category_slug>/edit/', methods=['GET', 'POST'])
def editCategory(category_slug):
    if 'username' not in login_session:
        return redirect('/login')
    editCategory = session.query(Category).filter_by(slug=category_slug).one()
    if request.method == 'POST':
        if request.form['name']:
            editCategory.slug = request.form['name'].replace(" ", "")
            editCategory.name = request.form['name']
            return redirect(url_for('indexCatalog'))
    else:
        return render_template('category_edit.html', category=editCategory)

@app.route('/catalog/<category_slug>/delete/', methods=['GET', 'POST'])
def deleteCategory(category_slug):
    if 'username' not in login_session:
        return redirect('/login')
    categoryToDelete = session.query(Category).filter_by(slug=category_slug).one()
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        return redirect(url_for('indexCatalog'))
    else:
        return render_template('category_delete.html', category=categoryToDelete)

# Item CRUD Routes
@app.route('/catalog/<category_slug>/new/', methods=['GET', 'POST'])
def newItem(category_slug):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(slug=category_slug).one()
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],description=request.form['description'],category_id=category.id,user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        return redirect(url_for('showCategory', category_slug=category.slug))
    else:
        return render_template('item_new.html')

@app.route('/catalog/<category_slug>/<int:item_id>/')
def showItem(category_slug, item_id):
    category = session.query(Category).filter_by(slug=category_slug).one()
    item = session.query(Item).filter_by(id=item_id).one()
    return render_template('item_show.html', item=item, category=category)

@app.route('/catalog/<category_slug>/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(category_slug, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(slug=category_slug).one()
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('showCategory', category_slug=category.slug))
    else:
        return render_template('item_edit.html', item=editedItem, category=category)

@app.route('/catalog/<category_slug>/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteItem(category_slug, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(slug=category_slug).one()
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showCategory', category_slug=category.slug))
    else:
        return render_template('item_delete.html', item=itemToDelete, category=category)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
