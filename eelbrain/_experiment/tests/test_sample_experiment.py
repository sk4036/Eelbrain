# Author: Christian Brodbeck <christianbrodbeck@nyu.edu>
"""Test MneExperiment using mne-python sample data"""
from pathlib import Path
from os.path import join, exists
import pytest
import shutil
from warnings import catch_warnings, filterwarnings

import numpy as np
from numpy.testing import assert_almost_equal

from eelbrain import *
from eelbrain.pipeline import *
from eelbrain._exceptions import DefinitionError
from eelbrain.testing import TempDir, assert_dataobj_equal, import_attr, requires_mne_sample_data, slow_test


sample_path = Path(__file__).parents[3] / 'examples/experiment'


@requires_mne_sample_data
def test_sample():
    set_log_level('warning', 'mne')
    # import from file:  http://stackoverflow.com/a/67692/166700
    SampleExperiment = import_attr(sample_path / 'sample_experiment.py', 'SampleExperiment')
    tempdir = TempDir()
    datasets.setup_samples_experiment(tempdir, 3, 2)

    root = join(tempdir, 'SampleExperiment')
    e = SampleExperiment(root)

    assert e.get('raw') == '1-40'
    assert e.get('subject') == 'R0000'
    assert e.get('subject', subject='R0002') == 'R0002'

    # events
    e.set('R0001', rej='')
    ds = e.load_selected_events(epoch='target')
    assert ds.n_cases == 39
    ds = e.load_selected_events(epoch='auditory')
    assert ds.n_cases == 20
    ds = e.load_selected_events(epoch='av')
    assert ds.n_cases == 39
    
    # evoked cache invalidated by change in bads
    e.set('R0001', rej='', epoch='target')
    ds = e.load_evoked()
    assert ds[0, 'evoked'].info['bads'] == []
    e.make_bad_channels(['MEG 0331'])
    ds = e.load_evoked()
    assert ds[0, 'evoked'].info['bads'] == ['MEG 0331']

    e.set(rej='man', model='modality')
    sds = []
    for _ in e:
        e.make_epoch_selection(auto=2.5e-12)
        sds.append(e.load_evoked())

    ds = e.load_evoked('all')
    assert_dataobj_equal(combine(sds), ds)

    # sensor space tests
    megs = [e.load_evoked(cat='auditory')['meg'] for _ in e]
    res = e.load_test('a>v', 0.05, 0.2, 0.05, samples=100, data='sensor.rms', baseline=False, make=True)
    meg_rms = combine(meg.rms('sensor') for meg in megs).mean('case', name='auditory')
    assert_dataobj_equal(res.c1_mean, meg_rms, decimal=21)
    res = e.load_test('a>v', 0.05, 0.2, 0.05, samples=100, data='sensor.mean', baseline=False, make=True)
    meg_mean = combine(meg.mean('sensor') for meg in megs).mean('case', name='auditory')
    assert_dataobj_equal(res.c1_mean, meg_mean, decimal=21)
    with pytest.raises(IOError):
        res = e.load_test('a>v', 0.05, 0.2, 0.05, samples=20, data='sensor', baseline=False)
    res = e.load_test('a>v', 0.05, 0.2, 0.05, samples=20, data='sensor', baseline=False, make=True)
    assert res.p.min() == pytest.approx(.143, abs=.001)
    assert res.difference.max() == pytest.approx(4.47e-13, 1e-15)
    # plot
    e.plot_evoked(1, epoch='target', model='')

    # e._report_subject_info() broke with non-alphabetic subject order
    subjects = e.get_field_values('subject')
    ds = Dataset()
    ds['subject'] = Factor(reversed(subjects))
    ds['n'] = Var(range(3))
    s_table = e._report_subject_info(ds, '')

    # post_baseline_trigger_shift
    # use multiple of tstep to shift by even number of samples
    tstep = 0.008324800548266162
    shift = -7 * tstep
    class Experiment(SampleExperiment):
        epochs = {
            **SampleExperiment.epochs,
            'visual-s': SecondaryEpoch('target', "modality == 'visual'", post_baseline_trigger_shift='shift', post_baseline_trigger_shift_max=0, post_baseline_trigger_shift_min=shift),
        }
        variables = {
            **SampleExperiment.variables,
            'shift': LabelVar('side', {'left': 0, 'right': shift}),
            'shift_t': LabelVar('trigger', {(1, 3): 0, (2, 4): shift})
        }
    e = Experiment(root)
    # test shift in events
    ds = e.load_events()
    assert_dataobj_equal(ds['shift_t'], ds['shift'], name=False)
    # compare against epochs (baseline correction on epoch level rather than evoked for smaller numerical error)
    ep = e.load_epochs(baseline=True, epoch='visual', rej='').aggregate('side')
    evs = e.load_evoked(baseline=True, epoch='visual-s', rej='', model='side')
    tstart = ep['meg'].time.tmin - shift
    assert_dataobj_equal(evs[0, 'meg'], ep[0, 'meg'].sub(time=(tstart, None)), decimal=20)
    tstop = ep['meg'].time.tstop + shift
    assert_almost_equal(evs[1, 'meg'].x, ep[1, 'meg'].sub(time=(None, tstop)).x, decimal=20)

    # post_baseline_trigger_shift & multiple epochs with same time stamp
    class Experiment(SampleExperiment):
        epochs = {
            **SampleExperiment.epochs,
            'v1': {'base': 'visual', 'vars': {'shift': 'Var([0.0], repeat=len(side))'}},
            'v2': {'base': 'visual', 'vars': {'shift': 'Var([0.1], repeat=len(side))'}},
            'vc': {'sub_epochs': ('v1', 'v2'), 'post_baseline_trigger_shift': 'shift', 'post_baseline_trigger_shift_max': 0.1, 'post_baseline_trigger_shift_min': 0.0},
        }
        groups = {
            'group0': Group(['R0000']),
            'group1': SubGroup('all', ['R0000']),
        }
        variables = {
            'group': GroupVar(['group0', 'group1']),
            **SampleExperiment.variables,
        }
    e = Experiment(root)
    events = e.load_selected_events(epoch='vc')
    ds = e.load_epochs(baseline=True, epoch='vc')
    v1 = ds.sub("epoch=='v1'", 'meg').sub(time=(0, 0.199))
    v2 = ds.sub("epoch=='v2'", 'meg').sub(time=(-0.1, 0.099))
    assert_almost_equal(v1.x, v2.x, decimal=20)

    # duplicate subject
    class BadExperiment(SampleExperiment):
        groups = {'group': ('R0001', 'R0002', 'R0002')}
    with pytest.raises(DefinitionError):
        BadExperiment(root)

    # non-existing subject
    class BadExperiment(SampleExperiment):
        groups = {'group': ('R0001', 'R0003', 'R0002')}
    with pytest.raises(DefinitionError):
        BadExperiment(root)

    # unsorted subjects
    class Experiment(SampleExperiment):
        groups = {'group': ('R0002', 'R0000', 'R0001')}
    e = Experiment(root)
    assert [s for s in e] == ['R0000', 'R0001', 'R0002']

    # changes
    class Changed(SampleExperiment):
        variables = {
            'event': {(1, 2, 3, 4): 'target', 5: 'smiley', 32: 'button'},
            'side': {(1, 3): 'left', (2, 4): 'right_changed'},
            'modality': {(1, 2): 'auditory', (3, 4): 'visual'}
        }
        tests = {
            'twostage': TwoStageTest(
                'side_left + modality_a',
                {'side_left': "side == 'left'",
                 'modality_a': "modality == 'auditory'"}),
            'novars': TwoStageTest('side + modality'),
        }
    e = Changed(root)

    # changed variable, while a test with model=None is not changed
    class Changed(Changed):
        variables = {
            'side': {(1, 3): 'left', (2, 4): 'right_changed'},
            'modality': {(1, 2): 'auditory', (3, 4): 'visual_changed'}
        }
    e = Changed(root)

    # changed variable, unchanged test with vardef=None
    class Changed(Changed):
        variables = {
            'side': {(1, 3): 'left', (2, 4): 'right_changed'},
            'modality': {(1, 2): 'auditory', (3, 4): 'visual_changed'}
        }
    e = Changed(root)

    # ICA
    # ---
    class Experiment(SampleExperiment):
        raw = {
            'apply-ica': RawApplyICA('tsss', 'ica'),
            **SampleExperiment.raw,
        }
    e = Experiment(root)
    ica_path = e.make_ica(raw='ica')
    e.set(raw='ica1-40', model='')
    e.make_epoch_selection(auto=2e-12, overwrite=True)
    ds1 = e.load_evoked(raw='ica1-40')
    ica = e.load_ica(raw='ica')
    ica.exclude = [0, 1, 2]
    ica.save(ica_path)
    ds2 = e.load_evoked(raw='ica1-40')
    assert not np.allclose(ds1['meg'].x, ds2['meg'].x, atol=1e-20), "ICA change ignored"
    # apply-ICA
    with catch_warnings():
        filterwarnings('ignore', "The measurement information indicates a low-pass frequency", RuntimeWarning)
        ds1 = e.load_evoked(raw='ica', rej='')
        ds2 = e.load_evoked(raw='apply-ica', rej='')
    assert_dataobj_equal(ds2, ds1)

    # rename subject
    # --------------
    src = Path(e.get('raw-dir', subject='R0001'))
    dst = Path(e.get('raw-dir', subject='R0003', match=False))
    shutil.move(src, dst)
    for path in dst.glob('*.fif'):
        shutil.move(path, dst / path.parent / path.name.replace('R0001', 'R0003'))
    # check subject list
    e = SampleExperiment(root)
    assert list(e) == ['R0000', 'R0002', 'R0003']
    # check that cached test got deleted
    assert e.get('raw') == '1-40'
    with pytest.raises(IOError):
        e.load_test('a>v', 0.05, 0.2, 0.05, samples=20, data='sensor', baseline=False)
    res = e.load_test('a>v', 0.05, 0.2, 0.05, samples=20, data='sensor', baseline=False, make=True)
    assert res.df == 2
    assert res.p.min() == pytest.approx(.143, abs=.001)
    assert res.difference.max() == pytest.approx(4.47e-13, 1e-15)

    # remove subject
    # --------------
    shutil.rmtree(dst)
    # check cache
    e = SampleExperiment(root)
    assert list(e) == ['R0000', 'R0002']
    # check that cached test got deleted
    assert e.get('raw') == '1-40'
    with pytest.raises(IOError):
        e.load_test('a>v', 0.05, 0.2, 0.05, samples=20, data='sensor', baseline=False)


@requires_mne_sample_data
@slow_test
def test_sample_source():
    set_log_level('warning', 'mne')
    SampleExperiment = import_attr(sample_path / 'sample_experiment.py', 'SampleExperiment')
    tempdir = TempDir()
    datasets.setup_samples_experiment(tempdir, 3, 2, mris=True)  # TODO: use sample MRI which already has forward solution
    root = join(tempdir, 'SampleExperiment')
    e = SampleExperiment(root)

    # source space tests
    e.set(src='ico-4', rej='', epoch='auditory')
    # These two tests are only identical if the evoked has been cached before the first test is loaded
    ds = e.load_evoked(-1, model='side')
    resp = e.load_test('left=right', 0.05, 0.2, 0.05, samples=100, parc='ac', make=True)
    resm = e.load_test('left=right', 0.05, 0.2, 0.05, samples=100, mask='ac', make=True)
    assert_dataobj_equal(resp.t, resm.t)
    # ROI tests
    e.set(epoch='target')
    ress = e.load_test('left=right', 0.05, 0.2, 0.05, samples=100, data='source.rms', parc='ac', make=True)
    res = ress.res['ac-lh']
    assert res.p.min() == pytest.approx(0.429, abs=.001)
    ress = e.load_test('twostage', 0.05, 0.2, 0.05, samples=100, data='source.rms', parc='ac', make=True)
    res = ress.res['ac-lh']


@requires_mne_sample_data
def test_sample_sessions():
    set_log_level('warning', 'mne')
    SampleExperiment = import_attr(sample_path / 'sample_experiment_sessions.py', 'SampleExperiment')
    tempdir = TempDir()
    datasets.setup_samples_experiment(tempdir, 2, 1, 2)

    class Experiment(SampleExperiment):

        raw = {
            'ica': RawICA('raw', ('sample1', 'sample2'), 'fastica', max_iter=1),
            **SampleExperiment.raw,
        }

    root = join(tempdir, 'SampleExperiment')
    e = Experiment(root)
    # bad channels
    e.make_bad_channels('0111')
    assert e.load_bad_channels() == ['MEG 0111']
    assert e.load_bad_channels(session='sample2') == []
    e.show_bad_channels()
    e.merge_bad_channels()
    assert e.load_bad_channels(session='sample2') == ['MEG 0111']
    e.show_bad_channels()

    # rejection
    for _ in e:
        for epoch in ('target1', 'target2'):
            e.set(epoch=epoch)
            e.make_epoch_selection(auto=2e-12)

    ds = e.load_evoked('R0000', epoch='target2')
    e.set(session='sample1')
    ds2 = e.load_evoked('R0000')
    assert_dataobj_equal(ds2, ds)

    # super-epoch
    ds1 = e.load_epochs(epoch='target1')
    ds2 = e.load_epochs(epoch='target2')
    ds_super = e.load_epochs(epoch='super')
    assert_dataobj_equal(ds_super['meg'], combine((ds1['meg'], ds2['meg'])))

    # conflicting session and epoch settings
    rej_path = join(root, 'meg', 'R0000', 'epoch selection', 'sample2_1-40_target2-man.pickled')
    e.set(epoch='target2', raw='1-40')
    assert not exists(rej_path)
    e.set(session='sample1')
    e.make_epoch_selection(auto=2e-12)
    assert exists(rej_path)

    # ica
    e.set('R0000', raw='ica')
    with catch_warnings():
        filterwarnings('ignore', "FastICA did not converge", UserWarning)
        assert e.make_ica() == join(root, 'meg', 'R0000', 'R0000 ica-ica.fif')
