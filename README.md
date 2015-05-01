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

## Loading data into Hadoop via Spring-XD

One of the goals of this project was to demonstrate loading data into Hadoop and running queries via HAWQ and visualizations via other tools, so we have to get the data in there.  

To do this, we deployed a Pivotal HD VM and then installed Spring-XD onto that same VM.   

This could be done by simply POSTing the data from the tilt _ server.py script directly to Spring, but without knowing where the Spring-XD server would be, a script was created (collect.py found in the contrib folder) to pull data from the tilt _ server and write it to a local file, which can then be monitored by Spring-XD and loaded thusly.

The process for implementing this:

 1. Copy contrib/collect.py to a convenient location on your VM.
 2. Edit the collect.py script to reflect the appropriate URL for the tilt and location you wish it to write the output file.
 3. Run collect.py via nohup or supervisord or in another terminal window as you move on.

Once you have confirmed that collect.py is running and data is being written to the log file when you move your mobile
device, you can setup the Spring-XD stream.  You will first want to confirm that your Spring-XD install is talking to
your Hadoop cluster, which is outside of the scope of this document.

    xd> stream create --name tilt --definition "tail --lines=1 --name=/home/gpadmin/tilt _ collect/tilt _ output.log | hdfs --rollover=256" --deploy

At this point you should be able to look in the hdfs filesystem and see a /xd/tilt/tilt-#.txt file being created as your
move your device (assuming collect.py is still running).  

With your data loading into Hadoop if you have HAWQ available, you can now create the external table definition so you
are able to run queries.   Execute the following in a psql window:

    create external table tilt ( id bigint, device_id varchar(20), tiltlr DECIMAL, tiltfb DECIMAL, direction DECIMAL, deviceos VARCHAR(20)) LOCATION
    ('pxf://pivhdsne:50070/xd/tilt/*.txt?Fragmenter=HdfsDataFragmenter&Accessor=TextFileAccessor&Resolver=TextResolver')
    FORMAT 'TEXT' (DELIMITER ':' NULL '');

You should now be able to query the data via psql and connect the visualization/engines of your choice to show off the
data collected.

