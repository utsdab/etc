# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import json
import math
import time
import uuid
import errno
import struct
import socket
import logging
import threading
import xml.etree.cElementTree as etree

from PySide import QtCore, QtGui

from . import callback_event

PYTHON_REQUEST = 1
PYTHON_RESPONSE = 2
PYTHON_QUIT = 3
ACTIVATE_PYTHON = 4

PING = 5  # ENQ
PONG = 6  # ACK

PYTHON_CALLBACK = 10004
SET_PORT = 10005

HEARTBEAT_TIMEOUT = 'SGTK_PHOTOSHOP_HEARTBEAT_TIMEOUT'
HEARTBEAT_INTERVAL = 'SGTK_PHOTOSHOP_HEARTBEAT_INTERVAL'
HEARTBEAT_TOLERANCE = 'SGTK_PHOTOSHOP_HEARTBEAT_TOLERANCE'
PHOTOSHOP_TIMEOUT = 'SGTK_PHOTOSHOP_TIMEOUT'
NETWORK_DEBUG = os.getenv('SGTK_PHOTOSHOP_NETWORK_DEBUG')

# global RemoteObject for the photoshop application itself
photoshop_instance = None


def handle_show_log():
    app = QtCore.QCoreApplication.instance()
    win = app.property('tk-photoshop.log_console')
    win.setHidden(False)
    win.activateWindow()
    win.raise_()


class FlexRequest(object):
    @classmethod
    def setup(cls, remote_port, heartbeat_port):

        cls.requests = {}
        cls.callbacks = {}
        cls.remote_port = remote_port
        cls.heartbeat_port = heartbeat_port
        cls.local_port = None
        cls.logger = logging.getLogger('sgtk.photoshop.flexbase.FlexRequest')

        # create a server socket
        cls.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cls.server.bind(('127.0.0.1', 0))
        cls.server.listen(socket.SOMAXCONN)
        cls.local_port = cls.server.getsockname()[1]
        cls.logger.info('listening on port %s', cls.local_port)
        # send the local port back to the plugin
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', cls.remote_port))
        # send in multiple pack calls to avoid alignment issues
        sent = s.send(struct.pack("=i", SET_PORT))
        if sent == 0:
            cls.logger.error("setup: error sending listen port command")
        sent = s.send(struct.pack("=i", cls.local_port))
        if sent == 0:
            cls.logger.error("setup: error sending listen port")
        s.close()

        server = threading.Thread(target=cls.ListenThreadRun, name="FlexListenThread")
        server.start()

        heartbeat = threading.Thread(target=cls.HeartbeatThreadRun, name="HeartbeatThread")
        heartbeat.start()

        # initialize the photoshop app
        global photoshop_instance
        photoshop_instance = requestStatic('com.adobe.csawlib.photoshop.Photoshop', 'app')

    @classmethod
    def ActivatePython(cls):
        """
        This method will send a signal to Photoshop which will set the foreground window to
        be the QT window.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', cls.remote_port))
        sent = s.send(struct.pack("=i", ACTIVATE_PYTHON))
        if sent == 0:
            cls.logger.error("ActivatePython: send did not send data")
        if NETWORK_DEBUG is not None:
            cls.logger.info("[Network Debug] ActivatePython send %d to 127.0.0.1:%s",
                sent, cls.remote_port)

    @classmethod
    def HeartbeatThreadRun(cls):
        try:
            timeout = float(os.getenv(HEARTBEAT_TIMEOUT, '0.5'))
        except:
            cls.logger.error("Error setting timeout from %s: %s",
                HEARTBEAT_TIMEOUT, os.getenv(HEARTBEAT_TIMEOUT))

        try:
            interval = float(os.getenv(HEARTBEAT_INTERVAL, '0.2'))
        except:
            cls.logger.error("Error setting interval from %s: %s",
                HEARTBEAT_INTERVAL, os.getenv(HEARTBEAT_INTERVAL))

        try:
            tolerance = int(os.getenv(HEARTBEAT_TOLERANCE, '2'))
        except:
            cls.logger.error("Error setting tolerance from %s: %s",
                HEARTBEAT_TOLERANCE, os.getenv(HEARTBEAT_TOLERANCE))

        error_cycle = 0
        while True:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect(('127.0.0.1', cls.heartbeat_port))

            while True:
                time.sleep(interval)
                try:
                    sent = s.send(struct.pack("=i", PING))
                    if sent == 0:
                        cls.logger.error("Heartbeat: send did not send data")
                        error_cycle += 1
                        continue

                    bytes = struct.calcsize("=i")
                    received = s.recv(bytes)
                    if len(received) != bytes:
                        cls.logger.error("Python: Heartbeat protocol error: too few bytes read: %d/%d" % (len(received), bytes))
                        error_cycle += 1
                        continue

                    response = struct.unpack("=i", received)[0]
                    if response == PONG:
                        error_cycle = 0
                    else:
                        cls.logger.error("Python: Heartbeat unknown response: %s", response)
                        error_cycle += 1
                except socket.timeout:
                    cls.logger.info("Python: Heartbeat timeout")
                    error_cycle += 1
                except socket.error, e:
                    cls.logger.exception("Python: Heartbeat standard error: %s", errno.errorcode[e.errno])
                    error_cycle += 1
                except Exception, e:
                    cls.logger.exception("Python: Heartbeat unknown exception: %s" % e)
                if error_cycle >= tolerance:
                    cls.logger.error("Python: Quitting.  Heartbeat errors greater than tolerance.")
                    os._exit(0)

    @classmethod
    def ListenThreadRun(cls):
        while True:
            (client, _) = cls.server.accept()

            if NETWORK_DEBUG is not None:
                cls.logger.info("[Network Debug] Accepted Connection")

            handler = threading.Thread(target=cls.HandleConnection, name="FlexConnectionHandler", args=(client, ))
            handler.start()

    @classmethod
    def HandleConnection(cls, sock):
        bytes = struct.calcsize("=i")
        received = sock.recv(bytes)
        if len(received) != bytes:
            cls.logger.error("protocol error: type could not be read")
            return

        type = struct.unpack("=i", received)[0]
        if type == PYTHON_RESPONSE:
            xml = ''
            while True:
                buf = sock.recv(4096)
                if not buf:
                    break
                xml += buf
            if NETWORK_DEBUG is not None:
                cls.logger.info("[Network Debug] Received Python Response\n\n%s\n\n", xml)
            dom = etree.XML(xml)
            type = dom.find('type').text
            if type == 'requestResponse':
                uid = dom.find('uid').text
                response = dom.find('data').text
                # and send it back to the request
                FlexRequest.requests[uid]['cond'].acquire()
                FlexRequest.requests[uid]['response'] = response
                FlexRequest.requests[uid]['responded'] = True
                FlexRequest.requests[uid]['cond'].notify_all()
                FlexRequest.requests[uid]['cond'].release()
            elif type == 'callback':
                uid = dom.find('uid').text
                cls.logger.debug('callback: %s', uid)
                callback_event.send_to_main_thread(cls.callbacks[uid])
            elif type == 'menu_click':
                menu_id = dom.find('id').text
                if menu_id == 'show_log':
                    callback_event.send_to_main_thread(handle_show_log)
            elif type == 'app_event':
                event = dom.find('event').text
                cls.logger.debug("event: %s", event)
            elif type == 'reinitialize':
                # panel has been closed and reopened
                # the flex uid cache is cleared when that happens, so update the app object
                global photoshop_instance
                new_app = requestStatic('com.adobe.csawlib.photoshop.Photoshop', 'app')
                photoshop_instance._uid = new_app._uid
            else:
                cls.logger.error('unknown python request type %s', type)
        else:
            cls.logger.error('unknown event type %d', type)

    def __init__(self, request):
        self.request = request
        self.response = None

    def __call__(self):
        # register this call for the response
        uid = str(uuid.uuid4())
        self.requests[uid] = {
            'cond': threading.Condition(),
            'response': None,
            'responded': False,
        }

        try:
            # build up request xml
            request = etree.Element("request")

            element = etree.Element("uid")
            element.text = str(uid)
            request.append(element)

            element = etree.Element("data")
            element.text = str(self.request)
            request.append(element)

            # send request
            FlexRequest.requests[uid]['cond'].acquire()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('127.0.0.1', self.remote_port))

            req_str = etree.tostring(request)
            sent = s.send(struct.pack("ii", PYTHON_REQUEST, len(req_str)))
            totalsent = 0
            while totalsent < len(req_str):
                sent = s.send(req_str[totalsent:])
                if sent == 0:
                    self.logger.info("SENT 0, error in sending")
                    return
                totalsent += sent

            bytes = struct.calcsize("=i")
            recieved = s.recv(bytes)
            if len(recieved) != bytes:
                raise RuntimeError("protocol error reading flex response")
            response = struct.unpack("=i", recieved)[0]
            if (response != 0):
                self.logger.error("SENT response non-zero: %d", response)

            s.close()

            if NETWORK_DEBUG is not None:
                self.logger.info("[Network Debug] Sent Python Request %d bytes "
                    "to 127.0.0.1:%s\n%s\n", totalsent, self.remote_port, req_str)

            self.logger.debug("--> Sent Flex Request: %s" % req_str)

            # wait for response to come through
            try:
                timeout = float(os.getenv(PHOTOSHOP_TIMEOUT, '300.0'))
            except:
                self.logger.error("Error setting timeout from %s: %s",
                    PHOTOSHOP_TIMEOUT, os.getenv(PHOTOSHOP_TIMEOUT))
            tick_length = 0.1
            num_ticks = math.ceil(timeout/tick_length)
            for tick in range(0, int(num_ticks)):
                if self.requests[uid]['responded']:
                    break
                # self.logger.error("Tick: %d" % tick)
                self.requests[uid]['cond'].wait(timeout/num_ticks)

                # make sure QApplication has had a chance to process events:
                QtGui.QApplication.processEvents()

            if not self.requests[uid]['responded']:
                self.logger.error("No response to: %s" % uid)
                raise RuntimeError('timeout waiting for response: %s' % self.request)

            # response is now available, grab it
            result = self.requests[uid]['response']
            self.logger.debug("<-- Got Flex Response: %s" % result)
        except:
            self.logger.exception("Error in FlexRequest.__call__")
            raise
        finally:
            del self.requests[uid]

        return result


def setup(remote_port, heartbeat_port):
    FlexRequest.setup(remote_port, heartbeat_port)


def initialize():
    FlexRequest.initialize()


def dictToPython(d):
    # Boolean, Date, Error, Function, Vector, XML, XMLList
    if d is None:
        return None
    if d['type'] in ['null', 'undefined']:
        return None
    if d['type'] in ['String', 'Number', 'Boolean', 'int', 'uint']:
        return d['value']
    if d['type'] == 'Array':
        return [dictToPython(e) for e in d['value']]
    if d['type'] == 'class':
        return RemoteClass(d['cls'])
    if d['type'] == 'RemoteObject':
        return RemoteObject(d['cls'], uid=d['obj_uid'])
    if d['type'] == 'error':
        raise RuntimeError(d['stack'])
    raise ValueError("Unknown reponse object '%s'", d)


def pythonToDict(v):
    if v is None:
        return {'type': 'null'}
    if isinstance(v, str) or isinstance(v, unicode):
        return {'type': 'String', 'value': v}
    if isinstance(v, bool):
        return {'type': 'Boolean', 'value': v}
    if isinstance(v, int):
        return {'type': 'int', 'value': v}
    if isinstance(v, float):
        return {'type': 'Number', 'value': v}
    if isinstance(v, (list, tuple)):
        return {'type': 'Array', 'value': [pythonToDict(e) for e in v]}
    if isinstance(v, RemoteClass):
        return {'type': 'Class', 'cls': v._cls}
    if isinstance(v, RemoteObject):
        return {'type': 'RemoteObject', 'cls': v._cls, 'obj_uid': v._uid}
    raise ValueError("Unhandled python object (%s) '%s'" % (type(v), v))


def requestSetMessage(message):
    logger = logging.getLogger('sgtk.photoshop.flexbase')
    logger.debug("requestSetMessage('%s')", message)
    request = {
        'type': 'setmessage',
        'message': message,
    }
    FlexRequest(json.dumps(request))()
    FlexRequest.callbacks.clear()


def requestClearPanel():
    logger = logging.getLogger('sgtk.photoshop.flexbase')
    logger.debug("requestClearPanel()")
    request = {'type': 'clearpanel'}
    FlexRequest(json.dumps(request))()
    FlexRequest.callbacks.clear()


def requestAddButton(label, callback):
    logger = logging.getLogger('sgtk.photoshop.flexbase')
    logger.debug("requestAddButton('%s')", label)
    request = {
        'type': 'addbutton',
        'label': label,
    }
    results = FlexRequest(json.dumps(request))()
    results = json.loads(results)
    results = dictToPython(results)
    FlexRequest.callbacks[results] = callback


def requestStatic(cls, prop):
    logger = logging.getLogger('sgtk.photoshop.flexbase')
    logger.debug("requestStatic('%s', '%s')", cls, prop)
    request = {
        'type': 'static',
        'cls': cls,
        'prop': prop,
    }
    results = FlexRequest(json.dumps(request))()
    results = json.loads(results)
    return dictToPython(results)


def requestClass(cls):
    logger = logging.getLogger('sgtk.photoshop.flexbase')
    logger.debug("requestClass('%s')", cls)
    request = {
        'type': 'getclass',
        'cls': cls,
    }
    results = FlexRequest(json.dumps(request))()
    results = json.loads(results)
    return dictToPython(results)


def requestClassDesc(cls):
    logger = logging.getLogger('sgtk.photoshop.flexbase')
    logger.debug("requestClassDesc('%s')", cls)
    request = {
        'type': 'classdef',
        'cls': cls,
    }
    results = FlexRequest(json.dumps(request))()
    try:
        dom = etree.XML(results)
    except Exception:
        raise ValueError("Invalid class description: %s" % results)
    return dom


class RemoteClass(object):
    """A wrapper around a flex class"""
    def __init__(self, cls):
        self._logger = logging.getLogger('sgtk.photoshop.flexbase.RemoteClass')
        self._cls = cls

    def __repr__(self):
        return "<%s>" % self._cls

    def __getattr__(self, attr):
        request = {
            'type': 'getprop',
            'obj': pythonToDict(self),
            'prop': attr,
        }
        results = FlexRequest(json.dumps(request))()
        results = json.loads(results)
        self._logger.debug("__getattr__(%s) = %s", attr, results)
        return dictToPython(results)


class RemoteObject(object):
    """A wrapper around a flex object"""
    classMap = {}

    def __init__(self, cls, *args, **kwargs):
        self._logger = logging.getLogger('sgtk.photoshop.flexbase.RemoteObject')
        if 'uid' in kwargs:
            uid = kwargs['uid']
            del kwargs['uid']
        else:
            uid = None

        if kwargs:
            raise ValueError('unknown arguments to __init__: %s' % kwargs)
        self._cls = cls
        self._dom = self.classMap.get(cls)
        if self._dom is None:
            self._dom = requestClassDesc(cls)
        if uid is not None and args:
            raise ValueError('cannot specify both uid and init args')
        if uid is not None:
            self._uid = uid
        else:
            self._logger.debug("%s.__init__(%s)", cls, args)
            request = {
                'type': 'objcreate',
                'cls': cls,
                'args': pythonToDict(args)
            }
            results = FlexRequest(json.dumps(request))()
            results = json.loads(results)
            self._logger.debug("Remote Object Constructor Returned: %s" % results)
            self._uid = results['obj_uid']

    def __repr__(self):
        return "<%s %s>" % (self._cls, self._uid)

    def __setattr__(self, attr, value):
        if attr.startswith('_'):
            super(RemoteObject, self).__setattr__(attr, value)
            return

        self._logger.debug("%s.__setattr__(%s, %s)", self, attr, value)

        # check if attr is an accessor
        accessor = None
        accessors = self._dom.findall('factory/accessor')
        for candidate in accessors:
            if candidate.get('name') == attr:
                accessor = candidate
                break
        if accessor is not None:
            if accessor.get('access') == 'readonly':
                raise ValueError("attempting to set a readonly property '%s'" % attr)
            request = {
                'type': 'setprop',
                'obj': pythonToDict(self),
                'prop': attr,
                'value': pythonToDict(value),
            }
            results = FlexRequest(json.dumps(request))()

            # check results in case an error occurred
            results = json.loads(results)
            dictToPython(results)

    def __getattr__(self, attr):
        # check if attr is an accessor
        accessor = None
        accessors = self._dom.findall('factory/accessor')
        for candidate in accessors:
            if candidate.get('name') == attr:
                accessor = candidate
                break
        if accessor is not None:
            if accessor.get('access') == 'writeonly':
                raise ValueError("attempting to access writeonly property '%s'" % attr)
            request = {
                'type': 'getprop',
                'obj': pythonToDict(self),
                'prop': attr,
            }
            results = FlexRequest(json.dumps(request))()
            results = json.loads(results)
            self._logger.debug("__getattr__(%s) = %s", attr, results)
            return dictToPython(results)

        # check if attr is a method
        method = None
        methods = self._dom.findall('factory/method')
        for candidate in methods:
            if candidate.get('name') == attr:
                method = candidate
                break
        if method is not None:
            return RemoteMethod(self, method)

        raise AttributeError("unknown attribute '%s'" % attr)


class RemoteMethod(object):
    def __init__(self, parent, method):
        self._parent = parent
        self._method = method
        self._logger = logging.getLogger('sgtk.photoshop.flexbase.RemoteMethod')

    def __call__(self, *args):
        name = self._method.get('name')
        request = {
            'type': 'callmethod',
            'obj': pythonToDict(self._parent),
            'method': name,
            'args': pythonToDict(args)
        }
        results = FlexRequest(json.dumps(request))()
        results = json.loads(results)
        self._logger.debug("%s(%s) = %s", name, args, results)
        return dictToPython(results)
