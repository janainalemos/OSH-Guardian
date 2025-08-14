# Example multiples popular algorithms
# https://machinelearningmastery.com/how-to-configure-k-fold-cross-validation/

# correlation between test harness and ideal test condition
import numpy as np
import pickle
import copy
import glob

from utils.util_function import UtilFunction
from decouple import config
from utils.metrics import Metrics
from utils.util_function import UtilFunction

from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import RidgeClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.tree import ExtraTreeClassifier
from sklearn.svm import LinearSVC
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import AdaBoostClassifier
from sklearn.ensemble import BaggingClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.metrics import mean_absolute_error


class ClassifierModels(object):
		MODEL_ID = {'model': 0, 'model_name': 1}
		
		def __init__(self, _kfolds, _directory, _verbose=True):
				self.kfolds = _kfolds
				self.directory = _directory
				self.metrics = Metrics(_directory)
				self.util_function = UtilFunction()
				self.verbose = _verbose
		
		def train_test_models(self, data_arr):
				header = ['sensor_read', 'model_index', 'expected', 'predicted']
				
				# get the list of models to consider
				models = self.__get_models()
				
				# prepare dataset for crossvalidation
				data_x, data_y = data_arr[:, :-1], data_arr[:, -1]
				np.random.shuffle(data_arr)
				data_batches = np.array_split(data_arr, self.kfolds)
				
				# evaluate each model
				for model in models:
						content = []
						confusion_matrix_lst = []
						roc_curve_lst = []
						
						# Apply cross fold validation, kfold model train, where 1 fold is for test, n-1 folds for train
						for index_fold_test in range(0, self.kfolds):
								model_name = '{}_model_{}'.format(model[self.MODEL_ID.get('model_name')], index_fold_test)
								
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
								predictions = self.__evaluate_model(train, testX, model[self.MODEL_ID.get('model')], model_name)
								
								# summarize progress
								for i in range(0, len(testy)):
										content.append([testX[i], index_fold_test, testy[i], predictions[i][0]])
										if self.verbose:
												print('Sample Test %.1f, expected=%.1f, predicted=%.1f' % (index_fold_test, testy[i],
																																									 predictions[i][0]))
								
								self.util_function.write_to_csv(header, content, "{}/{}.csv".format(self.directory, model_name))
								error = mean_absolute_error(test[:, -1], predictions)
								print('Model {} - MAE: {:.3f}'.format(model_name, error))
								self.metrics.absolute_error(testy, np.round(predictions), model_name)
								
								confusion_matrix_lst.append(self.metrics.confusion_matrix_metric(testy, np.round(predictions),
																																								 model_name))
								roc_curve_lst.append(self.metrics.roc_curve(testy, np.round(predictions), model_name))
						
						self.util_function.write_to_csv(['model_name', 'c_matrix', 'precision', 'recall', 'f1', 'support'],
																						confusion_matrix_lst,
																						"{}/confusion_metrics_train_models.csv".format(self.directory))
						self.util_function.write_to_csv(['model_name', 'fpr', 'tpr', 'thresholds', 'roc_auc'], roc_curve_lst,
																						"{}/roc_curve_train_models.csv".format(self.directory))
		
		def load_and_test_final_models(self, test_x, test_y):
				model_lst = sorted(glob.glob('{}/*.pkl'.format(self.directory)))
				
				for filename_model in model_lst:
						model_name = filename_model.split('/')[-1].replace('.plk', '')
						model = pickle.load(open(filename_model, "rb"))
						y = []
						y_pred = []
						for index, sensor_reads in enumerate(test_x):
								y.append(test_y[index])
								y_pred.append(model.predict(np.asarray([sensor_reads]))[0])
								print(
										"Sensor read: {}, Prediction Class: {}, Real Class: {}".format(str(sensor_reads), round(y_pred[-1]),
																																									 y[-1]))
						error = mean_absolute_error(y, y_pred)
						print('Model {} - MAE: {:.3f}'.format(model_name, error))
						self.metrics.absolute_error(y, np.round(y_pred), model_name, type_dataset='test')
						
						self.util_function.write_to_csv(['model_name', 'c_matrix', 'precision', 'recall', 'f1', 'support'],
																						[self.metrics.confusion_matrix_metric(y, np.round(y_pred), model_name,
																																									type_dataset='test')],
																						"{}/confusion_metrics_test_model.csv".format(self.directory))
						
						self.util_function.write_to_csv(['model_name', 'fpr', 'tpr', 'thresholds', 'roc_auc'],
																						[self.metrics.roc_curve(y, np.round(y_pred), model_name,
																																		type_dataset='test')],
																						"{}/roc_curve_test_model.csv".format(self.directory))
		
		# evaluate the model using a given test condition
		def __evaluate_model(self, train, testX, model, model_name):
				# transform list into array
				train = np.asarray(train)
				# split into input and output columns
				trainX, trainy = train[:, :-1], train[:, -1]
				# fit model
				model.fit(trainX, trainy)
				# make a one-step prediction
				yhat = []
				for test_x in testX:
						yhat.append(model.predict(np.asarray([test_x])))
				
				# save
				pickle.dump(model, open("{}/{}.pkl".format(self.directory, model_name), "wb"))
				
				return yhat
		
		@staticmethod
		def __get_models():
				models = list()
				
				models.append([LogisticRegression(), 'LogisticRegression'])
				models.append([RidgeClassifier(), 'RidgeClassifier'])
				models.append([SGDClassifier(), 'SGDClassifier'])
				models.append([PassiveAggressiveClassifier(), 'PassiveAggressiveClassifier'])
				models.append([KNeighborsClassifier(), 'KNeighborsClassifier'])
				models.append([DecisionTreeClassifier(), 'DecisionTreeClassifier'])
				models.append([ExtraTreeClassifier(), 'ExtraTreeClassifier'])
				models.append([LinearSVC(), 'LinearSVC'])
				models.append([SVC(), 'SVC'])
				models.append([GaussianNB(), 'GaussianNB'])
				models.append([AdaBoostClassifier(), 'AdaBoostClassifier'])
				models.append([BaggingClassifier(), 'BaggingClassifier'])
				models.append([RandomForestClassifier(), 'RandomForestClassifier'])
				models.append([GradientBoostingClassifier(), 'GradientBoostingClassifier'])
				models.append([LinearDiscriminantAnalysis(), 'LinearDiscriminantAnalysis'])
				models.append([QuadraticDiscriminantAnalysis(), 'QuadraticDiscriminantAnalysis'])
				
				return models
