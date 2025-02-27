from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.numeric import FloatField
from wtforms.validators import DataRequired
import requests
import os
from dotenv import load_dotenv

'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

load_dotenv()

# CREATE DB
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///movies.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()


# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# second_movie = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )
# with app.app_context():
#     db.session.add(new_movie)
#     db.session.add(second_movie)
#     db.session.commit()

class EditForm(FlaskForm):
    rating = FloatField(label='Your Rating out of 10')
    review = StringField(label='Your Review')
    submit = SubmitField(label='Done')

class AddForm(FlaskForm):
    title = StringField(label='Movie Title', validators=[DataRequired()])
    submit = SubmitField(label='Add Movie')


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie))
    movie_list = result.scalars().all()
    return render_template("index.html", movies=movie_list)

@app.route('/edit', methods=['GET', 'POST'])
def edit_movie_rating():
    edit_form = EditForm()
    movie_id = request.args.get('id')
    movie = db.get_or_404(Movie, movie_id)
    if edit_form.validate_on_submit():
        movie.rating = float(edit_form.rating.data)
        movie.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=movie, form=edit_form)

@app.route('/delete', methods=['GET', 'POST'])
def delete_movie():
    movie_id = request.args.get('id')
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['GET', 'POST'])
def add_movie():
    add_form = AddForm()
    if add_form.validate_on_submit():
        movie_title = add_form.title.data
        response = requests.get(
            'https://api.themoviedb.org/3/search/movie',
            params={'api_key': os.getenv('API_KEY'), 'query': movie_title}
            )
        data = response.json()['results']
        return render_template('select.html', movies_data=data)
    return render_template('add.html', form=add_form)


@app.route('/find')
def find_movie():
    movie_api_id = request.args.get('id')
    if movie_api_id:
        movie_db_image_url = "https://image.tmdb.org/t/p/w500"
        movie_api_url=f'https://api.themoviedb.org/3/movie/{movie_api_id}'
        response = requests.get(movie_api_url, params={'api_key': os.getenv('API_KEY'), 'language':'en-US'})
        data = response.json()
        new_movie_details = Movie(
            title = data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{movie_db_image_url}{data['poster_path']}",
            description=data["overview"],
            rating=0,
            ranking=data['popularity'],
            review='Write some'
        )
        db.session.add(new_movie_details)
        db.session.commit()
        return redirect(url_for('edit_movie_rating', id=new_movie_details.id))





if __name__ == '__main__':
    app.run(debug=True)
