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
        self.ground_stopped = {} #I want the format to be "airport":{"N12345":{proposed,total}}
        self.advisory_num = 000
        self.advisory_day = 00
        self.discord = "https://discord.com/api/webhooks/1124601273078005830/Nf2AARyX5Gif_gszLx4qYfp6Jf4_2p_4OfBhExtz-yMES84F3SQMscfFq5UTxkyunIEf"
        pass

    def listener(self):
        while(True):
            command = input("Good afternoon! What command would you like to run? ").upper()
            # ? maybe? command_matrix = ["command":"function"]
            if command in ("HELP","COMMANDS","CMDS","?"):
                print("Available commands are: HELP/COMMANDS/CMDS/?, GS/GROUNDSTOP/STOP, HOTLINE, ARR/ARRIVALDELAYS/ARRIVAL-DELAYS, CDR/SWAP/CDRSWAP")
            elif command in ("GS","GROUNDSTOP","STOP"):
                self.generate_ground_stop()
            elif command in ("CDR","SWAP","CDRSWAP"):
                self.cdr_swap_statement()
            elif command in ("ARR","ARRIVAL DELAYS","ARRIVALDELAYS","ARRIVAL-DELAYS"):
                self.arrival_delays()
            elif command in ("ADVZY"):
                self.set_advisory_number()
            elif command in ("PROGRAMS"):
                print(self.ground_stopped)
            elif command in ("HOTLINE"):
                self.hotline()
            else:
                print("Sorry... not sure I understand. Perhaps you should run the help command?")


    def set_advisory_number(self):
        print(f"Current advisory number: {self.advisory_num+1}.")
        new_number = input("Input new advisory number: ")
        if new_number.isdigit():
            self.advisory_num = int(new_number)
            print(f"Advisory number successfully changed to {self.advisory_num}.")
        else:
            print("Error. Returning to main menu.")

    def advisory_numberinator(self):
        day = time.gmtime().tm_mday
        if day == self.advisory_day:
            self.advisory_num = self.advisory_num + 1
        else: 
            self.advisory_num = 1
            self.advisory_day = day
        advisory_number = str(self.advisory_num)
        while len(advisory_number) < 3: advisory_number = f"0{advisory_number}"
        return advisory_number
    
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
                start_time = self.format_time()
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
                    if int(end_time[-2:]) > 59:
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

    def facility_stopper(self, overlying_artcc):
        centers = set()
        tiers = 0
        manual = False
        while(True):
            stopped_centers = input("Enter stopped centers. Leave a blank entry when completed: ").upper()
            stopped_centers = stopped_centers.replace(","," ")
            stopped_centers = stopped_centers.replace("  "," ")
            if stopped_centers != "":
                if stopped_centers[0] == "T" and len(stopped_centers) == 2:
                    tiers, centers_to_add = self.process_tiers(stopped_centers, overlying_artcc)
                    centers = centers.union(centers_to_add)
                    print(centers)
                    # print(centers_to_add)
                elif stopped_centers[0] != "Z" and stopped_centers[0] != "-":
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
                                tiers, centers_to_add = self.process_tiers(stopped_centers, overlying_artcc)
                                centers = centers.union(centers_to_add)
                                print(centers)
                                # centers = self.new_method(centers, centers_to_add)
                    print(f"STOPPED CENTERS: {centers}")
            else:
                print(f"STOPPED CENTERS: {centers}")
                return manual, tiers, centers

    def new_method(self, centers, centers_to_add):
        centers = centers.union(centers_to_add)
        return centers

    def process_tiers(self, intended_tier, overlying_artcc):
        #How many tiers are we looking for?
        tiers = 0
        tier_count = 0
        neighbors = set()
        neighbors_to_add = set()
        if intended_tier[-1:].isdigit():
            tiers = intended_tier[-1:]
            tiers = int(tiers)
            intended_tier = intended_tier[:-1]
            neighbors.add(overlying_artcc)
        while tiers > tier_count:
            try:                
                for next_tier in neighbors:
                    for neighbor in self.tier1_db['centers'][next_tier]:
                        # print(self.tier1_db[next_tier])
                        # print(next_tier)
                        # print(neighbor)
                        neighbors_to_add.add(neighbor)
                neighbors = neighbors.union(neighbors_to_add)
                neighbors_to_add = set()
                tier_count = tier_count + 1
            except:
                tier_count = tiers
                print("exception D:")
        return tiers, neighbors #placeholder so it doesn't error...
        
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
                        if origin is not None and origin in self.airport_db:
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
    
    def stopped_flights(self, flight_plans, facilities, airports, start_date, start_time, end_time, control_element):
        affected = []
        for pilot in flight_plans:
             if self.captured[pilot]["origin_center"] in facilities:
                 affected.append(pilot)
             elif self.captured[pilot]["origin"] in airports:
                 affected.append(pilot)
        delays = {}
        maxDelay = 0
        totalDelay = 0
        flights_delayed = 0
        average_delay = 0
        for delayed_flight in affected:
            end_time = str(end_time)
            end_hour = end_time[:2]
            end_hour = int(end_hour)
            end_minute = end_time[-2:]
            end_minute = int(end_minute)
            end_time = int(end_time)
            delay = 0
            ptime = self.captured[delayed_flight]["ptime"]
            # if end_time < int(ptime):
            #     end_time = end_time + 2400
            p_hour = ptime[:2]
            p_hour = int(p_hour)
            p_minute = ptime[-2:]
            p_minute = int(p_minute)
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
                delayhour = delayhour - 1
                delaymin = delaymin + 60
            if delaymin <= 0 and delayhour <= 0: #Means flight not subject to stop?
                affected.remove(delayed_flight)
            else:
            # delay = end_time - ptime
            # if delayed_flight in affected:
                delay = f"{delayhour}{delaymin}"
                delay = int(delay)
                delays.update({delayed_flight:{"proposed":ptime, "total_delay":delay}})
                if delay > maxDelay: maxDelay = delay
                totalDelay = totalDelay + delay
                flights_delayed = flights_delayed + 1
        if flights_delayed > 0:
            average_delay = totalDelay / flights_delayed
            average_delay = average_delay.__floor__()
        self.ground_stopped.update({control_element:{"Prog_Info":{"Total":totalDelay, "Maximum":maxDelay,"Average":average_delay}}})
        if self.ground_stopped[control_element].get("Prog_Info").get("CUM_START") is None:
            self.ground_stopped[control_element]["Prog_Info"].update({"CUM_START":f"{start_date}/{start_time}"})
        # print(self.ground_stopped[control_element]["Prog_Info"]["CUM_START"])
        for aircraft in delays:
            proposed_time = delays[aircraft]["proposed"]
            the_total_delay = delays[aircraft]["total_delay"]
            self.ground_stopped[control_element].update({aircraft:{"proposed":proposed_time,"total_delay":the_total_delay}})
        print(f"PROGRAM INFORMATION: {self.ground_stopped[control_element]}")
        return totalDelay, maxDelay, average_delay
        
    def format_lists_for_display(self, list):
        the_list = str(list)
        the_list = the_list.replace("'","")
        the_list = the_list.replace("{","")
        the_list = the_list.replace("}","")
        return the_list

    def publish_to_discord(self,username,content):
        staging = {'username':username,
                  'content':content}
        requests.post(self.discord, staging)

    def format_signatures(self):
        mon = str(time.gmtime().tm_mon)
        if len(mon) < 2: mon = f"0{mon}"
        date = str(time.gmtime().tm_mday)
        if len(date) < 2: date = f"0{date}"
        header_date = f"{mon}/{date}/{time.gmtime().tm_year}"
        hour = str(time.gmtime().tm_hour)
        if len(hour) < 2: hour = f"0{hour}"
        min = str(time.gmtime().tm_min)
        if len(min) < 2: min = f"0{min}"

        sig_date_time = f"{str(time.gmtime().tm_year)[-2:]}/{mon}/{date} {hour}:{min}"
        return header_date, sig_date_time
    
    def preview(self, content):
        print("Preview:")
        print(content)
        while True:
            verify = input("Do you want to publish this advisory? ").upper()
            if verify == "" or verify[0] == "Y": return True
            else: return False 
        
    def format_time(self):
        hour = str(time.gmtime().tm_hour)
        if len(hour) < 2: hour = f"0{hour}"
        min = str(time.gmtime().tm_min)
        if len(min) < 2: min = f"0{min}"
        return f"{hour}{min}"
    
    def hotline(self):
        advisory_number = self.advisory_numberinator()
        header_date, sig_date_time = self.format_signatures()
        hotline_name = input("Which hotline would you like to open/close? ").upper()
        status = input(f"Are you activating or deactivating the {hotline_name} hotline? ").upper()
        if status[0] == "A": status = "ACTIVATING" 
        else: status = "DEACTIVATING"
        adl_time = f"{time.gmtime().tm_hour}{time.gmtime().tm_min}"
        start_time = self.determine_start_time()
        start_date = self.determine_date(start_time, adl_time)
        end_time = self.determine_end_time()
        end_date = self.determine_date(end_time, adl_time)
        constrained_facs = input("What facilities are constrained? Enter all that apply.").upper()
        if status == "ACTIVATING":
            constrained_reason = input("Why is the hotline being activated? (VOLUME/WEATHER/OTHER) ").upper()
            location = input("Where is the hotline being hosted? (VATUSA TEAMSPEAK)").upper()
            location_link = input("Is there an IP/PIN to join? (TS.VATUSA.NET, NO PIN)").upper()
            participation_type = input("Is participation mandatory or recommended?").upper()
            participation_parties = input(f"Who is participation {participation_type} for?").upper()
            poc = input("Who is the point of contact if there are issues?").upper()
            content = f"""```vATCSCC ADVZY {advisory_number} {header_date} {hotline_name} HOTLINE_FYI
EVENT TIME: {start_date}/{start_time} - {end_date}/{end_time}
CONSTRAINED FACILITIES: {constrained_facs}
THE {hotline_name} HOTLINE IS BEING ACTIVATED TO ADDRESS {constrained_reason} IN {constrained_facs}.
THE LOCATION IS THE {location}, {hotline_name} HOTLINE, {location_link}.
PARTICIPATION IS {participation_type} FOR {participation_parties}. AFFECTED
MAJOR UNDERLYING FACILITIES ARE STRONGLY ENCOURAGED TO ATTEND. ALL OTHER
PARTICIPANTS ARE WELCOME TO JOIN. PLEASE MESSAGE {poc} IF YOU HAVE ISSUES OR QUESTIONS.

{start_date}{start_time} - {end_date}{end_time}
{sig_date_time}```
"""
        else:
            content = f"""```vATCSCC ADVZY {advisory_number} {header_date} {hotline_name} HOTLINE_FYI
EVENT TIME: {time.gmtime().tm_mday}/{start_time} - {time.gmtime().tm_mday}/{end_time}
CONSTRAINED FACILITIES: {constrained_facs}
THE {hotline_name} HOTLINE IS NOW TERMINATED.

{time.gmtime().tm_mday}{start_time} - {time.gmtime().tm_mday}{end_time}
{sig_date_time}```
            """

        if self.preview(content): self.publish_to_discord("HOTLINE STATUS",content)
        print("Returning to menu.")

        
    def arrival_delays(self):
        advisory_number = self.advisory_numberinator()
        airport = self.determine_airport()
        adl_time = f"{time.gmtime().tm_hour}{time.gmtime().tm_min}"
        airport_center = self.airport_db.get(airport).get("ARTCC")
        airport_long_name = self.airport_db.get(airport).get("NAME")
        start_time = self.determine_start_time()
        start_date = self.determine_date(start_time, adl_time)
        end_time = self.determine_end_time()
        end_date = self.determine_date(end_time, adl_time)
        Condition = input("Impacting Condition(s): ").upper()
        Duration = input("Length of Holding (Minutes): ").upper()
        Comments = input("Remarks: ").upper()
        header_date, sig_date_time = self.format_signatures()
        content = f"""```vATCSCC ADVZY {advisory_number} {header_date} {airport_long_name} ARRIVAL DELAYS
EVENT TIME: {start_date}/{start_time} - {end_date}/{end_time}
CONSTRAINED FACILITIES: {airport_center}
USERS CAN EXPECT ARRIVAL DELAYS / AIRBORNE HOLDING INTO 
{airport_long_name} AIRPORT OF UP TO {Duration} MINUTES DUE TO 
{Condition} IMPACTING THE TERMINAL(S) / ARRIVAL ROUTES. {Comments}
UPDATES WILL FOLLOW IF NECESSARY.

{start_date}{start_time} - {end_date}{end_time}
{sig_date_time}```
        """
        if self.preview(content): self.publish_to_discord("ARRIVAL DELAY ALERT",content)
        print("Returning to menu.")
        
    
    def cdr_swap_statement(self):
        advisory_number = self.advisory_numberinator()
        airport = self.determine_airport()
        adl_time = self.format_time()
        airport_center = self.airport_db.get(airport).get("ARTCC")
        start_time = self.determine_start_time()
        start_date = self.determine_date(start_time, adl_time)
        end_time = self.determine_end_time()
        end_date = self.determine_date(end_time, adl_time)
        tier, facilities_included = self.process_tiers("T1", airport_center)
        facilities_included = self.format_lists_for_display(facilities_included)
        POE = input("Probability of extension? NONE/LOW/MODERATE/HIGH ").upper()
        Condition = input("Impacting Conditions: ").upper()
        Comments = input("Comments: ").upper()
        Restrictions = input("Associated Restrictions: ").upper()
        Modifies = input("Modifies route structure in (list previous advisories, or, leave blank): ").upper()
        header_date, sig_date_time = self.format_signatures()
        target_space_distance = 20 - len(airport)
        space = ""
        while len(space) < target_space_distance: space = f" {space}"
        content = f"""```vATCSCC ADVZY {advisory_number} DCC {header_date} ROUTE FYI
NAME: {airport}_CDRS_SWAP
CONSTRAINED AREA: {airport_center}
REASON: {Condition}
INCLUDE TRAFFIC: {airport} DEPARTURES TO UNKN
FACILITIES INCLUDED: {facilities_included}
FLIGHT STATUS: ALL_FLIGHTS
VALID: ETD {start_date}{start_time} TO {end_date}{end_time}
PROBABILITY OF EXTENSION: {POE}
REMARKS: {Comments}
ASSOCIATED RESTRICTIONS: {Restrictions}
MODIFICATIONS: {Modifies}
ROUTES:

ORIG                DEST                 ROUTE
----                ----                 -----
{airport}{space}UNKN                 CDR RTE:DEPARTURES CAN     
                                         EXPECT CDRS/SWAP DUE TO    
                                         WEATHER. USERS SHOULD FILE 
                                         NORMAL ROUTES BUT FUEL     
                                         ACCORDINGLY.
                                         
{start_date}{start_time} - {end_date}{end_time}
{sig_date_time}```
        """
        
        if self.preview(content): self.publish_to_discord("Shane (real)",content)
        print("Returning to menu.")
        
    def generate_ground_stop(self):
        header_date, sig_date_time = self.format_signatures()
        print(f"The current zulu date/time is {self.format_time()}.")
        advisory_number = self.advisory_numberinator()
        airport = self.determine_airport()
        control_element = airport
        prev_delays = ""            
        airport_center = self.airport_db.get(airport).get("ARTCC")
        current_data = requests.get(self.json_url).json()
        potential_pilots = self.capture_pilots(airport, current_data)
        adl_time = self.format_time()
        start_time = self.determine_start_time()
        start_date = self.determine_date(start_time, adl_time)
        end_time = self.determine_end_time()
        end_date = self.determine_date(end_time, adl_time)
        cum_start = f"{start_date}/{start_time}Z"
        if control_element in self.ground_stopped:
            prev_delays = self.ground_stopped[control_element]["Prog_Info"]
            prev_delay_amounts = f"{prev_delays['Total']}/{prev_delays['Maximum']}/{prev_delays['Average']}"
            if prev_delays.get("CUM_START") is not None: cum_start = f"{prev_delays['CUM_START']}Z"
            prev_delays = f"""
PREV TOTAL, MAXIMUM, AVERAGE DELAYS: {prev_delay_amounts}"""
        manual, tiers, stopped_facilities = self.facility_stopper(airport_center)
        if len(stopped_facilities) == 0:
            stopped_facilities.add(airport_center)
        scope = "(MANUAL)"
        if manual == False:
            scope = f"(TIER {tiers}) "
        stopped_airports = self.airport_stopper()
        calculate_delays = self.stopped_flights(potential_pilots, stopped_facilities, stopped_airports, start_date, start_time, end_time, control_element)
        if len(stopped_airports) > 0:
            stopped_airports = self.format_lists_for_display(stopped_airports)
            stopped_airports = f"""
ADDITIONAL DEP FACILITIES INCLUDED: {stopped_airports}"""
        else:
            stopped_airports = ""
        stopped_facilities = self.format_lists_for_display(stopped_facilities)
        POE = input("Probability of extension? NONE/LOW/MODERATE/HIGH ").upper()
        Condition = input("Impacting Conditions: ").upper()
        Comments = input("Comments: ").upper()
        signature = f"{sig_date_time}"
        content = (f"""```
vATCSCC ADVZY {advisory_number} {airport[-3:]}/{airport_center} CDM GROUND STOP
CTL ELEMENT: {airport[-3:]}
ELEMENT TYPE: APT
ADL TIME: {adl_time}Z
GROUND STOP PERIOD: {start_date}/{start_time}Z - {end_date}/{end_time}Z
CUMULATIVE PROGRAM PERIOD:{cum_start} - {end_date}/{end_time}Z
FLT INCL: {scope} {stopped_facilities} {stopped_airports} {prev_delays}
NEW TOTAL, MAXIMUM, AVERAGE DELAYS: {calculate_delays}
PROBABILITY OF EXTENSION: {POE}
IMPACTING CONDITION: {Condition}
COMMENTS: {Comments}

EFFECTIVE TIME: {start_date}{start_time} - {end_date}{end_time}
SIGNATURE: {signature}```
  """)
        
        if self.preview(content): self.publish_to_discord("Shane (Goodest)",content)
        print("Returning to menu.")