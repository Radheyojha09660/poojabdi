from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json

app = Flask(__name__)

DATA_FILE = "data/products.json"

# Ensure data folder exists
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

# Load or create product list
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)


def load_products():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_products(products):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)


@app.route("/")
def home():
    products = load_products()
    return render_template("index.html", products=products)


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    password = "admin123"

    if request.method == "POST":
        entered_pass = request.form.get("password")
        if entered_pass != password:
            return render_template("admin.html", error="❌ गलत पासवर्ड!")
        return redirect(url_for("admin_panel"))

    return render_template("admin.html")


@app.route("/admin/panel")
def admin_panel():
    products = load_products()
    return render_template("admin_panel.html", products=products)


@app.route("/add_product", methods=["POST"])
def add_product():
    data = request.form
    new_product = {
        "id": len(load_products()) + 1,
        "name": data.get("name"),
        "price": data.get("price"),
        "image": data.get("image"),
        "desc": data.get("desc", "")
    }

    products = load_products()
    products.append(new_product)
    save_products(products)

    return redirect(url_for("admin_panel"))


@app.route("/delete_product/<int:pid>")
def delete_product(pid):
    products = load_products()
    products = [p for p in products if p["id"] != pid]
    save_products(products)
    return redirect(url_for("admin_panel"))


@app.route("/cart")
def cart():
    return render_template("cart.html")


# ------------------- MAIN ENTRY -------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render-compatible port
    app.run(host="0.0.0.0", port=port, debug=False)
