import functions as fn

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# from googleapiclient.discovery import build
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request


def main():
	print("working on getting the data")

	client = fn.start_client()
	sheet = fn.get_sheet(client)
	# all_sheet_data = fn.get_all_data(sheet) #comment out lines above for debug

	# all_sheet_data = fn.unpickle_all_sheet_data() #comment in line for debug 

	# headers = sheet.row_values(1)
	# headers_dict = {}
	# for column_name in headers:
	# 	column_index = headers.index(column_name)
	# 	headers_dict[column_name] = column_index
		# print(column_name,column_index)

	# cell_list = []

	# print(all_sheet_data)

	##Updating Sheet testing
	# sheet.update_cell(3,3,test_list)
	
	# test_list = ['this','is','a','test','list','foo','bar']
	# cell_list = sheet.range('A5:G5')

	# for index, cell in enumerate(cell_list):
	# 	print('value: {}\n row: \n column: '.format(cell.value,cell.row,cell.col))

	# for index, cell_value in enumerate(test_list):
	# 	print('value: {}\n row: {}\n column: {}'.format(
	# 		cell_list[index].value,
	# 		cell_list[index].row,
	# 		cell_list[index].col))
	# 	cell_list[index].value = cell_value

	# sheet.update_cells(cell_list)


	##Parser/Maps testing
	fn.walk_sheet_data(sheet)
	# print(sheet.cell(2,1))


	# print(all_sheet_data)



if __name__ == '__main__':
	main()