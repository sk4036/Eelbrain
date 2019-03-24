# Author: Christian Brodbeck <christianbrodbeck@nyu.edu>
"""
Sample MneExperiment. This experiment can be used with a sample dataset that
treats different parts of the recording from the MNE sample dataset as different
subjects. To produce the data directory for this experiment use (make sure
that the directory you specify exists)::

    >>> from eelbrain import datasets
    >>> datasets.setup_samples_experiment('~/Data')

Then you can use::

    >>> from sample_experiment import SampleExperiment
    >>> e = SampleExperiment("~/Data/SampleExperiment")

"""
from eelbrain.pipeline import *
from eelbrain import MneExperiment


FILTER_KWARGS = {
    'filter_length': 'auto',
    'l_trans_bandwidth': 'auto',
    'h_trans_bandwidth': 'auto',
    'phase': 'zero',
    'fir_window': 'hamming',
    'fir_design': 'firwin',
}


class SampleExperiment(MneExperiment):

    owner = "me@nyu.edu"

    meg_system = 'neuromag306mag'

    sessions = 'sample'

    defaults = {
        'epoch': 'target',
        'select_clusters': 'all',
    }

    variables = {
        'event': {(1, 2, 3, 4): 'target', 5: 'smiley', 32: 'button'},
        'side': {(1, 3): 'left', (2, 4): 'right'},
        'modality': {(1, 2): 'auditory', (3, 4): 'visual'}
    }

    raw = {
        'tsss': RawMaxwell('raw', st_duration=10., ignore_ref=True, st_correlation=.9, st_only=True),
        '1-40': RawFilter('tsss', 1, 40, **FILTER_KWARGS),
        'ica': RawICA('tsss', 'sample', method='fastica', n_components=0.95),
        'ica1-40': RawFilter('ica', 1, 40, **FILTER_KWARGS),
    }

    epochs = {
        # all target stimuli:
        'target': PrimaryEpoch('sample', "event == 'target'", tmax=0.3, decim=5),
        # only auditory stimulation
        'auditory': SecondaryEpoch('target', "modality == 'auditory'"),
        # only visual stimulation
        'visual': SecondaryEpoch('target', "modality == 'visual'"),
        # recombine auditory and visual
        'av': SuperEpoch(('auditory', 'visual')),
        # noise covariance
        'cov': SecondaryEpoch('target', tmax=0),
    }

    tests = {
        # T-test to compare left-sided vs right-sided stimulation
        'left=right': TTestRel('side', 'left', 'right'),
        # One-tailed test for auditory > visual stimulation
        'a>v': TTestRel('modality', 'auditory', 'visual', tail=1),
        # Two-stage
        'twostage': TwoStageTest(
            stage_1='side_left + modality_a',
            model='side % modality',
            vars={'side_left': "side == 'left'",
                  'modality_a': "modality == 'auditory'"}),
    }

    parcs = {
        'ac': CombinationParc('aparc', {'ac': 'transversetemporal'}),
    }


if __name__ == '__main__':
    e = SampleExperiment("~/Data/SampleExperiment")
