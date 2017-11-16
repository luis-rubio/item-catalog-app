from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/catalog/')
def indexCatalog():
    categories = session.query(Category).all()
    return render_template('index.html', categories = categories)

# Category CRUD Routes
@app.route('/catalog/new/', methods=['GET', 'POST'])
def newCategory():
    if request.method == 'POST':
        urlSlug = request.form['name'].replace(" ", "")
        newCategory = Category(name=request.form['name'],slug=urlSlug)
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
    category = session.query(Category).filter_by(slug=category_slug).one()
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],description=request.form['description'],category_id=category.id)
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

@app.route('/catalog/<category_slug>/<int:item_id>/edit/')
def editItem(category_slug, item_id):
    return render_template('item_edit.html')

@app.route('/catalog/<category_slug>/<int:item_id>/delete/')
def deleteItem(category_slug, item_id):
    return render_template('item_delete.html')


if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
