import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# ---------------------------
# Flask App Configuration
# ---------------------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "mysecret")

# Database Configuration (SQLite local file)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ---------------------------
# Database Model
# ---------------------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500))
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(300))

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def home():
    products = Product.query.all()
    return render_template("index.html", products=products)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form.get("password")
        admin_pass = os.getenv("ADMIN_PASSWORD", "admin123")
        if password == admin_pass:
            products = Product.query.all()
            return render_template("admin.html", products=products)
        else:
            flash("गलत पासवर्ड!", "danger")
    return render_template("login.html")

@app.route("/add_product", methods=["POST"])
def add_product():
    name = request.form["name"]
    description = request.form["description"]
    price = request.form["price"]
    image = request.form["image"]

    product = Product(name=name, description=description, price=price, image=image)
    db.session.add(product)
    db.session.commit()
    flash("प्रोडक्ट जोड़ा गया!", "success")
    return redirect(url_for("admin"))

@app.route("/delete_product/<int:id>")
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash("प्रोडक्ट डिलीट किया गया!", "info")
    return redirect(url_for("admin"))

@app.route("/update_product/<int:id>", methods=["POST"])
def update_product(id):
    product = Product.query.get_or_404(id)
    product.name = request.form["name"]
    product.description = request.form["description"]
    product.price = request.form["price"]
    product.image = request.form["image"]
    db.session.commit()
    flash("प्रोडक्ट अपडेट हुआ!", "success")
    return redirect(url_for("admin"))

# ---------------------------
# Social Links JSON API
# ---------------------------
@app.route("/social")
def social():
    return jsonify({
        "whatsapp": "https://wa.me/919999999999",
        "facebook": "https://facebook.com/poojabadi",
        "instagram": "https://instagram.com/poojabadi",
    })

# ---------------------------
# Main entry point
# ---------------------------
if __name__ == "__main__":
    # ✅ FIX: Flask app context added for Render
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
