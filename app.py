from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Database configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "poojabdi.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =====================================================
# MODELS
# =====================================================

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100))
    tagline = db.Column(db.String(200))
    logo = db.Column(db.String(200))
    accent = db.Column(db.String(20))


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(50))


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    image = db.Column(db.String(200))


# =====================================================
# INITIAL DATABASE SETUP
# =====================================================

@app.cli.command("init-db")
def init_db():
    """Manual init: flask --app app.py init-db"""
    db.create_all()

    if not Setting.query.first():
        default_setting = Setting(
            site_name="Pooja Badi Papad Udyog",
            tagline="Rajasthan ki paramparik recipe ka swaad",
            logo="/static/img/logo.png",
            accent="#eab308"
        )
        db.session.add(default_setting)

    if not Admin.query.first():
        default_admin = Admin(username="admin", password="admin123")
        db.session.add(default_admin)

    db.session.commit()
    print("✅ Database initialized successfully.")


# Auto create tables on startup (useful for Render)
with app.app_context():
    try:
        db.create_all()
        if not Setting.query.first():
            default_setting = Setting(
                site_name="Pooja Badi Papad Udyog",
                tagline="Rajasthan ki paramparik recipe ka swaad",
                logo="/static/img/logo.png",
                accent="#eab308"
            )
            db.session.add(default_setting)
        if not Admin.query.first():
            default_admin = Admin(username="admin", password="admin123")
            db.session.add(default_admin)
        db.session.commit()
    except Exception as e:
        print("⚠️ DB init error:", e)


# =====================================================
# ROUTES
# =====================================================

@app.route("/")
def home():
    setting = Setting.query.first()
    products = Product.query.all()
    return render_template("index.html", setting=setting, products=products)


@app.route("/cart")
def cart():
    setting = Setting.query.first()
    return render_template("cart.html", setting=setting)


# ------------------ ADMIN PANEL ----------------------

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("❌ Invalid credentials")
    return render_template("admin/login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    setting = Setting.query.first()
    products = Product.query.all()
    return render_template("admin/dashboard.html", setting=setting, products=products)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin/add_product", methods=["POST"])
def add_product():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    name = request.form["name"]
    description = request.form["description"]
    price = float(request.form["price"])
    image = request.form["image"]
    new_product = Product(name=name, description=description, price=price, image=image)
    db.session.add(new_product)
    db.session.commit()
    flash("✅ Product added successfully!")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/update_settings", methods=["POST"])
def update_settings():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    setting = Setting.query.first()
    setting.site_name = request.form["site_name"]
    setting.tagline = request.form["tagline"]
    setting.logo = request.form["logo"]
    setting.accent = request.form["accent"]
    db.session.commit()
    flash("✅ Settings updated successfully!")
    return redirect(url_for("admin_dashboard"))


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
