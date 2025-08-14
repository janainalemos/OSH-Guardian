"""Class dedicated at preprocess dataset for IA model train"""
import pandas as pd
import numpy as np
from ia_model.connectors.postgres import Postgres
from decouple import config


class PreprocessData(object):
	
		def generate_dataset(self, dataset_src, dataset_dst, sensor, subset_type='train', ds_format='full_date_value'):
				pg_con = Postgres(_dataset=dataset_src, _host=config('PG_DATASET_HOST'), _port=config('PG_DATASET_PORT'),
													_user=config('PG_DATASET_USER'), _passwd=config('PG_DATASET_PASSWD'))
				
				sql = """SELECT {col_names} FROM {sensor}.sensor_readings sr
								 JOIN {sensor}.type_serie ts ON ts.id = sr.type_serie_id
								 WHERE ts.subset_type = '{subset_type}'
								 ORDER BY ts.id, sr."time",
								 ts.data_class, ts.subset_type""".format(sensor=sensor, col_names=self.__columns_dataset(ds_format),
																												 subset_type=subset_type)
				
				data_df = pg_con.select(sql)
				
				if not data_df.empty:
						data_npy = self.__preprocess_dataset_to_numpy(data_df)
						self.save_dataset_to_numpy(data_npy, dataset_dst)
						self.save_dataset_to_pandas(data_df, dataset_dst)
		
		def generate_hum_tmp_dataset(self, dataset_src, dataset_dst, schemas, subset_type='train', only_array=True):
				pg_con = Postgres(_dataset=dataset_src, _host=config('PG_DATASET_HOST'), _port=config('PG_DATASET_PORT'),
													_user=config('PG_DATASET_USER'), _passwd=config('PG_DATASET_PASSWD'))
				
				data_lst = []
				for schema in schemas:
						data_lst.append(
								pg_con.select("""SELECT ts.id, ts.subset_type AS {schema}_subset_type, sr.value AS {schema}_value,
																 CASE WHEN ts.data_class = 'risk' THEN 1 ELSE 0 END AS {schema}_class
																 FROM {schema}.sensor_readings sr
																 JOIN {schema}.type_serie ts ON ts.id = sr.type_serie_id
																 WHERE ts.subset_type = '{subset_type}'
																 ORDER BY ts.id, sr."time",
																 ts.data_class, ts.subset_type""".format(schema=schema, subset_type=subset_type))
						)
			
				if len(data_lst) == 2:
						df_hum = data_lst[0].sort_values('id')
						df_tmp = data_lst[1].sort_values('id')
						
						df_hum.insert(df_hum.columns.__len__(), 'temperature_value', None)
						data_df = df_hum.set_index("id")
						df_tmp = df_tmp.set_index("id")
						data_df.loc[:, 'temperature_value'] = df_tmp.temperature_value
						data_df = data_df.reset_index()
						
						data_npy = self.__preprocess_dataset_to_numpy(data_df, drop_columns=['id', 'humidity_subset_type'],
																													total_values=3, only_array=only_array)
						self.save_dataset_to_numpy(data_npy, dataset_dst)
						self.save_dataset_to_pandas(data_df, dataset_dst)
		
		def __columns_dataset(self, dataset_fmt):
				if dataset_fmt == 'month_value':
						col_names = "ts.id, to_char(sr.time, 'MM')::integer as dt_month, ts.subset_type, sr.value, ts.data_class"
				elif dataset_fmt == 'month_hour_value':
						col_names = "ts.id, to_char(sr.time, 'MM')::integer as dt_month," \
												"to_char(sr.time, 'HH')::integer as dt_hour, ts.subset_type, sr.value, ts.data_class"
				elif dataset_fmt == 'month_day_hour_value':
						col_names = "ts.id, to_char(sr.time, 'MM')::integer as dt_month, " \
												"to_char(sr.time, 'DD')::integer as dt_day, to_char(sr.time, 'HH')::integer as dt_hour," \
												"ts.subset_type, sr.value, ts.data_class"
				elif dataset_fmt == 'only_values':
						col_names = "ts.id, ts.subset_type, sr.value, " \
												"CASE WHEN ts.data_class = 'risk' THEN 1 ELSE 0 END AS data_class"
				else: #'full_date_value':
						col_names = "ts.id, to_char(sr.time, 'YYYY.DD.MM.HH.MI') as dt_str, ts.subset_type, sr.value, ts.data_class"
				
				return col_names

		@staticmethod
		def save_dataset_to_pandas(data_df, name_dataset):
				data_df.to_pickle("{}/datasets/{}.pkl".format(config('ROOT_PATH'), name_dataset))
		
		@staticmethod
		def load_dataset_to_pandas(name_dataset):
				return pd.read_pickle("{}/datasets/{}.pkl".format(config('ROOT_PATH'), name_dataset))
		
		@staticmethod
		def save_dataset_to_numpy(data_npy, name_dataset):
				with open("{}/datasets/{}.npy".format(config('ROOT_PATH'), name_dataset.format(name_dataset)), 'wb') as f:
						np.save(f, data_npy)
		
		@staticmethod
		def load_dataset_to_numpy(name_dataset):
				with open("{}/datasets/{}.npy".format(config('ROOT_PATH'), name_dataset.format(name_dataset)), 'rb') as f:
						data_npy = np.load(f, allow_pickle=True)
				return data_npy
		
		"""Option only generate dataset in the 'full_date_value' format"""
		@staticmethod
		def __preprocess_dataset_rows(data_df):
				type_series_ids = data_df['id'].unique()
				time_cols = ['time_' + str(n) for n in range(1, 7)]
				value_cols = ['value_' + str(n) for n in range(1, 7)]
				name_cols = np.concatenate((time_cols, value_cols, ['y']), axis=0)
				
				data_lst = []
				for type_series_id in type_series_ids:
						aux_df = data_df[['dt_str', 'value', 'data_class']][data_df.id == type_series_id].T
						data_lst.append(pd.DataFrame([np.concatenate((aux_df.values[0], aux_df.values[1],
																													[aux_df.values[2][0]]), axis=0)], columns=name_cols))
				
				return pd.concat(data_lst)
		
		@staticmethod
		def __preprocess_dataset_to_numpy(data_df, drop_columns=['id', 'subset_type'], only_array=True, total_values=2):
				type_series_ids = data_df['id'].unique()
				
				data_np = []
				for type_series_id in type_series_ids:
						aux_df = data_df[data_df.id == type_series_id]
						aux_df = aux_df.drop(columns=drop_columns)
						final_value = aux_df.T.to_numpy()
						if total_values == 2:
								data_np.append(np.append(final_value[0], final_value[1][0]))
						else:
								hum = final_value[0]
								tmp = final_value[2]
								y = final_value[1][0]
								if only_array:
									data_np.append(np.append([[hum[idx], tmp[idx]] for idx in range(0, len(hum))], [y]))
								else:
									data_np.append(np.append(np.append(hum, tmp), [y]))
				
				return np.array(data_np)

