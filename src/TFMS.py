import requests
import time
import json

class TFMS:
    def __init__(self, airport_db, wp_db, json_url, tier1_db) -> None:
        self.json_url = json_url
        #Pull waypoint database
        self.waypoint_db = wp_db
        #Tier 1 Database
        self.tier1_db = tier1_db
        #Pull airports database
        self.airport_db = airport_db["airfields"]
        self.fence = 0.026079 #How far from the airport should we look to see if we have a pilot?
        #Keep track of ground stops by airport.
        ground_stopped = [] #this doesn't do anything rn lool
        self.discord = "https://discord.com/api/webhooks/1124601273078005830/Nf2AARyX5Gif_gszLx4qYfp6Jf4_2p_4OfBhExtz-yMES84F3SQMscfFq5UTxkyunIEf"
        pass

    def determine_airport(self):
        while(True):
            airport = input("Enter airfield: ").upper()
            airport = airport.replace(" ", "")
            icao_prefix = ["K", "C", "P"]
            if len(airport) < 4:
                for prefix in icao_prefix:
                    test_airport = f"{prefix}{airport}"
                    if len(test_airport) == 4 and test_airport in self.airport_db:
                        airport = test_airport
                        continue
            if len(airport) > 4 or airport not in self.airport_db: #Error
                print(f"I'm sorry. I don't know of a(n) {airport}. Please try again.")
                continue
            else:
                return airport 

    def determine_start_time(self):
        while(True):
            start_time = input("(LEAVE BLANK IF NOW OR IN THE PAST!) Enter start time: ").upper()
            start_time = start_time.replace(" ", "")
            if start_time == "": 
                start_time = f"{time.gmtime().tm_hour}{time.gmtime().tm_min}"
                return start_time
            else:
                if start_time.isdigit() and len(start_time) == 4:
                    if 0 <= int(start_time) < 2360: return start_time
                    else: 
                        print("I'm sorry... I can't seem to process that start time. Please try again.") 
                        continue
                else: continue
                        
    def determine_end_time(self):
        while(True):
            end_time = input("Enter end time: ").upper()
            end_time = end_time.replace(" ", "")
            if end_time.isdigit() and 3 <= len(end_time) <= 4:
                if len(end_time) == 3: end_time = f"0{end_time}"
                if 0 <= int(end_time) < 2360: 
                    if end_time[-2:] > 59:
                        print(f"I'm sorry. I am unable to process an end_time of {end_time}. Please try again.")
                        continue
                    else: return end_time
                else:
                    print(f"I'm sorry. I am unable to process an end_time of {end_time}. Please try again.")
                continue
    
    def determine_date(self,time_in_question,adl_time):
        if int(time_in_question) < int(adl_time): #tomorrow
            day = time.gmtime().tm_mday + 1
            month = time.gmtime().tm_mon
            if month in (4,6,9,11) and day > 30:
                day = 1
            if month == 2 and day > 28:
                day = 1
            return day
        else:#today
            return time.gmtime().tm_mday

    def facility_stopper(self):
        centers = set()
        tiers = 0
        manual = False
        while(True):
            stopped_centers = input("Enter stopped centers. Leave a blank entry when completed: ").upper()
            stopped_centers = stopped_centers.replace(","," ")
            stopped_centers = stopped_centers.replace("  "," ")
            if stopped_centers != "":
                if stopped_centers[1] == "T" and len(stopped_centers) == 2:
                    tiers, centers_to_add = self.process_tiers(facility)
                    centers.add(centers_to_add)
                elif stopped_centers[1] != "Z" and stopped_centers[1] != "-":
                    print(f"Sorry... not sure I understand what you mean by {stopped_centers}. Please try again.")
                else:
                    for facility in stopped_centers.split(" "):
                        if len(facility) == 3:
                            centers.add(facility)
                            manual = True
                        elif len(facility) == 4:
                            if facility[0] == "-":
                                try:
                                    centers.remove(facility[1:])
                                    manual = True
                                except:
                                    pass
                            elif facility.isalnum():
                                tiers, centers_to_add = self.process_tiers(facility)
                                centers.add(centers_to_add)
                    print(centers)
            else:
                return manual, tiers, centers

    def process_tiers(self, center):
        #How many tiers are we looking for?
        tiers = 0
        tier_count = 0
        neighbors = set()
        if center[:-1].isdigit():
            tier = center[-1:]
            center = center[:-1]
            neighbors.add(center)
        while tiers < tier_count:
            for next_tier in neighbors:
                for neighbor in self.tier1_db[next_tier]:
                    neighbors.add(neighbor)
            tiers = tiers + 1
        # neighbors.remove(center)
        return tier_count, neighbors #placeholder so it doesn't error...
        
    def airport_stopper(self):
        airports = set()
        while(True):
            stopped_airports = input("Enter ADDITIONAL stopped airports. Leave a blank entry when completed: ").upper()
            stopped_airports = stopped_airports.replace(","," ")
            stopped_airports = stopped_airports.replace("  "," ")
            icao_prefix = ["K", "C", "P"]
            if stopped_airports != "":
                for facility in stopped_airports.split(" "):
                    if len(facility) < 4:
                        for prefix in icao_prefix:
                            test_airport = f"{prefix}{facility}"
                            if len(test_airport) == 4 and test_airport in self.airport_db:
                                facility = test_airport
                                airports.add(facility)
                                continue
                    elif len(facility) == 4 and facility in self.airport_db:
                        airports.add(facility)
                        # if len(facility) > 4 or facility not in self.airport_db: #Error
                        #     print(f"I'm sorry. I don't know of a(n) {facility}. Please try again.")
                        #     pass
                    elif 4 <= len(facility) <= 5 and facility[0] == "-":
                        if len(facility) == 4:
                            for prefix in icao_prefix:
                                test_airport = f"{prefix}{facility[1:]}"
                                if len(test_airport) == 4 and test_airport in self.airport_db:
                                    facility = f"{test_airport}"
                                    airports.remove(facility)
                                    continue
                        try:
                            airports.remove(facility[1:])
                        except:
                            pass
                print(airports)
            else:
                return airports

    def capture_pilots(self, airport, current_data):
        self.captured = {} # "callsign":{"ptime":"","origin":"","center":""}
        self.airport_location_lat = self.airport_db[airport]['LAT']
        self.airport_location_lon = self.airport_db[airport]['LON']
        pilots = current_data["pilots"]
        plans = current_data["prefiles"]
        for x in pilots:
            self.hostage_checker(airport, x)
        for x in plans:
            self.hostage_checker(airport, x)
        return(self.captured)
    
    def hostage_checker(self, airport, flight_plan:dict):
        # record proposal time for each callsign that is filed to the destination airport
        flight_plan_route:str = flight_plan.get("flight_plan")
        if flight_plan_route is not None:
            arrival_airport = flight_plan_route.get("arrival")
            if arrival_airport is not None and arrival_airport == airport:
                is_connected = False
                if flight_plan.get("logon_time") is not None: is_connected = True
                if is_connected:
                    if self.locate_flights(flight_plan):
                        callsign = flight_plan.get("callsign")
                        p_time = flight_plan.get("flight_plan").get("deptime")
                        origin = flight_plan.get("flight_plan").get("departure")
                        origin_center = "ZZZ"
                        if origin is not None:
                            origin_center = self.airport_db[origin]["ARTCC"]
                        data = {callsign : {"ptime":p_time,"origin":origin, "origin_center":origin_center}}
                        self.captured.update(data)
                else:
                    callsign = flight_plan.get("callsign")
                    p_time = flight_plan.get("flight_plan").get("deptime")
                    origin = flight_plan.get("flight_plan").get("departure")
                    origin_center = "ZZZ"
                    if origin is not None:
                        origin_center = self.airport_db[origin]["ARTCC"]
                    data = {callsign : {"ptime":p_time,"origin":origin, "origin_center":origin_center}}
                    self.captured.update(data)

    def locate_flights(self, proposal):
        flight_lat:str = proposal.get("latitude")
        flight_lon:str = proposal.get("longitude")
        flight_location_speed:int = proposal.get("groundspeed")
        if flight_location_speed < 60:
            origin = proposal.get("flight_plan").get("departure")
            if origin is not None:
                in_lat = False
                in_lon = False
                try:
                    origin_lat = self.airport_db[origin]["LAT"]
                    origin_lon = self.airport_db[origin]["LON"]
                    if (origin_lat - self.fence) < flight_lat < (origin_lat + self.fence): in_lat = True
                    if (origin_lon - self.fence) < flight_lon < (origin_lon + self.fence): in_lon = True
                    if in_lat and in_lon: return True
                except:
                    return False
    
    def stopped_flights(self, flight_plans, facilities, airports, end_time):
        affected = []
        for pilot in flight_plans:
             if self.captured[pilot]["origin_center"] in facilities:
                 affected.append(pilot)
             elif self.captured[pilot]["origin"] in airports:
                 affected.append(pilot)
        delays = []
        maxDelay = 0
        totalDelay = 0
        flights_delayed = 0
        for delayed_flight in affected:
            int(end_hour) = end_time[2:]
            int(end_minute) = end_time[-2:]
            end_time = int(end_time)
            delay = 0
            ptime = int(self.captured[delayed_flight]["ptime"])
            # if end_time < int(ptime):
            #     end_time = end_time + 2400
            int(p_hour) = ptime[2:]
            int(p_minute) = ptime[-2:]
            if end_hour < p_hour:
                p_hour = p_hour + 24
            # if end_minute < p_minute:
            #     p_minute = p_minute + 60
            delayhour = end_hour - p_hour
            delaymin = end_minute - p_minute
            while delaymin < 0 and delayhour > 0:
                delaymin = delaymin + 60
                delayhour = delayhour - 1
            while delayhour > 0:
                delayhour = delayhour + 1
                delaymin = delaymin - 60
            while delaymin <= 0 and delayhour <= 0: #Means flight not subject to stop?
                affected.pop(delayed_flight)
                pass
            # delay = end_time - ptime
            int(delay) = f"{delayhour}{delaymin}"
            delays.append(delay)
            if delay > maxDelay: maxDelay = delay
            totalDelay = totalDelay + delay
            flights_delayed = flights_delayed + 1
        if flights_delayed > 0:
            average_delay = totalDelay / flights_delayed
        return totalDelay, maxDelay, average_delay
        
    def generate_advisory(self):
        airport = self.determine_airport()
        airport_center = self.airport_db.get(airport).get("ARTCC")
        current_data = requests.get(self.json_url).json()
        potential_pilots = self.capture_pilots(airport, current_data)
        adl_time = f"{time.gmtime().tm_hour}{time.gmtime().tm_min}"
        start_time = self.determine_start_time()
        start_date = self.determine_date(start_time, adl_time)
        end_time = self.determine_end_time()
        end_date = self.determine_date(end_time, adl_time)
        manual, tiers, stopped_facilities = self.facility_stopper()
        if len(stopped_facilities) == 0:
            stopped_facilities.add(airport_center)
        scope = "(MANUAL)"
        if manual == False:
            scope = f"(TIER {tiers}) "
        stopped_airports = self.airport_stopper()
        calculate_delays = self.stopped_flights(potential_pilots, stopped_facilities, stopped_airports, end_time)
        if len(stopped_airports) > 0:
            stopped_airports = f"ADDITIONAL DEP FACILITIES INCLUDED: {stopped_airports}"
        else:
            stopped_airports = ""
        POE = input("Probability of extension? NONE/LOW/MEDIUM/HIGH ").upper()
        Condition = input("Impacting Conditions: ").upper()
        Comments = input("Comments: ").upper()
        signature = f"{time.gmtime().tm_year}/{time.gmtime().tm_mon}/{time.gmtime().tm_mday} {time.gmtime().tm_hour}:{time.gmtime().tm_min}"
        content = f"vATCSCC ADVZY 000 {airport[-3:]}/{airport_center} CDM GROUND STOP CTL ELEMENT: {airport[-3:]} ELEMENT TYPE: APT ADL TIME: {adl_time}Z GROUND STOP PERIOD: {start_date}/{start_time}Z - {end_date}/{end_time}Z CUMULATIVE PROGRAM PERIOD:{start_date}/{start_time}Z - {end_date}/{end_time}Z FLT INCL: (MANUAL) {stopped_facilities} {stopped_airports} PREV TOTAL, MAXIMUM, AVERAGE DELAYS: UNKNOWN NEW TOTAL, MAXIMUM, AVERAGE DELAYS: {calculate_delays} PROBABILITY OF EXTENSION: {POE} IMPACTING CONDITION: {Condition} COMMENTS: {Comments}  EFFECTIVE TIME: {start_date}{start_time} - {end_date}{end_time} SIGNATURE: {signature}"
        content1 = (f"""
vATCSCC ADVZY 000 {airport[-3:]}/{airport_center} CDM GROUND STOP
CTL ELEMENT: {airport[-3:]}
ELEMENT TYPE: APT
ADL TIME: {adl_time}Z
GROUND STOP PERIOD: {start_date}/{start_time}Z - {end_date}/{end_time}Z
CUMULATIVE PROGRAM PERIOD:{start_date}/{start_time}Z - {end_date}/{end_time}Z
FLT INCL: {scope} {stopped_facilities}
{stopped_airports}
PREV TOTAL, MAXIMUM, AVERAGE DELAYS: UNKNOWN
NEW TOTAL, MAXIMUM, AVERAGE DELAYS: {calculate_delays}
PROBABILITY OF EXTENSION: {POE}
IMPACTING CONDITION: {Condition}
COMMENTS: {Comments}

EFFECTIVE TIME: {start_date}{start_time} - {end_date}{end_time}
SIGNATURE: {signature}
  """)
        discord_dum = {'username':'Shane (Gooder)',
                      'content': content}
        # requests.post(f'{self.discord}, "content="{content}')
        requests.post(self.discord, discord_dum) #Will this post???

