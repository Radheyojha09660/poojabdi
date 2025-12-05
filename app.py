from flask import Flask, render_template

app = Flask(__name__)

# Sample product list
products = [
    {"id": 1, "name": "Aloo Bhujia", "price": 120, "img": "/static/images/p1.jpg"},
    {"id": 2, "name": "Kaju Barfi", "price": 450, "img": "/static/images/p2.jpg"},
    {"id": 3, "name": "Besan Ladoo", "price": 300, "img": "/static/images/p3.jpg"},
]

@app.route("/")
def home():
    return render_template("index.html", products=products)

@app.route("/product/<int:id>")
def product(id):
    item = next((p for p in products if p["id"] == id), None)
    return render_template("product.html", item=item)

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
