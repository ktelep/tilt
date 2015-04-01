# tilt

# Tilt is a demo CloudFoundry application utilizing the python buildpack, Flask, and HTML5

# Requirements

CloudFoundry
Redis

# Instructions

Simply perform a "cf push tilt", then bind a redis server instance to the application.

Accessing the app via it's URL will present you with an HTML5
Accessing the app via URL/show will give you a page that provides the most recent data every 500ms
