#################################
##### Name: Qifan Wu ############
##### Uniqname: qifanw ##########
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets
import sqlite3
import pgeocode
import sys
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import plot
from flask import Flask, render_template, url_for, Markup

cache_filename = 'theatres.json'
cache_dict = {}
res_cache_filename = 'restaurants.json'
res_cache_dict = {}
YELP_API_Key = secrets.YELP_API_Key
mapbox_access_token = secrets.mapbox_access_token
theatres_db_name = 'theatres.sqlite'

headers = {'Authorization': 'Bearer {}'.format(YELP_API_Key)}

class Theatre:
    '''
    a theatre

    Instance Attributes
    -------------------
    name: string
        the name of a theatre (e.g. 'Isle Royale'
    address: string
        the city and state of a theatre (e.g. 'Houghton, MI')
    zipcode: string
        the zip-code of a theatre (e.g. '49931', '82190-0168')
    screen: integer
        the number of screens in the theatre (e.g. 2)
    website: string
        the url of the theatre website (e.g. https://jazzhall.com/)
    phone: string
        the phone of a theatre (e.g. '(616) 319-7906', '307-344-7381')

    '''
    def __init__(self, name, address, zipcode, screen, website, phone):
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.screen = screen
        self.website = website
        self.phone = phone

    def info(self):
        # return f"{self.name} ({self.screen} screens): {self.address} {self.zipcode}"
        return f"{self.name} ({self.screen} screens): {self.address} zipcode {self.zipcode} {self.website}{self.phone}"

class Restaurant:
    '''
    a theatre

    Instance Attributes
    -------------------
    name: string
        the name of a restaurant (e.g. 'Isle Royale'
    rating: float
        the rating of a restaurant on yelp (e.g. 4.5)
    review_count: int
        the count of review (e.g. 300)

    '''
    def __init__(self, name, rating, review_count):
        self.name = name
        self.rating = rating
        self.review_count = review_count

    def info(self):
        return f"{self.name} (Rating: {self.rating} Review: {self.review_count})"

def open_cache(cache_filename):
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    cache_filename
    cache file's name  e.g.'theatres.json'
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(cache_filename, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict, cache_filename):
    ''' Saves the current state of the cache to disk
    
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save

    cache_filename
    cache file's name  e.g.'theatres.json'
    
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(cache_filename,"w")
    fw.write(dumped_json_cache)
    fw.close()

def construct_unique_key(baseurl, params):
    uniq_key = baseurl
    for k in params.keys():
        uniq_key = uniq_key + '_' + k + '_' + str(params[k])
    return uniq_key

def build_state_url_dict():
    '''Make a dictionary that maps state name to state page from 'http://cinematreasures.org/theaters/united-states/'

    Parameters
    --------
    None

    Returns
    ----------
    dict
        key is a state name and value is the url
        e.g. {'arizona':'http://cinematreasures.org/theaters/united-states/arizona?sort=screens&order=desc', ...}
    '''
    theatre_baseurl = 'http://cinematreasures.org/theaters/united-states/'
    if theatre_baseurl in cache_dict.keys():
        print("Using Cache")
        soup = BeautifulSoup(cache_dict[theatre_baseurl], 'html.parser')
    else:
        print("Fetching")
        response = requests.get(theatre_baseurl)
        soup = BeautifulSoup(response.text, 'html.parser')
        cache_dict[theatre_baseurl] = response.text
        save_cache(cache_dict, cache_filename)
        # http://cinematreasures.org/theaters/united-states/arizona?sort=screens&order=desc

    state_dict = {}
    course_listing_parent = soup.find('select', id='child_region_select')
    course_listing_options = course_listing_parent.find_all('option', recursive=False)[1:]
    for course_listing_option in course_listing_options:
        state_path = course_listing_option['value']
        state_name = course_listing_option.text.strip()
        each_state_url = 'http://cinematreasures.org' + state_path + '?sort=screens&order=desc'
        state_name = state_name.lower()
        state_dict[state_name] = each_state_url
    return state_dict

def get_theatre_instance(theatre_url):
    '''
    Make an instance from the theatre url

    Parameters
    ----------
    theatre_url: string
        The URL for a theatre
    
    Returns
    -------
    instance
        a theatre instance
    '''
    if theatre_url in cache_dict.keys():
        print("Using Cache")
        soup = BeautifulSoup(cache_dict[theatre_url], 'html.parser')
    else:
        print("Fetching")
        response = requests.get(theatre_url)
        cache_dict[theatre_url] = response.text
        save_cache(cache_dict, cache_filename)
        soup = BeautifulSoup(response.text, 'html.parser')
    # name = soup.find('div', id='breadcrumb').find('h1', recursive=False).text.strip()
    name = soup.find('div', id='breadcrumb').find('ul').find_all('li', recursive=False)[4].text.strip()
    address = soup.find('div', class_='street-address').text.strip() + ' ' + soup.find('span', class_='locality').text.strip()[:-1]
    try:
        zipcode = soup.find('span', class_='postal-code').text.strip()
    except:
        zipcode = 'NULL'
    screen = soup.find('div', id='facts').find_all('div', class_='fact')[1].text.strip()
    if 'screen' not in screen:
        screen = soup.find('div', id='facts').find_all('div', class_='fact')[2].text.strip()
    if screen[-1] == 's':
        try:
            screen = int(screen[:-8])
        except:
            pass
    else:
        screen = int(screen[:-7])

    try:
        website = soup.find('div', class_='vcard').find("p", recursive=False).find('a')['href']
    except:
        website = 'NULL'
    if website[0] == '/':
        website = 'http://cinematreasures.org' + website
    try:
        phone = soup.find('span', class_='tel').text.strip()
    except:
        phone = 'NULL'
    theatre_instance = Theatre(name, address, zipcode, screen, website, phone)
    return theatre_instance
    # soup.select('div > p')[1].get_text(strip=True)

def get_10_theatres_for_state(state_url):
    '''Make a dictionary that maps state name to state page from 'http://cinematreasures.org/theaters/united-states/?sort=screens&order=desc'

    Parameters
    --------
    state_url: string
        the url for the theatres page of a state

    Returns
    ----------
    list
        key is a state name and value is a list of 10 urls of the biggest theatres
        e.g. {'arizona':'http://cinematreasures.org/theaters/united-states/arizona?sort=screens&order=desc', ...}
    '''
    theatres_list = []
    response = requests.get(state_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    theatres = soup.find('table', class_='theaters').find_all('tr', recursive=False)
    for theatre in theatres[:10]:
        theatre_url = 'http://cinematreasures.org' + theatre.find('a')['href']
        theatre_instance = get_theatre_instance(theatre_url)
        theatres_list.append(theatre_instance)
    return theatres_list

def create_states_db():
    '''
    Create a database of states'

    Parameters
    --------
    None

    Returns
    ----------
    None
    '''
    conn = sqlite3.connect(theatres_db_name)
    cur = conn.cursor()
    drop_states = '''
    DROP TABLE IF EXISTS "states";
    '''

    create_states = '''
        CREATE TABLE IF NOT EXISTS "states" (
            "ID"  INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "State" TEXT NOT NULL,
            "Website" TEXT NOT NULL
    );
    '''
    insert_states = '''
        INSERT INTO "states"
        VALUES (NULL, ?, ?);
    '''
    cur.execute(drop_states)
    cur.execute(create_states)

    state_dict = build_state_url_dict()
    for state, state_url in state_dict.items():
        states_info = [state, state_url]
        cur.execute(insert_states, states_info)
    conn.commit()

def get_states_info():
    '''get all the information of states from database
    '''
    conn = sqlite3.connect(theatres_db_name)
    cur = conn.cursor()
    states_list = []
    query = '''
    SELECT ID, State, Website FROM states;
    '''
    cur.execute(query)
    for row in cur:
        state_id = row[0]
        state_name = row[1]
        state_url = row[2]
        state = (state_id, state_name, state_url)
        states_list.append(state)
    return states_list

def create_theatres_db():
    '''
    Create a database of theatres' infomation

    Parameters
    --------
    None

    Returns
    ----------
    None
    '''
    conn = sqlite3.connect(theatres_db_name)
    cur = conn.cursor()
    drop_theatres = '''
        DROP TABLE IF EXISTS theatres;
    '''
    create_theatres = '''
        CREATE TABLE IF NOT EXISTS theatres (
            "ID"  INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "State_ID" INT NOT NULL,
            "Name" TEXT NOT NULL,
            "Address" TEXT NOT NULL,
            "Zipcode" TEXT NOT NULL,
            "Screen" INTEGER NOT NULL,
            "Phone" TEXT NOT NULL,
            "Website" TEXT NOT NULL,
            FOREIGN KEY ("State_id") REFERENCES states("ID")
    );
    '''
    cur.execute(drop_theatres)
    cur.execute(create_theatres)
    states_list = get_states_info()

    ### Insert data
    for state in states_list:
        state_id = state[0]
        state_name = state[1]
        state_url = state[2]

        insert_theatres = '''
            INSERT INTO theatres
            VALUES (NULL, ?, ?, ?, ?, ?, ?, ?);
        '''

        print(f"Loading information of {state_name.capitalize()}...")
        theatres_list = get_10_theatres_for_state(state_url)
        for theatre in theatres_list:
            theatre_info = [state_id, theatre.name, theatre.address, theatre.zipcode, theatre.screen, theatre.phone, theatre.website]
            cur.execute(insert_theatres, theatre_info)
    conn.commit()
    print("Finish Creating Theatre Database")

##########################################
###### finish building the database ######

def get_theatre_info(state_name):
    '''get information of theatre from database
    Parameters
    ---------------
    state_name: string
        The state name

    Returns
    ---------------
    theatres_list: list
    list of 10 instances of biggest theatres in that state
    '''
    conn = sqlite3.connect(theatres_db_name)
    cur = conn.cursor()
    query = '''
    select s.State, t.Name, t.Address, t.Zipcode, t.Screen, t.Phone, t.Website FROM states s
    JOIN theatres t ON s.ID = t.State_ID
    where s.State = "{}";
    '''.format(state_name)
    theatres_list= []
    cur.execute(query)
    for row in cur:
        theatre = Theatre(row[1], row[2], row[3], row[4], row[6], row[5])
        theatres_list.append(theatre)
    return theatres_list

def get_coordinates(zipcode):
    '''
    Get the coordinates of theatre

    Parameters
    --------
    zipcode: string

    Returns
    ----------
    coordinates: tuple
    (latitude, longtitude)
    '''
    nomi = pgeocode.Nominatim('us')
    lat = nomi.query_postal_code(zipcode).latitude
    lon = nomi.query_postal_code(zipcode).longitude
    coordinates = (lat, lon)
    return coordinates

def get_nearby_res_json(coordinates):
    '''get the json file of nearby restaurants
    Parameters
    --------
    coordinates: tuple
    (latitude, longtitude)
    Returns
    --------
    json
    '''
    baseurl='https://api.yelp.com/v3/businesses/search'
    params = {'term':'restaurants','latitude': coordinates[0], 'longitude':coordinates[1],'sort_by':'rating', 'limit': 10}
    uniq_key = construct_unique_key(baseurl, params)

    if uniq_key in res_cache_dict.keys():
        print("Using Cache")
        restaurants_json = json.loads(res_cache_dict[uniq_key])
    else:
        print("Fetching")
        response = requests.get(baseurl, params=params, headers=headers)
        restaurants_json = json.loads(response.text)
        res_cache_dict[uniq_key] = response.text
        save_cache(res_cache_dict, res_cache_filename)
    return restaurants_json

def get_restaurant_instances_list(coordinates):
    '''get the 10 nearby restaurants instances list from theatre's coordinates
    Parameters
    --------
    coordinates: tuple
    (latitude, longtitude)
    Returns
    --------
    list
    '''
    restaurant_list = []
    json = get_nearby_res_json(coordinates)
    for restaurant in json["businesses"]:
        name = restaurant["name"]
        rating = restaurant["rating"]
        review_count = restaurant["review_count"]
        restaurant_instance = Restaurant(name, rating, review_count)
        restaurant_list.append(restaurant_instance)
    return restaurant_list

##########################
###### data presentation##

def draw_flask_barchart(x, y, title, color):
    '''draw a barchart
    Parameters
    --------
    x: list of x values
    y: list of y values 

    title: string
    barchart's title

    color: string
    bar's color

    Returns
    ---------
    fig_div: string
        the plot that is readable by html files
    '''
    fig = make_subplots(rows=1, cols=1, specs=[[{"type": 'bar'}]], subplot_titles=(title))
    fig.add_trace(go.Bar(x=x, y=y), row=1, col=1)
    fig.update_traces(marker_color=color)
    fig.update_layout(annotations=[dict(text=title, font_size=25, showarrow=False)])
    fig_div = plot(fig, output_type="div")
    return fig_div

def draw_res_barcharts(restaurant_dict):
    '''
    Parameters
    ------
    restaurants_list: list
    list of restaurants instances

    Returns
    -------
    list
    list of two figures
    '''
    title1 = 'Barchart of restaurants rating'
    title2 = 'Barchart of restaurants review count'
    name_list = []
    review_list = []
    rating_list = []
    for k, v in restaurant_dict.items():
        name_list.append(k)
        rating_list.append(v[0])
        review_list.append(v[1])
    figure1 = draw_flask_barchart(name_list, rating_list, title1, "rgb(252, 202, 109)")
    figure2 = draw_flask_barchart(name_list, review_list, title2, "rgb(102, 166, 218)")
    figures = [figure1, figure2]
    return figures

####### flask ########
######################

app = Flask(__name__)
@app.route('/')
def index():
    '''Home page of state names

    Returns
    --------
    A html template
    
    '''
    states_dict = {}
    query = '''
    SELECT ID, State FROM states;
    '''
    conn = sqlite3.connect(theatres_db_name)
    cur = conn.cursor()
    cur.execute(query)
    for row in cur:
        state_id = row[0]
        state_name = row[1]
        states_dict[state_id] = state_name.capitalize()
    return render_template('index.html', states_dict=states_dict)

@app.route('/theatres/<state_name>')
def find_theatres(state_name):
    '''
    Parameters
    -----------
    state_name: string
    state name in lowercase

    Returns
    --------
    a html template that contains a theatres table and a map
    '''
    state_name = state_name.lower()
    conn = sqlite3.connect(theatres_db_name)
    cur = conn.cursor()
    query = '''
    select t.Name, t.Address, t.Zipcode, t.Screen, t.Phone, t.Website FROM states s
    JOIN theatres t ON s.ID = t.State_ID
    where s.State = "{}";
    '''.format(state_name)
    theatres_dict= {}
    cur.execute(query)
    # state_name = state_name.capitalize()
    lat_list = []
    lon_list = []
    name_list = []
    for index, row in enumerate(cur):
        key = row[0].capitalize()
        theatres_dict[key] = [index+1, row[1], row[2], row[3], row[4], row[5]]
        lat, lon = get_coordinates(row[2])
        lat_list.append(lat)
        lon_list.append(lon)
        name_list.append(key)

    fig = go.Figure(go.Scattermapbox(
    lat=lat_list,
    lon=lon_list,
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=12
    ),
    text=name_list,
    ))

    fig.update_layout(
        autosize=True,
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat=lat_list[4],
                lon=lon_list[4]
            ),
            pitch=0,
            zoom=5
        ),
    )
    fig_div = plot(fig, output_type="div")
    # fig.write_html("atr.html", auto_open=True)
    # return render_template('theatres.html', theatres_dict=theatres_dict, name=state_name)
    return render_template('theatres.html', theatres_dict=theatres_dict, name=state_name, fig_div=Markup(fig_div))

@app.route('/nearby_restaurants/<theatre_name>')
def find_nearby_restaurants(theatre_name):
    '''
    Parameters
    -----------
    theatre_name: string
    
    Returns
    --------
    a html template that contains a restaurants table
    '''
    # theatre_name = theatre_name.replace('%20', ' ')
    # theatre_name = theatre_name.capitalize()

    conn = sqlite3.connect(theatres_db_name)
    cur = conn.cursor()
    query = '''
    select Zipcode FROM theatres
    where upper(Name) = "{}";
    '''.format(theatre_name.upper())
    cur.execute(query)
    restaurant_dict = {}
    for row in cur:
        zipcode = row[0]
        rlist = get_restaurant_instances_list(get_coordinates(zipcode))
        for r in rlist:
            restaurant_dict[r.name] = [r.rating, r.review_count]
    return render_template('restaurant.html', restaurant_dict=restaurant_dict, name=theatre_name)

@app.route('/restaurants_barcharts/<theatre_name>')
def draw_barcharts(theatre_name):
    '''
    Parameters
    -----------
    theatre_name: string

    Returns
    --------
    a html template that contains two barcharts of nearby restaurants rating and review count
    '''
    conn = sqlite3.connect(theatres_db_name)
    cur = conn.cursor()
    query = '''
    select Zipcode FROM theatres
    where upper(Name) = "{}";
    '''.format(theatre_name.upper())
    cur.execute(query)
    restaurant_dict = {}
    for row in cur:
        zipcode = row[0]
        rlist = get_restaurant_instances_list(get_coordinates(zipcode))
        for r in rlist:
            restaurant_dict[r.name] = [r.rating, r.review_count]
    figures = draw_res_barcharts(restaurant_dict)
    figure1 = figures[0]
    figure2 = figures[1]
    return render_template('barcharts.html', figure1=Markup(figure1), figure2=Markup(figure2))

if __name__ == "__main__":
    cache_dict = open_cache(cache_filename)
    res_cache_dict = open_cache(res_cache_filename)
    # create_states_db()
    # create_theatres_db()
    app.run(debug=True)