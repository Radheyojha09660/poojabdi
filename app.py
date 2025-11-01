from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secretkey")

# ✅ Database setup (SQLite)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "database.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
db = SQLAlchemy(app)

# ============================
# DATABASE MODELS
# ============================
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    image = db.Column(db.String(300))

# ============================
# HOME PAGE
# ============================
@app.route("/")
def home():
    products = Product.query.all()
    return render_template("index.html", products=products)

# ============================
# CART PAGE
# ============================
cart = []

@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    if product:
        cart.append(product)
        flash(f"{product.name} added to cart!", "success")
    return redirect(url_for("home"))

@app.route("/cart")
def view_cart():
    total = sum(item.price for item in cart)
    return render_template("cart.html", cart=cart, total=total)

@app.route("/remove_from_cart/<int:product_id>")
def remove_from_cart(product_id):
    global cart
    cart = [item for item in cart if item.id != product_id]
    flash("Item removed from cart.", "info")
    return redirect(url_for("view_cart"))

# ============================
# ADMIN LOGIN
# ============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        admin_pass = os.environ.get("ADMIN_PASSWORD", "admin123")
        if password == admin_pass:
            return redirect(url_for("admin"))
        flash("Incorrect password!", "danger")
    return render_template("login.html")

# ============================
# ADMIN PANEL
# ============================
@app.route("/admin")
def admin():
    products = Product.query.all()
    return render_template("admin.html", products=products)

@app.route("/add_product", methods=["POST"])
def add_product():
    name = request.form["name"]
    description = request.form["description"]
    price = request.form["price"]
    image = request.form["image"]
    new_product = Product(name=name, description=description, price=float(price), image=image)
    db.session.add(new_product)
    db.session.commit()
    flash("Product added successfully!", "success")
    return redirect(url_for("admin"))

@app.route("/delete_product/<int:id>")
def delete_product(id):
    product = Product.query.get(id)
    if product:
        db.session.delete(product)
        db.session.commit()
        flash("Product deleted successfully!", "success")
    return redirect(url_for("admin"))

# ============================
# CREATE DATABASE
# ============================
with app.app_context():
    db.create_all()

# ============================
# RUN APP
# ============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000) or 5000)
    app.run(host="0.0.0.0", port=port)
