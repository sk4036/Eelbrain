# Author: Christian Brodbeck <christianbrodbeck@nyu.edu>
import pytest

pytest.register_assert_rewrite('eelbrain.testing._testing')

from ._testing import (
    gui_test,
    requires_mne_sample_data, requires_module, requires_r_ez, slow_test,
    skip_on_windows,
    TempDir,
    assert_dataset_equal, assert_dataobj_equal, assert_source_space_equal,
    file_path, import_attr, path,
)
