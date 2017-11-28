# Item Catalog App
A project for Udacity that displays an item catalog. The purpose is to create a RESTful web application using the Flask framework (Python). The app is implemented with a third-party OAuth authentication (Google API) and has the basic CRUD functionality.
## Installation
1. Install Vagrant and Virtualbox
2. Clone `item-catalog-app`
3. Add `catalog` to virtual host
4. Launch VM (vagrant up)
5. CD into `catalog` folder
6. Run `python app.py` on terminal
## Usage
1. Go to "http://localhost:8000" on your browser.
2. Create an account by clicking on the **login** button.
3. Click on a category to view all items. (Read)
4. Click "Add item to category" to add new item. (Create)
- You can **edit** or **delete** an item if you created it.
- Click **logout** button to disconnect.
## To Do List
1. Make an admin table for users
2. Have category CRUD function available only to admins.
