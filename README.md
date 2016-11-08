# tilt

tilt is a web application designed to show the functionality that can be provided by working with tools provided by
Pivotal Labs, including Cloud Foundry, Spring-XD, Hadoop, and HAWQ.   

## Requirements

Running in Cloud Foundry
* A running Cloud Foundry implementation 
** Pivotal CF, IBM Blumix or bosh-lite have been tested
* Redis service running withing Cloud Foundry

Running locally
* Python 2.7
* Redis Server

## Instructions

Running in Cloud Foundry

From the root of the repo

 1. Clone this repository
 2. Create a redis service called 'TILT _ REDIS'
 3. Review the manifest.yml file
 4. Push the app


    cf push 

Running locally

 1. Clone this repostory
 2. Install the necessary python modules 
   
    pip install -r requirements.txt

 3. Execute the application


    python tilt_server.py

## Accessing the tool

 1. Access the site at 'http://*hostname*' from a mobile device to begin sending data
 2. While data is entering the application from your mobile device, access 'http://*hostname*/show' to view the results


