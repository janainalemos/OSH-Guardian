"""
This code simulates three monitoring devices - 6066, 6067, 6068

The objective of the simulation is to feed the server without the need to keep the prototype working uninterruptedly
and to provide data for AI training.
Data referring to each sensor is generated every ten minutes and published through the MQTT protocol.
In temperature and humidity there is little variation in the values to maintain consistency with reality.
Gas must not be considered in AI and is always set to zero.
"""

from datetime import datetime as dt
import time
from utils.sensor import Sensor


def ligth_value_handler(ctrl_lvalue, ligth_value):
		if ctrl_lvalue == 1:
				ctrl_ligth_value = 0
				
				# Please consider number of devices added in sensor
				ligth_value = [None,None,None]
		else:
				ctrl_ligth_value = ctrl_lvalue + 1
		
		return ctrl_ligth_value, ligth_value
		

def run_simulation():
		sensor = Sensor(debug=True)
		
		# Please consider number of devices added in sensor
		ligth_value = [None, None, None]
		ctrl_lvalue = 0

		while True:
				# Publishes data between 8 a.m and 6 p.m in UTC-3
				if dt.now().hour in range(11, 21, 1):				
						ligth_value = sensor.publish_message(ligth_value)
						ctrl_lvalue, ligth_value = ligth_value_handler(ctrl_lvalue, ligth_value)
				
				# Sleeps for 10 minutes
				time.sleep(600)
				
				#test
				##time.sleep(150)


if __name__ == '__main__':
		run_simulation()

	




