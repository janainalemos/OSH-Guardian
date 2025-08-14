from sklearn.metrics import mean_absolute_error
from xgboost import XGBClassifier, plot_tree
from utils.metrics import Metrics
from utils.util_function import UtilFunction
import numpy as np
import pickle
import copy
import glob


class XboostModel(object):
		def __init__(self, _directory, _model_obj, _model_estimators, _kfolds, _verbose=True):
				self.directory = _directory
				self.model_estimators = _model_estimators
				self.model_obj = _model_obj
				self.kfolds = _kfolds
				self.verbose = _verbose
				self.metrics = Metrics(_directory)
				self.util_function = UtilFunction()

		# walk-forward validation for univariate data
		def train_test_models(self, data_arr):
				# save for metrics
				header = ['sensor_read', 'model_index', 'expected', 'predicted']
				content = []
				confusion_matrix_lst = []
				roc_curve_lst = []
				
				# crossfold validation kfold=10
				# shuffle sample
				np.random.shuffle(data_arr)
				
				# split array in kfold batches
				data_batches = np.array_split(data_arr, self.kfolds)
				
				# Apply cross fold validation, kfold model train, where 1 fold is for test, n-1 folds for train
				for index_fold_test in range(0, self.kfolds):
						model_name = 'XGBClassifier_model_{}'.format(index_fold_test)
						
						# Select a new batch for test
						test = data_batches[index_fold_test]
						
						# Create new train subdataset with others batches
						train_batches = copy.copy(data_batches)
						del train_batches[index_fold_test]
						
						# Unify batchs is generating one train subdataset array
						train_batches = (train_arr for train_arr in train_batches)
						train = np.vstack(list(train_batches))
						
						# step over each time-step in the test set
						testX, testy = test[:, :-1], test[:, -1]
						
						# fit model on history and make a prediction and store forecast in list of predictions
						predictions = self.__xgboost_forecast(train, testX, index_fold_test)
						
						# summarize progress
						for i in range(0, len(testy)):
								content.append([testX[i], index_fold_test, testy[i], predictions[i][0]])
								if self.verbose:
									print('Sample Test %.1f, expected=%.1f, predicted=%.1f' % (index_fold_test, testy[i],
																																						 predictions[i][0]))
						
						self.util_function.write_to_csv(header, content, "{}/{}.csv".format(self.directory, model_name))
						# estimate prediction error
						error = mean_absolute_error(test[:, -1], predictions)
						print('Model {} - MAE: {:.3f}'.format(model_name, error))
						self.metrics.absolute_error(testy, np.round(predictions), model_name)

						confusion_matrix_lst.append(self.metrics.confusion_matrix_metric(testy, np.round(predictions), model_name))
						roc_curve_lst.append(self.metrics.roc_curve(testy, np.round(predictions), model_name))
				
				self.util_function.write_to_csv(['model_name', 'c_matrix', 'precision', 'recall', 'f1', 'support'],
																				confusion_matrix_lst,
																				"{}/confusion_metrics_train_models.csv".format(self.directory))
				self.util_function.write_to_csv(['model_name', 'fpr', 'tpr', 'thresholds', 'roc_auc'], roc_curve_lst,
																				"{}/roc_curve_train_models.csv".format(self.directory))
		
		def load_and_test_final_models(self, test_x, test_y):
				model_lst = sorted(glob.glob('{}/XGB*_model*.pkl'.format(self.directory)))
				
				for filename_model in model_lst:
						model_name = filename_model.split('/')[-1].replace('.plk', '')
						model = pickle.load(open(filename_model, "rb"))
						y = []
						y_pred = []
						for index, sensor_reads in enumerate(test_x):
								y.append(test_y[index])
								y_pred.append(model.predict(np.asarray([sensor_reads]))[0])
								print("Sensor read: {}, Prediction Class: {}, Real Class: {}".format(str(sensor_reads), round(y_pred[-1]),
																																										 y[-1]))
						error = mean_absolute_error(y, y_pred)
						print('Model {} - MAE: {:.3f}'.format(model_name, error))
						self.metrics.absolute_error(y, np.round(y_pred), model_name, type_dataset='test')
						
						self.util_function.write_to_csv(['model_name', 'c_matrix', 'precision', 'recall', 'f1', 'support'],
																						[self.metrics.confusion_matrix_metric(y, np.round(y_pred), model_name,
																																									type_dataset='test')],
																						"{}/confusion_metrics_test_model.csv".format(self.directory))
		
						self.util_function.write_to_csv(['model_name', 'fpr', 'tpr', 'thresholds', 'roc_auc'],
																						[self.metrics.roc_curve(y, np.round(y_pred), model_name, type_dataset='test')],
																						"{}/roc_curve_test_model.csv".format(self.directory))
		
		def print_model_structure(self, model):
				plot_tree(model)
		
		def __xgboost_forecast(self, train, testX, index_test):
				# transform list into array
				train = np.asarray(train)
				# split into input and output columns
				trainX, trainy = train[:, :-1], train[:, -1]
				# fit model
				model = XGBClassifier(objective=self.model_obj, n_estimators=self.model_estimators)
				model.fit(trainX, trainy)
				# make a one-step prediction
				yhat = []
				for test_x in testX:
						yhat.append(model.predict(np.asarray([test_x])))
				
				# save
				pickle.dump(model, open("{}/XGBClassifier_model_{}.pkl".format(self.directory, index_test), "wb"))
				
				return yhat
