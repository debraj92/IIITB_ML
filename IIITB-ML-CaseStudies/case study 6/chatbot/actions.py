from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from rasa_core.actions.action import Action
from rasa_core.actions.forms import FormAction, FormField
from rasa_core.actions.forms import EntityFormField
from rasa_core.events import SlotSet
import re
from zomato import initialize_app
import json
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

restaurants_response = ''


def get_zamoto_search_response(city, cuisine, price_range, num_result=10):
    def _fliter_restaurants(price_range_index=0):
        for restaurant in d['restaurants']:
            if price_range_index == 1 and restaurant['restaurant']['average_cost_for_two'] < 300:
                response.append(restaurant)
            if price_range_index == 2 and 300 <= restaurant['restaurant'][
                'average_cost_for_two'] <= 700:
                response.append(restaurant)
            if price_range_index == 3 and restaurant['restaurant']['average_cost_for_two'] > 700:
                response.append(restaurant)

    config = {"user_key": "8d0689af176e3122714681e343fae263"}
    zomato = initialize_app(config)
    # RETURN CODES
    CITY_NOT_FOUND = -1
    NO_RESULTS = 0
    SUCCESS = 1
    try:
        city_id = zomato.get_city_ID(city)
    except:
        print("Unfortunately Zomato does not have this city in its database")
        return ([], CITY_NOT_FOUND)

    # TODO need to update with new cusines - DONE
    cuisines_dict = {'bakery': 5, 'chinese': 25, 'cafe': 30, 'italian': 55, 'biryani': 7,
                     'north indian': 50, 'south indian': 85, 'Mexican': 73, 'american': 1}
    response = []
    start = 0
    ### We will only try top 100 (sorted by rating) records, if there is no restaurants with given
    # price range, we will return "not found" . We are doing this because it is not production,
    # making so many calls to ZOMOTO can hit API LIMIT (1000 calls per day)
    while start < 100:
        if start % 100 == 0:
            print("Searching : Please Wait")
        results = zomato.restaurant_search("", city_id=city_id,
                                           cuisines=str(cuisines_dict.get(cuisine)),
                                           limit=20, sort='rating', order="desc",
                                           start_offset=start)
        d = json.loads(results)

        if d['restaurants'] == 0:
            break
        else:
            _fliter_restaurants(price_range)

        if len(response) >= num_result: break
        start += 20
        time.sleep(1)

    if len(response) == 0:
        return (response, NO_RESULTS)
    else:
        return (response, SUCCESS)


def generate_response_msg(restaurants, cuisine, number_of_records=5):
    response_msg = "Showing you top rated {} restaurants : \n'".format(cuisine)
    if not restaurants:
        response_msg = "no Restaurant found (we have looked into top 100 records from " \
                       "zomato), can you please try a higher budget category"
    else:
        index = 0
        for restaurant in restaurants:
            if index > number_of_records: break
            response_msg = response_msg + "{} in {} has been rated {} : [ " \
                                          "average_cost_for_two = {}] ".format(
                restaurant['restaurant']['name'],
                restaurant['restaurant']['location']['address'],
                restaurant['restaurant']['user_rating']['aggregate_rating'],
                restaurant['restaurant']['average_cost_for_two']) + "\n"
            index += 1
    return response_msg

'''
We will use FormActions to accept input from the user, validate the inputs and execute required actions

'''
class LocationFormField(EntityFormField):
    ''' Custom form field to validate location '''

    def __init__(self, entity_name, slot_name):
        EntityFormField.__init__(self, entity_name, slot_name)

    def validate(self, value):
        valid_locations = ['ahmedabad', 'bangalore', 'chennai', 'delhi', 'hyderabad', 'kolkata',
                           'mumbai', 'pune', 'agra', 'ajmer', 'aligarh', 'amravati',
                           'amritsar', 'asansol', 'aurangabad', 'bareilly', 'belgaum', 'bhavnagar',
                           'bhiwandi', 'bhopal', 'bhubaneswar', 'bikaner',
                           'bokaro steel city', 'chandigarh', 'coimbatore', 'cuttack', 'dehradun',
                           'dhanbad', 'durg bhilai nagar', 'durgapur', 'erode',
                           'faridabad', 'firozabad', 'ghaziabad', 'gorakhpur', 'gulbarga', 'guntur',
                           'gurgaon', 'guwahati‚ gwalior', 'hubli dharwad', 'indore',
                           'jabalpur', 'jaipur', 'jalandhar', 'jammu', 'jamnagar', 'jamshedpur',
                           'jhansi', 'jodhpur', 'kannur', 'kanpur', 'kakinada', 'kochi',
                           'kottayam', 'kolhapur', 'kollam', 'kota', 'kozhikode', 'kurnool',
                           'lucknow', 'ludhiana', 'madurai', 'malappuram', 'mathura', 'goa',
                           'mangalore', 'meerut', 'moradabad', 'mysore', 'nagpur', 'nanded',
                           'nashik', 'nellore', 'noida', 'palakkad', 'patna', 'pondicherry',
                           'prayagraj', 'raipur', 'rajkot', 'rajahmundry', 'ranchi', 'rourkela',
                           'salem', 'sangli', 'siliguri', 'solapur', 'srinagar', 'sultanpur',
                           'surat', 'thiruvananthapuram', 'thrissur', 'tiruchirappalli',
                           'tirunelveli', 'tiruppur', 'ujjain', 'bijapur', 'vadodara', 'varanasi',
                           'vasai virar city', 'vijayawada', 'visakhapatnam', 'warangal']

        if (str(value).lower() in valid_locations):
            return value
        elif (value != None):
            print('Sorry, we are not present in this location')

        return None

    def extract(self, tracker):
        value = tracker.get_slot(self.entity_name)
        validated = self.validate(value)
        if validated is not None:
            return [SlotSet(self.slot_name, validated)]
        else:
            return [SlotSet(self.slot_name, None)]


class CuisineFormField(EntityFormField):
    ''' Custom form field to validate cuisine '''
    
    def __init__(self, entity_name, slot_name):
        EntityFormField.__init__(self, entity_name, slot_name)

    def validate(self, value):
        valid_cuisine = ["chinese", "mexican", "italian", "american", "south indian",
                         "north indian"]

        if (str(value).lower() in valid_cuisine):
            return value
        elif (value != None):
            print('Sorry, we do not serve that cuisine')

        return None

    def extract(self, tracker):
        value = tracker.get_slot(self.entity_name)
        validated = self.validate(value)
        if validated is not None:
            return [SlotSet(self.slot_name, validated)]
        else:
            return [SlotSet(self.slot_name, None)]


class BudgetFormField(EntityFormField):
    ''' Custom form field to validate budget '''
    
    def __init__(self, entity_name, slot_name):
        EntityFormField.__init__(self, entity_name, slot_name)

    def validate(self, value):
        
        low_cost_options = ["less than 300", "<300", "< 300", "low", "cheap", "inexpensive","lesser than 300","lower than 300","within 300"]
        medium_cost_options = ["300 to 700", "300 - 700", "300-700", "mid", "moderate", "average", "medium"]
        high_cost_options = ["more than 700", ">700", "> 700", "pricey", "expensive", "premium", "costly", "greater than 700"]
        
        for i in low_cost_options:
            if i in str(value):
                return value
        
        for i in medium_cost_options:
            if i in str(value):
                return value
        
        for i in high_cost_options:
            if i in str(value):
                return value
        
        if value != None:
            print('Sorry, we do not have that budget category')
        
        return None
    

    def extract(self, tracker):
        value = tracker.get_slot(self.entity_name)
        validated = self.validate(value)
        if validated is not None:
            return [SlotSet(self.slot_name, validated)]
        else:
            return [SlotSet(self.slot_name, None)]


class EmailFormField(EntityFormField):
    ''' Custom form field to validate email '''
    
    def __init__(self, entity_name, slot_name):
        EntityFormField.__init__(self, entity_name, slot_name)

    def validate(self, value):

        pattern = re.compile("^[a-zA-Z0-9_.]+@[a-zA-Z_]+?\\.[a-zA-Z]{2,3}(\\.[a-zA-Z]{2,3})?$")
        if pattern.match(str(value)):
            return value
        elif (value != None):
            print("Sorry, I can't find a valid email id in your respoonse")

        return None

    def extract(self, tracker):
        # value = next(tracker.get_latest_entity_values(self.entity_name), None)
        value = tracker.get_slot(self.entity_name)
        validated = self.validate(value)
        if validated is not None:
            return [SlotSet(self.slot_name, validated)]
        else:
            return [SlotSet(self.slot_name, None)]


class ActionSearchRestaurants(FormAction):
    ''' Form Action for searching restaurants in Zomato '''
    
    def name(self):
        return 'action_restaurant_form'

    @staticmethod
    def required_fields():
        return [
            LocationFormField("location", "location"),
            CuisineFormField("cuisine", "cuisine"),
            BudgetFormField("budget", "budget")
        ]

    def submit(self, dispatcher, tracker, domain):
        global restaurants_response
        print('Zomato Search')

        loc = tracker.get_slot('location')
        cuisine = tracker.get_slot('cuisine')
        budget = tracker.get_slot('budget')
        BUDGET_LOW = 1
        BUDGET_MID = 2
        BUDGET_HIGH = 3
        
        low_cost_options = ["less than 300", "<300", "< 300", "low", "cheap", "inexpensive","lesser than 300","lower than 300","within 300"]
        medium_cost_options = ["300 to 700", "300 - 700", "300-700", "mid", "moderate", "average", "medium"]
        high_cost_options = ["more than 700", ">700", "> 700", "pricey", "expensive", "premium", "costly", "greater than 700"]
        
        for i in low_cost_options:
            if i in str(budget):
                buget_category = BUDGET_LOW
        
        for i in medium_cost_options:
            if i in str(budget):
                buget_category = BUDGET_MID
        
        for i in high_cost_options:
            if i in str(budget):
                buget_category = BUDGET_HIGH

        print("Searching restaurants in Zomato which are located in ",str(loc), " and serves ",str(cuisine), 
              " cuisine belonging to the budget category: ",str(budget))

        restaurants_response, RESULT_CODE = get_zamoto_search_response(loc, cuisine, buget_category)

        if RESULT_CODE != -1:
            response_msg = generate_response_msg(restaurants_response, cuisine, 5)

        print(response_msg)


class ActionSendEmail(FormAction):
    ''' Form Action for sending email '''
    
    def name(self):
        return 'action_send_email_form'

    @staticmethod
    def required_fields():
        return [
            EmailFormField("email", "email")
        ]

    def submit(self, dispatcher, tracker, domain):
        global restaurants_response
        email = tracker.get_slot('email')

        print("Sending email to ", str(email))
        print("Please wait ...")
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("ajay.pundhir.mlai3@iiitb.net", "R)7VdJaTDMCiZjudmV3cj;QL")

        fromaddr = "ajay.pundhir.mlai3@iiitb.net"
        toaddr = email
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = "Your search results from RASA chatbot_y"

        body = generate_response_msg(restaurants_response, tracker.get_slot('cuisine'), 10)
        msg.attach(MIMEText(body, 'plain'))

        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()


class ActionFallback(Action):
    ''' Custom Action for fallback when user message is unknown to bot '''
    
    def name(self):
        return "action_fallback"

    def run(self, dispatcher, tracker, domain):
        print("Sorry, didn't get that. Please try again")
