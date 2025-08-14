"""Class responsible for creating the database structure and populating it with data simulation for training
	 the AI models. """


import copy
from ia_model.migrations.postgres_schema import PostgresSchema
from ia_model.connectors.postgres import Postgres
from utils.data_generator import DataGenerator
from decouple import config
from datetime import timedelta



class DatasetIA(object):
		DATA_CLASS = ['risk', 'normal']
		PAGE_BATCH_INSERT = 10000
		DATA_PAGE_LEN = 1000
		TOTAL_READ_BY_HOUR = 6
		TOTAL_READ_BY_DAY = 9
		TOTAL_DAYS = 60
		
		def __init__(self, _start_timestamp, _season, _debug=False):
				self.start_timestamp = _start_timestamp
				self.subset_types = ['train', 'test', 'valid']
				self.season = _season
				self.debug = _debug

		def data_generate(self):
				print("Start to create dataset strutucture for train IA models...")
				pg_schema = PostgresSchema(self.debug)
				
				if pg_schema.create_structure_database():
						self.__generate_data_simulation()
				
				print("Finished to create dataset strutucture for train IA models...")
				
		def __generate_data_simulation(self):
				pg_con = Postgres(_dataset=config('PG_DATASET_SENSORS'), _host=config('PG_DATASET_HOST'),
													_port=config('PG_DATASET_PORT'), _user=config('PG_DATASET_USER'),
													_passwd=config('PG_DATASET_PASSWD'))
				
				for subset in self.subset_types: #train/test/valid
						for class_data in self.DATA_CLASS: #risk/normal
								sensors_dct = {'luminosity': [], 'temperature': [], 'humidity': [], 'noise': [], 'dust': [],
															 'ultraviolet': []}
								for day in range(0, self.TOTAL_DAYS):
										ini_date = self.start_timestamp + timedelta(days=day)
										
										sensors_dct = self.__build_one_type_serie_data(ini_date, pg_con, subset, class_data, sensors_dct)
		
										# Insert in batch each 30 days by transaction postgres
										if ((day) % 30) == 0:
												self.__insert_simulation_data(pg_con, sensors_dct)
												sensors_dct = {'luminosity': [], 'temperature': [], 'humidity': [], 'noise': [], 'dust': [],
																			 'ultraviolet': []}
				
								self.__insert_simulation_data(pg_con, sensors_dct)
		
		def __insert_new_type_serie(self, pg_con, subset, class_data, sensors_dct):
				sensor_lst = sensors_dct.keys()
				type_serie_dct = dict()
				for sensor_data in sensor_lst:
						sql_txt = """INSERT INTO {}.type_serie (data_class, subset_type) VALUES ('{}', '{}') RETURNING id;"""\
											.format(sensor_data, class_data, subset)
						
						sql = """INSERT INTO {}.type_serie (data_class, subset_type) VALUES (%s, %s) RETURNING id;"""\
									.format(sensor_data)
						type_serie_id = pg_con.insert(sql_txt, sql, (class_data, subset))
						type_serie_dct.update({sensor_data: type_serie_id[0][0]})
				
				return type_serie_dct
				
		def __insert_simulation_data(self, pg_con, sensors_dct):
				sensor_lst = sensors_dct.keys()
				for sensor_data in sensor_lst:
						sql = '''INSERT INTO {}.sensor_readings (type_serie_id, value, obs, time)
										 VALUES (%(type_serie_id)s, %(value)s, %(obs)s, %(time)s);'''.format(sensor_data)
						
						_ = pg_con.insert_batch(sql, sensors_dct.get(sensor_data), self.DATA_PAGE_LEN)
				
		def __build_one_type_serie_data(self, ini_date, pg_con, subset, class_data, sensors_dct):
				data_gen = DataGenerator(5)
				for num_read in range(0, self.TOTAL_READ_BY_DAY):
						type_serie_dct = self.__insert_new_type_serie(pg_con, subset, class_data, sensors_dct)
						self.__print_msg('Generate new type serie: {}'.format(type_serie_dct))
						
						# 'luminosity':
						sensors_dct.update({'luminosity': sensors_dct.get('luminosity') +
																							self.__read_hour_luminosity(ini_date, type_serie_dct.get('luminosity'),
																																					data_gen, class_data)})
						
						# temperature, humidity, dust, noise, ultraviolet:
						temp, hum, dust, noise, uv = self.__read_other_sensors(ini_date, type_serie_dct, data_gen, class_data)
						sensors_dct.update({'temperature': sensors_dct.get('temperature') + temp})
						sensors_dct.update({'humidity': sensors_dct.get('humidity') + hum})
						sensors_dct.update({'dust': sensors_dct.get('dust') + dust})
						sensors_dct.update({'noise': sensors_dct.get('noise') + noise})
						sensors_dct.update({'ultraviolet': sensors_dct.get('ultraviolet') + uv})
						
						ini_date = ini_date + timedelta(hours=1)
				
				return sensors_dct

		def __print_msg(self, message):
				if self.debug:
						print(message)

		def __read_other_sensors(self, ini_date, type_serie_dct, data_generator, behavior):
				start_date = copy.copy(ini_date)
				temp_lst, hum_lst, dust_lst, noise_lst, uv_lst = [], [], [], [], []
				for read_hour in range(0, self.TOTAL_READ_BY_HOUR):
						temp, hum = data_generator.humidity_temperature_sensor(str(start_date.hour), season=self.season,
																																	 behavior=behavior)
				
						temp_lst.append({'type_serie_id': type_serie_dct.get('temperature'), 'value': temp, 'obs': self.season,
														 'time': start_date.strftime('%d-%m-%Y %H:%M:%S')})
						
						hum_lst.append({'type_serie_id': type_serie_dct.get('humidity'), 'value': hum, 'obs': self.season,
														'time': start_date.strftime('%d-%m-%Y %H:%M:%S')})
						
						dust_lst.append({'type_serie_id': type_serie_dct.get('dust'),
														 'value': data_generator.dust_sensor(behavior=behavior), 'obs': '',
														 'time': start_date.strftime('%d-%m-%Y %H:%M:%S')})
						
						noise_lst.append({'type_serie_id': type_serie_dct.get('noise'),
															'value': data_generator.noise_sensor(behavior=behavior), 'obs': '',
														  'time': start_date.strftime('%d-%m-%Y %H:%M:%S')})
						
						uv_lst.append({'type_serie_id': type_serie_dct.get('ultraviolet'),
													 'value': data_generator.uv_sensor(behavior=behavior), 'obs': '',
													 'time': start_date.strftime('%d-%m-%Y %H:%M:%S')})
						
						start_date = start_date + timedelta(minutes=10)
						
				return temp_lst, hum_lst, dust_lst, noise_lst, uv_lst


		@staticmethod
		def __read_hour_luminosity(ini_date, type_serie_id, data_generator, behavior):
				start_date = copy.copy(ini_date)
				value_lst = data_generator.light_sensor(behavior)
				data_read_lst = []
				for value in value_lst:
						data_read_lst.append({'type_serie_id': type_serie_id, 'value': value, 'obs': '',
																	'time': start_date.strftime('%d-%m-%Y %H:%M:%S')})
						
						start_date = start_date + timedelta(minutes=10)
				
				# Permutação é com 5 valores, repete o último para fechar 6 leituras/hora
				data_read_lst.append({'type_serie_id': type_serie_id, 'value': value, 'obs': '',
															'time': start_date.strftime('%d-%m-%Y %H:%M:%S')})
				
				return data_read_lst