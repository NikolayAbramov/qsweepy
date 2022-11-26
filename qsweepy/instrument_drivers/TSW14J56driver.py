from numpy import *

import warnings
import os

module_dir = os.path.dirname(os.path.abspath(__file__))

from qsweepy.instrument_drivers._ADS54J40.usb_intf import *
from qsweepy.instrument_drivers._ADS54J40.reg_intf import *
from qsweepy.instrument_drivers.ADS54J40 import *

import usb.core
import time
import zlib

class TSW14J56_evm_reducer():
	def __init__(self, adc):
		self.adc = adc
		self.output_raw = True
		self.last_cov = True
		self.avg_cov = True
		self.resultnumber = True
		self.trig = 'ext'
		self.avg_cov_mode = 'real' ## raw results from device
		self.cov_norms = {channel_id:1 for channel_id in range(4)}
		self.cov_signals = {channel_id:None for channel_id in range(4)}
		self.resultnumbers_dimension = 16
		self.devtype = 'SK'
		self.result_source = 'avg_cov'
		self.internal_avg = True
		#self.avg_cov_mode = 'norm_cmplx' ## normalized results in complex Volts, IQ

	def set_internal_avg(self, internal_avg):
		pass

	def get_clock(self):
		return self.adc.get_clock()

	def get_adc_nums(self):
		return self.adc.nsegm
	def get_adc_nop(self):
		return self.adc.nsamp
	def set_adc_nums(self, nums):
		self.adc.nsegm = nums
	def set_adc_nop(self, nop):
		self.adc.nsamp = nop

	def get_points(self):
		points = {}
		if self.output_raw:
			points.update({'Voltage':[('Sample',arange(self.adc.nsegm), ''),
								 ('Time',arange(self.adc.nsamp)/self.adc.get_clock(), 's')]})
		if self.last_cov:
			points.update({'last_cov'+str(i):[] for i in range(self.adc.num_covariances)})
		if self.avg_cov:
			if self.avg_cov_mode == 'real':
				points.update({'avg_cov'+str(i):[] for i in range(self.adc.num_covariances)})
			elif self.avg_cov_mode == 'iq':
				points.update({'avg_cov'+str(i):[] for i in range(self.adc.num_covariances//2)})
		if self.resultnumber:
			points.update({'resultnumbers':[('State', arange(self.resultnumbers_dimension), '')]})
		return (points)

	def get_dtype(self):
		dtypes = {}
		if self.output_raw:
			dtypes.update({'Voltage':complex})
		if self.last_cov:
			dtypes.update({'last_cov'+str(i):float for i in range(self.adc.num_covariances)})
		if self.avg_cov:
			if self.avg_cov_mode == 'real':
				dtypes.update({'avg_cov'+str(i):float for i in range(self.adc.num_covariances)})
			elif self.avg_cov_mode == 'iq':
				dtypes.update({'avg_cov'+str(i):complex for i in range(self.adc.num_covariances//2)})
		if self.resultnumber:
			dtypes.update({'resultnumbers': float})
		return (dtypes)

	def get_opts(self):
		opts = {}
		if self.output_raw:
			opts.update({'Voltage':{'log': None}})
		if self.last_cov:
			opts.update({'last_cov'+str(i):{'log': None} for i in range(self.adc.num_covariances)})
		if self.avg_cov:
			if self.avg_cov_mode == 'real':
				opts.update({'avg_cov'+str(i):{'log': None} for i in range(self.adc.num_covariances)})
			elif self.avg_cov_mode == 'iq':
				opts.update({'avg_cov'+str(i):{'log': None} for i in range(self.adc.num_covariances//2)})
		if self.resultnumber:
			opts.update({'resultnumbers': {'log': None}})
		return (opts)

	def measure(self):
		result = {}
		if self.avg_cov:
			avg_before =  {'avg_cov'+str(i):self.adc.get_cov_result_avg(i) for i in range(self.adc.num_covariances)}
		if self.resultnumber:
			resultnumbers_before = self.adc.get_resultnumbers()
		self.adc.capture(trig=self.trig, cov = (self.last_cov or self.avg_cov or self.resultnumber))
		if self.output_raw:
			result.update({'Voltage':self.adc.get_data()})
		if self.last_cov:
			result.update({'last_cov'+str(i):self.adc.get_cov_result(i)/self.cov_norms[i] for i in range(self.adc.num_covariances)})
		if self.avg_cov:
			result_raw = {'avg_cov'+str(i):(self.adc.get_cov_result_avg(i)-avg_before['avg_cov'+str(i)])/self.cov_norms[i] for i in range(self.adc.num_covariances)}
			if self.avg_cov_mode == 'real':
				result.update(result_raw)
			elif self.avg_cov_mode == 'iq':
				result.update({'avg_cov0': (result_raw['avg_cov0']+1j*result_raw['avg_cov1']),
							   'avg_cov1': (result_raw['avg_cov2']+1j*result_raw['avg_cov3'])})
		if self.resultnumber:
			result.update({'resultnumbers': [a-b for a,b in zip(self.adc.get_resultnumbers(), resultnumbers_before)][:self.resultnumbers_dimension]})

		return (result)

	def set_feature_iq(self, feature_id, feature):
		#self.avg_cov_mode = 'norm_cmplx'
		feature = feature[:self.adc.ram_size]/np.max(np.abs(feature[:self.adc.ram_size]))
		feature = np.asarray(2**13*feature, dtype=complex)
		feature_real_int = np.asarray(np.real(feature), dtype=np.int16)
		feature_imag_int = np.asarray(np.imag(feature), dtype=np.int16)

		self.adc.set_ram_data([feature_real_int.tolist(),     (feature_imag_int).tolist()],  feature_id*2)
		self.adc.set_ram_data([(feature_imag_int).tolist(),  (-feature_real_int).tolist()], feature_id*2+1)

		self.cov_norms[feature_id*2] = np.sqrt(np.mean(np.abs(feature)**2))*2**13
		self.cov_norms[feature_id*2+1] = np.sqrt(np.mean(np.abs(feature)**2))*2**13

	def set_feature_real(self, feature_id, feature, threshold=None):
		#self.avg_cov_mode = 'norm_cmplx'
		if threshold is not None:
			threshold = threshold/np.max(np.abs(feature[:self.adc.ram_size]))*(2**13)
			self.adc.set_threshold(thresh=threshold, ncov=feature_id)

		feature = feature[:self.adc.ram_size]/np.max(np.abs(feature[:self.adc.ram_size]))
		feature_padded = np.zeros(self.adc.ram_size, dtype=np.complex)
		feature_padded[:len(feature)] = feature
		feature = np.asarray(2**13*feature_padded, dtype=complex)
		feature_real_int = np.asarray(np.real(feature), dtype=np.int16)
		feature_imag_int = np.asarray(np.imag(feature), dtype=np.int16)

		self.adc.set_ram_data([feature_real_int.tolist(),    (feature_imag_int).tolist()],  feature_id)
		self.cov_norms[feature_id] = np.sqrt(np.mean(np.abs(feature)**2))*2**13

	def disable_feature(self, feature_id):
		self.adc.set_ram_data([np.zeros(self.adc.ram_size, dtype=np.int16).tolist(), np.zeros(self.adc.ram_size, dtype=np.int16).tolist()], feature_id)
		self.adc.set_threshold(thresh=1, ncov=feature_id)