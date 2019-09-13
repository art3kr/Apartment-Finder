def get_fees(soup, fields):
	"""Given a beautifulSoup parsed page, extract the rent and deposit fees"""

	fields['rent'] = ''
	fields['deposit'] = ''

	#get rent fee
	obj = soup.find('td', class_='rent')
	if obj is not None:
		rent = obj.getText()
		rent = prettify_text(rent)
		rent = rent.replace('$','')
		rent = rent.replace(',','')
		fields['rent'] = rent

	#get deposit fee
	obj = soup.find('td', class_='deposit')
	if obj is not None:
		deposit = obj.getText()
		deposit = prettify_text(deposit)
		deposit = deposit.replace('$','')
		deposit = deposit.replace(',','')
		fields['deposit'] = deposit

def get_property_size(soup, fields):

	fields['size'] = ''
	obj = soup.find('td', class_='sqft')
	if obj is not None:
		size = obj.getText()
		size = prettify_text(size)
		size = size.replace(' Sq Ft','')
		size = size.replace(',','')
		fields['size'] = size
