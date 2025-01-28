
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
import numpy as np
import datetime as dt

#################################################
# Database Setup 
#################################################
engine = create_engine("sqlite:///hawaii.sqlite")   #REFERENCE: https://docs.sqlalchemy.org/en/14/core/engines.html#sqlite

# reflect an existing database into a new model
Base = automap_base()
Base.prepare(engine, reflect=True)

# reflect the tables
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")                                         # REFERENCE: https://flask.palletsprojects.com/en/2.2.x/quickstart/
def welcome():
    return (
        f"Welcome to the Hawaii Climate API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
    )

# Precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    
    # Query for the last 12 months of precipitation data
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    year_ago = dt.datetime.strptime(last_date, '%Y-%m-%d') - dt.timedelta(days=365)
    prcp_data = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= year_ago).all()
    
    session.close()

    # Convert the query results to a dictionary
    prcp_dict = {date: prcp for date, prcp in prcp_data}
    
    return jsonify(prcp_dict)

# Stations route
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    
    # Query all stations
    stations_data = session.query(Station.station).all()
    
    session.close()

    # Convert list of tuples into a normal list
    stations_list = list(np.ravel(stations_data))
    
    return jsonify(stations_list)

# Temperature observations of the most active station route
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    
    # Get the most active station
    active_station = session.query(Measurement.station, func.count(Measurement.station))\
                            .group_by(Measurement.station)\
                            .order_by(func.count(Measurement.station).desc())\
                            .first()[0]
    
    # Get the last date and calculate the date one year ago
    last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
    year_ago = dt.datetime.strptime(last_date, '%Y-%m-%d') - dt.timedelta(days=365)
    
    # Query the temperature observations for the most active station for the last year
    tobs_data = session.query(Measurement.date, Measurement.tobs)\
                       .filter(Measurement.station == active_station)\
                       .filter(Measurement.date >= year_ago)\
                       .all()
    
    session.close()

    # Convert list of tuples into a normal list
    tobs_list = list(np.ravel(tobs_data))
    
    return jsonify(tobs_list)

# Start and start/end range route
@app.route("/api/v1.0/<start>")    # Reference:  chatgpt
@app.route("/api/v1.0/<start>/<end>")
def stats(start, end=None):
    session = Session(engine)

    # Select the min, avg, and max temperatures
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]

    if not end:
        # Query from the start date onwards
        results = session.query(*sel).filter(Measurement.date >= start).all()
    else:
        # Query from the start date to the end date
        results = session.query(*sel).filter(Measurement.date >= start).filter(Measurement.date <= end).all()
    
    session.close()

    # Convert list of tuples into a normal list
    temp_stats = list(np.ravel(results))
    
    return jsonify(temp_stats)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
