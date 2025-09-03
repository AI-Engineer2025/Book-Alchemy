from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Author(db.Model):
    """Author model representing a book author."""

    __tablename__ = 'authors'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    date_of_death = db.Column(db.Date, nullable=True)

    # Relationship to books
    books = db.relationship('Book', backref='author', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"Author('{self.name}')"

    def __str__(self):
        return f"Author('{self.name}')"


class Book(db.Model):
    """Book model representing a book."""

    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    publication_year = db.Column(db.Integer, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=False)

    def __repr__(self):
        return f"Book('{self.title}', '{self.isbn}')"

    def __str__(self):
        return f"Book('{self.title}', '{self.isbn}')"