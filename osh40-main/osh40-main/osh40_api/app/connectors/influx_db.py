import logging
import pandas as pd
from influxdb_client_3 import InfluxDBClient3
from decouple import config


class InfluxDB(object):
    
    def select(self, query):
        data_df = pd.DataFrame()
        try:
            conn = InfluxDBClient3(host=config('INFLUX_HOST'), org=None, database=config('INFLUX_DATABASE'),
                                   token=config('INFLUX_TOKEN'))
            table = conn.query(query)
            conn.close()
            
            data_df = table.to_pandas()
        except Exception as error:
            logging.error('Error to connect InfluxDB. Details: {}'.format(str(error)))

        return data_df
