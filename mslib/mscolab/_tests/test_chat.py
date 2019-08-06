# -*- coding: utf-8 -*-
"""

    mslib.mscolab._tests.test_chat
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tests for chat functionalities

    This file is part of mss.

    :copyright: Copyright 2019 Shivashis Padhi
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
import socketio
import requests
import json
import multiprocessing
import datetime
import time

from mslib.mscolab.models import Message
from mslib.mscolab.sockets_manager import cm
from mslib._tests.constants import MSCOLAB_URL_TEST
from mslib.mscolab.conf import TEST_SQLALCHEMY_DB_URI
from mslib.mscolab.server import db, sockio, app


class Test_Chat(object):

    def setup(self):
        self.sockets = []
        app.config['SQLALCHEMY_DATABASE_URI'] = TEST_SQLALCHEMY_DB_URI
        self.p = multiprocessing.Process(
            target=sockio.run,
            args=(app,),
            kwargs={'port': 8083})
        self.p.start()
        self.app = app
        db.init_app(self.app)
        time.sleep(3)

    def test_send_message(self):
        r = requests.post(MSCOLAB_URL_TEST + "/token", data={
                          'email': 'a',
                          'password': 'a'
                          })
        response = json.loads(r.text)
        # standard Python
        sio = socketio.Client()

        def handle_chat_message(message):
            pass

        sio.on('chat-message-client', handler=handle_chat_message)
        sio.connect(MSCOLAB_URL_TEST)
        sio.emit('start', response)
        sio.sleep(2)
        self.sockets.append(sio)
        sio.emit("chat-message", {
                 "p_id": 1,
                 "token": response['token'],
                 "message_text": "message from 1"
                 })
        # testing non-ascii message
        sio.emit("chat-message", {
                 "p_id": 1,
                 "token": response['token'],
                 "message_text": "® non ascii"
                 })
        sio.sleep(2)
        with self.app.app_context():
            message = Message.query.filter_by(text="message from 1").first()
            assert message.p_id == 1
            assert message.u_id == 8

            message = Message.query.filter_by(text="® non ascii").first()
            assert message is not None
            Message.query.filter_by(text="message from 1").delete()
            Message.query.filter_by(text="® non ascii").delete()
            db.session.commit()

    def test_get_messages(self):
        r = requests.post(MSCOLAB_URL_TEST + "/token", data={
                          'email': 'a',
                          'password': 'a'
                          })
        response = json.loads(r.text)
        # standard Python
        sio = socketio.Client()

        def handle_chat_message(message):
            pass

        sio.on('chat-message-client', handler=handle_chat_message)
        sio.connect(MSCOLAB_URL_TEST)
        sio.emit('start', response)
        sio.sleep(2)
        self.sockets.append(sio)
        sio.emit("chat-message", {
                 "p_id": 1,
                 "token": response['token'],
                 "message_text": "message from 1"
                 })
        sio.emit("chat-message", {
                 "p_id": 1,
                 "token": response['token'],
                 "message_text": "message from 1"
                 })
        sio.sleep(2)
        with self.app.app_context():
            messages = cm.get_messages(1)
            assert len(messages) == 2
            assert messages[0]["user"] == 8

            messages = cm.get_messages(1, last_timestamp=datetime.datetime(1970, 1, 1))
            assert len(messages) == 2
            assert messages[0]["user"] == 8

            messages = cm.get_messages(1, last_timestamp=datetime.datetime.now())
            assert len(messages) == 0

    def test_get_messages_api(self):
        r = requests.post(MSCOLAB_URL_TEST + "/token", data={
                          'email': 'a',
                          'password': 'a'
                          })
        response = json.loads(r.text)
        token = response["token"]
        data = {
            "token": token,
            "p_id": 1,
            "timestamp": datetime.datetime(1970, 1, 1).strftime("%m %d %Y, %H:%M:%S")
        }
        # returns an array of messages
        r = requests.post(MSCOLAB_URL_TEST + "/messages", data=data)
        response = json.loads(r.text)
        assert len(response["messages"]) == 2

        data["token"] = "dummy"
        # returns False due to bad authorization
        r = requests.post(MSCOLAB_URL_TEST + "/messages", data=data)
        assert r.text == "False"
        with self.app.app_context():
            Message.query.filter_by(text="message from 1").delete()
            db.session.commit()

    def teardown(self):
        for socket in self.sockets:
            socket.disconnect()
        self.p.terminate()
