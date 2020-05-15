#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(500))
    website = db.Column(db.String())
    seeking_talent = db.Column(db.String(120))
    seeking_description = db.Column(db.String())
    shows = db.relationship('Show', backref="venue",
                            passive_deletes=True, lazy=True)

    def __repr__(self):
        return ("---------------VENUE---------------\n"
                f"Venue:               {self.name}\n"
                f"city:                {self.city}\n"
                f"state:               {self.state}\n"
                f"address:             {self.address}\n"
                f"phone:               {self.phone}\n"
                f"genres:              {self.genres}\n"
                f"image_link:          {self.image_link}\n"
                f"facebook_link:       {self.facebook_link}\n"
                f"website:             {self.website}\n"
                f"seeking_talent:      {self.seeking_talent}\n"
                f"seeking_description: {self.seeking_description}\n\n"
                )


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(500))
    website = db.Column(db.String())
    seeking_venue = db.Column(db.String(120))
    seeking_description = db.Column(db.String())
    shows = db.relationship('Show', backref="artist",
                            passive_deletes=True, lazy=True)

    def __repr__(self):
        return ("--------------ARTIST---------------\n"
                f"Name:                {self.name}\n"
                f"city:                {self.city}\n"
                f"state:               {self.state}\n"
                f"phone:               {self.phone}\n"
                f"genres:              {self.genres}\n"
                f"image_link:          {self.image_link}\n"
                f"facebook_link:       {self.facebook_link}\n"
                f"website:             {self.website}\n"
                f"seeking_venue:       {self.seeking_venue}\n"
                f"seeking_description: {self.seeking_description}\n\n"
                )


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id', ondelete='CASCADE'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'Venue.id', ondelete='CASCADE'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return ("---------------SHOW----------------\n"
                f"artist_id:  {self.artist_id}\n"
                f"venue_id:   {self.venue_id}\n"
                f"start_time: {self.start_time}\n\n"
                )


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = []
    exist = []
    venues = Venue.query.order_by(Venue.state).order_by(
        Venue.city).order_by(Venue.name).all()

    for venue in venues:
        details = {}
        details["id"] = venue.id
        details["name"] = venue.name
        new_venue = {}
        new_venue["city"] = venue.city
        new_venue["state"] = venue.state
        new_venue["venues"] = [details]

        if (venue.city, venue.state) not in exist:
            data.append(new_venue)
            exist.append((venue.city, venue.state))
        else:
            for d in data:
                if d["city"] == venue.city and d["state"] == venue.state:
                    d["venues"].append(details)
                    break

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    word = "%{}%".format(request.form.get('search_term'))
    venues = Venue.query.filter(Venue.name.ilike(word)).all()
    data = []

    for venue in venues:
        current = {}
        current["id"] = venue.id
        current["name"] = venue.name

        data.append(current)

    response = {
        "count": len(data),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    error = False

    try:
        venue = Venue.query.get(venue_id)
        shows = venue.shows
        future_shows = []
        past_shows = []

        for show in shows:
            future_show = {}
            past_show = {}

            if datetime.datetime.now() < show.start_time:
                # future
                future_show['artist_id'] = show.artist_id
                future_show['artist_name'] = Artist.query.get(
                    show.artist_id).name
                future_show['artist_image_link'] = Artist.query.get(
                    show.artist_id).image_link
                future_show['start_time'] = show.start_time.strftime(
                    "%Y-%m-%d %H:%M:%S.%f")
                future_shows.append(future_show)
            elif datetime.datetime.now() >= show.start_time:
                # past
                past_show['artist_id'] = show.venue_id
                past_show['artist_name'] = Artist.query.get(show.venue_id).name
                past_show['artist_image_link'] = Artist.query.get(
                    show.venue_id).image_link
                past_show['start_time'] = show.start_time.strftime(
                    "%Y-%m-%d %H:%M:%S.%f")
                past_shows.append(past_show)

        data = {
            "id": venue.id,
            "name": venue.name,
            "genres": venue.genres,
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "website": venue.website,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description,
            "image_link": venue.image_link,
            "past_shows": past_shows,
            "upcoming_shows": future_shows,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(future_shows),
        }

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        print("\n -------------BROWSING--------------\n", venue)
        db.session.close()

    if not error:
        return render_template('pages/show_venue.html', venue=data)
    else:
        flash('An error occurred. Venue page does not exist!')
        return redirect(url_for('index'))


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    data = request.form
    if 'seeking_talent' not in data:
        s_talent = ''
    elif data['seeking_talent'] == 'y':
        s_talent = True

    form = VenueForm()
    if not form.validate_on_submit():
        flash('An error occurred. Venue ' +
              data['name'] + ' could not be listed.')
        return render_template('forms/new_venue.html', form=form)

    try:
        venue = Venue(
            name=data['name'],
            city=data['city'],
            state=data['state'],
            address=data['address'],
            phone=data['phone'],
            image_link=data['image_link'],
            facebook_link=data['facebook_link'],
            genres=data.getlist('genres'),
            website=data['website'],
            seeking_talent=s_talent,
            seeking_description=data['seeking_description']
        )
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        print("\n ----------------NEW----------------\n", venue)
        db.session.close()

    if not error:
        flash('Venue ' + data['name'] + ' was successfully listed!')
        return render_template('pages/home.html')
    else:
        flash('An error occurred. Venue ' +
              data['name'] + ' could not be listed.')
        return redirect(url_for('create_venue_form'))


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if not error:
        flash('Venue was successfully deleted!')
        return jsonify({'success': True})
    else:
        flash('An error occurred. Venue could not be deleted.')
        return redirect(url_for('index'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = []
    artists = Artist.query.order_by(Artist.name).all()

    for artist in artists:
        add = {}
        add["id"] = artist.id
        add["name"] = artist.name

        data.append(add)

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    word = "%{}%".format(request.form.get('search_term'))
    artists = Artist.query.filter(Artist.name.ilike(word)).all()
    data = []

    for artist in artists:
        current = {}
        current["id"] = artist.id
        current["name"] = artist.name

        data.append(current)

    response = {
        "count": len(data),
        "data": data
    }

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    error = False

    try:
        artist = Artist.query.get(artist_id)
        shows = artist.shows
        future_shows = []
        past_shows = []

        for show in shows:
            future_show = {}
            past_show = {}

            if datetime.datetime.now() < show.start_time:
                # future
                future_show['venue_id'] = show.venue_id
                future_show['venue_name'] = Venue.query.get(show.venue_id).name
                future_show['venue_image_link'] = Venue.query.get(
                    show.venue_id).image_link
                future_show['start_time'] = show.start_time.strftime(
                    "%Y-%m-%d %H:%M:%S.%f")
                future_shows.append(future_show)
            elif datetime.datetime.now() >= show.start_time:
                # past
                past_show['venue_id'] = show.venue_id
                past_show['venue_name'] = Venue.query.get(show.venue_id).name
                past_show['venue_image_link'] = Venue.query.get(
                    show.venue_id).image_link
                past_show['start_time'] = show.start_time.strftime(
                    "%Y-%m-%d %H:%M:%S.%f")
                past_shows.append(past_show)

        data = {
            "id": artist.id,
            "name": artist.name,
            "genres": artist.genres,
            "city": artist.city,
            "state": artist.state,
            "phone": artist.phone,
            "website": artist.website,
            "facebook_link": artist.facebook_link,
            "seeking_venue": artist.seeking_venue,
            "seeking_description": artist.seeking_description,
            "image_link": artist.image_link,
            "past_shows": past_shows,
            "upcoming_shows": future_shows,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(future_shows),
        }

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        print("\n -------------BROWSING--------------\n", artist)
        db.session.close()

    if not error:
        return render_template('pages/show_artist.html', artist=data)
    else:
        flash('An error occurred. Artist page does not exist!')
        return redirect(url_for('index'))


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    data = Artist.query.get(artist_id)

    form.name.data = data.name
    form.genres.data = data.genres
    form.city.data = data.city
    form.state.data = data.state
    form.phone.data = data.phone
    form.website.data = data.website
    form.facebook_link.data = data.facebook_link
    form.seeking_description.data = data.seeking_description
    form.image_link.data = data.image_link

    if data.seeking_venue == 'true':
        s_venue = 'checked'
    elif data.seeking_venue == '':
        s_venue = ''
    form.seeking_venue.data = s_venue

    artist = {
        "id": data.id,
        "name": data.name
    }

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    new = request.form

    if 'seeking_venue' not in new:
        s_venue = ''
    elif new['seeking_venue'] == 'y':
        s_venue = True

    try:
        current = Artist.query.get(artist_id)
        current.name = new['name']
        current.city = new['city']
        current.state = new['state']
        current.phone = new['phone']
        current.genres = new.getlist('genres')
        current.image_link = new['image_link']
        current.facebook_link = new['facebook_link']
        current.website = new['website']
        current.seeking_venue = s_venue
        current.seeking_description = new['seeking_description']

        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        print("\n --------------UPDATED---------------\n", current)
        db.session.close()

    if not error:
        flash('Artist ' + new['name'] + ' was successfully updated!')
        return redirect(url_for('show_artist', artist_id=artist_id))
    else:
        flash('An error occurred. Artist ' +
              new['name'] + ' could not be updated.')
        return redirect(url_for('index'))


@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
    error = False
    try:
        Artist.query.filter_by(id=artist_id).delete()
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if not error:
        flash('Artist was successfully deleted!')
        return jsonify({'success': True})
    else:
        flash('An error occurred. Artist could not be deleted.')
        return redirect(url_for('index'))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    data = Venue.query.get(venue_id)

    form.name.data = data.name
    form.genres.data = data.genres
    form.address.data = data.address
    form.city.data = data.city
    form.state.data = data.state
    form.phone.data = data.phone
    form.website.data = data.website
    form.facebook_link.data = data.facebook_link
    form.seeking_description.data = data.seeking_description
    form.image_link.data = data.image_link

    if data.seeking_talent == 'true':
        s_talent = 'checked'
    elif data.seeking_talent == '':
        s_talent = ''
    form.seeking_talent.data = s_talent

    venue = {
        "id": data.id,
        "name": data.name
    }

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False
    new = request.form

    if 'seeking_talent' not in new:
        s_talent = ''
    elif new['seeking_talent'] == 'y':
        s_talent = True

    try:
        current = Venue.query.get(venue_id)
        current.name = new['name']
        current.city = new['city']
        current.state = new['state']
        current.address = new['address']
        current.phone = new['phone']
        current.genres = new.getlist('genres')
        current.image_link = new['image_link']
        current.facebook_link = new['facebook_link']
        current.website = new['website']
        current.seeking_talent = s_talent
        current.seeking_description = new['seeking_description']

        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        print("\n --------------UPDATED---------------\n", current)
        db.session.close()

    if not error:
        flash('Venue ' + new['name'] + ' was successfully updated!')
        return redirect(url_for('show_venue', venue_id=venue_id))
    else:
        flash('An error occurred. Venue ' +
              new['name'] + ' could not be updated.')
        return redirect(url_for('index'))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    data = request.form
    if 'seeking_venue' not in data:
        s_venue = ''
    elif data['seeking_venue'] == 'y':
        s_venue = True

    form = ArtistForm()
    if not form.validate_on_submit():
        flash('An error occurred. Artist ' +
              data['name'] + ' could not be listed.')
        return render_template('forms/new_artist.html', form=form)

    try:
        artist = Artist(
            name=data['name'],
            city=data['city'],
            state=data['state'],
            phone=data['phone'],
            genres=data.getlist('genres'),
            image_link=data['image_link'],
            facebook_link=data['facebook_link'],
            website=data['website'],
            seeking_venue=s_venue,
            seeking_description=data['seeking_description']
        )
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        print("\n ----------------NEW----------------\n", artist)
        db.session.close()

    if not error:
        flash('Artist ' + data['name'] + ' was successfully listed!')
        return render_template('pages/home.html')
    else:
        flash('An error occurred. Artist ' +
              data['name'] + ' could not be listed.')
        return redirect(url_for('create_artist_form'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = Show.query.order_by(Show.start_time).all()
    data = []
    for show in shows:
        future_show = {}
        if datetime.datetime.now() < show.start_time:
            future_show['venue_id'] = show.venue_id
            future_show['venue_name'] = Venue.query.get(show.venue_id).name
            future_show['artist_id'] = show.artist_id
            future_show['artist_name'] = Artist.query.get(show.artist_id).name
            future_show['artist_image_link'] = Artist.query.get(
                show.artist_id).image_link
            future_show['start_time'] = show.start_time.strftime(
                "%Y-%m-%d %H:%M:%S.%f")

            data.append(future_show)

    if len(data) == 0:
        flash('There are currently no shows listed! Please bare with us.')
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    data = request.form

    try:
        show = Show(
            artist_id=data['artist_id'],
            venue_id=data['venue_id'],
            start_time=data['start_time']
        )
        artist = Artist.query.get(show.artist_id)
        venue = Venue.query.get(show.venue_id)
        if artist and venue:
            db.session.add(show)
            db.session.commit()
        elif artist and not venue:
            flash('Venue not found! Check Venue ID on Venue\'s page.')
            error = True
        elif venue and not artist:
            flash('Artist not found! Check Artist ID on Artist\'s page.')
            error = True
        else:
            flash('Venue and Artist not found! Check Artist ID and Venue ID.')
            error = True

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Show could not be listed.')
    finally:
        print("\n ----------------NEW----------------\n", show)
        db.session.close()

    if not error:
        flash('Show was successfully listed!')
        return render_template('pages/home.html')
    else:
        return redirect(url_for('create_shows'))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
