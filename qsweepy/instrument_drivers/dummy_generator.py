
from qsweepy.instrument_drivers.instrument import Instrument
import types
import logging
import numpy

class DummyGenerator(Instrument):
	'''
	This is the driver for dummy Signal Genarator

	Usage:
	Initialize with
	<name> = instruments.create('<name>', 'Agilent_E8257D', address='<GBIP address>, reset=<bool>')
	'''

	def __init__(self, name, address):
		'''
		Initializes the Agilent_E8257D, and communicates with the wrapper.

		Input:
		  name (string)	   : name of the instrument
		  address (string) : GPIB address
		  reset (bool)	   : resets to default values, default=False
		'''
		logging.info(__name__ + ' : Initializing instrument Dummy Generator')
		Instrument.__init__(self, name, tags=['physical'])

		# Add some global constants
		self._address = address

		self.add_parameter('power',
			flags=Instrument.FLAG_GETSET, units='dBm', minval=-20, maxval=18, type=float)
		self.add_parameter('phase',
			flags=Instrument.FLAG_GETSET, units='rad', minval=-numpy.inf, maxval=numpy.inf, type=float)
		self.add_parameter('frequency',
			flags=Instrument.FLAG_GETSET, units='Hz', minval=1e5, maxval=20e9, type=float)
		self.add_parameter('status',
			flags=Instrument.FLAG_GETSET, type=bool)

		self.add_function('reset')
		self.add_function ('get_all')

		self.set_power(0)
		self.set_frequency(1e9)
		self.set_status(0)
		self.set_phase(0)

	def reset(self):
		logging.info(__name__ + ' : resetting instrument')

	def get_all(self):
		ans = {}
		for key in self._parameters.keys():
			try:
				ans[key] = self._parameters[key]['value']
			except KeyError:
				pass
		return ans

	def do_get_power(self):
		logging.debug(__name__ + ' : get power')
		return self._parameters['power']['value']

	def do_set_power(self, amp):
		logging.debug(__name__ + ' : set power to %f' % amp)

	def do_get_phase(self):
		logging.debug(__name__ + ' : get phase')
		return self._parameters['phase']['value']

	def do_set_phase(self, phase):
		logging.debug(__name__ + ' : set phase to %f' % phase)

	def do_get_frequency(self):
		logging.debug(__name__ + ' : get frequency')
		return self._parameters['frequency']['value']

	def do_set_frequency(self, freq):
		logging.debug(__name__ + ' : set frequency to %f' % freq)

	def do_get_status(self):
		logging.debug(__name__ + ' : get status')
		return self._parameters['status']['value']

	def do_set_status(self, status):
		logging.debug(__name__ + ' : set status to %s' % status)

	# shortcuts
	def off(self):
		self.set_status('off')

	def on(self):
		self.set_status('on')