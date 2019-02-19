# skip test: data unavailable
from eelbrain.pipeline import *


class Mouse(MneExperiment):

    sessions = 'CAT'

    raw = {
        'tsss': RawMaxwell('raw', st_duration=10., ignore_ref=True, st_correlation=0.9, st_only=True),
        '1-40': RawFilter('tsss', 1, 40),
        'fastica': RawICA('tsss', 'CAT', 'fastica', n_components=0.99),
        'fastica1-40': RawFilter('fastica', 1, 40),
    }

    variables = {
        'stimulus': LabelVar('trigger', {(162, 163): 'target', (166, 167): 'prime'}),
        'prediction': LabelVar('trigger', {(162, 166): 'expected', (163, 167): 'unexpected'}),
    }

    epochs = {
        'word': PrimaryEpoch('CAT', "stimulus.isin(('prime', 'target'))", samplingrate=200),
        'prime': SecondaryEpoch('word', "stimulus == 'prime'"),
        'target': SecondaryEpoch('word', "stimulus == 'target'"),
        'cov': SecondaryEpoch('prime', tmax=0),
    }

    tests = {
        '=0': TTestOneSample(),
        'surprise': TTestRel('prediction', 'unexpected', 'expected'),
    }

    parcs = {
        'frontotemporal-lh': CombinationParc('aparc', {
            'frontal-lh': 'parsorbitalis + parstriangularis + parsopercularis',
            'temporal-lh': 'transversetemporal + superiortemporal + middletemporal + inferiortemporal + bankssts',
            }, views='lateral'),
    }


root = '~/Data/Mouse'
e = Mouse(root)
