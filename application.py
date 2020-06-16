import os, csv

from passlib.hash import sha256_crypt #secure passwords

from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

#have better forms
from flask_bootstrap import Bootstrap

from models.registration_form import RegistrationForm
from models.login_form import LoginForm

import requests

app = Flask(__name__, template_folder="ui")

#we need this to use flash(), for instantce
app.config.from_mapping(SECRET_KEY=b'\xd6\x04\xbdj\xfe\xed$c\x1e@\xad\x0f\x13,@G')

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

#this way the api returns the keys in the wanted order
app.config['JSON_SORT_KEYS'] = False

# This next line wasn't allowing me to get session["userId"], I know it was in the template, but I decided to remove it
# Session(app)

Bootstrap(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    #just redirecting here to be more clear to the user where he is
    return redirect(url_for("home"))

@app.route("/home")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm(request.form)

    if request.method == "GET":
        return render_template("register.html", form=form)

    #will get here if the method is POST
    
    if form.validate():
        #get the data given in the register form
        #notice WTForms gives me a list, so I get only the first value
        firstName = form.firstName.raw_data[0]
        lastName = form.lastName.raw_data[0]
        username = form.username.raw_data[0]
        email = form.email.raw_data[0]

        #make password secure
        password = sha256_crypt.encrypt(form.password.raw_data[0])

        userId = db.execute("INSERT INTO users (firstName, lastName, username, email, password) VALUES (:firstName, :lastName, :username, :email, :password) RETURNING id;", 
            {"firstName": firstName, "lastName": lastName, "username": username, "email": email, "password": password})

        session['userId'] = userId.first()[0]

        db.commit()

        return redirect(url_for("home"))

    return render_template('register.html', form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "GET":
        return render_template("login.html", form=form)

    #will get here if the method is POST
    
    if form.validate():
        #get the fields
        usernameOrEmail = form.usernameOrEmail.raw_data[0]
        password = form.password.raw_data[0]

        userResult = db.execute("SELECT * FROM users WHERE username = :usernameOrEmail OR email = :usernameOrEmail;", {"usernameOrEmail":usernameOrEmail}).fetchone()

        if userResult == None or not sha256_crypt.verify(password, userResult['password']):
            #for security, wont show which field is wrong
            form.password.errors.append('One of the fields is invalid')

            return render_template("login.html", form=form)
        
        session['userId'] = userResult['id']

        return redirect(url_for("home"))

    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    session.clear()

    return redirect(url_for("home"))

@app.route("/search", methods=["GET"])
def search():
    search = request.args.get("search")

    #user didnt fill the search field
    if not search:
        flash("You need to fill this field to search")

        return redirect(url_for('home'))

    #get filter used on search (default: all)
    searchFilter = request.args.get("searchFilter")
    
    #initialize lists
    resultTitle = []
    resultAuthor = []
    resultIsbn = []

    #notice here I made three queries instead of one
    #may seem unnecessary and even bad for performance
    #but I wanted the filters to work properly and (without knowing enough SQL)
    #this seemed to be the best way to do it

    #also, I wanted a good ordenation, I'm satisfied with the result this way
    #the lost of performance seems to be fine, since user will normally get only a few rows

    #get results for title
    if searchFilter == "all" or searchFilter == "title":
        resultTitle = db.execute("select title, author, isbn, year \
        from books \
            where  \
                title ilike '%' || :search || '%' \
            order by \
                (title  = :search) desc,\
                (title  ilike :search || '%') desc,\
                (title  ilike '%' || :search) desc",
        {"search": search}).fetchall()

    #get results for author
    if searchFilter == "all" or searchFilter == "author":
        resultAuthor = db.execute("select title, author, isbn, year \
            from books \
                where  \
                    author ilike '%' || :search || '%' \
                order by \
                    (author  = :search) desc,\
                    (author  ilike :search || '%') desc,\
                    (author  ilike '%' || :search) desc",
        {"search": search}).fetchall()

    #get results for isbn
    if searchFilter == "all" or searchFilter == "isbn":
        resultIsbn = db.execute("select title, author, isbn, year \
            from books \
                where  \
                    isbn ilike '%' || :search || '%' \
                order by \
                    (isbn  = :search) desc,\
                    (isbn  ilike :search || '%') desc,\
                    (isbn  ilike '%' || :search) desc",
        {"search": search}).fetchall()

    #add all results in a final list, well ordered and filtered
    result = resultTitle + resultAuthor + resultIsbn

    return render_template("result.html", search=search, result=result, searchFilter=searchFilter)

@app.route("/book/<isbn>", methods=["GET", "POST"])
def bookPage(isbn):

    #on user submit review
    if request.method == "POST":
        if not session.get('userId'):
            #not allowed to submit
            flash("You have to login to be able to submit reviews")

            return redirect(f"/book/{isbn}")

        #get the hidden input in form, for bookId
        bookId = request.form.get("bookId")

        #check if user already has a review for this book
        currentUserReviews = db.execute("SELECT * FROM reviews WHERE user_id = :userId AND book_id = :bookId", 
            {"userId": session['userId'], "bookId": bookId}).fetchone()

        if currentUserReviews:
            #not allowed to submit

            flash("You have already submitted a review for this book")

            return redirect(f"/book/{isbn}")

        #get fields
        review = request.form.get("review")
        rating = round(float(request.form.get("rating")), 2)

        #submit review
        db.execute("INSERT INTO reviews (user_id, book_id, review, rating) \
            VALUES (:userId, :bookId, :review, :rating)",
            {"userId": session['userId'], "bookId": bookId, "review": review, "rating": rating})

        db.commit()

        #reload as get method
        return redirect(f"/book/{isbn}")

    #get info from book and convert to dictionary (to be easier afterwards)
    bookInfo = dict(db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone())

    #get the reviews from the book, joining with the usernames
    reviews = db.execute("SELECT reviews.*, users.username FROM reviews \
        INNER JOIN users \
        ON users.id = reviews.user_id \
        WHERE book_id = :bookId",
        {"bookId": bookInfo["id"]}).fetchall()

    #initialize lists
    reviewsList = [] #complete reviews
    ratingsList = [] #only ratings (to calculate the average)

    #make a proper dictionary for the reviews and add some info on the lists
    for review in reviews:
        reviewDict = {
            "review": review["review"],
            "rating": review["rating"],
            "username": review["username"]
        }

        reviewsList.append(reviewDict)
        ratingsList.append(review["rating"])

    #calculate average using the list
    if ratingsList:
        averageRating = sum(ratingsList) / len(ratingsList)

    #add to bookInfo, to access on book_page.html
    bookInfo['reviews'] = reviewsList
    if ratingsList:
        bookInfo['averageRating'] = round(averageRating, 2)

    else:
        bookInfo['averageRating'] = 0.0

    #get goodreads info for the book
    res = requests.get("https://www.goodreads.com/book/review_counts.json", 
        params={"key": "o4oFG2BUty2204XAuTPHHw", "isbns": isbn})
    
    #add the average rating from goodreads to bookInfo
    bookInfo["goodreadsRating"] = res.json()['books'][0]['average_rating']

    return render_template("book_page.html", bookInfo=bookInfo)

@app.route("/api/<isbn>", methods=["GET"])
def api(isbn):

    #get the book info, except for reviews
    bookInfo = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

    if not bookInfo:
        return jsonify(Error = f"No book with the isbn {isbn}"), 404

    #get reviews
    reviews = db.execute("SELECT rating FROM reviews WHERE book_id = :bookId", 
        {"bookId": bookInfo["id"]}).fetchall()

    #if there are no reviews, rating is 0
    averageRating = 0

    if reviews:
        #initialize list
        ratingsList = [] #only ratings (to calculate the average)

        #add ratings to list
        for review in reviews:
            ratingsList.append(review["rating"])

        averageRating = sum(ratingsList) / len(ratingsList)

    return jsonify(
        title = bookInfo["title"],
        author = bookInfo["author"],
        year = bookInfo["year"],
        isbn = isbn,
        review_count = len(reviews),
        average_score = float(round(averageRating, 2))
    )