"""Class implement connector for Postgres Database"""

import psycopg2
import psycopg2.extras
import pandas as pd


class Postgres(object):
		def __init__(self, _dataset, _host, _port, _user, _passwd):
				self.dataset = _dataset
				self.host = _host
				self.port = _port
				self.user = _user
				self.passwd = _passwd
		
		def execute_command(self, sql):
				ret = True
				try:
						conn = self.__get_dataset_connector()
						conn.autocommit = True
						conn_cursor = conn.cursor()
						conn_cursor.execute(sql)
						conn_cursor.close()
						conn.close()
				except(Exception, psycopg2.Error) as error:
						ret = False
						print("Failed execute command {}. Details: {}.".format(sql, str(error)))
				
				return ret
		
		def insert(self, sql_command_txt, sql_command, values):
				ret = None
				try:
						conn = self.__get_dataset_connector()
						conn_cursor = conn.cursor()
						conn_cursor.execute(sql_command, values)
						ret = conn_cursor.fetchall()
						conn.commit()
						conn_cursor.close()
						conn.close()
				# count = self.conn_cursor.rowcount
				# print(count, "Record inserted successfully!")
				except(Exception, psycopg2.Error) as error:
						print("Failed to attempt to insert record {}. Details: {}".format(sql_command_txt, str(error)))
		
				return ret
		
		def insert_batch(self, sql_insert, list_values, page_size):
				ret = True
				try:
						conn = self.__get_dataset_connector()
						conn_cursor = conn.cursor()
						psycopg2.extras.execute_batch(conn_cursor, sql_insert, list_values, page_size=page_size)
						conn.commit()
						conn_cursor.close()
						conn.close()
				except(Exception, psycopg2.Error) as error:
						ret = False
						print("Failed to try to insert batch {}. Page size: {}. Details: {}".format(sql_insert, str(page_size),
																																												str(error)))

				return ret

		def select(self, sql_command):
				data_df = pd.DataFrame()
				
				try:
						# self.conn_cursor.execute(sql_command, values)
						# return self.conn_cursor.fetchall()
						conn = self.__get_dataset_connector()
						data_df = pd.read_sql_query(sql_command, conn)
						conn.close()
				except(Exception, psycopg2.Error) as error:
						print("Failed to attempt to insert record {}. Details: {}.".format(sql_command, str(error)))
						
				return data_df
		
		def __get_dataset_connector(self):
				return psycopg2.connect(database=self.dataset, host=self.host, port=self.port,
																user=self.user, password=self.passwd)
