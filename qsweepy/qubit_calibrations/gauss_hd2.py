from qsweepy.qubit_calibrations.excitation_pulse2 import *
from qsweepy.qubit_calibrations.Ramsey2 import *
from qsweepy.qubit_calibrations.channel_amplitudes import channel_amplitudes
from qsweepy.qubit_calibrations.readout_pulse2 import *
from qsweepy.qubit_calibrations import sequence_control
from qsweepy import zi_scripts


# def get_gauss_hd_pulse_sequence(device, channel_amplitudes, sigma, length, amp, alpha):
#   if tail_length > 0:
#        channel_pulses = [(c, pg.gauss_hd, a*amp*np.exp(1j*phase), self.sigma, self.alpha)
#                            for c, a in channel_amplitudes.items()]
#
#   return [device.pg.pmulti(length+2*tail_length, *tuple(channel_pulses))]


def gauss_hd_ape_pihalf(device, qubit_id, num_pulses_range, ex_sequencers, control_sequence, readout_sequencer, phase_sign='+'):
    readout_pulse, measurer = get_uncalibrated_measurer(device=device, qubit_id=qubit_id)
    # pi2_pulse = get_excitation_pulse_from_gauss_hd_Rabi_amplitude(device=device, qubit_id=qubit_id, rotation_angle=np.pi/2.)
    pi2_pulse = get_excitation_pulse_from_gauss_hd_Rabi_alpha(device=device, qubit_id=qubit_id,
                                                              rotation_angle=np.pi / 2.)
    channel_amplitudes_ = device.exdir_db.select_measurement_by_id(pi2_pulse.references['channel_amplitudes'])
    metadata = {'qubit_id': qubit_id}
    references = {'channel_amplitudes': channel_amplitudes_.id,
                  'pi_half_pulse': pi2_pulse.id}
    amplitude = float(pi2_pulse.metadata['amplitude'])
    sigma = float(pi2_pulse.metadata['sigma'])
    length = float(pi2_pulse.metadata['length'])
    alpha = float(pi2_pulse.metadata['alpha'])
    phase = float(pi2_pulse.metadata['phase'])

    def set_num_pulses(num_pulses):
        control_sequence.awg.set_register(control_sequence.params['sequencer_id'], control_sequence.params['var_reg0'],
                                          int(num_pulses))
        fast_control = False
        channel_pulses_xp = [(c, device.pg.gauss_hd, float(a) * amplitude, sigma, alpha, phase, fast_control)
                             for c, a in channel_amplitudes_.metadata.items()]
        channel_pulses_xm = [(c, device.pg.gauss_hd, -float(a) * amplitude, sigma, alpha, phase, fast_control)
                             for c, a in channel_amplitudes_.metadata.items()]
        channel_pulses_yp = [(c, device.pg.gauss_hd, float(a) * amplitude*1j, sigma, alpha, phase, fast_control)
                             for c, a in channel_amplitudes_.metadata.items()]
        channel_pulses_ym = [(c, device.pg.gauss_hd, -float(a) * amplitude*1j, sigma, alpha, phase, fast_control)
                             for c, a in channel_amplitudes_.metadata.items()]

        fast_control = 'phase_correction'
        channel_pulses = [(c, device.pg.gauss_hd, float(a) * amplitude, sigma, alpha, phase, fast_control)
                          for c, a in channel_amplitudes_.metadata.items()]
        if phase_sign == '+':
            prepare_seq = []
            prepare_seq.append([device.pg.pmulti(device, length, *tuple(channel_pulses_xp))])
            prepare_seq.append([device.pg.pmulti(device, length, *tuple(channel_pulses))])
            prepare_seq.append([device.pg.pmulti(device, length, *tuple(channel_pulses_xm))])
        elif phase_sign == '-':
            prepare_seq = []
            prepare_seq.append([device.pg.pmulti(device, length, *tuple(channel_pulses_xp))])
            prepare_seq.append([device.pg.pmulti(device, length, *tuple(channel_pulses))])
            prepare_seq.append([device.pg.pmulti(device, length, *tuple(channel_pulses_yp))])
        readout_sequencer.awg.stop_seq(readout_sequencer.params['sequencer_id'])
        sequence_control.set_preparation_sequence(device, ex_sequencers, prepare_seq,control_sequence)
        readout_sequencer.awg.start_seq(readout_sequencer.params['sequencer_id'])

    # measurement_name = [m for m in measurer.get_points().keys()][0]
    measurement_name = list(measurer.get_points().keys())[0]
    fitter_arguments = (measurement_name, exp_sin_fitter(), -1, [])
    measurement = device.sweeper.sweep_fit_dataset_1d_onfly(measurer,
                                                            (num_pulses_range, set_num_pulses,
                                                             'Quasiidentity pulse number'),
                                                            fitter_arguments=fitter_arguments,
                                                            measurement_type='gauss_hd_ape_pihalf',
                                                            metadata=metadata,
                                                            references=references)
    return measurement


def gauss_hd_ape_alpha(device, qubit_id, alphas, num_pulses, ex_sequencers, control_sequence, readout_sequencer, phase_sign='+'):
    readout_pulse, measurer = get_uncalibrated_measurer(device=device, qubit_id=qubit_id)
    pi2_pulse = get_excitation_pulse_from_gauss_hd_Rabi_amplitude(device=device, qubit_id=qubit_id,
                                                                  rotation_angle=np.pi / 2.)
    channel_amplitudes_ = device.exdir_db.select_measurement_by_id(pi2_pulse.references['channel_amplitudes'])
    metadata = {'qubit_id': qubit_id,
                'phase_sign': phase_sign,
                'num_pulses': num_pulses}
    references = {'channel_amplitudes': channel_amplitudes_.id,
                  'pi_half_pulse': pi2_pulse.id,
                  }
    amplitude = float(pi2_pulse.metadata['amplitude'])
    sigma = float(pi2_pulse.metadata['sigma'])
    length = float(pi2_pulse.metadata['length'])

    alpha = float(pi2_pulse.metadata['alpha'])

    control_sequence.awg.set_register(control_sequence.params['sequencer_id'], control_sequence.params['var_reg0'],
                                      int(num_pulses))

    def set_alphas1(alpha):
        channel_pulses_xp = [(c, device.pg.gauss_hd, float(a) * amplitude, sigma, alpha)
                             for c, a in channel_amplitudes_.metadata.items()]
        channel_pulses_xm = [(c, device.pg.gauss_hd, -float(a) * amplitude, sigma, alpha)
                             for c, a in channel_amplitudes_.metadata.items()]
        channel_pulses_yp = [(c, device.pg.gauss_hd, float(a) * amplitude * 1j, sigma, alpha)
                             for c, a in channel_amplitudes_.metadata.items()]
        channel_pulses_ym = [(c, device.pg.gauss_hd, -float(a) * amplitude * 1j, sigma, alpha)
                             for c, a in channel_amplitudes_.metadata.items()]
        if phase_sign == '+':
            pulse = [device.pg.pmulti(device, length, *tuple(channel_pulses_xp))] + \
                    ([device.pg.pmulti(device, length, *tuple(channel_pulses_xp))] +
                     [device.pg.pmulti(device, length, *tuple(channel_pulses_xm))]) * num_pulses + \
                    [device.pg.pmulti(device, length, *tuple(channel_pulses_xm))]
        elif phase_sign == '-':
            pulse = [device.pg.pmulti(device, length, *tuple(channel_pulses_xp))] + \
                    ([device.pg.pmulti(device, length, *tuple(channel_pulses_xp))] +
                     [device.pg.pmulti(device, length, *tuple(channel_pulses_xm))]) * num_pulses + \
                    [device.pg.pmulti(device, length, *tuple(channel_pulses_yp))]

        device.pg.set_seq(device.pre_pulses + pulse + device.trigger_readout_seq + readout_pulse.get_pulse_sequence())
        #TODO
    def set_phase(phase):

        fast_control = False
        alpha1 = alpha

        channel_pulses_xp = [(c, device.pg.gauss_hd, float(a) * amplitude, sigma, alpha1, phase, fast_control)
                             for c, a in channel_amplitudes_.metadata.items()]
        channel_pulses_xm = [(c, device.pg.gauss_hd, -float(a) * amplitude, sigma, alpha1, phase, fast_control)
                             for c, a in channel_amplitudes_.metadata.items()]
        channel_pulses_yp = [(c, device.pg.gauss_hd, float(a) * amplitude*1j, sigma, alpha1, phase, fast_control)
                             for c, a in channel_amplitudes_.metadata.items()]
        channel_pulses_ym = [(c, device.pg.gauss_hd, -float(a) * amplitude*1j, sigma, alpha1, phase, fast_control)
                             for c, a in channel_amplitudes_.metadata.items()]

        fast_control = 'phase_correction'
        channel_pulses = [(c, device.pg.gauss_hd, float(a) * amplitude, sigma, alpha1, phase, fast_control)
                          for c, a in channel_amplitudes_.metadata.items()]
        if phase_sign == '+':
            prepare_seq = []
            prepare_seq.append(device.pg.pmulti(device, length, *tuple(channel_pulses_xp)))
            prepare_seq.append(device.pg.pmulti(device, length, *tuple(channel_pulses)))
            prepare_seq.append(device.pg.pmulti(device, length, *tuple(channel_pulses_xm)))
        elif phase_sign == '-':
            prepare_seq = []
            prepare_seq.append(device.pg.pmulti(device, length, *tuple(channel_pulses_xp)))
            prepare_seq.append(device.pg.pmulti(device, length, *tuple(channel_pulses)))
            prepare_seq.append(device.pg.pmulti(device, length, *tuple(channel_pulses_yp)))
        readout_sequencer.awg.stop_seq(readout_sequencer.params['sequencer_id'])
        sequence_control.set_preparation_sequence(device, ex_sequencers, prepare_seq,control_sequence)
        readout_sequencer.awg.start_seq(readout_sequencer.params['sequencer_id'])


    measurement = device.sweeper.sweep(measurer,
                                       (alphas, set_phase, 'alpha'),
                                       measurement_type='gauss_hd_ape_alpha',
                                       metadata=metadata,
                                       references=references)
    return measurement


class GaussHDExcitationPulse(MeasurementState):
    def __init__(self, *args, **kwargs):
        self.device = args[0]
        if len(args) == 2 and isinstance(args[1], MeasurementState) and not len(kwargs):  # copy constructor
            super().__init__(args[1])
        else:  # otherwise initialize from dict and device
            metadata = {'rotation_angle': str(kwargs['rotation_angle']),
                        'pulse_type': 'rect',
                        'length': str(kwargs['length']),
                        'sigma': str(kwargs['sigma']),
                        'amplitude': str(kwargs['amplitude']),
                        'alpha': str(kwargs['alpha']),
                        'phase': str(kwargs['phase'])}

            if 'calibration_type' in kwargs:
                metadata['calibration_type'] = kwargs['calibration_type']

            references = {'channel_amplitudes': int(kwargs['channel_amplitudes']),
                          'Rabi_amplitude_iterative': int(kwargs['Rabi_amplitude_iterative_measurement'])}

            # check if such measurement exists
            try:
                measurement = self.device.exdir_db.select_measurement(measurement_type='qubit_excitation_pulse',
                                                                      metadata=metadata,
                                                                      references_that=references)
                super().__init__(measurement)
            except:
                traceback.print_exc()
                super().__init__(measurement_type='qubit_excitation_pulse',
                                 sample_name=self.device.exdir_db.sample_name,
                                 metadata=metadata,
                                 references=references)
                self.device.exdir_db.save_measurement(self)

        # inverse_references = {v:k for k,v in self.references.items()}
        # print ('inverse_references in __init__:', inverse_references)
        self.channel_amplitudes = channel_amplitudes.channel_amplitudes(
            self.device.exdir_db.select_measurement_by_id(self.references['channel_amplitudes']))

    def get_pulse_sequence(self, phase):
        return get_rect_cos_pulse_sequence(device=self.device,
                                           channel_amplitudes=self.channel_amplitudes,
                                           tail_length=float(self.metadata['tail_length']),
                                           length=float(self.metadata['length']),
                                           phase=phase)


def get_preferred_length(device, qubit_id, channel):
    '''
    calculates the preffered gate length for single-qubit gate on qubit_id applied through channel.
    Caluclation involves the Rabi max_Rabi_freq qubit or global parameter and the Rabi frequencies of other
    qubits driven through this iq_ex device and max_parasitic_Rabi_ratio control.

    Parameters
    ----------
    device
    qubit_id
    channel

    Returns
    -------
    prefered maximum gate length for rect pulses.

    '''
    max_Rabi_freq = float(device.get_qubit_constant(qubit_id=qubit_id, name='max_Rabi_freq'))
    max_parasitic_Rabi_ratio = float(device.get_qubit_constant(qubit_id=qubit_id, name='max_parasitic_Rabi_ratio'))
    pulse_length_alignment = float(device.get_qubit_constant(qubit_id=qubit_id, name='pulse_length_alignment'))
    sigmas_in_gauss = float(device.get_qubit_constant(qubit_id=qubit_id, name='sigmas_in_gauss'))
    amplitude_default = float(device.get_qubit_constant(qubit_id=qubit_id, name='amplitude_default'))

    channel_device = device.get_qubit_excitation_channel_list(qubit_id)[channel]
    # loop over other qubits
    pulse_amplitude = amplitude_default
    print('getting other qubit excitition pulse with qubit_id {} and channel {}'.format(qubit_id, channel))
    rect_pulse = get_rect_excitation_pulse(device=device,
                                           qubit_id=qubit_id,
                                           rotation_angle=2 * np.pi,
                                           channel_amplitudes_override=channel_amplitudes(device, **{
                                               channel: amplitude_default}),
                                           recalibrate=True)
    channel_amplitudes_ = device.exdir_db.select_measurement_by_id(rect_pulse.references['channel_amplitudes'])
    amplitude = float(channel_amplitudes_.metadata[channel])
    Rabi_freq = 1 / (float(rect_pulse.metadata['length']) * amplitude)
    if Rabi_freq > max_Rabi_freq:
        pulse_amplitude = max_Rabi_freq / Rabi_freq

    for other_qubit_id in device.get_qubit_list():
        if other_qubit_id == qubit_id:
            continue
        if channel_device not in device.get_qubit_excitation_channel_list(other_qubit_id).values():
            continue
        for other_qubit_channel, other_qubit_channel_device in device.get_qubit_excitation_channel_list(
                other_qubit_id).items():
            if other_qubit_channel_device == channel_device:
                other_qubit_channel_ = other_qubit_channel

        print('getting other qubit excitition pulse with qubit_id {} and channel {}'.format(other_qubit_id,
                                                                                            other_qubit_channel_))
        other_qubit_excitation_pulse = get_excitation_pulse(device=device,
                                                            qubit_id=other_qubit_id,
                                                            rotation_angle=2 * np.pi,
                                                            channel_amplitudes_override=channel_amplitudes(device, **{
                                                                other_qubit_channel_: amplitude_default}),
                                                            recalibrate=True)
        other_length = float(other_qubit_excitation_pulse.metadata['length'])
        channel_amplitudes_ = device.exdir_db.select_measurement_by_id(
            other_qubit_excitation_pulse.references['channel_amplitudes'])
        other_amplitude = float(channel_amplitudes_.metadata[other_qubit_channel_])

        other_qubit_Rabi_freq = 1 / (other_length * other_amplitude)
        print('other_qubit_Rabi_freq', other_qubit_Rabi_freq)

        if np.isfinite(other_qubit_Rabi_freq):

            max_parasitic_Rabi = max_parasitic_Rabi_ratio * np.abs(
                device.get_qubit_fq(other_qubit_id) - device.get_qubit_fq(qubit_id))
            # Rabi_freq_over_detuning = other_qubit_Rabi_freq/np.abs(device.get_qubit_fq(other_qubit_id)-device.get_qubit_ids(qubit_id))
            if other_qubit_Rabi_freq * pulse_amplitude > max_parasitic_Rabi:
                pulse_amplitude = max_parasitic_Rabi / other_qubit_Rabi_freq

            print('max_parasitic_Rabi', max_parasitic_Rabi)
            print('other_qubit_Rabi_freq', other_qubit_Rabi_freq)

    rect_length_preferred = 0.5 / (Rabi_freq * pulse_amplitude)  # for a pi-pulse
    gauss_length_preferred = rect_length_preferred / per_amplitude_angle_guess(1, 1 / sigmas_in_gauss)

    print('Rabi_freq', Rabi_freq, 'pulse_amplitude', pulse_amplitude)
    print('Non-rounded (rect): ', rect_length_preferred)
    print('Non-rounded (gauss_length_preferred):', gauss_length_preferred)

    rect_length_preferred = np.ceil(rect_length_preferred / pulse_length_alignment) * pulse_length_alignment
    gauss_length_preferred = np.ceil(gauss_length_preferred / pulse_length_alignment) * pulse_length_alignment

    print('gauss_length_preferred:', gauss_length_preferred)

    return gauss_length_preferred  # rect_length_preferred, gauss_length_preferred


def per_amplitude_angle_guess(length, sigma):
    from scipy.special import erf
    '''
    Caluclates the ratio of amplitude (or length) of rectangular pulses of given length with given sigma
    Parameters
    ----------
    length
    sigma

    Returns
    -------
    angle(gaussian)/angle(rect)
    '''
    erf_arg = length / (np.sqrt(8) * sigma)
    cutoff = np.exp(-erf_arg ** 2)
    erf_results = 0.5 * (1 + erf(erf_arg))
    print('length: ', length)
    print('sigma: ', sigma)
    print('cutoff: ', cutoff)
    print('erf_arg: ', erf_arg)
    print('erf result', erf_results)
    print('infinite length result: ', sigma * np.sqrt(2 * np.pi))
    result = 1 / (1 - cutoff) * (sigma * np.sqrt(2 * np.pi) * erf_results - length * np.exp(-erf_arg ** 2))
    print('finite length result', result)

    return result


def gauss_hd_Rabi_amplitude(device, qubit_id, channel_amplitudes, rotation_angle, amplitudes, length, sigma, alpha,
                            num_pulses, control_sequence):
    # readout_pulse = get_qubit_readout_pulse(device, qubit_id)
    readout_pulse, measurer = get_uncalibrated_measurer(device, qubit_id)

    metadata = {'qubit_id': qubit_id,
                'rotation_angle': rotation_angle,
                'sigma': sigma,
                'length': length,
                'num_pulses': num_pulses, }
    references = {'channel_amplitudes': channel_amplitudes.id}

    exitation_channel = [i for i in device.get_qubit_excitation_channel_list(qubit_id).keys()][0]
    control_sequence.awg.set_register(control_sequence.params['sequencer_id'], control_sequence.params['var_reg0'], num_pulses)

    def set_amplitude(amplitude):
        control_sequence.set_awg_amp(amplitude*float(channel_amplitudes.metadata[exitation_channel]))
        #raise ValueError('fallos')
    measurement = device.sweeper.sweep(measurer,
                                       (amplitudes, set_amplitude, 'Amplitude'),
                                       measurement_type='gauss_hd_Rabi_amplitude',
                                       metadata=metadata,
                                       references=references)
    return measurement


def gauss_hd_Rabi_alpha_adaptive(device, qubit_id, preferred_length=None, transition='01'):
    # min_step = float(device.get_qubit_constant(qubit_id=qubit_id, name='adaptive_Rabi_min_step'))
    readout_pulse, measurer = get_uncalibrated_measurer(device=device, qubit_id=qubit_id)

    #scan_points = int(device.get_qubit_constant(qubit_id=qubit_id, name='adaptive_Rabi_alpha_scan_points'))
    scan_points = 32
    _range = float(device.get_qubit_constant(qubit_id=qubit_id, name='adaptive_Rabi_alpha_range'))
    max_scan_length = float(device.get_qubit_constant(qubit_id=qubit_id, name='adaptive_Rabi_max_scan_length'))
    sigmas_in_gauss = float(device.get_qubit_constant(qubit_id=qubit_id, name='sigmas_in_gauss'))

    adaptive_measurements = []

    def infer_alpha_from_measurements():
        alphas = adaptive_measurements[-1].datasets['iq' + qubit_id].parameters[0].values
        measurement_interpolated_combined = np.zeros(alphas.shape)
        measurement_projector = np.conj(np.mean(adaptive_measurements[0].datasets['iq' + qubit_id].data))
        for measurement in adaptive_measurements:
            measurement_interpolated_combined += np.interp(alphas,
                                                           measurement.datasets['iq' + qubit_id].parameters[0].values,
                                                           np.real(measurement.datasets[
                                                                       'iq' + qubit_id].data * measurement_projector), )
        return alphas[np.argmin(measurement_interpolated_combined)]

    pi2_pulse = get_excitation_pulse_from_gauss_hd_Rabi_amplitude(device=device, qubit_id=qubit_id,
                                                                  rotation_angle=np.pi / 2.)
    channel_amplitudes_ = device.exdir_db.select_measurement_by_id(pi2_pulse.references['channel_amplitudes'])
    if len(channel_amplitudes_.metadata) > 2:
        raise ValueError('Default excitation pulse has more than one excitation channel')
    channel = [channel for channel in channel_amplitudes_.metadata.keys()][0]

    if preferred_length is None:
        pulse_length = float(pi2_pulse.metadata['length'])
    else:
        pulse_length = preferred_length
    #amplitude = float(pi2_pulse.metadata['amplitude'])
    #sigma = pulse_length / sigmas_in_gauss

    max_num_pulses = max_scan_length / pulse_length
    num_pulses = 1
    #alpha_guess = 0.0  # np.pi
    #alpha_range = 1e-8  # 2*np.pi
    #alphas = np.linspace(alpha_guess - 0.5 * alpha_range, alpha_guess + 0.5 * alpha_range, scan_points)
    #measurement = gauss_hd_ape_alpha(device, qubit_id, alphas, 0, phase_sign='+')
    #adaptive_measurements.append(measurement)

    amplitude = float(pi2_pulse.metadata['amplitude'])
    sigma = float(pi2_pulse.metadata['sigma'])
    length = float(pi2_pulse.metadata['length'])

    fast_control = False
    alpha1 = 0
    phase = 0
    channel_pulses_xp = [(c, device.pg.gauss_hd, float(a) * amplitude, sigma, alpha1, phase, fast_control)
                             for c, a in channel_amplitudes_.metadata.items()]
    channel_pulses_xm = [(c, device.pg.gauss_hd, -float(a) * amplitude, sigma, alpha1, phase, fast_control)
                             for c, a in channel_amplitudes_.metadata.items()]
    fast_control = 'phase_correction'
    channel_pulses = [(c, device.pg.gauss_hd, float(a) * amplitude, sigma, alpha1, phase, fast_control)
                      for c, a in channel_amplitudes_.metadata.items()]

    prepare_seq = []
    prepare_seq.append(device.pg.pmulti(device, length, *tuple(channel_pulses_xp)))
    prepare_seq.append(device.pg.pmulti(device, length, *tuple(channel_pulses)))
    prepare_seq.append(device.pg.pmulti(device, length, *tuple(channel_pulses_xm)))

    #TODO
    exitation_channel = [i for i in device.get_qubit_excitation_channel_list(qubit_id).keys()][0]
    ex_channel = device.awg_channels[exitation_channel]
    if ex_channel.is_iq():
        control_seq_id = ex_channel.parent.sequencer_id
    else:
        control_seq_id = ex_channel.channel // 2
    ex_sequencers = []

    for seq_id in device.pre_pulses.seq_in_use:
        if seq_id != control_seq_id:
            ex_seq = zi_scripts.SIMPLESequence(sequencer_id=seq_id, awg=device.modem.awg,
                                               awg_amp=1, use_modulation=True, pre_pulses = [])
        else:
            ex_seq = zi_scripts.SIMPLESequence(sequencer_id=seq_id, awg=device.modem.awg,
                                               awg_amp=1, use_modulation=True, pre_pulses=[], control=True)
            control_sequence = ex_seq
        device.pre_pulses.set_seq_offsets(ex_seq)
        device.pre_pulses.set_seq_prepulses(ex_seq)
        ex_seq.start()
        ex_sequencers.append(ex_seq)
    control_sequence.awg.set_register(control_sequence.params['sequencer_id'],
                                      control_sequence.params['var_reg1'], int(1))

    sequence_control.set_preparation_sequence(device, ex_sequencers, prepare_seq)
    readout_sequencer = sequence_control.define_readout_control_seq(device, readout_pulse)
    readout_sequencer.start()

    alpha_guess = 0
    alpha_range = 2*np.pi
    alphas = np.linspace(alpha_guess - 0.5 * alpha_range, alpha_guess + 0.5 * alpha_range, scan_points)
    measurement = gauss_hd_ape_alpha(device, qubit_id, alphas, 0, ex_sequencers,
                                     control_sequence, readout_sequencer, phase_sign='+')
    adaptive_measurements.append(measurement)
    alpha_range /= int(_range)


    while (num_pulses <= max_num_pulses):
        # adaptive_measurements = []
        alphas = np.linspace(alpha_guess - 0.5 * alpha_range, alpha_guess + 0.5 * alpha_range, scan_points)
        measurement = gauss_hd_ape_alpha(device, qubit_id, alphas, num_pulses, ex_sequencers,
                                         control_sequence, readout_sequencer, phase_sign='+')
        adaptive_measurements.append(measurement)
        alpha_guess = infer_alpha_from_measurements()
        num_pulses *= int(_range)
        alpha_range /= int(_range)

    references = {('gauss_hd_Rabi_alpha', measurement.metadata['num_pulses']): measurement.id
                  for measurement in adaptive_measurements}
    references['channel_amplitudes'] = channel_amplitudes_.id
    references['frequency_controls'] = device.get_frequency_control_measurement_id(qubit_id)
    references['gauss_hd_Rabi_amplitude_adaptive'] = pi2_pulse.id

    metadata = {'amplitude': amplitude,
                'qubit_id': qubit_id,
                'alpha_guess': alpha1,
                'phase_guess': alpha_guess,
                'length': pulse_length,
                'sigma': sigma,
                'transition': transition
                }

    return device.exdir_db.save(measurement_type='gauss_hd_Rabi_alpha_adaptive',
                                references=references,
                                metadata=metadata)


def get_excitation_pulse_from_gauss_hd_Rabi_alpha(device, qubit_id, rotation_angle, transition='01', recalibrate=True):
    amplitude_scan = get_excitation_pulse_from_gauss_hd_Rabi_amplitude(device, qubit_id, rotation_angle,
                                                                       transition=transition, recalibrate=True)
    try:
        meas = device.exdir_db.select_measurement(measurement_type='gauss_hd_Rabi_alpha_adaptive',
                                                  metadata={'qubit_id': qubit_id,
                                                            'transition': transition,
                                                            })
        if rotation_angle == np.pi/2:
            phase = meas.metadata['phase_guess']
        if rotation_angle == np.pi:
            phase = 4*float(meas.metadata['phase_guess'])
        return gauss_hd_excitation_pulse(device, qubit_id=qubit_id, transition=transition,
                                         rotation_angle=rotation_angle,
                                         length=amplitude_scan.metadata['length'],
                                         sigma=amplitude_scan.metadata['sigma'],
                                         alpha=meas.metadata['alpha_guess'],
                                         phase=phase,
                                         amplitude=amplitude_scan.metadata['amplitude'],
                                         gauss_hd_Rabi_amplitude_adaptive_measurement=amplitude_scan.id,
                                         gauss_hd_ape_correction_adaptive_measurement=meas.id,
                                         channel_amplitudes=meas.references['channel_amplitudes'])
    except:
        if recalibrate:
            meas = gauss_hd_Rabi_alpha_adaptive(device, qubit_id, transition=transition)
            if rotation_angle == np.pi / 2:
                phase = meas.metadata['phase_guess']
            if rotation_angle == np.pi:
                phase = 4 * float(meas.metadata['phase_guess'])

        return gauss_hd_excitation_pulse(device, qubit_id=qubit_id, transition=transition,
                                         rotation_angle=rotation_angle,
                                         length=amplitude_scan.metadata['length'],
                                         sigma=amplitude_scan.metadata['sigma'],
                                         alpha=meas.metadata['alpha_guess'],
                                         phase=phase,
                                         amplitude=amplitude_scan.metadata['amplitude'],
                                         gauss_hd_Rabi_amplitude_adaptive_measurement=amplitude_scan.id,
                                         gauss_hd_ape_correction_adaptive_measurement=meas.id,
                                         channel_amplitudes=meas.references['channel_amplitudes'])


def gauss_hd_Rabi_amplitude_adaptive(device, qubit_id, inverse_rotation_cycles, preferred_length=None, transition='01',
                                     alpha=0, phase=0):
    # max_num_pulses =
    # get T2 result
    # coherence_measurement = get_Ramsey_coherence_measurement(device=device, qubit_id=qubit_id)
    # T2 = float(coherence_measurement.metadata['T'])
    # get default (rectangular) excitation pulse
    readout_pulse, measurer = get_uncalibrated_measurer(device, qubit_id)

    #min_step = float(device.get_qubit_constant(qubit_id=qubit_id, name='adaptive_Rabi_min_step'))
    #scan_points = int(device.get_qubit_constant(qubit_id=qubit_id, name='adaptive_Rabi_amplitude_scan_points'))
    scan_points = 32
    _range = float(device.get_qubit_constant(qubit_id=qubit_id, name='adaptive_Rabi_amplitude_range'))
    max_scan_length = float(device.get_qubit_constant(qubit_id=qubit_id, name='adaptive_Rabi_max_scan_length'))
    sigmas_in_gauss = float(device.get_qubit_constant(qubit_id=qubit_id, name='sigmas_in_gauss'))

    adaptive_measurements = []

    def infer_amplitude_from_measurements():
        amplitudes = adaptive_measurements[-1].datasets['iq' + qubit_id].parameters[0].values
        measurement_interpolated_combined = np.zeros(amplitudes.shape)
        measurement_projector = np.conj(np.mean(adaptive_measurements[0].datasets['iq' + qubit_id].data))
        for measurement in adaptive_measurements:
            measurement_interpolated_combined += np.interp(amplitudes,
                                                           measurement.datasets['iq' + qubit_id].parameters[0].values,
                                                           np.real(measurement.datasets[
                                                                       'iq' + qubit_id].data * measurement_projector), )
        return amplitudes[np.argmin(measurement_interpolated_combined)]

    rotation_angle = 2 * np.pi / inverse_rotation_cycles
    rect_pulse = get_rect_excitation_pulse(device, qubit_id, rotation_angle, transition=transition)
    channel_amplitudes = device.exdir_db.select_measurement_by_id(rect_pulse.references['channel_amplitudes'])
    if len(channel_amplitudes.metadata) > 2:
        raise ValueError('Default excitation pulse has more than one excitation channel')
    channel = [channel for channel in channel_amplitudes.metadata.keys()][0]
    if preferred_length is None:
        pulse_length = get_preferred_length(device, qubit_id, channel)
    else:
        pulse_length = preferred_length

    num_pulses = int(inverse_rotation_cycles)
    max_num_pulses = max_scan_length / pulse_length

    amplitude_guess = float(rect_pulse.metadata['length']) / per_amplitude_angle_guess(pulse_length,
                                                                                       pulse_length / sigmas_in_gauss)
    amplitude_range = 1.0*amplitude_guess
    # print ('rect_pulse.metadata[length]:', rect_pulse.metadata['length'])
    # print ('rotation_angle: ', rotation_angle)
    # print ('amplitude_guess: ', amplitude_guess)
    sigma = pulse_length / sigmas_in_gauss

    #TODO
    exitation_channel = [i for i in device.get_qubit_excitation_channel_list(qubit_id).keys()][0]
    ex_channel = device.awg_channels[exitation_channel]
    if ex_channel.is_iq():
        control_seq_id = ex_channel.parent.sequencer_id
    else:
        control_seq_id = ex_channel.channel // 2
    ex_sequencers = []

    for seq_id in device.pre_pulses.seq_in_use:
        if seq_id != control_seq_id:
            ex_seq = zi_scripts.SIMPLESequence(sequencer_id=seq_id, awg=device.modem.awg,
                                               awg_amp=1, use_modulation=True, pre_pulses = [])
        else:
            ex_seq = zi_scripts.SIMPLESequence(sequencer_id=seq_id, awg=device.modem.awg,
                                               awg_amp=1, use_modulation=True, pre_pulses=[], control=True)
            control_sequence = ex_seq
        device.pre_pulses.set_seq_offsets(ex_seq)
        device.pre_pulses.set_seq_prepulses(ex_seq)
        #device.modem.awg.set_sequence(ex_seq.params['sequencer_id'], ex_seq)
        ex_seq.start()
        ex_sequencers.append(ex_seq)
    fast_control = True
    channel_pulses = [(c, device.pg.gauss_hd, 1, sigma, alpha, phase, fast_control)
                      for c, a in channel_amplitudes.metadata.items()]
    prepare_seq = []
    prepare_seq.append(device.pg.pmulti(device, pulse_length, *tuple(channel_pulses)))
    sequence_control.set_preparation_sequence(device, ex_sequencers, prepare_seq)
    readout_sequencer = sequence_control.define_readout_control_seq(device, readout_pulse)
    readout_sequencer.start()


    while (num_pulses <= max_num_pulses):
        amplitudes = np.linspace(amplitude_guess - 0.5 * amplitude_range, amplitude_guess + 0.5 * amplitude_range,
                                 scan_points)

        control_sequence.awg.set_register(control_sequence.params['sequencer_id'], control_sequence.params['var_reg1'],
                                          int(inverse_rotation_cycles))
        measurement = gauss_hd_Rabi_amplitude(device, qubit_id, channel_amplitudes, rotation_angle, amplitudes,
                                              pulse_length, sigma, alpha, int(num_pulses/int(inverse_rotation_cycles)), control_sequence)

        adaptive_measurements.append(measurement)
        amplitude_guess = infer_amplitude_from_measurements()
        num_pulses *= int(_range)
        amplitude_range /= int(_range)

    references = {('gauss_hd_Rabi_amplitude', measurement.metadata['num_pulses']): measurement.id
                  for measurement in adaptive_measurements}
    references['channel_amplitudes'] = channel_amplitudes.id
    references['frequency_controls'] = device.get_frequency_control_measurement_id(qubit_id)
    metadata = {'amplitude_guess': amplitude_guess,
                'qubit_id': qubit_id,
                'alpha': alpha,
                'phase': phase,
                'inverse_rotation_cycles': inverse_rotation_cycles,
                'length': pulse_length,
                'sigma': sigma,
                'transition': transition}

    for seq in ex_sequencers:
        seq.stop()
    readout_sequencer.stop()

    return device.exdir_db.save(measurement_type='gauss_hd_Rabi_amplitude_adaptive',
                                references=references,
                                metadata=metadata)


def get_excitation_pulse_from_gauss_hd_Rabi_amplitude(device, qubit_id, rotation_angle, transition='01',
                                                      recalibrate=True):
    try:
        meas = device.exdir_db.select_measurement(measurement_type='gauss_hd_Rabi_amplitude_adaptive',
                                                  metadata={'qubit_id': qubit_id,
                                                            'inverse_rotation_cycles': int(
                                                                np.round(2 * np.pi / rotation_angle)),
                                                            'transition': transition,  # this is crap
                                                            })
        return gauss_hd_excitation_pulse(device, qubit_id=qubit_id, transition='01', rotation_angle=rotation_angle,
                                         length=meas.metadata['length'], sigma=meas.metadata['sigma'],
                                         alpha=meas.metadata['alpha'], amplitude=meas.metadata['amplitude_guess'],
                                         phase=meas.metadata['phase'],
                                         gauss_hd_Rabi_amplitude_adaptive_measurement=meas.id,
                                         channel_amplitudes=meas.references['channel_amplitudes'])
    except:
        traceback.print_stack()
        if recalibrate:
            meas = gauss_hd_Rabi_amplitude_adaptive(device, qubit_id, transition=transition,
                                                    inverse_rotation_cycles=int(np.round(2 * np.pi / rotation_angle)))
        else:
            raise

        return gauss_hd_excitation_pulse(device, qubit_id=qubit_id, transition=transition,
                                         rotation_angle=rotation_angle,
                                         length=meas.metadata['length'], sigma=meas.metadata['sigma'],
                                         alpha=meas.metadata['alpha'], amplitude=meas.metadata['amplitude_guess'],
                                         phase=meas.metadata['phase'],
                                         gauss_hd_Rabi_amplitude_adaptive_measurement=meas.id,
                                         channel_amplitudes=meas.references['channel_amplitudes'])


def Rabi_amplitude_measurements_query(qubit_id, frequency, transition, frequency_tolerance, frequency_controls,
                                      channel_amplitudes_override=None):
    '''
    Perfectly ugly query for retrieving Rabi oscillation measurements corresponding to a qubit, and, possibly, a 'channel'
    '''
    if channel_amplitudes_override is not None:
        channel_amplitudes_clause = 'AND channel_amplitudes.id = {}'.format(channel_amplitudes_override)
    else:
        channel_amplitudes_clause = ''

    query = '''SELECT measurement_id FROM (
    SELECT
        channel_amplitudes.id channel_amplitudes_id,
        measurement.id measurement_id,

    MIN(CAST (channel_calibration_frequency.value AS DECIMAL)) min_freq,
    MAX(CAST (channel_calibration_frequency.value AS DECIMAL)) max_freq

    FROM
    data measurement

    INNER JOIN metadata qubit_id_metadata ON
        qubit_id_metadata.data_id = measurement.id AND
        qubit_id_metadata.name = 'qubit_id' AND
        qubit_id_metadata.value = '{qubit_id}'

    INNER JOIN metadata transition_metadata ON
        transition_metadata.data_id = measurement.id AND
        transition_metadata.name = 'transition' AND
        transition_metadata.value = '{transition}'

    INNER JOIN reference channel_amplitudes_reference ON
        channel_amplitudes_reference.this = measurement.id AND
        channel_amplitudes_reference.ref_type = 'channel_amplitudes'

    INNER JOIN data channel_amplitudes ON
        channel_amplitudes.id = channel_amplitudes_reference.that

    INNER JOIN reference frequency_controls ON
        frequency_controls.this = measurement.id AND
        frequency_controls.ref_type = 'frequency_controls' AND
        frequency_controls.that = {frequency_controls}

    INNER JOIN metadata channel ON
        channel.data_id = channel_amplitudes.id

    INNER JOIN reference channel_calibration_reference ON
        channel_calibration_reference.ref_type='channel_calibration' AND
        channel_calibration_reference.this = channel.data_id

    INNER JOIN data channel_calibration ON
        channel_calibration.id = channel_calibration_reference.that

    INNER JOIN metadata channel_calibration_frequency ON
        channel_calibration_frequency.data_id = channel_calibration.id AND
        channel_calibration_frequency.name = 'frequency' 

    WHERE
        measurement.measurement_type = 'gauss_hd_Rabi_amplitude_adaptive' AND
        (NOT measurement.invalid OR (measurement.invalid IS NULL))
        {channel_amplitudes_clause}

    GROUP BY measurement_id, channel_amplitudes_id

    HAVING
        ABS(MIN(CAST (channel_calibration_frequency.value AS DECIMAL))- {frequency})<{frequency_tolerance}
        AND ABS(MAX(CAST (channel_calibration_frequency.value AS DECIMAL))- {frequency})<{frequency_tolerance}

    ) Rabi_measurements
'''
    return query.format(qubit_id=qubit_id,
                        transition=transition,
                        frequency=frequency,
                        frequency_tolerance=frequency_tolerance,
                        channel_amplitudes_clause=channel_amplitudes_clause,
                        frequency_controls=frequency_controls)


class gauss_hd_excitation_pulse(MeasurementState):
    def __init__(self, *args, **kwargs):
        self.device = args[0]
        if len(args) == 2 and isinstance(args[1], MeasurementState) and not len(kwargs):  # copy constructor
            super().__init__(args[1])
        else:  # otherwise initialize from dict and device
            metadata = {'qubit_id': kwargs['qubit_id'],
                        'transition': kwargs['transition'],
                        'rotation_angle': str(kwargs['rotation_angle']),
                        'pulse_type': 'gauss_hd',
                        'length': str(kwargs['length']),
                        'sigma': str(kwargs['sigma']),
                        'alpha': str(kwargs['alpha']),
                        'phase': str(kwargs['phase']),
                        'amplitude': str(kwargs['amplitude'])}

            if 'calibration_type' in kwargs:
                metadata['calibration_type'] = kwargs['calibration_type']

            references = {'channel_amplitudes': int(kwargs['channel_amplitudes']),
                          'gauss_hd_Rabi_amplitude_adaptive': int(
                              kwargs['gauss_hd_Rabi_amplitude_adaptive_measurement'])}

            if 'gauss_hd_ape_correction_adaptive_measurement' in kwargs:
                references['gauss_hd_ape_correction_adaptive'] = int(
                    kwargs['gauss_hd_ape_correction_adaptive_measurement'])

            # check if such measurement exists
            try:
                measurement = self.device.exdir_db.select_measurement(measurement_type='qubit_excitation_pulse',
                                                                      metadata=metadata, references_that=references)
                super().__init__(measurement)
            except:
                traceback.print_exc()
                super().__init__(measurement_type='qubit_excitation_pulse',
                                 sample_name=self.device.exdir_db.sample_name, metadata=metadata, references=references)
                self.device.exdir_db.save_measurement(self)

        # inverse_references = {v:k for k,v in self.references.items()}
        # print ('inverse_references in __init__:', inverse_references)
        self.channel_amplitudes = channel_amplitudes(
            self.device.exdir_db.select_measurement_by_id(self.references['channel_amplitudes']))

    def get_pulse_sequence(self, phase):
        channel_pulses = [
            (c, self.device.pg.gauss_hd, float(a) * float(self.metadata['amplitude']) * np.exp(1j * phase),
             float(self.metadata['sigma']), float(self.metadata['alpha']),float(self.metadata['phase']))
            for c, a in self.channel_amplitudes.metadata.items()]
        '''Warning'''
        pulse = [self.device.pg.pmulti(self.device, float(self.metadata['length']), *tuple(channel_pulses))]
        return pulse
