import os
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# -------------------------
# Config
# -------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change_this_secret")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'poojabdi.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Upload settings
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

MAX_CONTENT = 10 * 1024 * 1024  # 10 MB max per file
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT

db = SQLAlchemy(app)

# -------------------------
# Models
# -------------------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(220), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.String(50))
    image_filename = db.Column(db.String(300))  # stored file name (in static/uploads)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def image_url(self):
        if self.image_filename:
            return url_for("static", filename=f"uploads/{self.image_filename}")
        return url_for("static", filename="uploads/placeholder.png")

# -------------------------
# Helpers
# -------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------------
# Init DB (safe)
# -------------------------
with app.app_context():
    db.create_all()

# -------------------------
# Public routes
# -------------------------
@app.route("/")
def index():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("index.html", products=products)

@app.route("/product/<int:pid>")
def product_view(pid):
    p = Product.query.get_or_404(pid)
    return render_template("product_view.html", product=p)

@app.route("/cart")
def cart_view():
    # simple session-based cart (list of product ids)
    cart = session.get("cart", [])
    products = Product.query.filter(Product.id.in_(cart)).all() if cart else []
    total = sum(float(p.price or 0) for p in products)
    return render_template("cart.html", products=products, total=total)

# add to cart (GET link)
@app.route("/add-to-cart/<int:pid>")
def add_to_cart(pid):
    cart = session.get("cart", [])
    if pid not in cart:
        cart.append(pid)
    session["cart"] = cart
    flash("Product added to cart.", "success")
    return redirect(url_for("index"))

@app.route("/remove-from-cart/<int:pid>")
def remove_from_cart(pid):
    cart = session.get("cart", [])
    cart = [i for i in cart if i != pid]
    session["cart"] = cart
    flash("Removed from cart.", "info")
    return redirect(url_for("cart_view"))

# -------------------------
# Admin auth & dashboard
# -------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw == os.environ.get("ADMIN_PASSWORD", "admin123"):
            session["is_admin"] = True
            flash("Welcome, admin!", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid password.", "danger")
        return redirect(url_for("admin_login"))
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Logged out.", "info")
    return redirect(url_for("index"))

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin login required.", "warning")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/admin")
@admin_required
def admin_dashboard():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("admin_dashboard.html", products=products)

# Add product page (GET) and action (POST)
@app.route("/admin/add", methods=["GET", "POST"])
@admin_required
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
                # avoid collisions: prefix with timestamp
                import time
                filename = f"{int(time.time())}_{filename}"
                image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            else:
                flash("File type not allowed.", "danger")
                return redirect(url_for("admin_add"))

        p = Product(name=name, description=description, price=price, image_filename=filename)
        db.session.add(p)
        db.session.commit()
        flash("Product added.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("add_product.html")

# Edit product
@app.route("/admin/edit/<int:pid>", methods=["GET", "POST"])
@admin_required
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
                import time
                filename = f"{int(time.time())}_{filename}"
                image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                # optionally delete old file (best-effort)
                if p.image_filename:
                    try:
                        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], p.image_filename))
                    except Exception:
                        pass
                p.image_filename = filename
            else:
                flash("File type not allowed.", "danger")
                return redirect(url_for("admin_edit", pid=pid))
        db.session.commit()
        flash("Product updated.", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("edit_product.html", product=p)

# Delete product
@app.route("/admin/delete/<int:pid>", methods=["POST"])
@admin_required
def admin_delete(pid):
    p = Product.query.get_or_404(pid)
    if p.image_filename:
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], p.image_filename))
        except Exception:
            pass
    db.session.delete(p)
    db.session.commit()
    flash("Product deleted.", "info")
    return redirect(url_for("admin_dashboard"))

# Serve uploaded files (static already serves /static; this route is optional)
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# -------------------------
# Run (Render safe)
# -------------------------
if __name__ == "__main__":
    port_env = os.environ.get("PORT")
    try:
        port = int(port_env) if port_env and port_env.strip().isdigit() else 5000
    except Exception:
        port = 5000
    app.run(host="0.0.0.0", port=port)
