import qsweepy.libraries.instruments as instruments
import qsweepy
from qsweepy.libraries.awg_channel2 import awg_channel
from qsweepy.libraries.awg_digital2 import awg_digital
from qsweepy.libraries import awg_iq_multi2 as awg_iq_multi
import numpy as np
from time import sleep
# import rpyc

device_settings = { 'hdawg1_address': 'hdawg-dev8250',
                    'adc_ref' : "100MHz", #"100MHz" and "10MHz" are supported by QubitDAQ
                    'adc_timeout': 10,
                    'adc_trig_rep_period': 10,  # 12.5 MHz rate period
                    'adc_trig_width': 2,  # 32 ns trigger length
}

pulsed_settings = {'ex_clock': 2400e6,  # 1 GHz - clocks of some devices
                   'ro_clock': 1000e6,
                   'rep_rate': 20e3,  # 10 kHz - pulse sequence repetition rate
                   # 500 ex_clocks - all waves is shorten by this amount of clock cycles
                   # to verify that M3202 will not miss next trigger
                   # (awgs are always missing trigger while they are still outputting waveform)
                   'global_num_points_delta': 400,
                   'hdawg_ch0_amplitude': 0.8,
                   'hdawg_ch1_amplitude': 0.8,
                   'hdawg_ch2_amplitude': 0.8,
                   'hdawg_ch3_amplitude': 0.8,
                   'hdawg_ch4_amplitude': 0.8,
                   'hdawg_ch5_amplitude': 0.8,
                   'hdawg_ch6_amplitude': 0.8,
                   'hdawg_ch7_amplitude': 0.8,
                   'lo1_freq': 5.4e9,#4.9e9,
                   'pna_freq': 7.55e9,
                   # 'calibrate_delay_nop': 65536,
                   'calibrate_delay_nums': 200,
                   'trigger_readout_channel_name': 'ro_trg',
                   'trigger_readout_length': 200e-9,
                   'modem_dc_calibration_amplitude': 1.0,
                   'adc_nop': 1024,
                   'adc_nums': 10000,  ## Do we need control over this? Probably, but not now... WUT THE FUCK MAN
                   # 'adc_default_delay': 550,
                   }


class hardware_setup():
    def __init__(self, device_settings, pulsed_settings):
        self.device_settings = device_settings
        self.pulsed_settings = pulsed_settings
        self.hardware_state = 'undefined'

        self.lo = None

        self.hdawg1 = None
        self.adc_device = None
        self.adc = None

        self.ro_trg = None
        self.read_seq_id = None
        self.q1z = None
        self.q2z = None

        self.iq_devices = None

    def open_devices(self):

        self.lo = instruments.DummyGenerator('lo',0)
        self.hdawg1 = instruments.ZIDevice('hdawg-dev8250', server_host = '10.20.61.147',
                                           server_port = 8004,
                                           devtype='HDAWG', delay_int=0)
        
        for channel_id in range(8):
            self.hdawg1.daq.setDouble('/' + self.hdawg1.device + '/sigouts/%d/range' % channel_id, 1)

        #It is necessary if you want to use DIOs control features during pulse sequence
        self.hdawg1.daq.setInt('/' + self.hdawg1.device + '/dios/0/mode', 1)
        self.hdawg1.daq.setInt('/' + self.hdawg1.device + '/dios/0/drive', 1)
        self.hdawg1.daq.sync()

        self.q1z = awg_channel(self.hdawg1, 6)
        self.q2z = awg_channel(self.hdawg1, 7)
        self.q1z.set_offset(0)
        self.q2z.set_offset(0)

        self.adc_device = instruments.TSW14J56_evm()
        self.adc_device.timeout = self.device_settings['adc_timeout']
        self.adc = instruments.TSW14J56_evm_reducer(self.adc_device)
        self.adc.output_raw = True
        self.adc.last_cov = False
        self.adc.avg_cov = False
        self.adc.resultnumber = False

        self.adc_device.set_trig_src_period(self.device_settings['adc_trig_rep_period'])  # 10 kHz period rate
        self.adc_device.set_trig_src_width(self.device_settings['adc_trig_width'])  # 80 ns trigger length

        self.hardware_state = 'undefined'

    def set_cw_mode(self, channels_off=None):
        pass

    def set_pulsed_mode(self):
        if self.hardware_state == 'pulsed_mode':
            return
        self.hardware_state = 'undefined'

        self.hdawg1.stop()

        self.hdawg1.set_clock(self.pulsed_settings['ex_clock'])
        self.hdawg1.set_clock_source(0)

        self.hdawg1.set_trigger_impedance_1e3()
        self.hdawg1.set_dig_trig1_source([0, 0, 0, 0])
        self.hdawg1.set_dig_trig1_slope([1, 1, 1, 1])
        self.hdawg1.set_trig_level(0.3)

        self.hdawg1.set_marker_out(2, 0)

        self.hdawg1.set_offset(offset=0, channel=2)
        self.hdawg1.set_offset(offset=0, channel=3)

        self.ro_trg = awg_digital(self.hdawg1, 0, delay_tolerance=20e-9)  # triggers readout card
        self.ro_trg.adc = self.adc
        self.ro_trg.mode = 'waveform'
        self.hardware_state = 'pulsed_mode'

        # I don't know HOW but it works
        # For each excitation sequencers:
        # We need to set DIO slope as  Rise (0- off, 1 - rising edge, 2 - falling edge, 3 - both edges)
        for ex_seq_id in range(4):
            self.hdawg1.daq.setInt('/' + self.hdawg1.device + '/awgs/%d/dio/strobe/slope' % ex_seq_id, 1)
            # We need to set DIO valid polarity as High (0- none, 1 - low, 2 - high, 3 - both )
            self.hdawg1.daq.setInt('/' + self.hdawg1.device + '/awgs/%d/dio/valid/polarity' % ex_seq_id, 0)
            self.hdawg1.daq.setInt('/' + self.hdawg1.device + '/awgs/%d/dio/strobe/index' % ex_seq_id, 8)

        # For readout channels
        # For readout sequencer:
        self.read_seq_id = 0
        # We need to set DIO slope as  Fall (0- off, 1 - rising edge, 2 - falling edge, 3 - both edges)
        self.hdawg1.daq.setInt('/' + self.hdawg1.device + '/awgs/%d/dio/strobe/slope' % self.read_seq_id, 1)
        # We need to set DIO valid polarity as  None (0- none, 1 - low, 2 - high, 3 - both )
        self.hdawg1.daq.setInt('/' + self.hdawg1.device + '/awgs/%d/dio/valid/polarity' % self.read_seq_id, 0)
        self.hdawg1.daq.setInt('/' + self.hdawg1.device + '/awgs/%d/dio/strobe/index' % self.read_seq_id, 3)
        # self.hdawg.daq.setInt('/' + self.hdawg.device + '/awgs/%d/dio/mask/value' % read_seq_id, 2)
        # self.hdawg.daq.setInt('/' + self.hdawg.device + '/awgs/%d/dio/mask/shift' % read_seq_id, 1)
        # For readout channels

    def set_switch_if_not_set(self, value, channel):
        pass

    def setup_iq_channel_connections(self, exdir_db):
        # промежуточные частоты для гетеродинной схемы new:
        self.iq_devices = {'iq_ro':  awg_iq_multi.AWGIQMulti(awg=self.hdawg1,
                                                            sequencer_id=0,
                                                            lo=self.lo,
                                                            exdir_db=exdir_db),
                           'iq_ex1': awg_iq_multi.AWGIQMulti(awg = self.hdawg1,
                                                            sequencer_id=0,
                                                            lo=self.lo,
                                                            exdir_db=exdir_db),
                           'iq_ex2': awg_iq_multi.AWGIQMulti(awg=self.hdawg1,
                                                            sequencer_id=1,
                                                            lo=self.lo,
                                                            exdir_db=exdir_db)
                           }

        self.iq_devices['iq_ro'].name = 'ro'
        self.iq_devices['iq_ex1'].name = 'ex1'
        self.iq_devices['iq_ex2'].name = 'ex2'

        self.fast_controls = {}


    def get_readout_trigger_pulse_length(self):
        return self.pulsed_settings['trigger_readout_length']

    def get_modem_dc_calibration_amplitude(self):
        return self.pulsed_settings['modem_dc_calibration_amplitude']

    def revert_setup(self, old_settings):
        if 'adc_nums' in old_settings:
            self.adc.set_adc_nums(old_settings['adc_nums'])
        if 'adc_nop' in old_settings:
            self.adc.set_adc_nop(old_settings['adc_nop'])
        if 'adc_posttrigger' in old_settings:
            self.adc.set_posttrigger(old_settings['adc_posttrigger'])