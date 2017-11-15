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
def index():
    categories = session.query(Category).all()
    return render_template('category_index.html', categories = categories)

# Category CRUD Routes
@app.route('/catalog/new', methods=['GET', 'POST'])
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
    return render_template('category_show.html', category=category)

@app.route('/catalog/<category_slug>/edit', methods=['GET', 'POST'])
def editCategory(category_slug):
    editCategory = session.query(Category).filter_by(slug=category_slug).one()

    if request.method == 'POST':
        if request.form['name']:
            editCategory.slug = request.form['name'].replace(" ", "")
            editCategory.name = request.form['name']
            return redirect(url_for('indexCatalog'))
    else:
        return render_template('category_edit.html', category=editCategory)

@app.route('/catalog/<category_slug>/delete', methods=['GET', 'POST'])
def deleteCategory(category_slug):
    categoryToDelete = session.query(Category).filter_by(slug=category_slug).one()
    if request.method == 'POST':
        session.delete(categoryToDelete)
        session.commit()
        return redirect(url_for('indexCatalog'))
    else:
        return render_template('category_delete.html', category=categoryToDelete)

# Item CRUD Routes
@app.route('/catalog/<category_slug>/new')
def newItem(category_slug):
    return "add item"

@app.route('/catalog/<category_slug>/<int:item_id>')
def showItem(category_slug, item_id):
    return "display item"

@app.route('/catalog/<category_slug>/<int:item_id>/edit')
def editItem(category_slug, item_id):
    return "edit item"

@app.route('/catalog/<category_slug>/<int:item_id>/delete')
def deleteItem(category_slug, item_id):
    return "delete item"


if __name__ == '__main__':
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
