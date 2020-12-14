from flask import Flask, render_template, abort, request, redirect, url_for, g, session, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}/{}'.format(app.root_path, 'marketplace.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'b2de7FkqvkMyqzNFzxCkgnPKIGP6i4Rc'
db = SQLAlchemy(app)


class Category(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)

class Manufacturer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref=db.backref('category', lazy=True))
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('manufacturer.id'), nullable=False)
    manufacturer = db.relationship('Manufacturer', backref=db.backref('manufacturer'), lazy=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(50), nullable=False, default = 'https://static.thenounproject.com/png/261694-200.png')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100),unique=True, nullable=False)
    password = db.Column(db.String(100), nullable = False)

    def check_password(self,value): 
        return check_password_hash(self.password,value)


db.create_all()


@app.before_request
def load_user(): 
    user_id = session.get("user_id")
    g.user = User.query.get(user_id) if user_id is not None else None

def login_required(func): 
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if g.user is None: 
            return redirect(url_for("login", next = request.url))
        return func(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == "POST": 
        username = request.form["username"]
        password = request.form["password"]

        error = None 

        user = User.query.filter_by(username=username).first()

        if user is None: 
            error = "Incorrect username."
        elif not user.check_password(password): 
            error = "Incorrect password."
        
        if error is None:
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("admin_categories"))

        flash(error)
    return render_template("admin/login.html")

@app.route("/logout")
def logout(): 
    session.clear()
    return redirect(url_for("login"))

@app.route("/register", methods=('GET', 'POST'))
def register(): 
    if request.method == "POST": 
        username = request.form["username"]
        password = request.form["password"]

        error = None 

        users = User.query.all()

        for singleUser in users: 
            if singleUser.username == username:
                error = 'That login already exists'

        if error is None: 
            user = User(username = username, password = generate_password_hash(password))
            db.session.add(user)
            db.session.commit() 
            return redirect(url_for("login"))
        flash(error)
    return render_template("admin/register.html")



@app.route('/')
def index():
    return render_template("index.html")

@app.route("/categories")
def categories(): 
    categories = Category.query.all()
    return render_template("categories.html", categories = categories)

@app.route("/category/<categoryPass>")
def category(categoryPass):
    chosenCategory = Category.query.filter(Category.name == categoryPass).first()
    products = Product.query.filter(Product.category_id == chosenCategory.id)
    return render_template("category.html", category = chosenCategory, products = products)

@app.route("/product/<id>")
def product(id): 
    import decimal
    product = Product.query.get(id)
    productPrice = product.price
    dollars = decimal.Decimal(productPrice) / 100
    return render_template("product.html", product = product, price = dollars)

@app.route('/admin')
@app.route('/admin/categories')
@login_required
def admin_categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/products')
@login_required
def admin_products():
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/manufacturers')
@login_required
def admin_manufacturers():
    manufacturers = Manufacturer.query.all()
    return render_template('admin/manufacturers.html', manufacturers=manufacturers)

@app.route('/admin/create/category', methods=('GET', 'POST'))
@login_required
def create_category():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
    
        error = None
        
        if not name:
            error = 'Name is required.'

        if not description: 
            error = 'Description is required.'
            
        if error is None:
            category = Category(name=name, description = description)
            db.session.add(category)
            db.session.commit()
            return redirect(url_for('admin_categories'))
    
        flash(error)

    categories = Category.query.all()
    return render_template('admin/category_form.html', categories=categories)    

@app.route('/admin/create/manufacturer', methods=('GET', 'POST'))
@login_required
def create_manufacturer():
    if request.method == 'POST':
        name = request.form['name']

        error = None
        
        if not name:
            error = 'Name is required.'
     
        if error is None:
            manufacturer = Manufacturer(name=name)
            db.session.add(manufacturer)
            db.session.commit()
            return redirect(url_for('admin_manufacturers'))
    
        flash(error)

    manufacturers = Manufacturer.query.all()
    return render_template('admin/manufacturer_form.html', manufacturers=manufacturers)

@app.route('/admin/create/product', methods=('GET', 'POST'))
@login_required
def create_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        manufacturer_id = request.form['manufacturer_id']
        category_id = request.form['category_id']
        price = request.form['price']
        image_file = request.form['image_file']

        error = None
            
        if error is None:
            product = Product(name=name,description=description,manufacturer_id = manufacturer_id,category_id=category_id, price = price, image_file = image_file)
            db.session.add(product)
            db.session.commit()
            return redirect(url_for('admin_products'))
    
        flash(error)

    products = Product.query.all()
    categories = Category.query.all()
    manufacturers = Manufacturer.query.all()
    return render_template('admin/product_form.html', products=products, manufacturers = manufacturers, categories = categories)

@app.route('/admin/edit/category/<id>', methods=('GET', 'POST'))
@login_required
def edit_category(id):

    category = Category.query.get_or_404(id)

    if request.method == 'POST':
        category.name = request.form['name']
        category.description = request.form['description']

        error = None
        
        if not request.form['name']:
            error = 'Name is required.'
       
        if error is None:
            db.session.commit()
            return redirect(url_for('admin_categories'))
    
        flash(error)

    return render_template('admin/category_form.html', name=category.name, description=category.description)

@app.route('/admin/edit/manufacturer/<id>', methods=('GET', 'POST'))
@login_required
def edit_manufacturer(id):

    manufacturer = Manufacturer.query.get_or_404(id)

    if request.method == 'POST':
        Manufacturer.name = request.form['name']

        error = None
        
        if not request.form['name']:
            error = 'Name is required.'
       
        if error is None:
            db.session.commit()
            return redirect(url_for('admin_manufacturers'))
    
        flash(error)

    return render_template('admin/manufacturer_form.html', name=manufacturer.name)

@app.route('/admin/edit/product/<id>', methods=('GET', 'POST'))
@login_required
def edit_product(id):

    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        manufacturer_id = request.form['manufacturer_id']
        category_id = request.form['category_id']
        price = request.form['price']
        image_file = request.form['image_file']

        error = None
            
        if error is None:
            db.session.commit()
            return redirect(url_for('admin_products'))
    
        flash(error)

    products = Product.query.all()
    categories = Category.query.all()
    manufacturers = Manufacturer.query.all()
    return render_template('admin/product_form.html', products=products, manufacturers = manufacturers, categories = categories, name = product.name, description = product.description, price = product.price, image_file = product.image_file)


@app.route('/admin/delete/category/<id>', methods=('GET', 'POST'))
@login_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    if request.method == 'POST':
        error = None
      
        if error is None:
            Category.query.filter_by(id=id).delete()
            db.session.commit()
            return redirect(url_for('admin_categories'))
    
        flash(error)

    return render_template('admin/category_delete.html', name=category.name)


@app.route('/admin/delete/product/<id>', methods=('GET', 'POST'))
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        error = None
      
        if error is None:
            Product.query.filter_by(id=id).delete()
            db.session.commit()
            return redirect(url_for('admin_products'))
    
        flash(error)

    return render_template('admin/product_delete.html', name=product.name)

@app.route('/admin/delete/manufacturer/<id>', methods=('GET', 'POST'))
@login_required
def delete_manufacturer(id):
    manufacturer = Manufacturer.query.get_or_404(id)
    if request.method == 'POST':
        error = None
      
        if error is None:
            Manufacturer.query.filter_by(id=id).delete()
            db.session.commit()
            return redirect(url_for('admin_manufacturers'))
    
        flash(error)

    return render_template('admin/manufacturer_delete.html', name=manufacturer.name)

