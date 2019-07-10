import numpy as np
import time
import sys
from . import save_pkl
from . import plotting
from . import sweep
import shutil as sh
import pathlib
from .data_structures import *
from . import plotly_plot
from .fitters.fit_dataset import fit_dataset_1d

'''
Interactive stuff:
- (matplotlib) UI &  & telegram bot,
- telegram bot
- plotly UI
- time_left UI
'''
'''
Hooks for sweep.
(1) state.id = db.create_in_database(state)
(2) db.update_in_database(state)
(3) save_exdir.save_exdir(state)
'''

class sweeper:
	def mkdir(self):
		pass
	def __init__(self, db, sample_name=None):
		from . import save_exdir
		self.db = db
		self.default_save_path = ''
		self.sample_name = sample_name
		self.on_start = [(db.create_in_database,tuple()), 
						 (save_exdir.save_exdir,(True,)), 
						 (db.update_in_database,tuple()),
						 #(sweep_fit.fit_on_start, (db,))
						 ]
		self.on_update = [(save_exdir.update_exdir,tuple()),
						  #(sweep_fit.sweep_fit, (db, ))
						  ]
		self.on_finish = [#(sweep_fit.fit_on_finish, (db, )),
						  (db.update_in_database,tuple()), 
						  (save_exdir.close_exdir,tuple()),
						  (plotly_plot.save_default_plot,(self.db,))]
		
		self.on_start_fit = [(lambda x: db.create_in_database(x.fit),     				tuple()),
							 (lambda x: save_exdir.save_exdir(x.fit, True),             tuple()),
							 (lambda x: db.update_in_database(x.fit),     				tuple())]
							 
		self.on_update_fit = [(lambda x, y: x.update_fit(x.fit, y),                       tuple()),
							  (lambda x, y: save_exdir.update_exdir(x.fit, None),         tuple()),
							  (lambda x, y: db.update_in_database(x.fit),     				  tuple())]
							  
		self.on_finish_fit = [(lambda x: db.update_in_database(x.fit),                    tuple()),
							  (lambda x: save_exdir.close_exdir(x.fit),                   tuple()),
							  (lambda x: plotly_plot.save_default_plot(x, db), tuple())]

	
	def sweep(self, *args, on_start=[], on_update=[], on_finish=[], **kwargs):
		return sweep.sweep(*args, 
		                   sample_name = self.sample_name, 
						   on_start = on_start+self.on_start, 
						   on_finish = on_finish+self.on_finish, 
						   on_update = on_update+self.on_update, 
						   **kwargs)
	
	def sweep_fit_dataset_1d_onfly(self, *args, on_start=[], on_update=[], on_finish=[], fitter_arguments=tuple(), **kwargs):
		fitter_callback = (fit_dataset_1d, fitter_arguments)
		#print ('on_start:', on_start)
		#print ('fitter_callback:', [fitter_callback])
		#print ('on_start_fit:', self.on_start_fit)
		
		#print ('on_update: ', on_update)
		#print ('self.on_update: ', self.on_update)
		#print ('self.on_update_fit', self.on_update_fit)
		
		#print ('on_finish: ', on_finish)
		#print ('self.on_finish: ', self.on_finish)
		#print ('self.on_finish_fit', self.on_finish_fit)
		return sweep.sweep(*args, 
						   sample_name = self.sample_name, 
						   on_start = on_start+self.on_start+[fitter_callback]+self.on_start_fit,
						   on_update = on_update+self.on_update+self.on_update_fit, 
						   on_finish = on_finish+self.on_finish+self.on_finish_fit, 
						   **kwargs)