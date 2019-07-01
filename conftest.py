# -*- coding: utf-8 -*-
"""

    mslib.conftest
    ~~~~~~~~~~~~~~

    common definitions for py.test

    This file is part of mss.

    :copyright: Copyright 2016-2017 Reimar Bauer
    :copyright: Copyright 2016-2019 by the mss team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
from __future__ import print_function


import imp
import sys
import pytest

from mslib.mswms.demodata import DataFiles
import mslib._tests.constants as constants


try:
    # package currently on pypi only
    # ToDo conda-forge package similiar to pykml
    from pyvirtualdisplay import Display
except ImportError:
    Display = None

if not constants.SERVER_CONFIG_FS.exists(constants.SERVER_CONFIG_FILE):
    print('\n configure testdata')
    # ToDo check pytest tmpdir_factory
    examples = DataFiles(data_fs=constants.DATA_FS,
                         server_config_fs=constants.SERVER_CONFIG_FS)
    examples.create_server_config(detailed_information=True)
    examples.create_data()

imp.load_source('mss_wms_settings', constants.SERVER_CONFIG_FILE_PATH)

sys.path.insert(0, constants.SERVER_CONFIG_FS.root_path)

# ToDo refactor
from mslib.mscolab.demodata import create_data
create_data()


@pytest.fixture(scope="session", autouse=True)
def configure_testsetup(request):
    if Display is not None:
        # needs for invisible window output xvfb installed,
        # default backend for visible output is xephyr
        # by visible=0 you get xvfb
        VIRT_DISPLAY = Display(visible=0, size=(1280, 1024))
        VIRT_DISPLAY.start()
        yield
        VIRT_DISPLAY.stop()
    else:
        yield


@pytest.fixture(scope="class")
def testdata_exists():
    if not constants.ROOT_FS.exists(u'mss'):
        pytest.skip("testdata not existing")
