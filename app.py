import os
from pathlib import Path
from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    jsonify, session, send_from_directory, abort
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import csv
from io import StringIO
import json

# ---- Config / Paths ----
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
DATA_DIR = BASE_DIR / "instance"
DB_PATH = DATA_DIR / "site.db"
DEFAULT_ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# ---- Flask App ----
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB

db = SQLAlchemy(app)

# ---- Models ----
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name_hi = db.Column(db.String(255))
    name_en = db.Column(db.String(255))
    price = db.Column(db.String(64))
    price_num = db.Column(db.Float, default=0.0)
    img = db.Column(db.String(1024))
    description_hi = db.Column(db.Text)
    description_en = db.Column(db.Text)

class Setting(db.Model):
    key = db.Column(db.String(128), primary_key=True)
    value = db.Column(db.Text)

# ---- Helpers ----
def get_setting(key, default=None):
    s = Setting.query.get(key)
    return s.value if s else default

def set_setting(key, value):
    s = Setting.query.get(key)
    if not s:
        s = Setting(key=key, value=value)
        db.session.add(s)
    else:
        s.value = value
    db.session.commit()

def save_upload(file_storage):
    if not file_storage:
        return None
    filename = secure_filename(file_storage.filename)
    if filename == "":
        return None
    dest = Path(app.config["UPLOAD_FOLDER"]) / filename
    base, ext = os.path.splitext(filename)
    i = 1
    while dest.exists():
        filename = f"{base}_{i}{ext}"
        dest = Path(app.config["UPLOAD_FOLDER"]) / filename
        i += 1
    file_storage.save(dest)
    return f"/static/uploads/{filename}"

def ensure_defaults():
    # create DB defaults if missing
    defaults = {
        "bizName": "पूजा बड़ी पापड़ उद्योग",
        "tagline_hi": "स्वाद और परंपरा — सीधे आपकी रसोई में",
        "tagline_en": "Fresh & Traditional — Straight to your kitchen",
        "address": "मोहता का चौक",
        "phone": "9660131376",
        "email": "ojha.radhey096@gmail.com",
        "about_hi": "हम पारंपरिक विधि से हाथ से पापड़ बनाते हैं।",
        "about_en": "We handcraft traditional papads using authentic recipes.",
        "footer": "© पूजा बड़ी पापड़ उद्योग",
        "social_json": json.dumps({"whatsapp":"","facebook":"","instagram":"","youtube":"","telegram":""}),
        "slider_json": json.dumps([])
    }
    for k, v in defaults.items():
        if Setting.query.get(k) is None:
            db.session.add(Setting(key=k, value=v))
    if Product.query.count() == 0:
        p1 = Product(name_hi="मूंग बड़ी", name_en="Moong Badi", price="₹60 / 250g", price_num=60,
                     img="https://bazaarmantri.com/images/products/40409_1.jpg",
                     description_hi="ताज़ा मूंग बड़ी", description_en="Fresh Moong Badi")
        p2 = Product(name_hi="मसाला पापड़", name_en="Masala Papad", price="₹55 / 200g", price_num=55,
                     img="https://5.imimg.com/data5/JR/NA/MY-67982735/moong-bari-namkeen-500x500.jpg",
                     description_hi="मसालेदार पापड़", description_en="Spicy Masala Papad")
        db.session.add_all([p1, p2])
    db.session.commit()

# ---- CLI command to init DB ----
@app.cli.command("init-db")
def init_db():
    db.create_all()
    ensure_defaults()
    print("Database created & seeded.")

# ---- Frontend Routes ----
@app.route("/")
def index():
    site = {
        "bizName": get_setting("bizName"),
        "tagline_hi": get_setting("tagline_hi"),
        "tagline_en": get_setting("tagline_en"),
        "address": get_setting("address"),
        "phone": get_setting("phone"),
        "email": get_setting("email"),
        "about_hi": get_setting("about_hi"),
        "about_en": get_setting("about_en"),
        "footer": get_setting("footer")
    }
    return render_template("index.html", site=site)

@app.route("/products.json")
def products_json():
    prods = Product.query.order_by(Product.id.desc()).all()
    out = []
    for p in prods:
        out.append({
            "id": p.id,
            "name_hi": p.name_hi,
            "name_en": p.name_en,
            "price": p.price,
            "price_num": p.price_num,
            "img": p.img,
            "description_hi": p.description_hi,
            "description_en": p.description_en
        })
    return jsonify(out)

# Cart endpoints (session)
@app.route("/api/cart", methods=["GET", "POST", "DELETE"])
def api_cart():
    cart = session.get("cart", {})
    if request.method == "GET":
        return jsonify(cart)
    if request.method == "POST":
        payload = request.json or {}
        pid = str(payload.get("id"))
        qty = int(payload.get("qty", 1))
        if not pid:
            return jsonify({"error": "no id"}), 400
        cart = session.get("cart", {})
        cart[pid] = cart.get(pid, 0) + qty
        session["cart"] = cart
        return jsonify(cart)
    if request.method == "DELETE":
        payload = request.json or {}
        pid = str(payload.get("id"))
        if not pid:
            return jsonify({"error": "no id"}), 400
        cart = session.get("cart", {})
        if pid in cart:
            del cart[pid]
            session["cart"] = cart
        return jsonify(cart)

# ---- Admin auth + pages ----
def is_logged_in():
    return session.get("admin_logged", False)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form.get("password", "")
        admin_pass = os.environ.get("ADMIN_PASS", DEFAULT_ADMIN_PASS)
        if password == admin_pass:
            session["admin_logged"] = True
            flash("Login successful", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Incorrect password", "danger")
            return redirect(url_for("admin"))
    if not is_logged_in():
        return render_template("admin.html", login_required=True)
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if not is_logged_in():
        return redirect(url_for("admin"))
    settings = {s.key: s.value for s in Setting.query.all()}
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template("admin_panel.html", settings=settings, products=products)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged", None)
    flash("Logged out", "info")
    return redirect(url_for("admin"))

# ---- Admin APIs ----
@app.route("/admin/api/product", methods=["POST", "PUT", "DELETE"])
def admin_product():
    if not is_logged_in():
        return jsonify({"error": "unauthorized"}), 401
    if request.method == "POST":
        data = request.form.to_dict()
        img = data.get("img")
        if "file" in request.files and request.files["file"].filename:
            img = save_upload(request.files["file"])
        p = Product(
            name_hi=data.get("name_hi"),
            name_en=data.get("name_en"),
            price=data.get("price"),
            price_num=float(data.get("price_num") or 0),
            img=img,
            description_hi=data.get("description_hi"),
            description_en=data.get("description_en")
        )
        db.session.add(p)
        db.session.commit()
        return jsonify({"ok": True, "id": p.id})
    if request.method == "PUT":
        data = request.form.to_dict()
        pid = data.get("id")
        p = Product.query.get(pid)
        if not p:
            return jsonify({"error": "not found"}), 404
        if "file" in request.files and request.files["file"].filename:
            p.img = save_upload(request.files["file"])
        else:
            p.img = data.get("img") or p.img
        p.name_hi = data.get("name_hi") or p.name_hi
        p.name_en = data.get("name_en") or p.name_en
        p.price = data.get("price") or p.price
        p.price_num = float(data.get("price_num") or p.price_num or 0)
        p.description_hi = data.get("description_hi") or p.description_hi
        p.description_en = data.get("description_en") or p.description_en
        db.session.commit()
        return jsonify({"ok": True})
    if request.method == "DELETE":
        data = request.get_json() or {}
        pid = data.get("id")
        p = Product.query.get(pid)
        if not p:
            return jsonify({"error": "not found"}), 404
        db.session.delete(p)
        db.session.commit()
        return jsonify({"ok": True})

@app.route("/admin/api/upload", methods=["POST"])
def admin_upload():
    if not is_logged_in():
        return jsonify({"error": "unauthorized"}), 401
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "no file"}), 400
    path = save_upload(f)
    return jsonify({"path": path})

@app.route("/admin/api/settings", methods=["POST"])
def admin_settings():
    if not is_logged_in():
        return jsonify({"error":"unauthorized"}), 401
    payload = request.form.to_dict()
    for k, v in payload.items():
        set_setting(k, v)
    return jsonify({"ok": True})

@app.route("/admin/export-products.csv")
def export_products_csv():
    if not is_logged_in():
        return redirect(url_for("admin"))
    products = Product.query.order_by(Product.id).all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["id","name_hi","name_en","price","price_num","img","description_hi","description_en"])
    for p in products:
        cw.writerow([p.id, p.name_hi, p.name_en, p.price, p.price_num, p.img, p.description_hi, p.description_en])
    output = si.getvalue()
    return app.response_class(output, mimetype='text/csv', headers={"Content-Disposition":"attachment;filename=products.csv"})

@app.route("/admin/import-products", methods=["POST"])
def import_products():
    if not is_logged_in():
        return jsonify({"error":"unauthorized"}),401
    f = request.files.get("file")
    if not f:
        return jsonify({"error":"no file"}),400
    stream = StringIO(f.stream.read().decode("utf-8"))
    reader = csv.DictReader(stream)
    added = 0
    for row in reader:
        if not (row.get("name_hi") or row.get("name_en")):
            continue
        p = Product(
            name_hi=row.get("name_hi"),
            name_en=row.get("name_en"),
            price=row.get("price") or "₹0",
            price_num=float(row.get("price_num") or 0),
            img=row.get("img"),
            description_hi=row.get("description_hi"),
            description_en=row.get("description_en")
        )
        db.session.add(p)
        added += 1
    db.session.commit()
    return jsonify({"ok": True, "added": added})

# ---- Static uploads route (handled by flask static, but keep helper) ----
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ---- Fallback: default image url ----
def default_image():
    return "/static/images/no-image.png"

# ---- Error handlers ----
@app.errorhandler(500)
def internal_error(e):
    # show nice page but also log
    app.logger.exception("Server error:")
    return render_template("500.html", error=e), 500

# ---- Run ----
if __name__ == "__main__":
    # ensure DB exists
    db.create_all()
    ensure_defaults()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
