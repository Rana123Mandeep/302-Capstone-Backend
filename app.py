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
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import jsonify, request
from sqlalchemy import func


app = Flask(__name__)  
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:mandeepsingh@localhost:5432/thrift store _db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)
s = URLSafeTimedSerializer(app.secret_key)#for forgot password
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
    __tablename__="products"

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
@app.route("/toggle_wishlist/<int:product_id>")
def toggle_wishlist(product_id):
     user_id = session.get("user_id")
     if "user_id" not in session:
         flash("Please login first to view your Wishlist.","Warning")
         return redirect(url_for("login"))
     existing = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()

     if existing:
            db.session.delete(existing)
            db.session.commit()
            flash("Item removed from wishlist.", "info")
     else:
            new_item = Wishlist(user_id=user_id, product_id=product_id)
            db.session.add(new_item)
            db.session.commit()
            flash("Item added to wishlist!", "success")

            # Return to the same page you came from
            return redirect(request.referrer or url_for("wishlist"))

#wishlist 
@app.route("/wishlist")
def Wishlist():
    user_id = session["user_id"]
    if "user_id" not in session:
        flash("Please login first to view your Wishlist.","Warning")
        return redirect(url_for("login"))

    wishlist_items = Wishlist.query.filter_by(user_id=user_id).all()
    products = [item.product for item in wishlist_items]
   
    return render_template("wishlist.html")
    user_id = session["user_id"]
    wishlist_items = Wishlist.query.filter_by(user_id=user_id).all()
    products = [item.product for item in wishlist_items]

    return render_template("wishlist.html", products=products)
        
    

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
    #  else:
    #             flash("⚠️ Please upload a valid image file (png, jpg, jpeg, gif).", "danger")
    
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
    return render_template("Products.html" ,products=all_products )





@app.route("/category/")
def all_categories():
    products = Products.query.all()
    message = None if products else "No products found."
    return render_template("Products.html", products=products, message=message)

@app.route("/category/<category_name>")
def category(category_name):
    products = Products.query.filter(func.lower(Products.category) == category_name.lower()).all()
    message = None if products else f"No products found in '{category_name.title()}' category."
    return render_template("Products.html", products=products, message=message)

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



@app.route("/forgot-password",methods=["GET","POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
   

       
        user = User.query.filter_by(email=email).first()

        if not user:
            flash ("No account found with that e-mail", "danger")
            return redirect(url_for("forgot_password"))
        
         # Create token
        token = s.dumps(email, salt="password-reset")
        print("Generated token:", token)

        # Build a proper local link
        # reset_link = url_for("reset_password", token=token, _external=True)
        # reset_link = reset_link.replace("0.0.0.0", "127.0.0.1")
        # print("Reset link for testing:", reset_link)
        reset_link = url_for("reset_password", token=token, _external=True)

# local development host
        reset_link = reset_link.replace("0.0.0.0", "127.0.0.1")  
        reset_link = reset_link.replace("localhost", "127.0.0.1")

        print("Reset link for testing:", reset_link)



        # Send email
        msg = Message(
            subject="🔑Password Reset Request",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f"""
        Hi {user.first_name},

      
        Click the link below to reset your password:
        {reset_link}

        This link will expire in 1 hour.
         
         Best regards,  
            Thrift Store App Team
        """

    

        mail.send(msg)

        flash("✅ A password reset link has been sent to your email.", "success")
        return redirect(url_for("login")) 



    return render_template("ForgotPassword.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = s.loads(token, salt="password-reset", max_age=3600)
            
    except (SignatureExpired, BadSignature):
        flash("The reset link is invalid or has expired.", "danger")
        return redirect(url_for("forgot_password"))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Invalid email!", "danger")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("reset_password", token=token))

        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash("Password updated successfully!", "success")
        return redirect(url_for('login'))

    return render_template("ResetPassword.html",token=token)


@app.route("/reset-password/", methods=["GET", "POST"])
def reset_password_missing_token():
    flash("Invalid or missing password reset token.", "danger")
    return redirect(url_for("forgot_password"))


if __name__ == "__main__":
    #  app.run(debug=True)

 app.run(debug=True, host="127.0.0.1", port=5000)