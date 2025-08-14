"""File with auxiliar functions """
import csv
import os


class UtilFunction(object):
		
		@staticmethod
		def write_to_csv(header, content, filepath, mode='a+'):
				fl_exist = os.path.exists(filepath)
				with open(filepath, mode, newline='') as file:
						writer = csv.writer(file)
						if not fl_exist:
								writer.writerow(header)
						
						writer.writerows(content)
