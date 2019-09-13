# Apartment-Finder
Scrape Apartments.com with BeautifulSoup, find use Google Distance Matrix/Places/Geocode APIs to get commute info

1. Backend for data is Google Sheets (using gspread python library to access, push data). 
  Links, info scraped from Apartments.com, and info retreived from Google APIs is stored here
  
2. Given an apartments.com url, uses BeautifulSoup to scrape rent info, beds, baths, address, lease length, and more.
3. Given an address, uses Google's Distance Matrix Api to find commute times to work in morning and afternoon
4. Given an address, uses Google's Places Api to find nearest metro stop, and Distance Matrix to find commute time to metro by walking. 
5. You'll need a Google API key an developer account to access Sheets API, and the Maps APIs
