from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message as MailMessage
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import func
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from flask import get_flashed_messages
import os
from dotenv import load_dotenv
load_dotenv()



app = Flask(__name__)

# Database Configuration
# our database uri
if 'RDS_DB_NAME' in os.environ:
    # app.config['SQLALCHEMY_DATABASE_URI'] = \
    #     'postgresql://{username}:{password}@{host}:{port}/{database}'.format(
    #     username=os.environ['RDS_USERNAME'],
    #     password=os.environ['RDS_PASSWORD'],
    #     host=os.environ['RDS_HOSTNAME'],
    #     port=os.environ['RDS_PORT'],
    #     database=os.environ['RDS_DB_NAME'],
    # )
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"postgresql://{os.environ['RDS_USERNAME']}:{os.environ['RDS_PASSWORD']}"
        f"@{os.environ['RDS_HOSTNAME']}:{os.environ['RDS_PORT']}/{os.environ['RDS_DB_NAME']}"
    )
else:
    # our database uri
     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/thrift.db'
     app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:mandeepsingh@localhost:5432/thrift'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))


# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

# File Upload Configuration
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# Initialize extensions
db = SQLAlchemy()
db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)

# For password reset
s = URLSafeTimedSerializer(app.secret_key)

# Helper function for file uploads
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

mail = Mail(app)
 
print(f"MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
print(f"MAIL_PASSWORD exists: {app.config['MAIL_PASSWORD'] is not None}")
 
with app.app_context():
    try:
        msg = MailMessage(  # Changed from Message
            subject="Test Email from Thrift Store",
            sender=app.config['MAIL_USERNAME'],
            recipients=[os.getenv("MAIL_USERNAME")]
        )
        msg.body = "This is a test email. If you receive this, your email configuration is working!"
        mail.send(msg)
        print("✓ Test email sent successfully!")
    except Exception as e:
        print(f"✗ Error sending email: {str(e)}")
    

# ================ DATABASE MODELS ================

class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(512), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User {self.email}>"

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    condition = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(200), nullable=False) 
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="active") # active, sold, deleted
    
    seller = db.relationship("User", backref="products")
    
    def __repr__(self):
        return f"<Product {self.title}>"

class Wishlist(db.Model):
    __tablename__ = "wishlist"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="wishlist_items")
    product = db.relationship("Product", backref="wishlisted_by")
    
    __table_args__ = (db.UniqueConstraint('user_id', 'product_id'),)

class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = db.relationship("User", foreign_keys=[receiver_id], backref="received_messages")
    product = db.relationship("Product", backref="messages")

class Reminder(db.Model):
    __tablename__ = "reminders"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(255), nullable=True)
    meeting_time = db.Column(db.DateTime, nullable=True)
    reminder_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship("User", backref="reminders")
    product = db.relationship("Product", backref="reminders")

# ================ MIDDLEWARE ================

# Authentication middleware
def login_required(f):
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Admin middleware
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page", "warning")
            return redirect(url_for("login"))
        
        user = User.query.get(session["user_id"])
        if not user or not user.is_admin:
            flash("You don't have permission to access this page", "danger")
            return redirect(url_for("products"))
            
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ================ ROUTES ================

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Home & authentication routes
@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No account found with that email. Please sign up first.", "danger")
            return redirect(url_for("login"))

        if check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.first_name
            session["is_admin"] = user.is_admin
            flash(f"Welcome back, {user.first_name}!", "success")
            return redirect(url_for("products"))
        else:
            flash("Incorrect password. Please try again.", "danger")
            
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Validation
        if not all([first_name, last_name, email, password, confirm_password]):
            flash("All fields are required", "danger")
            return redirect(url_for("signup"))
            
        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for("signup"))
        
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for("signup"))

        # Create user
        hashed_password = generate_password_hash(password)
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=hashed_password
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Send welcome email
            try:
                msg = MailMessage(
                   
                  "Account verification 🎉",
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[email]
                )
                msg.body = f"""
                Hi {first_name},
                
                Welcome to  Thrift store Marketplace! Your account has been created successfully.
                
                Happy shopping and selling!
                
                Regards,
                The Thrift store Marketplace Team
                """
                mail.send(msg)
            except Exception as e:
                print(f"Failed to send welcome email: {e}")

            flash("Account created successfully! You can now log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for("signup"))
            
    return render_template("signup.html")

@app.route("/test-email")
def test_email():
    try:
        msg = MailMessage(
            "Test Email from Flask",
            sender=app.config['MAIL_USERNAME'],
            recipients=["msinghthrift@gmail.com"]
        )
        msg.body = "This is a test email. If you receive this, everything is working!"
        mail.send(msg)
        return "✅ Email sent successfully! Check your inbox (and spam folder)."
    except Exception as e:
        return f"❌ Failed to send email: {str(e)}"

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No account found with that email address", "danger")
            return redirect(url_for("forgot_password"))
            
        # Create token
        token = s.dumps(email, salt="password-reset")
        reset_link = url_for("reset_password", token=token, _external=True)

        # Fix for local development
        reset_link = reset_link.replace("0.0.0.0", "127.0.0.1")
        reset_link = reset_link.replace("localhost", "127.0.0.1")
        
        # Send email
        try:
            msg = MailMessage(
                "Password Reset Request",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )
            msg.body = f"""
            Hi {user.first_name},
            
            Click the link below to reset your password:
            {reset_link}
            
            This link will expire in 1 hour.
            
            If you didn't request a password reset, please ignore this email.
            
            Regards,
            The Thrift Store Marketplace Team
            """
            mail.send(msg)
            flash("Password reset link has been sent to your email", "success")
        except Exception as e:
            flash(f"Failed to send reset email: {str(e)}", "danger")
            
        return redirect(url_for("login"))
        
    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = s.loads(token, salt="password-reset", max_age=3600)
    except (SignatureExpired, BadSignature):
        flash("The password reset link is invalid or has expired", "danger")
        return redirect(url_for("forgot_password"))
        
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Invalid user", "danger")
        return redirect(url_for("forgot_password"))
        
    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for("reset_password", token=token))
            
        user.password = generate_password_hash(password)
        db.session.commit()
        
        flash("Your password has been updated successfully", "success")
        return redirect(url_for("login"))
        
    return render_template("reset_password.html", token=token)

# Product routes
@app.route("/products")
def products():
    all_products = Product.query.filter_by(status="active").all()
    return render_template("products.html", products=all_products)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    
    if product.status != "active":
        flash("This product is no longer available", "warning")
        return redirect(url_for("products"))
    
    # Check if in user's wishlist
    is_in_wishlist = False
    if "user_id" in session:
        is_in_wishlist = Wishlist.query.filter_by(
            user_id=session["user_id"], 
            product_id=product_id
        ).first() is not None
    
    return render_template(
        "product_detail.html", 
        product=product,
        is_in_wishlist=is_in_wishlist
    )

@app.route("/category/<category_name>")
def category(category_name):
    products = Product.query.filter(
        func.lower(Product.category) == category_name.lower(),
        Product.status == "active"
    ).all()
    
    if not products:
        flash(f"No products found in the '{category_name}' category", "info")
        
    return render_template(
        "products.html", 
        products=products, 
        category=category_name
    )

@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    
    if not query:
        return redirect(url_for("products"))
        
    products = Product.query.filter(
        db.or_(
            Product.title.ilike(f"%{query}%"),
            Product.description.ilike(f"%{query}%"),
            Product.category.ilike(f"%{query}%")
        ),
        Product.status == "active"
    ).all()
    
    if not products:
        flash(f"No products found matching '{query}'", "info")
        
    return render_template(
        "products.html", 
        products=products, 
        search_query=query
    )

# User product management
@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        title = request.form.get("title")
        price = request.form.get("price")
        category = request.form.get("category")
        condition = request.form.get("condition")
        description = request.form.get("description")
        
        # Validation
        if not all([title, price, category, condition, description]):
            flash("All fields are required", "danger")
            return redirect(url_for("upload"))
            
        # File upload
        if "image" not in request.files:
            flash("No image file provided", "danger")
            return redirect(url_for("upload"))
            
        file = request.files["image"]
        if file.filename == "":
            flash("No image selected", "danger")
            return redirect(url_for("upload"))
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            
            # Create product
            new_product = Product(
                title=title,
                price=float(price),
                category=category,
                condition=condition,
                description=description,
                image_filename=filename,
                seller_id=session["user_id"]
            )
            
            db.session.add(new_product)
            db.session.commit()
            
            flash("Product uploaded successfully!", "success")
            return redirect(url_for("your_listings"))
        else:
            flash("Invalid file type. Only PNG, JPG, JPEG, and GIF are allowed.", "danger")
            
    return render_template("upload.html")

@app.route("/your-listings")
@login_required
def your_listings():
    user_id = session["user_id"]
    products = Product.query.filter_by(seller_id=user_id).all()
    return render_template("your_listings.html", products=products)

@app.route("/edit-product/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if user owns this product
    if product.seller_id != session["user_id"]:
        flash("You don't have permission to edit this product", "danger")
        return redirect(url_for("products"))
        
    if request.method == "POST":
        product.title = request.form.get("title")
        product.price = float(request.form.get("price"))
        product.category = request.form.get("category")
        product.condition = request.form.get("condition")
        product.description = request.form.get("description")
        
        # Handle image update if provided
        if request.files["image"] and request.files["image"].filename != "":
            file = request.files["image"]
            
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                product.image_filename = filename
            else:
                flash("Invalid file type. Only PNG, JPG, JPEG, and GIF are allowed.", "danger")
                return redirect(url_for("edit_product", product_id=product_id))
                
        db.session.commit()
        flash("Product updated successfully!", "success")
        return redirect(url_for("your_listings"))
        
    return render_template("edit_product.html", product=product)

@app.route("/delete-product/<int:product_id>")
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if user owns this product
    if product.seller_id != session["user_id"]:
        flash("You don't have permission to delete this product", "danger")
        return redirect(url_for("products"))
        
    # Soft delete - change status to deleted
    product.status = "deleted"
    db.session.commit()
    
    flash("Product deleted successfully", "success")
    return redirect(url_for("your_listings"))

@app.route("/restore-product/<int:product_id>")
@login_required
def restore_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if user owns this product
    if product.seller_id != session["user_id"]:
        flash("You don't have permission to restore this product", "danger")
        return redirect(url_for("products"))
        
    product.status = "active"
    db.session.commit()
    
    flash("Product restored successfully", "success")
    return redirect(url_for("your_listings"))

# Wishlist routes
@app.route("/wishlist")
@login_required
def wishlist():
    user_id = session["user_id"]
    wishlist_items = Wishlist.query.filter_by(user_id=user_id).all()
    
    products = []
    for item in wishlist_items:
        # Only show active products
        if item.product.status == "active":
            products.append(item.product)
    
    return render_template("wishlist.html", products=products)

@app.route("/toggle-wishlist/<int:product_id>")
@login_required
def toggle_wishlist(product_id):
    user_id = session["user_id"]
    
    # Check if product exists and is active
    product = Product.query.get_or_404(product_id)
    if product.status != "active":
        if request.args.get("ajax") == "1":
            return jsonify({
                "success": False,
                "message": "This product is no longer available"
            })
        flash("This product is no longer available", "warning")
        return redirect(url_for("products"))
    
    existing = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
    
    if existing:
        # Remove from wishlist
        db.session.delete(existing)
        db.session.commit()
        message = "Product removed from wishlist"
        is_in_wishlist = False
    else:
        # Add to wishlist
        new_item = Wishlist(user_id=user_id, product_id=product_id)
        db.session.add(new_item)
        db.session.commit()
        message = "Product added to wishlist"
        is_in_wishlist = True
    
    # Handle AJAX requests
    if request.args.get("ajax") == "1":
        return jsonify({
            "success": True,
            "is_in_wishlist": is_in_wishlist,
            "message": message
        })
    
    flash(message, "success")
    return redirect(request.referrer or url_for("products"))

# Messaging routes
@app.route("/messages")
@login_required
def messages():
    user_id = session["user_id"]
    
    # Get unique conversations
    # This query finds all products where the user has sent or received messages
    products_with_conversations = db.session.query(Product).distinct().join(
        Message, Product.id == Message.product_id
    ).filter(
        db.or_(
            Message.sender_id == user_id,
            Message.receiver_id == user_id
        ),
        Product.status != "deleted"
    ).all()
    
    conversations = []
    for product in products_with_conversations:
        # Determine the other user in this conversation
        if product.seller_id == user_id:
            # Find users who have messaged this seller about this product
            message = Message.query.filter(
                Message.product_id == product.id,
                Message.receiver_id == user_id
            ).order_by(Message.timestamp.desc()).first()
            
            if message:
                other_user = User.query.get(message.sender_id)
                last_message = message.content
                timestamp = message.timestamp
                unread_count = Message.query.filter_by(
                    product_id=product.id,
                    receiver_id=user_id,
                    sender_id=message.sender_id,
                    read=False
                ).count()
                
                conversations.append({
                    'product': product,
                    'other_user': other_user,
                    'last_message': last_message,
                    'timestamp': timestamp,
                    'unread_count': unread_count
                })
        else:
            # User is a buyer
            other_user = User.query.get(product.seller_id)
            message = Message.query.filter(
                Message.product_id == product.id,
                db.or_(
                    Message.sender_id == user_id,
                    Message.receiver_id == user_id
                )
            ).order_by(Message.timestamp.desc()).first()
            
            if message:
                last_message = message.content
                timestamp = message.timestamp
                unread_count = Message.query.filter_by(
                    product_id=product.id,
                    receiver_id=user_id,
                    read=False
                ).count()
                
                conversations.append({
                    'product': product,
                    'other_user': other_user,
                    'last_message': last_message,
                    'timestamp': timestamp,
                    'unread_count': unread_count
                })
    
    # Sort conversations by most recent message
    conversations.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template("messages.html", conversations=conversations)

@app.route("/chat/<int:product_id>/<int:other_user_id>")
@login_required
def chat(product_id, other_user_id):
    user_id = session["user_id"]
    
    # Get product
    product = Product.query.get_or_404(product_id)
    
    # Get other user
    other_user = User.query.get_or_404(other_user_id)
    
    # Get messages between these users about this product
    messages = Message.query.filter(
        Message.product_id == product_id,
        db.or_(
            db.and_(
                Message.sender_id == user_id,
                Message.receiver_id == other_user_id
            ),
            db.and_(
                Message.sender_id == other_user_id,
                Message.receiver_id == user_id
            )
        )
    ).order_by(Message.timestamp).all()
    
    # Mark messages as read
    unread_messages = Message.query.filter_by(
        product_id=product_id,
        receiver_id=user_id,
        sender_id=other_user_id,
        read=False
    ).all()
    
    for msg in unread_messages:
        msg.read = True
    
    db.session.commit()
    
    return render_template(
        "chat.html", 
        product=product, 
        other_user=other_user,
        messages=messages
    )

@app.route("/send-message", methods=["POST"])
@login_required
def send_message():
    user_id = session["user_id"]
    product_id = request.form.get("product_id")
    receiver_id = request.form.get("receiver_id")
    content = request.form.get("content")
    
    if not content or not content.strip():
        flash("Message cannot be empty", "danger")
        return redirect(request.referrer)
    
    # Create message
    new_message = Message(
        sender_id=user_id,
        receiver_id=receiver_id,
        product_id=product_id,
        content=content.strip()
    )
    
    db.session.add(new_message)
    db.session.commit()
    
    return redirect(request.referrer)

@app.route("/contact-seller/<int:product_id>", methods=["GET", "POST"])
@login_required
def contact_seller(product_id):
    user_id = session["user_id"]
    product = Product.query.get_or_404(product_id)
    
    # Check if product is available
    if product.status != "active":
        flash("This product is no longer available", "warning")
        return redirect(url_for("products"))
    
    # Check if user is trying to message themselves
    if product.seller_id == user_id:
     flash("You cannot message yourself", "info")
    return redirect(url_for("product_detail", product_id=product_id))
    
    if request.method == "POST":
        content = request.form.get("message")
        
        if not content or not content.strip():
            flash("Message cannot be empty", "danger")
            return redirect(url_for("contact_seller", product_id=product_id))
        
        # Create message
        new_message = Message(
            sender_id=user_id,
            receiver_id=product.seller_id,
            product_id=product_id,
            content=content.strip()
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        flash("Message sent successfully!", "success")
        return redirect(url_for("chat", product_id=product_id, other_user_id=product.seller_id))
    
    return render_template("contact_seller.html", product=product)

# Dashboard routes
@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    user = User.query.get(user_id)
    
    # Count active listings
    active_listings = Product.query.filter_by(
        seller_id=user_id,
        status="active"
    ).count()
    
    # Count wishlist items
    wishlist_count = Wishlist.query.filter_by(user_id=user_id).count()
    
    # Count unread messages
    unread_messages = Message.query.filter_by(
        receiver_id=user_id,
        read=False
    ).count()
    
    # Get recent activity (messages, new wishlist items, etc.)
    recent_messages = Message.query.filter(
        db.or_(
            Message.sender_id == user_id,
            Message.receiver_id == user_id
        )
    ).order_by(Message.timestamp.desc()).limit(5).all()
    
    recent_wishlist = db.session.query(
        Wishlist, Product
    ).join(
        Product, Wishlist.product_id == Product.id
    ).filter(
        Wishlist.user_id == user_id
    ).order_by(
        Wishlist.created_at.desc()
    ).limit(5).all()
    
    return render_template(
        "dashboard.html",
        user=user,
        active_listings=active_listings,
        wishlist_count=wishlist_count,
        unread_messages=unread_messages,
        recent_messages=recent_messages,
        recent_wishlist=recent_wishlist
    )

# Admin routes
@app.route("/admin")
@admin_required
def admin_dashboard():
    # Count users
    user_count = User.query.count()
    
    # Count products
    product_count = Product.query.count()
    active_product_count = Product.query.filter_by(status="active").count()
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    
    return render_template(
        "admin/dashboard.html",
        user_count=user_count,
        product_count=product_count,
        active_product_count=active_product_count,
        recent_users=recent_users,
        recent_products=recent_products
    )

@app.route("/admin/users")
@admin_required
def admin_users():
    users = User.query.all()
    return render_template("admin/users.html", users=users)

@app.route("/admin/products")
@admin_required
def admin_products():
    products = Product.query.all()
    return render_template("admin/products.html", products=products)

@app.route("/admin/toggle-product-status/<int:product_id>")
@admin_required
def admin_toggle_product_status(product_id):
    product = Product.query.get_or_404(product_id)
    
    if product.status == "active":
        product.status = "deleted"
        message = "Product hidden successfully"
    else:
        product.status = "active"
        message = "Product activated successfully"
    
    db.session.commit()
    flash(message, "success")
    
    return redirect(url_for("admin_products"))

@app.route("/admin/toggle-admin/<int:user_id>")
@admin_required
def admin_toggle_admin(user_id):
    # Don't allow changing your own admin status
    if user_id == session["user_id"]:
        flash("You cannot change your own admin status", "danger")
        return redirect(url_for("admin_users"))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    
    flash(f"Admin status for {user.email} updated successfully", "success")
    return redirect(url_for("admin_users"))

@app.route("/admin/toggle-user-status/<int:user_id>")
@admin_required
def admin_toggle_user_status(user_id):
    # Don't allow deactivating yourself
    if user_id == session["user_id"]:
        flash("You cannot deactivate your own account", "danger")
        return redirect(url_for("admin_users"))
    
    user = User.query.get_or_404(user_id)
    
    if user.is_active:
        user.is_active = False
        message = f"User {user.email} has been deactivated"
    else:
        user.is_active = True
        message = f"User {user.email} has been activated"
    
    db.session.commit()
    flash(message, "success")
    
    return redirect(url_for("admin_users"))

@app.route("/admin/delete-user/<int:user_id>")
@admin_required
def admin_delete_user(user_id):
    # Don't allow deleting yourself
    if user_id == session["user_id"]:
        flash("You cannot delete your own account", "danger")
        return redirect(url_for("admin_users"))
    
    user = User.query.get_or_404(user_id)
    
    # Delete user's products
    Product.query.filter_by(seller_id=user_id).delete()
    
    # Delete user's wishlist items
    Wishlist.query.filter_by(user_id=user_id).delete()
    
    # Delete user's messages
    Message.query.filter(
        db.or_(
            Message.sender_id == user_id,
            Message.receiver_id == user_id
        )
    ).delete()
    
    # Delete user's reminders
    Reminder.query.filter_by(user_id=user_id).delete()
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    flash(f"User {user.email} and all associated data has been permanently deleted", "success")
    return redirect(url_for("admin_users"))

# Reminder/Booking routes
@app.route("/reminder", methods=["GET", "POST"])
@login_required
def reminder():
    if request.method == "POST":
        product_id = request.form.get("product_id")
        location = request.form.get("location")
        meeting_date = request.form.get("meeting_date")
        meeting_time = request.form.get("meeting_time")
        
        # Validation
        if not all([product_id, location, meeting_date, meeting_time]):
            flash("All fields are required", "danger")
            return redirect(request.referrer)
        
        # Parse date and time
        try:
            meeting_datetime = datetime.strptime(
                f"{meeting_date} {meeting_time}", 
                "%Y-%m-%d %H:%M"
            )
        except ValueError:
            flash("Invalid date or time format", "danger")
            return redirect(request.referrer)
        
        # Check if meeting time is in the future
        if meeting_datetime < datetime.now():
            flash("Meeting time must be in the future", "danger")
            return redirect(request.referrer)
        
        user_id = session["user_id"]
        user = User.query.get(user_id)
        
        # Create reminder
        reminder = Reminder(
            user_id=user_id,
            product_id=product_id,
            email=user.email,
            location=location,
            meeting_time=meeting_datetime
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        # Send confirmation email
        try:
            product = Product.query.get(product_id)
            
            msg = Message(
                "Meeting Confirmation",
                sender=app.config['MAIL_USERNAME'],
                recipients=[user.email]
            )
            msg.body = f"""
            Hi {user.first_name},
            
            Your meeting for {product.title} has been scheduled for {meeting_datetime.strftime('%A, %B %d at %I:%M %p')}.
            
            Location: {location}
            
                    
            Safety Tips:
            • Meet in a public, well-lit place
            • Bring a friend if possible
            • Inspect the item carefully before paying
            • Trust your instincts
                        
            Regards,
            The Thrift store Marketplace Team
            """
           
            mail.send(msg)
            print(f"✅ Confirmation email sent to {user.email}")
        except Exception as e:
            print(f"❌ Failed to send confirmation email: {e}")
            # Don't fail the reminder creation if email fails
        
        flash(
            f"Meeting scheduled for {meeting_datetime.strftime('%B %d at %I:%M %p')}! "
            "Confirmation email sent. You'll receive a reminder 1 hour before.", 
            "success"
        )
        return redirect(url_for("product_detail", product_id=product_id))
    
    # GET request - show form
    product_id = request.args.get("product_id")
    if not product_id:
        flash("Product ID is required", "danger")
        return redirect(url_for("products"))
    
    product = Product.query.get_or_404(product_id)
    
    # Pass tomorrow's date to the template for minimum date
    from datetime import timedelta
    tomorrow = datetime.now() + timedelta(days=1)
    
    return render_template("reminder.html", product=product, tomorrow=tomorrow)
@app.route("/customer-support")
def customer_support():
    return render_template("customer_support.html")

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("errors/500.html"), 500

@app.route("/get_flash_messages")
def get_flash_messages():
    messages = get_flashed_messages(with_categories=True)
    return jsonify(messages)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
        
        # Create admin user if none exists
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
            admin = User(
                first_name="Admin",
                last_name="User",
                email="admin@marketplace.com",
                password=generate_password_hash(admin_password),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        
    app.run(debug=True, host="127.0.0.1", port=5000)
