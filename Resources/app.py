from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
import datetime as dt


app = Flask(__name__)

# Database setup
engine = create_engine("sqlite:///C:\\Users\\board\\sqlalchemy-challenge\\Resources\\hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)
Measurement = Base.classes.measurement
Station = Base.classes.station

@app.route("/")
def home():
    """List all available API routes."""
    return """
    <h1>Welcome to the Climate Analysis API!</h1>
    <p>Available Routes:</p>
    <ul>
        <li><a href='/api/v1.0/precipitation'>/api/v1.0/precipitation</a> - List last year's precipitation data</li>
        <li><a href='/api/v1.0/stations'>/api/v1.0/stations</a> - List of weather observation stations</li>
        <li><a href='/api/v1.0/tobs'>/api/v1.0/tobs</a> - Temperature observations from the most active station for the last year</li>
        <li><a href='/api/v1.0/<start>'>/api/v1.0/<start></a> - Temperature summaries from a start date</li>
        <li><a href='/api/v1.0/<start>/<end>'>/api/v1.0/<start>/<end></a> - Temperature summaries from a start to an end date</li>
    </ul>
    """

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    # Calculate the date one year ago from the most recent date in the database
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = dt.datetime.strptime(most_recent_date, '%Y-%m-%d')
    one_year_ago = most_recent_date - dt.timedelta(days=365)
    
    # Query precipitation data from the last year
    results = session.query(Measurement.date, Measurement.prcp).\
              filter(Measurement.date >= one_year_ago.strftime('%Y-%m-%d')).\
              order_by(Measurement.date).all()
    session.close()

    # Convert query results to a dictionary using date as the key and prcp as the value
    precipitation_dict = {date: prcp for date, prcp in results if prcp is not None}
    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    results = session.query(Station.station).all()
    session.close()
    stations = [station[0] for station in results]
    return jsonify(stations)

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    # Get the most recent date from the database
    most_recent_date_str = session.query(func.max(Measurement.date)).scalar()
    # Convert the string date to a datetime object
    most_recent_date = dt.datetime.strptime(most_recent_date_str, '%Y-%m-%d')
    # Calculate the date one year ago from the most recent date
    one_year_ago = most_recent_date - dt.timedelta(days=365)

    # Retrieve temperature observations for the most active station from the last year
    most_active_station = session.query(Measurement.station).group_by(Measurement.station).order_by(func.count(Measurement.id).desc()).first()[0]
    results = session.query(Measurement.tobs).filter(Measurement.station == most_active_station).filter(Measurement.date >= one_year_ago).all()
    session.close()

    # List comprehension to extract temperatures
    temperatures = [temp[0] for temp in results]
    return jsonify(temperatures)



@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temp_range(start, end=None):
    session = Session(engine)
    
    # Validate start date format
    try:
        start = dt.datetime.strptime(start, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid start date format. Please use YYYY-MM-DD."}), 400
    
    # Validate end date format
    if end:
        try:
            end = dt.datetime.strptime(end, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Invalid end date format. Please use YYYY-MM-DD."}), 400
    else:
        end = start  # Default end date is start date if not provided

    # Query to get the temperature statistics
    results = session.query(
        func.min(Measurement.tobs),
        func.avg(Measurement.tobs),
        func.max(Measurement.tobs)
    ).filter(
        Measurement.date >= start,
        Measurement.date <= end
    ).all()
    session.close()

    # Format the results
    temp_stats = {
        'TMIN': results[0][0],
        'TAVG': round(results[0][1], 1),
        'TMAX': results[0][2]
    }
    
    return jsonify(temp_stats)

if __name__ == "__main__":
    app.run(debug=True)

if __name__ == "__main__":
    app.run(debug=True)