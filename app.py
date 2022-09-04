#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import (
  Flask, 
  render_template, 
  request, 
  Response, 
  flash, 
  redirect, 
  url_for
)
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate

# importing models
from models import db, Venue, Artist, Show

from datetime import datetime
from sqlalchemy import desc

import collections
collections.Callable = collections.abc.Callable

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

# Initialization of SQLALchemy from models.py
db.init_app(app)

migrate = Migrate(app, db)


# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  # Query for venues and artists then arrange them in descending order of their id values, since the id increments,
  # meaning the highest value indicates the latest record/
  # The query returns 10 most latest records
  
  venues = Venue.query.order_by(desc(Venue.id)).limit(10).all()
  latestVenues = []
  for venue in venues:
        latestVenues.append({
          'name': venue.name, 
          'id': venue.id            
        })
  
  artists = Artist.query.order_by(desc(Artist.id)).limit(10).all()                
  latestArtists = []
  for artist in artists:
        latestArtists.append({
          'id': artist.id,
          'name': artist.name
        })
      
  return render_template('pages/home.html', artists = latestArtists, venues = latestVenues)



#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  venues = Venue.query.all()
  data = []
  
  locations = Venue.query.distinct(Venue.city, Venue.state).all()
  
  for location in locations:
        data.append({
          'city': location.city,
          'state': location.state,
          'venues': [{
          'id':venue.id,
          'name': venue.name,
          'num_upcoming_shows': len([show for show in venue.shows if show.start_time > datetime.now()])
          }
        for venue in venues if
        venue.city == location.city and venue.state == location.state
        ]
        })

  return render_template('pages/venues.html', areas=data ); 

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form['search_term']
  
  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  
  data =[]
  for venue in venues:
        #takes count of upcoming shows in the venue
        count_shows = 0
        for shows in venue.shows:
              if shows.start_time > datetime.now():
                    count_shows += 1
                    
        data.append({
          'id': venue.id,
          'name': venue.name,
          'num_upcoming_shows': count_shows
        })
   
  response = {
    'count':len(data),
    'data': data
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get_or_404(venue_id)
  
  upcoming_shows = []
  past_shows = []
 
  for this_show in venue.shows:
        show = {}
        show['artist_id'] = this_show.artist_id
        show['artist_name'] = this_show.artist.name
        show['artist_image_link'] = this_show.artist.image_link
        show['start_time'] = str(this_show.start_time)
        if this_show.start_time <= datetime.now():
              past_shows.append(show)
        else:
              upcoming_shows.append(show)
 
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  form = VenueForm(request.form)
  error = False
  
  try:
    # gets data from input fields using the wtform data collection syntax
    venue = Venue(
      name = form.name.data,
      city = form.city.data,
      state = form.state.data,
      address = form.address.data,
      phone = form.phone.data,
      image_link = form.image_link.data,
      facebook_link = form.facebook_link.data,
      website_link = form.website_link.data,
      seeking_talent = form.seeking_talent.data,
      seeking_description = form.seeking_description.data,
      genres = form.genres.data
    )
    db.session.add(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  
  # TODO: modify data to be the data object returned from db insertion
  if error:
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    return render_template('pages/home.html')
  # on successful db insert, flash success
  else:  
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  
    return render_template('pages/home.html')

#   Delete Venue
#------------------------------------------------------------------
@app.route('/venues/<venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  venue = Venue.query.get(venue_id)
  error = False
  try:
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()

  if error:
        flash('Could not delete '+venue.name+'!')
  else:
        flash(venue.name + ' successfully deleted!')
 
  return render_template('pages/home.html')

#     Delete Artist
#------------------------------------------------------------------
@app.route('/artists/<artist_id>/delete', methods=['POST'])
def delete_artist(artist_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
   # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  
  artist = Artist.query.get(artist_id)
  error = False
  try:
    db.session.delete(artist)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()

  if error:
        flash('Could not delete '+artist.name+'!')
  else:
        flash(artist.name + ' successfully deleted!')
        
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.order_by(Artist.name).all()
  
  data = []
  for a in artists:
        data.append({
          "id": a.id,
          "name": a.name
        })
   
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form['search_term']
  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  
  data =[]
  
  for artist in artists:
        
        # take count of total upcoming show the artist has
        count_shows = 0
        for shows in artist.shows:
              if shows.start_time > datetime.now():
                    count_shows += 1
                    
        data.append({
          'id': artist.id,
          'name': artist.name,
          'num_upcoming_shows': count_shows
        })
   
  response = {
    'count':len(data),
    'data': data
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.get_or_404(artist_id)
  
  upcoming_shows = []
  past_shows = []
  
  for this_show in artist.shows:
        show = {
          'venue_id': this_show.venue_id,
          'venue_name': this_show.venue.name,
          'venue_image_link': this_show.venue.image_link,
          'start_time': str(this_show.start_time)
        }
          
        if this_show.start_time <= datetime.now():
            past_shows.append(show)
        else:
            upcoming_shows.append(show)
        
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm(request.form)
  target_artist = Artist.query.get(artist_id)
  
  artist = {
    "id": target_artist.id,
    "name": target_artist.name,
    "genres": target_artist.genres,
    "city": target_artist.city,
    "state": target_artist.state,
    "phone": target_artist.phone,
    "website": target_artist.website_link,
    "facebook_link": target_artist.facebook_link,
    "seeking_venue": target_artist.seeking_venue,
    "seeking_description": target_artist.seeking_description,
    "image_link": target_artist.image_link
  }
  
  # TODO: populate form with fields from artist with ID <artist_id>
  form.name.data = artist['name']
  form.genres.data = artist['genres']
  form.city.data = artist['city']
  form.state.data = artist['state']
  form.phone.data = artist['phone']
  form.website_link.data = artist['website']
  form.facebook_link.data = artist['facebook_link']
  form.seeking_venue.data = artist['seeking_venue']
  form.seeking_description.data = artist['seeking_description']
  form.image_link.data = artist['image_link']
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  target = Artist.query.get(artist_id)
  error = False
  
  try:
    target.name = form.name.data 
    target.genres = form.genres.data
    target.city = form.city.data 
    target.state = form.state.data
    target.phone = form.phone.data
    target.website_link = form.website_link.data
    target.facebook_link = form.facebook_link.data
    target.seeking_venue = form.seeking_venue.data
    target.seeking_description = form.seeking_description.data 
    target.image_link = form.image_link.data
    
    db.session.add(target)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
    
  if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated!')
        return redirect(url_for('show_artist', artist_id=artist_id))
  else:  
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
    return redirect(url_for('show_artist', artist_id=artist_id))
    

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm(request.form)
  target_venue = Venue.query.get(venue_id)
  
  venue = {
    "id": target_venue.id,
    "name": target_venue.name,
    "genres": target_venue.genres,
    "address": target_venue.address,
    "city": target_venue.city,
    "state": target_venue.state,
    "phone": target_venue.phone,
    "website": target_venue.website_link,
    "facebook_link": target_venue.facebook_link,
    "seeking_talent": target_venue.seeking_talent,
    "seeking_description": target_venue.seeking_description,
    "image_link": target_venue.image_link
  }
  
  # TODO: populate form with values from venue with ID <venue_id>
  form.name.data = venue['name']
  form.genres.data = venue['genres']
  form.address.data = venue['address']
  form.city.data = venue['city']
  form.state.data = venue['state']
  form.phone.data = venue['phone']
  form.website_link.data = venue['website']
  form.facebook_link.data = venue['facebook_link']
  form.seeking_talent.data = venue['seeking_talent']
  form.seeking_description.data = venue['seeking_description']
  form.image_link.data = venue['image_link'] 
  
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
      
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)
  target_venue = Venue.query.get(venue_id)
  error = False
  
  try:
    target_venue.name = form.name.data
    target_venue.city = form.city.data
    target_venue.state = form.state.data
    target_venue.address = form.address.data
    target_venue.phone = form.phone.data
    target_venue.image_link = form.image_link.data
    target_venue.facebook_link = form.facebook_link.data
    target_venue.website_link = form.website_link.data
    target_venue.seeking_talent = form.seeking_talent.data
    target_venue.seeking_description = form.seeking_description.data
    target_venue.genres = form.genres.data
    
    db.session.add(target_venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  
  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))
  else:  
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  error = False
  form = ArtistForm(request.form)
    
  try:
    artist = Artist(
      name = form.name.data,
      city = form.city.data, 
      state = form.state.data,
      phone = form.phone.data,
      genres = form.genres.data,
      image_link = form.image_link.data,
      facebook_link = form.facebook_link.data,
      seeking_description = form.seeking_description.data,
      seeking_venue = form.seeking_venue.data,
      website_link = form.website_link.data
    )
    db.session.add(artist)
    db.session.commit()

  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
    
  # TODO: modify data to be the data object returned from db insertion
  data = Artist.query
  if error:
    flash('An error occurred. Artist ' + data.name +'  could not be listed.')
    return render_template('pages/home.html')
  # on successful db insert, flash success
  else:  
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  
  data = []
  shows = Show.query.all()
  
  for show in shows:
        detail ={}
        detail['venue_id'] = show.venue_id
        detail['venue_name'] = show.venue.name
        detail['artist_id'] = show.artist_id
        detail['artist_name'] = show.artist.name
        detail['artist_image_link'] = show.artist.image_link
        detail['start_time'] = str(show.start_time)
        
        data.append(detail)
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  form = ShowForm(request.form)
  error = False

  # TODO: insert form data as a new Show record in the db, instead
  try:
    show = Show(
      artist_id = form.artist_id.data,
      venue_id = form.venue_id.data,
      start_time = form.start_time.data
    )
    
    db.session.add(show)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
    
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  if error:
        flash('An error occurred. Show could not be listed.')
        return render_template('pages/home.html')

  # on successful db insert, flash success
  # flash('Show was successfully listed!')
  else:
        flash('Show was successfully listed!')
        return render_template('pages/home.html')

  

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
