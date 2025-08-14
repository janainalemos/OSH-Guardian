"""Class to simulate sensors reading"""
import paho.mqtt.client as mqtt
import random
from datetime import datetime as dt
from utils.data_generator import DataGenerator


class Sensor(object):
		def __init__(self, host="localhost", port=1883, total_devices=3, debug=False):
				self.debug = True
				self.total_devices = total_devices

				self.client = mqtt.Client()
				self.client.on_publish = self.__on_publish
				self.client.connect(host, port, keepalive=43200)

		def publish_message(self, light_value=[None, None, None]):
				# MQTT topics (first simulated device)
				topic_noise = "6066/noise"
				topic_light = "6066/light"
				topic_dust = "6066/dust"
				topic_uv = "6066/uv"
				topic_temp = "6066/temperature"
				topic_hum = "6066/humidity"
				topic_gas = "6066/gas"

				# Deals with ASCII to get MQTT topics for all devices, from 6066 to 6068
				# To add more devices, just adjust the loop
				for i in range(self.total_devices):
						n = ord('6') + i
						ch = chr(n)

						topic_noise = topic_noise[:3] + ch + topic_noise[4:]
						topic_light = topic_light[:3] + ch + topic_light[4:]
						topic_dust = topic_dust[:3] + ch + topic_dust[4:]
						topic_uv = topic_uv[:3] + ch + topic_uv[4:]
						topic_temp = topic_temp[:3] + ch + topic_temp[4:]
						topic_hum = topic_hum[:3] + ch + topic_hum[4:]
						topic_gas = topic_gas[:3] + ch + topic_gas[4:]

						# i indicates the device index
						sensor_reading = self.__generate_data(i, light_value[i])

						# Publishes
						self.client.publish(topic_noise, sensor_reading.get('noise'))

						# create logical to ligth sequence read according to test scenario
						if light_value[i] is None:
								self.client.publish(topic_light, str(sensor_reading.get('light')[0]))
								light_value[i] = str(sensor_reading.get('light')[1])
						else:
								self.client.publish(topic_light, light_value[i])

						self.client.publish(topic_dust, sensor_reading.get('dust'))
						self.client.publish(topic_uv, sensor_reading.get('uv'))
						self.client.publish(topic_temp, sensor_reading.get('temp'))
						self.client.publish(topic_hum, sensor_reading.get('hum'))
						self.client.publish(topic_gas, sensor_reading.get('gas'))
										
				return light_value

		def __on_publish(self, client, userdata, result):
				print("Data published msg id {}".format(result))

		# Generates data random data inside and outside the limits given by legislation
		def __generate_data(self, device_index, light_value):
				behavior = ['normal', 'risk']
				data_gen = DataGenerator()

				# Dust is very different for each worker
				if device_index in [0, 1]:  # device 6066
						dust = data_gen.dust_sensor(behavior='normal')
						# Temperature increases and humidity decreases depending on the time of day
						temp, hum = data_gen.humidity_temperature_sensor(hour=str(dt.now().hour),
																														 season='summer',
																														 behavior='risk')
						light = data_gen.light_sensor(behavior='risk') if light_value is None else light_value
						uv = str(data_gen.uv_sensor(behavior='risk'))

				else:  # device_index == 2 --> device 6068
						if dt.now().hour >= 16:
								dust = data_gen.dust_sensor(behavior='risk')
						else:
								dust = data_gen.dust_sensor(behavior='normal')

						temp, hum = data_gen.humidity_temperature_sensor(hour=str(dt.now().hour),
																														 season='summer',
																														 behavior='normal')
						light = data_gen.light_sensor(behavior='normal') if light_value is None else light_value
						uv = str(data_gen.uv_sensor(behavior='risk'))

				sensor_reading = dict({'light': light,
															 'uv': str(uv),
															 'noise': str(data_gen.noise_sensor(behavior=random.sample(behavior, 1))),
															 'dust': str(dust),
															 'temp': str(temp),
															 'hum': str(hum),
															 'gas': str(data_gen.gas_sensor())})

				if self.debug:
						print("Device Index: {}, Sensors: {}".format(device_index, sensor_reading))

				return sensor_reading

