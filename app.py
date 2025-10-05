from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import os


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
app.config['MAIL_USERNAME'] = "customercarethriftstore@gmail.com"   
app.config['MAIL_PASSWORD'] =  "your_16_char_app_password"     
mail = Mail(app)



class User(db.Model):
    __tablename__= "users"

    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(512), nullable=False)

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
@app.route('/')
def index():
    return render_template("index.html")



if __name__ == "__main__":
    app.run(debug=True)