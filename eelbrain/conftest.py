# Author: Christian Brodbeck <christianbrodbeck@nyu.edu>


def pytest_addoption(parser):
    parser.addoption('--slowtests', action='store_true', dest="slow_tests", default=False, help="Enable slow tests")
