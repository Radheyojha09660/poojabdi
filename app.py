from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///poojabdi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(500), nullable=True)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    active = db.Column(db.Boolean, default=True)

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(200), default='पूजा बड़ी पापड़ उद्योग')
    tagline = db.Column(db.String(300), default='राजस्थान की पारंपरिक रेसिपी का स्वाद')
    logo = db.Column(db.String(500), default='')
    accent = db.Column(db.String(20), default='#ef4444')

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)
    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

# Helpers
def get_settings():
    s = Setting.query.first()
    if not s:
        s = Setting()
        db.session.add(s)
        db.session.commit()
    return s

def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*a, **k):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return fn(*a, **k)
    return wrapper

# Routes
@app.route('/')
def index():
    settings = get_settings()
    products = Product.query.filter_by(active=True).all()
    return render_template('index.html', products=products, settings=settings)

@app.route('/product/<slug>')
def product_detail(slug):
    p = Product.query.filter_by(slug=slug).first_or_404()
    settings = get_settings()
    return render_template('product.html', product=p, settings=settings)

@app.route('/cart')
def view_cart():
    settings = get_settings()
    return render_template('cart.html', settings=settings)

@app.route('/api/products')
def api_products():
    prods = Product.query.filter_by(active=True).all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'price': p.price,
        'image': p.image,
        'slug': p.slug
    } for p in prods])

# Admin routes
@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        admin = Admin.query.filter_by(username=u).first()
        if admin and admin.check_password(p):
            session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials','danger')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    products = Product.query.order_by(Product.id.desc()).all()
    settings = get_settings()
    return render_template('admin/dashboard.html', products=products, settings=settings)

@app.route('/admin/product/new', methods=['GET','POST'])
@admin_required
def admin_new_product():
    if request.method=='POST':
        title = request.form['title']
        slug = request.form['slug']
        price = float(request.form['price'])
        desc = request.form.get('description','')
        image = request.form.get('image','')
        p = Product(title=title, slug=slug, price=price, description=desc, image=image)
        db.session.add(p)
        db.session.commit()
        flash('Product added','success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/product_form.html', product=None)

@app.route('/admin/product/edit/<int:pid>', methods=['GET','POST'])
@admin_required
def admin_edit_product(pid):
    p = Product.query.get_or_404(pid)
    if request.method=='POST':
        p.title = request.form['title']
        p.slug = request.form['slug']
        p.price = float(request.form['price'])
        p.description = request.form.get('description','')
        p.image = request.form.get('image','')
        p.active = bool(request.form.get('active'))
        db.session.commit()
        flash('Product updated','success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/product_form.html', product=p)

@app.route('/admin/product/delete/<int:pid>', methods=['POST'])
@admin_required
def admin_delete_product(pid):
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash('Deleted','success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/settings', methods=['GET','POST'])
@admin_required
def admin_settings():
    s = get_settings()
    if request.method=='POST':
        s.site_name = request.form.get('site_name', s.site_name)
        s.tagline = request.form.get('tagline', s.tagline)
        s.logo = request.form.get('logo', s.logo)
        s.accent = request.form.get('accent', s.accent)
        db.session.commit()
        flash('Settings saved and applied','success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/settings.html', settings=s)

@app.route('/admin/preview/<int:pid>')
@admin_required
def admin_preview(pid):
    p = Product.query.get_or_404(pid)
    settings = get_settings()
    return render_template('admin/preview.html', product=p, settings=settings)

# CLI command to init DB
@app.cli.command('init-db')
def init_db():
    db.create_all()
    if not Admin.query.first():
        a = Admin(username='admin')
        a.set_password('admin123')
        db.session.add(a)
    if not Setting.query.first():
        db.session.add(Setting())
    db.session.commit()
    print('DB initialized')

if __name__=='__main__':
    app.run(debug=True)
