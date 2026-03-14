import os

from datetime import datetime

from flask import Flask, request, jsonify, render_template, redirect, flash, get_flashed_messages, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecretdevkey123"  # change to a secure random key in production
CORS(app)

# Ensure the SQLite database is created inside the project folder.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "inventory.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DATABASE_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------------
# DATABASE MODELS
# ---------------------

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    sku = db.Column(db.String(50))
    category = db.Column(db.String(50))
    stock = db.Column(db.Integer)
    location = db.Column(db.String(100), default="Main Store")

class StockMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer)
    type = db.Column(db.String(50))
    quantity = db.Column(db.Integer)
    from_location = db.Column(db.String(100), nullable=True)
    to_location = db.Column(db.String(100), nullable=True)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    shortcode = db.Column(db.String(50), nullable=False)
    warehouse = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect("/login")
        return func(*args, **kwargs)
    return wrapper


@app.context_processor
def inject_user():
    return {"current_user": session.get("user")}


# ---------------------
# HOME ROUTE
# ---------------------

@app.route("/")
@login_required
def home():
    print("Home route called")
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next") or request.form.get("next") or "/"
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == "admin" and password == "password":
            session["user"] = username
            flash("Logged in successfully", "success")
            return redirect(next_url)
        flash("Invalid username or password", "danger")
        return render_template("login.html", next_url=next_url)
    if session.get("user"):
        return redirect(next_url or "/")
    return render_template("login.html", next_url=next_url)


@app.route("/home")
@login_required
def home_redirect():
    return redirect("/")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out", "info")
    return redirect("/login")

@app.route("/dashboard")
@login_required
def dashboard():
    return redirect("/")

@app.route("/receive_stock")
@login_required
def receive_stock_redirect():
    return redirect("/inventory")

@app.route("/deliver_stock")
@login_required
def deliver_stock_redirect():
    return redirect("/inventory")

@app.route("/settings")
@login_required
def settings():
    flash("Settings page is coming soon.", "info")
    return redirect("/")

@app.route("/profile")
@login_required
def profile():
    flash("Profile page is coming soon.", "info")
    return redirect("/")


# ---------------------
# ADD PRODUCT PAGE
# ---------------------

@app.route("/add-product", methods=["GET", "POST"])
@login_required
def add_product_page():
    if request.method == "POST":
        name = request.form["name"]
        sku = request.form["sku"]
        category = request.form["category"]
        stock = int(request.form["stock"])

        product = Product(
            name=name,
            sku=sku,
            category=category,
            stock=stock
        )

        db.session.add(product)
        db.session.commit()

        flash("Product added successfully!", "success")
        return redirect("/inventory")

    return render_template("add_product.html")


# ---------------------
# VIEW PRODUCTS PAGE
# ---------------------

@app.route("/inventory")
@login_required
def view_products():
    products = Product.query.all()
    messages = get_flashed_messages(with_categories=True)
    return render_template("products.html", products=products, messages=messages)


# ---------------------
# RECEIVE STOCK PAGE
# ---------------------

@app.route("/receive/<int:id>", methods=["GET", "POST"])
@login_required
def receive_stock_page(id):
    product = Product.query.get_or_404(id)
    if request.method == "POST":
        qty = int(request.form["qty"])
        product.stock += qty

        movement = StockMovement(
            product_id=id,
            type="receipt",
            quantity=qty,
            to_location=product.location,
            note=request.form.get("note")
        )

        db.session.add(movement)
        db.session.commit()

        flash(f"Received {qty} units of {product.name}", "success")
        return redirect("/inventory")

    return render_template("receive_stock.html", product=product)



# DELIVER STOCK


@app.route("/deliver/<int:id>", methods=["GET", "POST"])
@login_required
def deliver_stock_page(id):
    product = Product.query.get_or_404(id)
    if request.method == "POST":
        qty = int(request.form["qty"])
        if product.stock >= qty:
            product.stock -= qty

            movement = StockMovement(
                product_id=id,
                type="delivery",
                quantity=qty,
                from_location=product.location,
                note=request.form.get("note")
            )

            db.session.add(movement)
            db.session.commit()

            flash(f"Delivered {qty} units of {product.name}", "success")
            return redirect("/inventory")
        else:
            flash("Insufficient stock for delivery", "danger")
            return render_template("deliver_stock.html", product=product, error="Insufficient stock")

    return render_template("deliver_stock.html", product=product)


# ---------------------
# MANAGE STOCK PAGE (redirect to inventory)
# ---------------------

@app.route("/manage-stock")
@login_required
def manage_stock():
    return redirect("/inventory")


@app.route("/transfer/<int:id>", methods=["GET", "POST"])
@login_required
def transfer_stock(id):
    product = Product.query.get_or_404(id)
    if request.method == "POST":
        from_loc = request.form.get("from_location") or product.location
        to_loc = request.form.get("to_location")
        if not to_loc:
            flash("Destination location is required", "danger")
            return render_template("transfer_stock.html", product=product)

        # Stock total remains the same, only location changes
        old_loc = product.location
        product.location = to_loc

        movement = StockMovement(
            product_id=id,
            type="transfer",
            quantity=0,
            from_location=from_loc,
            to_location=to_loc,
            note=request.form.get("note")
        )

        db.session.add(movement)
        db.session.commit()

        flash(f"Transferred {product.name} from {from_loc} to {to_loc}", "success")
        return redirect("/inventory")

    return render_template("transfer_stock.html", product=product)


@app.route("/damage/<int:id>", methods=["GET", "POST"])
@login_required
def damage_stock(id):
    product = Product.query.get_or_404(id)
    if request.method == "POST":
        qty = int(request.form["qty"])
        if product.stock >= qty:
            product.stock -= qty

            movement = StockMovement(
                product_id=id,
                type="damage",
                quantity=qty,
                from_location=product.location,
                note=request.form.get("note")
            )

            db.session.add(movement)
            db.session.commit()

            flash(f"Recorded {qty} damaged units for {product.name}", "success")
            return redirect("/inventory")
        else:
            flash("Insufficient stock to mark as damaged", "danger")
            return render_template("damage_stock.html", product=product, error="Insufficient stock")

    return render_template("damage_stock.html", product=product)


@app.route("/movements")
@login_required
def view_movements():
    movements = StockMovement.query.order_by(StockMovement.id.desc()).all()
    return render_template("movements.html", movements=movements)

@app.route("/warehouse", methods=["GET","POST"])
def warehouse():
    if request.method == "POST":
        name = request.form["name"]
        shortcode = request.form["shortcode"]
        address = request.form["address"]

        print(name, shortcode, address)  # later store in DB

    return render_template("warehouse.html")


@app.route("/warehousesetting", methods=["GET", "POST"])
@login_required
def warehouse_settings():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        shortcode = request.form.get("shortcode", "").strip()
        warehouse = request.form.get("warehouse", "").strip()

        if not name or not shortcode or not warehouse:
            flash("Please fill in all location fields", "danger")
            return redirect("/warehousesetting")

        location = Location(name=name, shortcode=shortcode, warehouse=warehouse)
        db.session.add(location)
        db.session.commit()
        flash("Location saved successfully", "success")
        return redirect("/warehousesetting")

    locations = Location.query.order_by(Location.id.desc()).all()
    return render_template("warehousesetting.html", locations=locations)


# ---------------------
# RUN SERVER
# ---------------------

if __name__ == "__main__":

    with app.app_context():
        db.create_all()
        print("Database created")

    print("Starting server")
    app.run(debug=True)
