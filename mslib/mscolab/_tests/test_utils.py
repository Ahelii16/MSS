# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_user.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for user related routes.

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi

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

from mslib.mscolab.server import db, app
from mslib.mscolab.models import User
from mslib.mscolab.utils import get_recent_pid


class Test_Utils(object):
    def setup(self):
        self._app = app
        db.init_app(self._app)
        with self._app.app_context():
            self.user = User.query.filter_by(id=8).first()

    def test_get_recent_pid(self):
        with self._app.app_context():
            p_id = get_recent_pid(self.user)
        assert p_id == 3

    def teardown(self):
        pass
