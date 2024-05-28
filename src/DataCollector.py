import requests
import json

class DataCollector:
    def __init__(self, json_url:str, airports:dict) -> None:
        self.callsign_list = {}
        self.json_url = json_url
        self.airports = airports

    def check_for_updates(self):
        self.update_json(self.json_url)
        self.scan_pilots()

    def get_json(self):
        return self.json_file
    
    def get_callsign_list(self):
        return self.callsign_list
    
    def add_callsign_to_dep_list(self, pilot_callsign:str, new_pilot_data_associated_with_callsign:dict):
        new_pilot_route:str = new_pilot_data_associated_with_callsign['flight_plan']['route']
        if '+' in new_pilot_route:
            new_pilot_route = new_pilot_route.replace('+', '')
        
        if pilot_callsign in self.callsign_list:
            current_pilot_route:str = self.callsign_list[pilot_callsign]['flight_plan']['route']
            if '+' in current_pilot_route:
                current_pilot_route = current_pilot_route.replace('+', '')

            if new_pilot_route != current_pilot_route:
                # pilot has received a reroute
                self.callsign_list[pilot_callsign] = new_pilot_data_associated_with_callsign
        else:
            # new_pilot_data_associated_with_callsign['flight_plan']['route'] = new_pilot_route
            self.callsign_list[pilot_callsign] = new_pilot_data_associated_with_callsign

    def get_callsign_data(self, callsign) -> dict:
        if callsign not in self.callsign_list:
            return None
        else:
            return self.callsign_list.get(callsign)
    
    def in_geographical_region_wip(self, airport:str, airplane_lat_long:tuple) -> bool:
        airports_dict = self.airports['airfields']
        self.fence = 0.026079

        #create fence
        #Airport NW Lat_Long point
        northern_latitude = airports_dict.get(airport)["LAT"] + self.fence
        western_longitude = airports_dict.get(airport)["LON"] - self.fence
        #Airport SE Lat_long point
        southern_latitude = airports_dict.get(airport)["LAT"] - self.fence
        eastern_longitude = airports_dict.get(airport)["LON"] + self.fence

        # airplane lat_long position
        airplane_lat, airplane_long = airplane_lat_long
    
        if (airplane_lat < northern_latitude and airplane_lat > southern_latitude) and (airplane_long > western_longitude and airplane_long < eastern_longitude):
            return True
        
    def scan_pilots(self):
        connected_pilots = self.json_file['pilots']

        # Determine what aircraft have disconnected and alert someone so the strip can be retrieved.
        disconnected = []
        for departure in self.callsign_list:
            disconnected.append(departure)

        # Interpreting/Filtering JSON Data
        for i in range(len(connected_pilots)):
            #What field should we check for? Departing or Arriving?
            lookfor = self.control_area['stripType']
            # pilot at index i information
            current_pilot = connected_pilots[i]
            #If they're connected, remove the callsign from the "disconnected" list
            if current_pilot['callsign'] in disconnected:
                disconnected.remove(current_pilot['callsign'].upper())
            
            try:
                if str(lookfor) == 'both':
                    #print(f"checking to see if {current_pilot['flight_plan']['departure']} is in {self.control_area['airports']}")
                    if current_pilot['flight_plan']['departure'] in tuple(self.control_area['airports']):
                        lookfor = 'departure'
                    elif current_pilot['flight_plan']['arrival'] in tuple(self.control_area['airports']):
                        lookfor = 'arrival'
                if lookfor != 'both':
                    lat_long_tuple = (current_pilot['latitude'], current_pilot['longitude'])
                    pilot_callsign = current_pilot['callsign'].upper()
                    pilot_departure_airport = current_pilot['flight_plan'][lookfor]
                    if pilot_departure_airport in tuple(self.control_area['airports']) and self.in_geographical_region_wip(self.control_area, pilot_departure_airport, lat_long_tuple):
                        # Save callsign of pilot and associated JSON Info
                        # to access, use: self.callsign_list.get(**callsign**)
                        # that will return the portion of the JSON with all of the pilot's info from when the system added them(flightplan, CID, etc.)
                        self.add_callsign_to_dep_list(pilot_callsign, current_pilot, lookfor)
            except TypeError as e1:
                pass        
            except Exception as e2:
                print(e2)

    def update_json(self, json_url):
        r = requests.get(json_url)
        self.json_file = r.json()