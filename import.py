import os, csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(os.getenv("DATABASE_URL"))

db = scoped_session(sessionmaker(bind=engine))

file = open("books.csv")

reader = csv.reader(file)

#since the year column is of type smallint, teh first line of the .csv file would cause an error
next(reader) #skip first line, where we have the columns names

for isbn, title, author, year in reader:
    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
        {"isbn": isbn,"title":title,"author":author,"year":int(year)})

db.commit()

print('success')