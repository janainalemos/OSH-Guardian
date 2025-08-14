"""Class for connection influx db"""
import influxdb_client
import pandas as pd

from decouple import config


class InfluxdbCon(object):
		def __init__(self, _debug=False):
				self.degub = _debug
				self.url_conn = "{}:{}".format(config('IFX_DATASET_HOST'), config('IFX_DATASET_PORT'))
				self.user = config('IFX_DATASET_USER')
				self.passwd = config('IFX_DATASET_PASSWD')
		
		def execute_command(self, cmd_sql):
				ret = True
				try:
						self.client_influxdb = influxdb_client.InfluxDBClient(url=self.url_conn, username=self.user,
																																	password=self.passwd)
						self.client_influxdb.write_api(cmd_sql)
						self.client_influxdb.close()
				except Exception as e:
						ret = False
						print("Failed to execute command {}. Details: {}.".format(str(cmd_sql), str(e)))
				
				return ret

		def select_data(self, query_sql):
				data_df = pd.DataFrame()
				try:
						self.client_influxdb = influxdb_client.InfluxDBClient(url=self.url_conn, username=self.user,
																																	password=self.passwd)
						data_df = self.client_influxdb.query_api().query_data_frame(query=query_sql)
						self.client_influxdb.close()
				except Exception as e:
						print("Failed to select data query {}. Details: {}.".format(str(query_sql), str(e)))

				return data_df

