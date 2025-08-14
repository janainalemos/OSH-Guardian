import pickle
import numpy as np
from decouple import config


class LoadModels(object):
		PREDICTOR_CLASSES = {0: 'Normal', 1: 'RISK'}
		SENSORS = ['dust', 'hum_tmp', 'light', 'noise', 'uv']
		MODELS = ['RandomForestClassifier_model_3.pkl', 'RandomForestClassifier_model_5.pkl',
							'RandomForestClassifier_model_3.pkl', 'RandomForestClassifier_model_3.pkl',
							'RandomForestClassifier_model_3.pkl']

		def __init__(self):
				self.models = self.__load_models()

		def predict_status(self, sensor_reads):
				response = dict()
				for sensor_model in self.SENSORS:
						y_hat = self.models.get(sensor_model).predict(np.asarray([sensor_reads.get(sensor_model)]))[0]
						response.update({sensor_model: self.PREDICTOR_CLASSES.get(y_hat)})
				
				return response
		
		def __load_models(self):
				models_dct = dict()
				for idx, sensor_model in enumerate(self.SENSORS):
						model = pickle.load(open("{}/{}/{}".format(config('PATH_MODELS'), sensor_model, self.MODELS[idx]), "rb"))
						models_dct.update({sensor_model: model})
				
				return models_dct
