from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Database setup (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///poojabdi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model for Admin Posts
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)

with app.app_context():
    db.create_all()

# Homepage
@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

# About Page
@app.route('/about')
def about():
    return render_template('about.html')

# Contact Page
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Admin Panel
@app.route('/admin')
def admin():
    products = Product.query.all()
    return render_template('admin.html', products=products)

# Add Product (Admin)
@app.route('/add', methods=['POST'])
def add_product():
    name = request.form['name']
    image_url = request.form['image_url']
    description = request.form['description']
    if not name:
        flash("Please enter product name", "error")
        return redirect(url_for('admin'))
    new_product = Product(name=name, image_url=image_url, description=description)
    db.session.add(new_product)
    db.session.commit()
    flash("Product added successfully!", "success")
    return redirect(url_for('admin'))

# Delete Product (Admin)
@app.route('/delete/<int:id>')
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted successfully!", "success")
    return redirect(url_for('admin'))

# Render-compatible run block
if __name__ == "__main__":
    port = os.environ.get("PORT")
    if not port or port == "":
        port = 5000
    else:
        port = int(port)
    app.run(host="0.0.0.0", port=port)
