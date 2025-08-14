import numpy as np
from ia_model.xboost_model import XboostModel
from ia_model.classifier_models import ClassifierModels


class ModelTests(object):
		
		def __init__(self, _dataset_path, _dir_results, _kfolds):
				self.dataset_path = _dataset_path
				self.dir_results = _dir_results
				self.kfolds = _kfolds
				
		def build_model_tests(self):
				train_arr, test_arr = self.__load_datasets()
				test_x, test_y = test_arr[:, :-1], test_arr[:, -1]
		
				# train and evaluate validation model
				xboost_m = XboostModel(self.dir_results, _model_obj='binary:logistic', _model_estimators=100,
															 _kfolds=self.kfolds)
				xboost_m.train_test_models(train_arr)
				xboost_m.load_and_test_final_models(test_x, test_y)
				
				# train and evaluate validation other models
				cl_models = ClassifierModels(_kfolds=self.kfolds, _directory=self.dir_results)
				cl_models.train_test_models(train_arr)
				cl_models.load_and_test_final_models(test_x, test_y)
		
		def __load_datasets(self):
				train_arr = np.load('{}_{}.npy'.format(self.dataset_path, 'train'), allow_pickle=True)
				valid_arr = np.load('{}_{}.npy'.format(self.dataset_path, 'valid'), allow_pickle=True)
				print("Train Len: {}".format(train_arr.shape))
				print("Valid Len: {}".format(valid_arr.shape))
				
				train_arr = np.concatenate((train_arr, valid_arr))
				print("Train+Valid Len: {}".format(train_arr.shape))
				
				test_arr = np.load('{}_{}.npy'.format(self.dataset_path, 'test'), allow_pickle=True)

				return train_arr, test_arr
