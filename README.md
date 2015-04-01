# tilt

## Tilt is a demo CloudFoundry application utilizing the python buildpack, Flask, and HTML5

## Requirements

* CloudFoundry
* Redis

## Instructions

From the root of the repo

    cf push tilt

Then bind a redis server to the instance via cloudfoundry.  You may need to restage after you bind the redis instance

Accessing the app via it's URL will present you with an HTML5

Accessing the app via URL/show will give you a page that provides the most recent data every 500ms
