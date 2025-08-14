"""Class models the structure in the postgres database"""

from time import sleep
from ia_model.connectors.postgres import Postgres
from decouple import config


class PostgresSchema(object):
		def __init__(self, _debug=False):
				self.type_sensors = ['luminosity', 'temperature', 'humidity', 'noise', 'dust', 'ultraviolet']
				self.dataset = config('PG_DATASET_SENSORS')
				self.debug = _debug
		
		def create_structure_database(self):
				ret = False
				if self.__create_structure():
						print("Dataset structure created successfully for sensors_data!")
						ret = True
				
				return ret
		
		def __create_structure(self):
				sql = "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = '{}') AS dataset_exist".format(self.dataset)
				data_df = self.__query(config('PG_DATASET_NAME_DEFAULT'), sql)

				ret = data_df["dataset_exist"][0] if not data_df.empty else False
				if ret:
						print("Dataset '{}' already exists!".format(self.dataset))
				else:
						ret = self.__create_database()
						if ret:
								for schema_name in self.type_sensors:
										ret = self.__create_extension_for_pivot_tables and self.__create_schema(schema_name) and \
													self.__create_type_serie_table(schema_name) and \
													self.__create_sensor_readings_table(schema_name)
										if not ret:
												break
									
				return ret

		def __create_database(self):
				sql = "CREATE DATABASE {};".format(self.dataset)
				ret = self.__execute_command(config('PG_DATASET_NAME_DEFAULT'), sql)
				
				if ret:
					sleep(2)
				
				return ret
		
		def __create_extension_for_pivot_tables(self):
				sql = "CREATE EXTENSION IF NOT EXISTS tablefunc;"
				ret = self.__execute_command(self.dataset, sql)
				
				if ret:
						sleep(2)
				
				return ret
		
		def __create_schema(self, schema_name):
				sql = "CREATE SCHEMA IF NOT EXISTS {};".format(schema_name)
				ret = self.__execute_command(self.dataset, sql)
				
				if ret:
						sleep(2)
				
				return ret

		
		def __create_type_serie_table(self, schema_name):
				sql = """CREATE TABLE IF NOT EXISTS {}.type_serie(
										id BIGSERIAL,
										data_class varchar(10),
										subset_type varchar(10),
										PRIMARY KEY(id));""".format(schema_name)

				ret = self.__execute_command(self.dataset, sql)
				if ret:
						sql = """CREATE INDEX class_subset_type_idx ON {}.type_serie(data_class, subset_type);"""\
								  .format(schema_name)
						ret = self.__execute_command(self.dataset, sql)

				return ret
		
		def __create_sensor_readings_table(self, schema_name):
				sql = """CREATE TABLE IF NOT EXISTS {schema_name}.sensor_readings(
									id BIGSERIAL,
									value numeric(10,2),
									obs varchar(10) NOT NULL DEFAULT '',
									time timestamp,
									type_serie_id bigint,
									CONSTRAINT fk_type_serie_id FOREIGN KEY(type_serie_id)
										REFERENCES {schema_name}.type_serie(id));""".format(schema_name=schema_name)
				
				ret = self.__execute_command(self.dataset, sql)
				
				return ret
		
		def __execute_command(self, dataset_name, sql):
				postgres = self._build_postgres_conn(dataset_name)
				ret = postgres.execute_command(sql)
				if ret and self.debug:
					print("'{}' successfully executed!".format(sql))

				return ret
		
		def __query(self, dataset_name, sql):
				postgres = self._build_postgres_conn(dataset_name)
				data_df = postgres.select(sql)
				
				return data_df
		
		def _build_postgres_conn(self, dataset_name):
				return Postgres(_dataset=dataset_name, _host=config('PG_DATASET_HOST'),
												_port=config('PG_DATASET_PORT'), _user=config('PG_DATASET_USER'),
												_passwd=config('PG_DATASET_PASSWD'))

