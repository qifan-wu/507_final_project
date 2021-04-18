#################################
##### Name:Qifan Wu
##### Uniqname:qifanw
#################################


from bs4 import BeautifulSoup
import requests
import json
import secrets
import sqlite3
import pgeocode
import sys

cache_filename = 'theatres.json'
cache_dict = {}
res_cache_filename = 'restaurants.json'
res_cache_dict = {}
Mapquest_API_key = secrets.Mapquest_API_key
YELP_API_Key = secrets.YELP_API_Key
theatres_db_name = 'theatres.sqlite'
restaurant_db_name = 'theatres.sqlite'

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
        return f"{self.name} ({self.screen} screens): {self.address} {self.zipcode}{self.website}{self.phone}"

class Restaurant:
    '''
    a theatre

    Instance Attributes
    -------------------
    name: string
        the name of a theatre (e.g. 'Isle Royale'

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
    Create a database states and url'

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
    Create a database of theatres' infomation in the states'

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


###### finish building database

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
    params = {'term':'restaurants','latitude': coordinates[0], 'longitude':coordinates[1],'sort_by':'rating', 'limit': 8}
    # # params = {'term':'restaurants','latitude': 34.135343, 'longitude':-85.592379,'sort_by':'rating', 'limit': 3}
    # response = requests.get(baseurl, params=params, headers=headers)
    # return json.loads(response.text)
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
    restaurant_list = []
    json = get_nearby_res_json(coordinates)
    for restaurant in json["businesses"]:
        # yelp_id = restaurant["id"]
        name = restaurant["name"]
        rating = restaurant["rating"]
        review_count = restaurant["review_count"]
        restaurant_instance = Restaurant(name, rating, review_count)
        restaurant_list.append(restaurant_instance)
    return restaurant_list


if __name__ == "__main__":
        # print(get_theatre_instance('http://cinematreasures.org/theaters/55344').info())
    cache_dict = open_cache(cache_filename)
    res_cache_dict = open_cache(res_cache_filename)
    # theatre = get_theatre_instance('http://cinematreasures.org/theaters/32905')
    # print(theatre.info())
    # state_dict = build_state_url_dict()
    # print(state_dict)
    # theatres = get_10_theatres_for_state('http://cinematreasures.org/theaters/united-states/michigan?sort=screens&order=desc')
    # for theatre in theatres:
    #     print(theatre.info())
    
    # create_theatres_db()


    # coordinates = (34.135343, -85.592379)
    
    # print(get_nearby_res_json(coordinates)["businesses"])
    # for each in get_restaurant_instances_list(coordinates):
    #     print(each.info())
    # print(get_states_info()[2])
    print("blaaaaa")
    for instance in get_theatre_info('michigan')[:3]:
        coordinates = get_coordinates(instance.zipcode)
        for i in get_restaurant_instances_list(coordinates):
            print(i.info())