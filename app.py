from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
load_dotenv()
from flask import session


app = Flask(__name__)  
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:mandeepsingh@localhost:5432/thrift store _db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)
db = SQLAlchemy()
db.init_app(app)
migrate=Migrate(app, db)


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME") 
app.config['MAIL_PASSWORD'] =   os.getenv("MAIL_PASSWORD")
mail = Mail(app)

#Setup config the upload the file  
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

#Table for Singnup&Login
class User(db.Model):
    __tablename__= "users"

    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(512), nullable=False)
#Table for upload file in products 
class Products(db .Model):
    __tabblename__="products"

    id = db.Column(db.Integer, primary_key=True)
    Producttitle = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    condition = db.Column(db.String(50), nullable=False)
    Productdescription = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(200), nullable=False) 

    #Table for Wishlist 
class Wishlist(db.Model):
    __tablename__ = "wishlist"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)

    user = db.relationship("User", backref="wishlist_items", lazy=True)
    product = db.relationship("Products", backref="wishlisted_by", lazy=True)

#Route for add product in wishlist
@app.route("/add_to_wishlist/<int:product_id>")
def add_to_wishlist(product_id):
    if "user_id" not in session:
        flash("Please login first to add the item in Wishlist.","Warning")
        return redirect(url_for("login"))
    user_id = session["user_id"]
    existing = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()

    if existing:
        flash("Item already in your wishlist!", "info")
    else:
        new_item = Wishlist(user_id=user_id, product_id=product_id)
        db.session.add(new_item)
        db.session.commit()
        flash("Item added to wishlist!", "success")

    return redirect(url_for("Products"))

#Route for remove item from wishlist 
@app.route("/remove_from_wishlist/<int:item_id>")
def remove_from_wishlist(item_id):
    if "user_id" not in session:
     return redirect(url_for("login"))
    user_id = session["user_id"]
    item = Wishlist.query.filter_by(user_id=user_id, product_id=item_id).first()

    if item:
        db.session.delete(item)
        db.session.commit()
        flash("Item removed from wishlist.", "success")

    return redirect(url_for("wishlist"))

#wishlist 
@app.route("/wishlist")
def wishlist():
#    if "user_id" not in session:
#         flash("Please login first to view your Wishlist.","Warning")
#         return redirect(url_for("login"))
#    user_id = session["user_id"]
#    wishlist_items = Wishlist.query.filter_by(user_id=user_id).all()
#    products = [item.product for item in wishlist_items]
   
   return render_template("wishlist.html")
        
    

@app.route("/upload" , methods=["GET", "POST"])
def upload():
     if request.method == "POST":
        Producttitle = request.form["title"]
        price = request.form["price"]
        category = request.form["category"]
        condition = request.form["condition"]
        Productdescription = request.form["features"]
        file = request.files["image"]

        if file and allowed_file(file.filename):#uplaod file from device 
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)

                new_product = Products(
                    Producttitle=Producttitle,
                    price=price,
                    category=category,
                    condition=condition,
                    Productdescription=Productdescription,
                    image_filename=filename
                )
                db.session.add(new_product)
                db.session.commit()

                flash("✅ Product uploaded successfully!", "success")
                return redirect(url_for("products"))
     else:
                flash("⚠️ Please upload a valid image file (png, jpg, jpeg, gif).", "danger")
    
     return render_template("Upload.html")

            
      

@app.route('/user')
def add_user():
    temp_first_name = ": sunny"
    temp_last_name = "gandhi"
    temp_email = "sunnygandhi548@gmail.com"
    temp_password = "mash123"  

    # new_user = User(
    #     first_name=temp_first_name,
    #     last_name=temp_last_name,
    #     email=temp_email,
    #     password=temp_password,
    # )

    # try:
    #     db.session.add(new_user)
    #     db.session.commit()
    #     return "Added New user"
    # except Exception as e:
    #     db.session.rollback()
    #     return f"Error: {e}"
    
        
@app.route("/Signup", methods=["GET", "POST"])
def Signup():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!", "Retry")
            return redirect(url_for("Signup"))
        
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for("Signup"))


        hashed_password = generate_password_hash(password)

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password,
        )

        try:
            # Save to DB
            db.session.add(new_user)
            db.session.commit()

            # Send email
            msg = Message(
                subject="Account verification 🎉",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )
            msg.body = f"""
            Hi {first_name},

            Congratulations! Your account has been verified and Registered  successfully.
            You can now log in.

            Best regards,  
            Thrift Store App Team
            """
            mail.send(msg)

            flash("User created successfully! Check your email.", "success")
            return redirect(url_for("login")) 

        except Exception as e:
            db.session.rollback()
            return f"Error: {e}"
        
        
    return render_template("Signup.html")
   
        


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

       
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("No account found with that email. Please sign up first.", "danger")
            return redirect(url_for("login"))

   
        if check_password_hash(user.password, password):
            flash(f"Welcome back, {user.first_name}! Login successful.",  "success")
            return redirect(url_for("products")) 
        else:
            flash("Incorrect password. Please try again.", "danger")
            return redirect(url_for("login"))

    
    return render_template("login.html")




@app.route("/")
def index():
    return render_template("login.html")




@app.route("/products")
def products():
    all_products =Products.query.all()
    return render_template("Products.html" ,products=all_products)


@app. route("/message_seller/<int:item_id>")
def message_seller(item_id):
      return f"This is a placeholder page for messaging item {item_id}"



@app.route("/itemmessage/<int:item_id>")
def item_message(item_id):
    item = Products.query.get(item_id)
    if not item:
        # Handle missing product
        return f"❌ Item with ID {item_id} not found.", 404

    # Prepare the item data for template
    item_data = {
        "name": item.Producttitle,
        "price": item.price,
        "category": item.category,
        "condition": item.condition,
        "features": item.Productdescription,
        "image": f"uploads/{item.image_filename}"  # image path in static folder
    }


    # ✅ return the rendered template
    return render_template(
        "ItemMessage.html",
        item=item_data,
        item_id=item_id,
      
    )


@app.route("/chat_with_seller/<int:item_id>")
def chat_with_seller(item_id):
   item = Products.query.get(item_id)
   if not item:
        return f" Item with ID {item_id} not found", 404
    
    # For now, render the same ItemMessage page
        return render_template("ItemMessage.html", item=item, item_id=item_id, is_in_wishlist=False)



#Search Function
@app.route("/search")
def search():
    query = request.args.get('q', '').strip()

    if not query:
        # If empty search, show all products
        results = Products.query.all()
    else:
        # Search by title, description, or category
        results = Products.query.filter(
            (Products.Producttitle.ilike(f"%{query}%")) |
            (Products.Productdescription.ilike(f"%{query}%")) |
            (Products.category.ilike(f"%{query}%"))
        ).all()
        
    message = None if results else "No matching products found."# message if serched item not found 


 
    return render_template("Products.html", products=results, message= message)
     

@app.route("/logout")
def logout():
  
    return redirect(url_for("login"))



@app.route("/forgot-password")
def forgot_password():
    return render_template("ForgotPassword.html")
if __name__ == "__main__":
    app.run(debug=True)