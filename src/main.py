import threading
import json
from TFMS import TFMS

__author__ = "Zack"

class Main():
    def __init__(self) -> None:
        airports_path = "./data/airports.json"
        waypoint_database = "./data/waypoint_database.json"
        tier_1_database = "./data/neighbors.json"

        json_url = "https://data.vatsim.net/v3/vatsim-data.json"

        # TODO: Handle empty pickle file


        #7/3 BEGIN
        # ---Open Airports File----
        airfields_file = open(airports_path, 'rb')
        airports = json.load(airfields_file)
        airfields_file.close()
        
        # ---Open Waypoint Database---
        waypoint_file = open(waypoint_database, 'rb')
        waypoint_db = json.load(waypoint_file)
        waypoint_file.close()

        # ---Open Tier 1 Database---
        neighbors_file = open(tier_1_database, 'rb')
        neighbors_db = json.load(neighbors_file)
        neighbors_file.close()

        # TODO move this to it's own class
        print("Initializing setup...")

        tfms = TFMS(airports, waypoint_db, json_url, neighbors_db)


        # thread1: Timer that updates flightplan data when I new JSON is uploaded
        # user_input = threading.Thread(target=callsign_requester.request_callsign_from_user)
        # thread2: listens for user inputs for ground stop requests
        groundstops = threading.Thread(target=tfms.generate_ground_stop)



        # start other threads
        # JSON_timer.start()
        groundstops.start()

        

if __name__ == "__main__":
   main = Main()
