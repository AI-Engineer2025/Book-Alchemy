import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

from data_models import db, Author, Book


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/library.sqlite')}"

db.init_app(app)


@app.route('/')
def home():
    """Display the home page with books and search functionality."""
    # Suchparameter und Sortierparameter aus URL holen
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'title')

    # Basisquery erstellen
    query = db.session.query(Book, Author).join(Author)

    # Suche anwenden, wenn ein Suchbegriff vorhanden ist
    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Book.title.ilike(search_filter),
                Author.name.ilike(search_filter),
                Book.isbn.ilike(search_filter)
            )
        )

    # Sortierung anwenden
    if sort_by == 'author':
        query = query.order_by(Author.name, Book.title)
    else:  # Standard: nach Titel sortieren
        query = query.order_by(Book.title, Author.name)

    books_with_authors = query.all()

    return render_template('home.html',
                           books_with_authors=books_with_authors,
                           current_sort=sort_by,
                           search_query=search_query)


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    """Add a new author to the database."""
    if request.method == 'POST':
        # Daten aus dem Formular holen
        name = request.form.get('name')
        birthdate = request.form.get('birthdate')
        date_of_death = request.form.get('date_of_death') or None

        # Validierung
        if not name or not birthdate:
            flash('Name and birthdate are required!', 'error')
            return render_template('add_author.html')

        try:
            # Datumsstrings in Datumsobjekte umwandeln
            birth_date_obj = datetime.strptime(birthdate, '%Y-%m-%d').date()
            date_of_death_obj = None

            # Nur wenn ein Todesdatum eingegeben wurde, in Datumsobjekt umwandeln
            if date_of_death:
                date_of_death_obj = datetime.strptime(date_of_death, '%Y-%m-%d').date()

            # Neuen Autor erstellen
            new_author = Author(
                name=name,
                birth_date=birth_date_obj,
                date_of_death=date_of_death_obj
            )
            # In Datenbank speichern
            db.session.add(new_author)
            db.session.commit()

            flash('Author added successfully.', 'success')
            return redirect(url_for('add_author'))

        except Exception as error:  # Korrigiert: 'fehler' → 'error'
            db.session.rollback()
            flash(f'Error adding author: {str(error)}', 'error')
            return render_template('add_author.html')

    # GET Request - Formular anzeigen
    return render_template('add_author.html')


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    """Add a new book to the database."""
    if request.method == 'POST':
        # Daten aus dem Formular holen
        isbn = request.form.get('isbn')
        title = request.form.get('title')
        publication_year = request.form.get('publication_year')
        author_id = request.form.get('author_id')

        # Validierung
        if not isbn or not title or not publication_year or not author_id:
            flash('All fields are required!', 'error')
            authors = Author.query.all()
            return render_template('add_book.html', authors=authors)

        try:
            # Neues Buch erstellen
            new_book = Book(
                isbn=isbn,
                title=title,
                publication_year=int(publication_year),  # Korrigiert: Typumwandlung
                author_id=int(author_id)
            )

            # In Datenbank speichern
            db.session.add(new_book)
            db.session.commit()

            flash('Book added successfully.', 'success')
            return redirect(url_for('add_book'))

        except Exception as error:  # Korrigiert: 'fehler' → 'error'
            db.session.rollback()
            flash(f'Error adding book: {str(error)}', 'error')
            authors = Author.query.all()
            return render_template('add_book.html', authors=authors)

    # GET Request - Formular mit Autorenliste anzeigen
    authors = Author.query.all()
    return render_template('add_book.html', authors=authors)


@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    """Delete a book and potentially its author if no other books exist."""
    try:
        # Buch finden
        book = Book.query.get_or_404(book_id)
        author_id = book.author_id
        book_title = book.title

        # Buch löschen
        db.session.delete(book)
        db.session.commit()

        # Prüfen ob der Autor noch andere Bücher hat
        remaining_books = Book.query.filter_by(author_id=author_id).count()
        author_name = "Unknown"

        if remaining_books == 0:
            # Autor hat keine weiteren Bücher -> Autor löschen
            author = Author.query.get(author_id)
            if author:
                author_name = author.name
                db.session.delete(author)
                db.session.commit()
                flash(f'Book "{book_title}" and author "{author_name}" successfully deleted!', 'success')
            else:
                flash(f'Book "{book_title}" successfully deleted!', 'success')
        else:
            flash(f'Book "{book_title}" successfully deleted!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting book: {str(e)}', 'error')

    return redirect(url_for('home'))


def get_book_cover_url(isbn):
    """Return an Open Library cover URL."""
    return f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"


# Funktion global verfügbar machen
@app.context_processor
def utility_processor():
    """Make functions available in templates."""
    return dict(get_book_cover_url=get_book_cover_url)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)