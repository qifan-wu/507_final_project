# WN 2021 SI 507 Final Project

# Introduction
This project built a web application that allows the user to find the largest theatres in a US state, and find the best restaurants around the theatre.

# Data Source
(1) Theatres in the US: html
http://cinematreasures.org/theaters/united-states
(2) Restaurants around the selected theatre: json
https://www.yelp.com/developers/documentation/v3/business_search


# API keys
(1) mapbox API
https://docs.mapbox.com/api/overview/
(2) yelp fusion API
"https://www.yelp.com/developers/documentation/v3/authentication"

# Packages
bs4
requests
Flask
sqlite3
plotly
pgeocode

# Interact with the Program
(1) Open http://127.0.0.1:5000/ on a browser
(2) Click on a state name to find the 10 largest theatres in that state
(3) Click on the theatre name to find the 10 best restaurants around the threatre, or click on the url to go to the theatre's website
(4) Click on "Click me to show the barcharts of ratings and review count" to show the barcharts
