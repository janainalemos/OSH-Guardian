""" Class to simulate data sensors read """

import random
from itertools import permutations
from random import randint
from random import uniform


class DataGenerator(object):
		def __init__(self, total_read_light=2):
				self.noise = 0
				self.light = 0
				self.dust = 0
				self.uv = 0
				self.temperature = 0
				self.humidity = 0
				self.gas = 0
				self.scenario_by_sensor = dict({
						'noise': {'normal': {'less_or_equal': 84}, 'risk': {'greater_or_equal': 85}},
						'light': self.__range_ligth_generator(total_read_light),
						'dust': {'normal': {'min_value': 0, 'max_value': 999999},
										 'risk': {'min_value': 1000000, 'max_value': 28000000}},
						'uv': {'normal': {'less_or_equal': 0.5}, 'risk': {'greater': 0.5}},
						'gas': None,
						'humidity_temperature':	{'risk': {'summer': {'11': {'temp': [20, 21], 'hum': [68, 71]},
																												 '12': {'temp': [22, 24], 'hum': [64, 67]},
																												 '13': {'temp': [25, 26], 'hum': [60, 63]},
																												 '14': {'temp': [27, 29], 'hum': [56, 59]},
																												 '15': {'temp': [30, 31], 'hum': [52, 55]},
																												 '16': {'temp': [32, 34], 'hum': [48, 51]},
																												 '17': {'temp': [35, 36], 'hum': [44, 47]},
																												 '18': {'temp': [37, 38], 'hum': [40, 43]},
																												 '19': {'temp': [39, 41], 'hum': [36, 39]},
																												 '20': {'temp': [42, 44], 'hum': [32, 35]},
																												 '21': {'temp': [43, 45], 'hum': [28, 31]},
																												 'other_hours': {'temp': [25, 26], 'hum': [49, 51]}},
																							'winter': {'11': {'temp': [6, 9], 'hum': [86, 90]},
																												 '12': {'temp': [6, 9], 'hum': [85, 89]},
																												 '13': {'temp': [7, 9], 'hum': [84, 88]},
																												 '14': {'temp': [8, 10], 'hum': [83, 87]},
																												 '15': {'temp': [9, 13], 'hum': [80, 84]},
																												 '16': {'temp': [11, 16], 'hum': [79, 82]},
																												 '17': {'temp': [12, 18], 'hum': [78, 81]},
																												 '18': {'temp': [13, 18], 'hum': [77, 80]},
																												 '19': {'temp': [14, 19], 'hum': [76, 79]},
																												 '20': {'temp': [12, 17], 'hum': [75, 78]},
																												 '21': {'temp': [11, 15], 'hum': [73, 77]}}},
																												 'other_hours': {'temp': [8, 11], 'hum': [82, 85]},
																		 'normal': {'summer': {'11': {'temp': [18, 20], 'hum': [68, 70]},
																													 '12': {'temp': [19, 22], 'hum': [66, 68]},
																													 '13': {'temp': [21, 23], 'hum': [63, 65]},
																													 '14': {'temp': [22, 24], 'hum': [61, 63]},
																													 '15': {'temp': [25, 26], 'hum': [60, 62]},
																													 '16': {'temp': [26, 27], 'hum': [57, 59]},
																													 '17': {'temp': [27, 28], 'hum': [55, 57]},
																													 '18': {'temp': [27, 28], 'hum': [53, 54]},
																													 '19': {'temp': [28, 29], 'hum': [51, 53]},
																													 '20': {'temp': [29, 30], 'hum': [50, 52]},
																													 '21': {'temp': [29, 30], 'hum': [50, 52]},
																													 'other_hours': {'temp': [20, 22], 'hum': [50, 51]}},
																								'winter': {'11': {'temp': [10, 12], 'hum': [69, 70]},
																													 '12': {'temp': [10, 13], 'hum': [68, 70]},
																													 '13': {'temp': [11, 14], 'hum': [67, 69]},
																													 '14': {'temp': [12, 15], 'hum': [66, 68]},
																													 '15': {'temp': [15, 17], 'hum': [64, 67]},
																													 '16': {'temp': [16, 18], 'hum': [63, 66]},
																													 '17': {'temp': [16, 19], 'hum': [60, 62]},
																													 '18': {'temp': [17, 19], 'hum': [59, 61]},
																													 '19': {'temp': [15, 17], 'hum': [58, 60]},
																													 '20': {'temp': [14, 16], 'hum': [57, 59]},
																													 '21': {'temp': [13, 15], 'hum': [57, 59]}}}}})
				
		def noise_sensor(self, behavior='normal'):
				range_sensor = self.scenario_by_sensor.get('noise')
				if behavior == 'normal':
						self.noise = randint(0, range_sensor.get('normal').get('less_or_equal'))
				else:
						self.noise = randint(range_sensor.get('risk').get('greater_or_equal'), 90)
				
				return self.noise
		
		def light_sensor(self, behavior='normal', ):
				self.light = list(random.sample(self.scenario_by_sensor.get('light').get(behavior), 1)[0])
				
				return self.light
		
		def dust_sensor(self, behavior='normal'):
				range_sensor = self.scenario_by_sensor.get('dust')
				self.dust = randint(range_sensor.get(behavior).get('min_value'),
														range_sensor.get(behavior).get('max_value'))
				
				return self.dust
				
		def uv_sensor(self, behavior='normal'):
				range_sensor = self.scenario_by_sensor.get('uv')
				if behavior == 'normal':
						self.uv = uniform(0, range_sensor.get('normal').get('less_or_equal'))
				else:
						self.uv = uniform(range_sensor.get('risk').get('greater'), 1.6)
				
				self.uv = round(self.uv, 1)
				return self.uv
		
		def humidity_temperature_sensor(self, hour, season, behavior='normal'):
				range_sensor = self.scenario_by_sensor.get('humidity_temperature')
				if hour in range_sensor.get(behavior).get(season).keys():
						rule_sensor = range_sensor.get(behavior).get(season).get(hour)
				else:
						rule_sensor = range_sensor.get(behavior).get(season).get('other_hours')
						
				self.temperature = uniform(rule_sensor.get('temp')[0], rule_sensor.get('temp')[1])
				self.temperature = round(self.temperature, 1)
				self.humidity = randint(rule_sensor.get('hum')[0], rule_sensor.get('hum')[1])
				
				return self.temperature, self.humidity
		
		def gas_sensor(self):
				return self.gas

		@staticmethod
		def __range_ligth_generator(total_read):
				accept_values = list(range(1,6))
				permut_values = permutations(accept_values, total_read)

				risk_values = []
				normal_values = []
				for par in permut_values:
						if abs(par[0] - par[1]) > 2:
								risk_values.append(par)
						else:
								normal_values.append(par)

				return {'normal': normal_values, 'risk': risk_values}

