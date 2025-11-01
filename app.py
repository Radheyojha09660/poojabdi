from flask import Flask, render_template, request, redirect, url_for, flash
import os

app = Flask(__name__)
app.secret_key = "secret-key"

# ✅ Sample static data (You can connect DB later)
products = [
    {"id": 1, "name": "उड़द बड़ी", "price": "₹200/kg", "image": "https://via.placeholder.com/150"},
    {"id": 2, "name": "पापड़", "price": "₹150/kg", "image": "https://via.placeholder.com/150"},
    {"id": 3, "name": "मूंग बड़ी", "price": "₹220/kg", "image": "https://via.placeholder.com/150"}
]

# ✅ Site Info dictionary (used in templates)
site = {
    "name": "पूजा बड़ी पापड़ उद्योग",
    "tagline": "स्वाद में परंपरा, गुणवत्ता में भरोसा",
    "logo": "https://via.placeholder.com/100x100.png?text=Logo",
    "address": "जयपुर, राजस्थान, भारत",
    "email": "info@poojapapad.com",
    "phone": "+91-9876543210"
}


# ✅ Home Page
@app.route("/")
def home():
    return render_template("index.html", products=products, site=site)


# ✅ About Page
@app.route("/about")
def about():
    return render_template("about.html", site=site)


# ✅ Products Page
@app.route("/products")
def product_page():
    return render_template("products.html", products=products, site=site)


# ✅ Contact Page
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        if not name or not email or not message:
            flash("कृपया सभी फ़ील्ड भरें!", "error")
        else:
            flash("आपका संदेश सफलतापूर्वक भेजा गया!", "success")
            print(f"Message from {name} ({email}): {message}")
        return redirect(url_for("contact"))

    return render_template("contact.html", site=site)


# ✅ Render compatible startup
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
