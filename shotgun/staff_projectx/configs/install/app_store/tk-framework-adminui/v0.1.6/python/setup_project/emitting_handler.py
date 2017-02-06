# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import logging

from sgtk.platform.qt import QtCore


class EmittingHandler(logging.Handler):
    """ Class to map logging messages to Qt signals """
    COLOR_MAP = {
        # colors from the Tomorrow Night Eighties theme
        logging.CRITICAL: '#f2777a',
        logging.ERROR: '#f2777a',
        logging.WARNING: '#ffcc66',
        logging.INFO: '#cccccc',
        logging.DEBUG: '#999999'
    }

    # Dummy type to hold the log_message signal.
    class LogSignaller(QtCore.QObject):
        log_message = QtCore.Signal(str)

    def __init__(self):
        logging.Handler.__init__(self)
        self.__formatter = logging.Formatter("%(message)s")

        # Wrap the real message logging with a signal/slot,
        # to ensure that the widget is updated within the UI thread.
        self.__signals = self.LogSignaller()

    def connect(self, slot):
        """ Connect the message logging to the given slot """
        self.__signals.log_message.connect(slot)

    def emit(self, record):
        # Convert the record to pretty HTML
        message = self.__formatter.format(record)
        if record.levelno in self.COLOR_MAP:
            color = self.COLOR_MAP[record.levelno]
            message = "<font color=\"%s\">%s</font>" % (color, message)
        message = "<pre>%s</pre>" % message

        # Update widget (possibly in a different thread than the current one)
        self.__signals.log_message.emit(message)
