import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np
from sklearn import metrics
from matplotlib import pyplot


class Metrics(object):
		def __init__(self, _directory):
				self.directory = _directory
		
		def confusion_matrix_metric(self, y, y_pred, model_name, type_dataset='train'):
				cm = metrics.confusion_matrix(y, y_pred)
				precision = metrics.precision_score(y, y_pred, labels=['Normal', 'Risk'], pos_label=1, average="binary")
				recall = metrics.recall_score(y, y_pred, labels=['Normal', 'Risk'], pos_label=1, average="binary")
				f1 = metrics.f1_score(y, y_pred, labels=['Normal', 'Risk'], pos_label=1, average="binary")
				support = np.sum(y)
				
				pyplot.figure(figsize=(15, 10))
				pyplot.clf()
				pyplot.imshow(cm, interpolation='nearest', cmap=pyplot.cm.Wistia)
				classNames = ['Normal', 'Risk']
				pyplot.title('Confusion Matrix')
				pyplot.ylabel('True label')
				pyplot.xlabel('Predicted label')
				tick_marks = np.arange(len(classNames))
				pyplot.xticks(tick_marks, classNames, rotation=45)
				pyplot.yticks(tick_marks, classNames)
				s = [['TN', 'FP'], ['FN', 'TP']]

				for i in range(2):
						for j in range(2):
								pyplot.text(j, i, str(s[i][j]) + " = " + str(cm[i][j]))
				pyplot.savefig('{}/confusion_matrix_{}_{}.png'.format(self.directory, type_dataset, model_name))
				
				return [model_name, str(cm).replace('/n', ' '), precision, recall, f1, support]
		
		def roc_curve(self, y, y_pred, model_name, type_dataset='train'):
				pyplot.figure(figsize=(15, 10))
				pyplot.clf()
				fpr, tpr, thresholds = metrics.roc_curve(y, y_pred)
				roc_auc = metrics.auc(fpr, tpr)
				display = metrics.RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc, estimator_name=model_name)
				display.plot()
				pyplot.savefig('{}/roc_curve_{}_{}.png'.format(self.directory, type_dataset, model_name))

				return [model_name, fpr, tpr, thresholds, roc_auc]
		
		def absolute_error(self, y, y_pred, model_name, type_dataset='train'):
				pyplot.figure(figsize=(15, 10))
				pyplot.clf()
				pyplot.plot(y, label='Expected')
				pyplot.plot(y_pred, label='Predicted')
				pyplot.legend()
				pyplot.title(model_name)
				pyplot.xlabel('Total Samples')
				pyplot.ylabel('Prediction vs Real Class Positive (Risk)')
				pyplot.savefig('{}/mean_absolute_error_{}_{}.png'.format(self.directory, type_dataset, model_name))
		
		def compare_models_precision_recall_curve(self, df, models, type_dataset='train'):
				fig = go.Figure()
				fig.add_shape(
						type='line', line=dict(dash='dash'),
						x0=0, x1=1, y0=0, y1=1
				)
				
				y_true = df['y_test_T']
				
				for model in models:
						y_score = df['y_pred_' + model + '_T']
						
						precision, recall, _ = metrics.precision_recall_curve(y_true, y_score)
						auc_score = metrics.average_precision_score(y_true, y_score)
						
						name = f"{model} (AP={auc_score:.2f})"
						fig.add_trace(go.Scatter(x=recall, y=precision, name=name, mode='lines', line=dict(width=3)))
				
				fig.update_layout(
						xaxis_title='Recall',
						yaxis_title='Precision',
						yaxis=dict(scaleanchor="x", scaleratio=1),
						xaxis=dict(constrain='domain'),
						xaxis_gridcolor='rgba(240,240,240,240)', yaxis_gridcolor='rgba(240,240,240,240)',
						plot_bgcolor='rgba(0,0,0,0)',
						legend=dict(orientation="h", yanchor="top", y=1.1, x=0.5, xanchor="center"),
						font=dict(size=16),
						width=700, height=700
				)
				fig.write_image('{}/compare_models_precision_recall_curve_{}.png'.format(self.directory, type_dataset))
		
		def compare_models_roc_curve(self, df, models, type_dataset='train'):
				fig = go.Figure()
				fig.add_shape(
						type='line', line=dict(dash='dash'),
						x0=0, x1=1, y0=0, y1=1
				)
				
				y_true = df['y_test_T']
				
				for model in models:
						y_score = df['y_pred_' + model + '_T']
						
						fpr, tpr, _ = metrics.roc_curve(y_true, y_score)
						auc_score = metrics.roc_auc_score(y_true, y_score)
						
						name = f"{model} (AUC={auc_score:.2f})"
						fig.add_trace(go.Scatter(x=fpr, y=tpr, name=name, mode='lines', line=dict(width=3)))
				
				fig.update_layout(
						xaxis_title='Taxa de Falso Positivo',
						yaxis_title='Taxa de Verdadeiro Positivo',
						yaxis=dict(scaleanchor="x", scaleratio=1),
						xaxis=dict(constrain='domain'),
						xaxis_gridcolor='rgba(240,240,240,240)', yaxis_gridcolor='rgba(240,240,240,240)',
						plot_bgcolor='rgba(0,0,0,0)',
						legend=dict(orientation="h", yanchor="top", y=1.1, x=0.5, xanchor="center"),
						width=700, height=700,
						font=dict(size=18)
						# font=dict(family="Courier New, monospace", size=18, color="RebeccaPurple")
				)
				fig.write_image('{}/compare_models_roc_curve_{}.png'.format(self.directory, type_dataset))
