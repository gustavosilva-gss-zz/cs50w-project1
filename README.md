# Project 1: Books

### Access
https://project-one-cs50w.herokuapp.com

### Registration
To register, user will need to provide:
* First and last name
* Username
* Email
* Password
##### Password security
For encription and validation of passwords, this project uses [passlib.hash.sha256_crypt](https://passlib.readthedocs.io/en/stable/lib/passlib.hash.sha256_crypt.html)

### Login
To login, user must input the username (or email) and password.
If one of the fields is invalid, the user will be shown a message indicating one of the fields is invalid

### Logout
Users can logout from the navbar, this will clear the session variables and redirect to the home page

### Import
`import.py` will go through every line in `books.csv` (skipping the first line, because it only gives the name of the columns) and add the data as an row in the table `books`

### Search
User can search by title, author or ISBN. If wanted, it is also possible to filter by each of these fields. 
To make the search, three queries can be made, according to the filters. Then, everything is added to one list of results.
There is also some ordering on these queries:
* if the field is the same as the inputted argument, show this first
* if similar after the inputted argument, show second
* if similar before the inputted argument, show third

Notice it will always show first the results for title, then for author, then for ISBN

### Book Page
The book page will show:
* Title
* Author
* Year of release
* ISBN
* Average rating from GoodReads
* Average rating from the `reviews` table
* Each review from the `reviews` table
* Fields for the submission of a new review
* Cover image of the book from the [Open Library Covers Api](https://openlibrary.org/dev/docs/api/covers)

### Review Submission
Users that are logged in can submit a review for each book with a rating (from 1 to 5, including decimals) and a short text with their opinions.
If user already submitted a review, a message will appear, saying they aren't allowed to submit multiple reviews.

### Api Acceess
To use the API, users can go tot the route `/api/<isbn>`, if the book isn't in the DB, user will get a 404 error saying not book was found with this ISBN.
If the API succeeds user will get a Json with:
* Title
* Author
* Year
* ISBN
* Review Count
* Average Score

### Youtube video
[Here is a quick video showing the website](https://www.youtube.com/)
