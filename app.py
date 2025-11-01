import os
import time
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# ---------- Config ----------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change_this_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'poojabdi.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Uploads
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif"}
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # 12 MB

db = SQLAlchemy(app)

# ---------- Models ----------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(240), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.String(50), nullable=True)
    image = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def image_url(self):
        if self.image:
            return url_for("static", filename=f"uploads/{self.image}")
        return url_for("static", filename="uploads/placeholder.png")

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# ---------- Helpers ----------
def allowed_file(fname):
    return "." in fname and fname.rsplit(".", 1)[1].lower() in ALLOWED_EXT

# ---------- DB init ----------
with app.app_context():
    db.create_all()

# ---------- Public routes ----------
@app.route("/")
def index():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("index.html", products=products)

@app.route("/product/<int:pid>")
def product_view(pid):
    p = Product.query.get_or_404(pid)
    return render_template("product_view.html", product=p)

# Cart (session based)
@app.route("/add-to-cart/<int:pid>")
def add_to_cart(pid):
    cart = session.get("cart", [])
    if pid not in cart:
        cart.append(pid)
    session["cart"] = cart
    flash("Product added to cart.", "success")
    return redirect(request.referrer or url_for("index"))

@app.route("/remove-from-cart/<int:pid>")
def remove_from_cart(pid):
    cart = session.get("cart", [])
    cart = [i for i in cart if i != pid]
    session["cart"] = cart
    flash("Removed from cart.", "info")
    return redirect(url_for("cart_view"))

@app.route("/cart")
def cart_view():
    cart = session.get("cart", [])
    products = Product.query.filter(Product.id.in_(cart)).all() if cart else []
    total = sum(float(p.price or 0) for p in products)
    return render_template("cart.html", products=products, total=total)

# Contact
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        c = Contact(name=name, email=email, message=message)
        db.session.add(c)
        db.session.commit()
        flash("Message received. We will contact you shortly.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")

# ---------- Admin auth ----------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw == os.environ.get("ADMIN_PASSWORD", "admin123"):
            session["is_admin"] = True
            flash("Welcome admin", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Incorrect password", "danger")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Logged out", "info")
    return redirect(url_for("index"))

def require_admin(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*a, **kw):
        if not session.get("is_admin"):
            flash("Please login as admin", "warning")
            return redirect(url_for("admin_login"))
        return fn(*a, **kw)
    return wrapper

# ---------- Admin dashboard & CRUD ----------
@app.route("/admin")
@require_admin
def admin_dashboard():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("admin_dashboard.html", products=products)

@app.route("/admin/add", methods=["GET", "POST"])
@require_admin
def admin_add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", "").strip()
        image_file = request.files.get("image")
        filename = None
        if image_file and image_file.filename:
            if allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                filename = f"{int(time.time())}_{filename}"
                image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            else:
                flash("File type not allowed", "danger")
                return redirect(url_for("admin_add"))
        p = Product(name=name, description=description, price=price, image=filename)
        db.session.add(p)
        db.session.commit()
        flash("Product added", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("add_product.html")

@app.route("/admin/edit/<int:pid>", methods=["GET", "POST"])
@require_admin
def admin_edit(pid):
    p = Product.query.get_or_404(pid)
    if request.method == "POST":
        p.name = request.form.get("name", p.name).strip()
        p.description = request.form.get("description", p.description).strip()
        p.price = request.form.get("price", p.price).strip()
        image_file = request.files.get("image")
        if image_file and image_file.filename:
            if allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                filename = f"{int(time.time())}_{filename}"
                image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                try:
                    if p.image:
                        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], p.image))
                except Exception:
                    pass
                p.image = filename
            else:
                flash("File type not allowed", "danger")
                return redirect(url_for("admin_edit", pid=pid))
        db.session.commit()
        flash("Product updated", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("edit_product.html", product=p)

@app.route("/admin/delete/<int:pid>", methods=["POST"])
@require_admin
def admin_delete(pid):
    p = Product.query.get_or_404(pid)
    try:
        if p.image:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], p.image))
    except Exception:
        pass
    db.session.delete(p)
    db.session.commit()
    flash("Product deleted", "info")
    return redirect(url_for("admin_dashboard"))

# ---------- API for instant updates (AJAX) ----------
@app.route("/api/update_product/<int:pid>", methods=["POST"])
@require_admin
def api_update_product(pid):
    p = Product.query.get_or_404(pid)
    data = request.form
    if "name" in data:
        p.name = data.get("name", p.name)
    if "description" in data:
        p.description = data.get("description", p.description)
    if "price" in data:
        p.price = data.get("price", p.price)
    db.session.commit()
    return jsonify({"status": "ok", "product": {"id": p.id, "name": p.name, "description": p.description, "price": p.price, "image_url": p.image_url()}})

# ---------- Serve uploads ----------
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=False)

# ---------- Run (Render safe) ----------
if __name__ == "__main__":
    port_env = os.environ.get("PORT")
    try:
        port = int(port_env) if port_env and port_env.strip().isdigit() else 5000
    except Exception:
        port = 5000
    app.run(host="0.0.0.0", port=port, debug=False)
