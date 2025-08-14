from osh40_api.app.settings.load_settings import influxdb, ia_models


class WorkerStatus(object):
		def __init__(self, _worker_ids, _period, _type_sensor):
				self.worker_ids = _worker_ids.split(',')
				self.period = _period if _period is None else _period.split(',')
				self.type_sensor = _type_sensor if _type_sensor is None else _type_sensor.split(',')

		def get_status_env(self):
				response = None
				
				read_sensors = self.__get_last_six_reads()
				if read_sensors:
						response = self.__predict_status(read_sensors)
				
				return response

		def __get_last_six_reads(self):
				data_df = influxdb.select("SELECT * FROM OSH WHERE topic = '6066/noise' order by time desc limit 6")
				print(data_df)
				# For all sensors, get six last reads from influxdb
				# and return json
				# Exemplo de retorno do influxdb:
				# vanessa @ vanessa - Inspiron - 7472: ~$ curl - G
				# http: // osh40.com: 8086 / query - u
				# readosh: readosh - -data - urlencode
				# "db=telegraf" - -data - urlencode
				# "q=SELECT * FROM OSH WHERE topic = 6066*/ order by time limit 6"
				# {"results":
        #    [{"statement_id": 0, "series": [
				# 		{"name": "OSH", "columns": ["time", "host", "topic", "user", "value"],
				# 		 "values": [["2023-05-05T20:09:41.270601589Z", "solvinghealth.digital", "6066/noise", "telegraf", 87],
				# 								["2023-05-05T20:09:41.310156929Z", "solvinghealth.digital", "6066/light", "telegraf", 5],
				# 								["2023-05-05T20:09:41.310200193Z", "solvinghealth.digital", "6066/dust", "telegraf", 33343],
				# 								["2023-05-05T20:09:41.310233238Z", "solvinghealth.digital", "6066/uv", "telegraf", 1.4],
				# 								["2023-05-05T20:09:41.31027292Z", "solvinghealth.digital", "6066/temperature", "telegraf",
				# 								 15.9], ["2023-05-05T20:09:41.310307615Z", "solvinghealth.digital", "6066/humidity", "telegraf",
				# 												 77]]}]}]}
				#
				#  curl -G http://osh40.com:8086/query -u readosh:readosh --data-urlencode "db=telegraf" --data-urlencode "q=SELECT * FROM OSH WHERE topic = '6066/noise' order by time desc limit 6"
				# {"results": [{"statement_id": 0, "series": [
				# 		{"name": "OSH", "columns": ["time", "host", "topic", "user", "value"],
				# 		 "values": [["2024-02-04T17:41:34.563431814Z", "solvinghealth.digital", "6066/noise", "telegraf", 89],
				# 								["2024-02-04T17:31:34.462107612Z", "solvinghealth.digital", "6066/noise", "telegraf", 86],
				# 								["2024-02-04T17:21:34.363274155Z", "solvinghealth.digital", "6066/noise", "telegraf", 90],
				# 								["2024-02-04T17:11:34.262398008Z", "solvinghealth.digital", "6066/noise", "telegraf", 86],
				# 								["2024-02-04T17:01:34.161216848Z", "solvinghealth.digital", "6066/noise", "telegraf", 90],
				# 								["2024-02-04T16:51:34.060750233Z", "solvinghealth.digital", "6066/noise", "telegraf", 85]]}]}]}
				
				return {'dust_sensor': [], 'hum_tmp_sensor': [], 'light_sensor': [], 'noise_sensor': [], 'uv_sensor': []}

		@staticmethod
		def __predict_status(read_sensors):
				return {'worker_status': ia_models.predict_status(read_sensors)}