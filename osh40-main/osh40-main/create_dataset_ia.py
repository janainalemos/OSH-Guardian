from ia_model.dataset_ia import DatasetIA
from datetime import datetime, timezone


if __name__ == '__main__':
		dt_ia = DatasetIA(datetime(2023, 1, 1, 8, 0, 0, 0).astimezone(timezone.utc), 'summer', _debug=True)
		dt_ia.data_generate()
		
		dt_ia = DatasetIA(datetime(2023, 6, 2, 8, 0, 0, 0).astimezone(timezone.utc), 'winter', _debug=True)
		dt_ia.data_generate()
