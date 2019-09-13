##Functions for DC Apartment scraper

import json
import requests
import pickle
import re
from bs4 import BeautifulSoup
import configparser
import os
import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# from googleapiclient.discovery import build
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request

#####SHEETS FUNCTIONS#####

def start_client():
	"""start up the google api client object"""
	creds_file = 'Google_Drive_secret_key.json'
	scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
	creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
	client = gspread.authorize(creds)
	return client

def get_sheet(client):
	"""Given a client object, pull and return the sheet object"""
	wb_name = 'DC Apartments - 7/9/19'
	sheet = client.open(wb_name).sheet1
	return sheet

def get_links(sheet):
	links_list = sheet.col_values(2)
	# links_list = sheet.get_all_records()
	return links_list

def get_all_data(sheet):
	"""Given a sheet object, pull and return the all the data as a list of dicts"""
	all_sheet_data = sheet.get_all_records()
	pickle_all_sheet_data(all_sheet_data) #debug
	return all_sheet_data

def walk_sheet_data(sheet):
	"""Given the data as a sheet, walk through the list of dicts"""
	all_sheet_data = get_all_data(sheet)
	for index, row_dict in enumerate(all_sheet_data):
		if 'y' not in row_dict['Parsed?'].lower() and row_dict['Link'] != '':
			url = row_dict['Link']
			fields = parse_apts_data(url)
			# print("fields",fields,len(fields))

			headers_dict = get_headers_indexes_dict(sheet)

			populate_sheet(sheet,fields,headers_dict,index)

		elif 'y' in row_dict['Parsed?'].lower():
			pass


def populate_sheet(sheet,fields,headers_dict,index):
	cells_to_update_list = []
	for field, value in fields.items():
		if field.lower() in headers_dict.keys():
			col = headers_dict[field.lower()] + 1
			row = index + 2
			cell_to_update = sheet.cell(row,col)
			cell_to_update.value = value
			cells_to_update_list.append(cell_to_update)
	# print("cells to update",cells_to_update_list,len(cells_to_update_list))
	sheet.update_cells(cells_to_update_list)
	sheet.update_cell(row,1,'yes')

def get_headers_indexes_dict(sheet):
	headers = sheet.row_values(1)
	headers_dict = {}
	for column_name in headers:
		column_index = headers.index(column_name)
		headers_dict[column_name.lower()] = column_index
	return headers_dict


#####END SHEETS FUNCTIONS#####



#######APTS FUNCTIONS#######

def parse_apts_data(url):
	"""For every apartment page, populate the required fields"""

	##read the current url
	headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
	page = requests.get(url, headers=headers)

	##soupify current url
	soup = BeautifulSoup(page.content, 'html.parser')
	soup.prettify()

	# the information we need to return as a dict
	fields = {}

	# get the name of the property
	get_property_name(soup, fields)

	# get the address of the property
	get_property_address(soup, fields)

	# get the monthly fees
	get_table_fields_based_on_tag(soup, fields, 'rent')

	# get the deposit fees
	get_table_fields_based_on_tag(soup, fields, 'deposit')

	# get the size of the property
	get_table_fields_based_on_tag(soup, fields, 'sqft','Size (ft^2)')

	# get the number of beds
	get_table_fields_based_on_tag(soup, fields, 'beds')

	# get the number of baths
	get_table_fields_based_on_tag(soup, fields, 'baths')

	# get the lease length
	get_table_fields_based_on_tag(soup, fields, 'leaseLength', 'Lease Length')

	# get the date available
	get_table_fields_based_on_tag(soup, fields, 'available', 'Date Available')

	soup = soup.find('section', class_='specGroup js-specGroup')

	# get the amenities we care about
	get_amenities(soup, fields, 'Washer/Dryer')

	# get parking info
	get_parking_info(soup, fields)

	# geocode address
	geocode_address(fields)

	# get nearby metro
	get_nearby_metro(fields)

	# get travel time from Google Maps
	get_travel_times(fields) #debug

	# fields['parsed?'] = 'yes'

	return fields


def get_property_name(soup, fields):
	"""Given a beautifulSoup parsed page, extract the name of the property"""
	fields['Name'] = ''

	# get the name of the property
	obj = soup.find('h1', class_='propertyName')
	if obj is not None:
		name = obj.getText()
		name = prettify_text(name)
		fields['Name'] = name

def get_property_address(soup, fields):
	"""Given a beautifulSoup parsed page, extract the address of the property"""

	address = ""

	# They changed how this works so I need to grab the script
	script = soup.findAll('script', type='text/javascript')[2].text
	# The address is everything in quotes after listingAddress
	address = find_addr(script, "listingAddress")
	# City
	address += ", " + find_addr(script, "listingCity")
	# State
	address += ", " + find_addr(script, "listingState")
	# Zip Code
	address += " " + find_addr(script, "listingZip")
	fields['Address'] = address

def get_table_fields_based_on_tag(soup, fields, tag, optional_name=None):
	"""Given a beautifulSoup parsed page, extract the quick table attributes"""

	#get field
	obj = soup.find('td', class_=tag)
	if obj is not None:
		field = obj.getText()
		field = prettify_text(field)
		field = field.replace('$','')
		field = field.replace(' Sq Ft','')
		field = field.replace(',','')

		#if bed or bath
		if tag == 'beds' or tag == 'baths':
			field = field[0:1]

		#if lease length
		if tag == 'leaseLength':
			field = field[0:2]

		#if optional name for field has been passed - use it instead
		if optional_name is not None:
			tag = optional_name

		fields[tag] = field

def get_amenities(soup, fields, amenity):
	"""Given a beautifulSoup parsed page, extract the amenities/features we want"""

	if soup is None: return
    
	obj = soup.find('i', class_='propertyIcon')

	if obj is not None:
		for obj in soup.find_all('i', class_='propertyIcon'):
			data = obj.parent.findNext('ul').getText()
			data = prettify_text(data)

			if obj.parent.findNext('h3').getText().strip() == 'Features':
				# format it nicely: remove trailing spaces
				if amenity in data:
					fields[amenity] = 'yes'
				else:
					fields[amenity] = 'no'

def get_parking_info(soup, fields):
	"""Given a beautifulSoup parsed page, extract the parking details"""

	fields['Parking'] = ''

	if soup is None: return

	obj = soup.find('div', class_='parkingDetails')
	if obj is not None:
		data = obj.getText()
		data = prettify_text(data)

		# format it nicely: remove trailing spaces
		fields['Parking'] = data

			
def find_addr(script, tag):
    """Given a script and a tag, use python find to find the text after tag"""

    tag = tag + ": \'"
    start = script.find(tag)+len(tag)
    end = script.find("\',", start)
    return script[start : end]

def prettify_text(data):
	"""Given a string, replace unicode chars and make it prettier"""

	# format it nicely: replace multiple spaces with just one
	data = re.sub(' +', ' ', data)
	# format it nicely: replace multiple new lines with just one
	data = re.sub('(\r?\n *)+', '\n', data)
	# format it nicely: replace bullet with *
	data = re.sub(u'\u2022', '* ', data)
	# format it nicely: replace registered symbol with (R)
	data = re.sub(u'\xae', ' (R) ', data)
	# format it nicely: remove trailing spaces
	data = data.strip()
	# # format it nicely: encode it, removing special symbols
	# data = data.encode('utf8', 'ignore')

	return str(data)

#######END APTS FUNCTIONS#######




#######MAPS FUNCTIONS#######

def get_travel_times(fields):
	"""Given the apartment address/metro address, find the travel time to and from the apt"""
	
	modes = ['Driving','Transit']
	apartment_address = fields['Address']
	metro_address = fields['metro address']

	#Retriving config parameters
	config_object = parse_config_file()
	units = config_object.get('all', 'mapsUnits')
	maps_url = config_object.get('all', 'mapsURL')
	maps_API_key = config_object.get('all', 'mapsAPIKey')

	#Base payload
	maps_payload = {'units':units,
					'key':maps_API_key}
	
	work_addresses = ''
	users = []
	for user in config_object['work addresses']:
		work_addresses += config_object['work addresses'][user] + '|'
		users.append(user)
	work_addresses = work_addresses[:-1]

	#Building payloads for each time and mode, getting API response
	for time in config_object['commute times']:
		for mode in modes:
			departure_time = parse_config_times(config_object['commute times'][time])

			if time.lower() == 'morning':
				origin = apartment_address
				destination = work_addresses
			elif time.lower() == 'evening':
				origin = work_addresses
				destination = apartment_address

			payload = maps_payload.copy()
			payload.update({'mode': mode, 
				'origins': origin,
				'destinations': destination,
				'departure_time': departure_time})

			j = 0
			response = requests.get(maps_url, params=payload).json()
			for row in response['rows']: 
				for element in row['elements']:
					user = users[j]
					duration = element['duration']['value']/60
					fields['{} {} {}'.format(user, time, mode)] = duration
					j+=1

	#Metro distance - getting API response
	metro_payload = maps_payload.copy()
	metro_payload.update({'mode': 'walking',
							'origins':apartment_address,
							'destinations':metro_address})

	response = requests.get(maps_url, params=metro_payload).json()
	metro_duration = response['rows'][0]['elements'][0]['duration']['value']/60
	fields['Metro Walk'] = metro_duration

def get_nearby_metro(fields):
	"""Given the apartment lat and long, get nearest metro name and address"""
	apartment_lat = fields['lat']
	apartment_long = fields['long']

	config_object = parse_config_file()
	nearby_url = config_object.get('all', 'nearbyURL')
	maps_API_key = config_object.get('all', 'mapsAPIKey')

	#Base payload
	nearby_payload = {'key':maps_API_key,
					  'input':'metro station',
					  'inputtype':'textquery',
					  'locationbias':'point:{},{}'.format(apartment_lat,apartment_long),
					  'fields':'name,formatted_address'}

	response = requests.get(nearby_url, params=nearby_payload).json()

	metro_name = response['candidates'][0]['name']
	metro_address = response['candidates'][0]['formatted_address']

	fields['metro'] = metro_name
	fields['metro address'] = metro_address

def geocode_address(fields):
	"""Given the apartment address, get the lat and long of the address"""
	apartment_address = fields['Address']

	config_object = parse_config_file()
	geocode_url = config_object.get('all', 'geocodeURL')
	maps_API_key = config_object.get('all', 'mapsAPIKey')

	geocode_payload = {'key':maps_API_key,
					  'address':apartment_address}

	response = requests.get(geocode_url, params=geocode_payload).json()

	lat = response['results'][0]['geometry']['location']['lat']
	lng = response['results'][0]['geometry']['location']['lng']

	fields['lat'] = lat
	fields['long'] = lng


#######END MAPS FUNCTIONS#######




#######CONFIG FUNCTIONS#######

def parse_config_file():
	"""Parse the config.ini file"""
	config_object = configparser.ConfigParser()
	config_file = 'config.ini'
	config_object.read(config_file)	

	return config_object

def parse_config_times(given_time):
	"""Convert the tomorrow at given_time New York time to seconds since epoch"""

	# tomorrow's date
	tomorrow = datetime.date.today() + datetime.timedelta(days=1)
	# tomorrow's date/time string based on time given
	date_string = str(tomorrow) + ' ' + given_time
	# tomorrow's datetime object
	format_ = '%Y-%m-%d %I:%M %p'
	date_time = datetime.datetime.strptime(date_string, format_)

	# the epoch
	epoch = datetime.datetime.utcfromtimestamp(0)

	# return time since epoch in seconds, string without decimals
	time_since_epoch = (date_time - epoch).total_seconds()

	return str(int(time_since_epoch))


#######END CONFIG FUNCTIONS#######




########DEBUG FUNCTIONS#######

##Pickling/Unpickling data
def pickle_all_sheet_data(all_sheet_data):
	pickle.dump(all_sheet_data, open('data.pkl', 'wb'))

def unpickle_all_sheet_data():
	all_sheet_data = pickle.load(open('data.pkl', 'rb'))
	return all_sheet_data

########END DEBUG FUNCTIONS#######