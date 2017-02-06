# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk.platform
from sgtk.platform.qt import QtCore

from .base_page import BasePage


class RunSetupThread(QtCore.QThread):
    """ Simple thread to run the wizard in the background """
    success = QtCore.Signal()
    failure = QtCore.Signal(str)

    def __init__(self, wizard, parent=None):
        QtCore.QThread.__init__(self, parent)
        self._wizard = wizard

    def run(self):
        try:
            self._wizard.execute()
            self.success.emit()
        except Exception, e:
            self.failure.emit(str(e))


class ProgressPage(BasePage):
    """ Page to show the progress bar during configuration setup. """
    def __init__(self, parent=None):
        BasePage.__init__(self, parent)

        self._thread_success = False
        self._original_next_css = None
        self._original_next_text = None
        self.execute_thread = None

    def setup_ui(self, page_id):
        BasePage.setup_ui(self, page_id)

        wiz = self.wizard()
        wiz.ui.progress_output.hide()
        wiz.ui.additional_details_button.pressed.connect(self.additional_details_pressed)

    def initializePage(self):
        # disable the cancel and back buttons
        wiz = self.wizard()
        wiz.button(wiz.NextButton).setEnabled(False)

        self._original_next_text = wiz.buttonText(wiz.NextButton)
        self._original_next_css = wiz.button(wiz.NextButton).styleSheet()

        wiz.setButtonText(wiz.NextButton, "Running...")
        wiz.button(wiz.NextButton).setStyleSheet("background-color: rgb(128, 128, 128);")

        # setup for progress reporting
        wiz.ui.progress.setValue(0)
        wiz.core_wizard.set_progress_callback(self.progress_callback)

        # run the thread
        self.execute_thread = RunSetupThread(wiz.core_wizard)
        self.execute_thread.success.connect(self._on_run_succeeded)
        self.execute_thread.failure.connect(self._on_run_failed)
        self.execute_thread.finished.connect(self._on_thread_finished)
        self.execute_thread.start()

        # can no longer cancel or hit back
        wiz.setButtonLayout([wiz.HelpButton, wiz.Stretch, wiz.NextButton, wiz.FinishButton])

    def additional_details_pressed(self):
        # handle the additional details toggle being pressed
        wiz = self.wizard()

        # show the additional details and hide the additional details button
        wiz.ui.progress_output.show()
        wiz.ui.additional_details_button.hide()

    def append_log_message(self, text):
        # since a thread could be calling this make sure we are doing GUI work on the main thread
        engine = sgtk.platform.current_engine()
        engine.execute_in_main_thread(self.__append_on_main_thread, text)

    def __append_on_main_thread(self, text):
        # append the log message to the end of the logging area
        wiz = self.wizard()
        wiz.ui.progress_output.appendHtml(text)
        cursor = wiz.ui.progress_output.textCursor()
        cursor.movePosition(cursor.End)
        cursor.movePosition(cursor.StartOfLine)
        wiz.ui.progress_output.setTextCursor(cursor)
        wiz.ui.progress_output.ensureCursorVisible()

    def progress_callback(self, chapter, progress):
        # since a thread could be calling this make sure we are doing GUI work on the main thread
        engine = sgtk.platform.current_engine()
        engine.execute_in_main_thread(self.__progress_on_main_thread, chapter, progress)

    def __progress_on_main_thread(self, chapter, progress):
        # update the progress display
        if progress is not None:
            wiz = self.wizard()
            wiz.ui.message.setText(chapter)
            wiz.ui.progress.setValue(progress)

    def _on_run_finished(self):
        # since a thread could be calling this make sure we are doing GUI work on the main thread
        engine = sgtk.platform.current_engine()
        engine.execute_in_main_thread(self._on_run_finished_main_thread)

    def _on_run_finished_main_thread(self):
        # thread has finished
        # clean up the page state
        wiz = self.wizard()
        wiz.button(wiz.NextButton).setEnabled(True)

    def _on_run_succeeded(self):
        # since a thread could be calling this make sure we are doing GUI work on the main thread
        engine = sgtk.platform.current_engine()
        engine.execute_in_main_thread(self._on_run_succeeded_main_thread)

    def _on_run_succeeded_main_thread(self):
        # thread finished successfully
        self._on_run_finished()

        self._thread_success = True

        wiz = self.wizard()
        wiz.ui.progress.setValue(100)
        wiz.ui.message.setText("Set up finished")
        wiz.setButtonText(wiz.NextButton, self._original_next_text)
        wiz.button(wiz.NextButton).setStyleSheet(self._original_next_css)

        if wiz.ui.progress_output.isHidden():
            # auto advance if details are not shown
            wiz.next()

    def _on_run_failed(self, message):
        # since a thread could be calling this make sure we are doing GUI work on the main thread
        engine = sgtk.platform.current_engine()
        engine.execute_in_main_thread(self._on_run_failed_main_thread, message)

    def _on_run_failed_main_thread(self, message):
        # thread failed
        self._on_run_finished()

        # show the failure icon and message
        wiz = self.wizard()
        wiz.button(wiz.CancelButton).setVisible(True)
        wiz.setButtonText(wiz.NextButton, "Quit")
        wiz.ui.complete_errors.setText(message)

    def _on_thread_finished(self):
        # since a thread could be calling this make sure we are doing GUI work on the main thread
        engine = sgtk.platform.current_engine()
        engine.execute_in_main_thread(self._on_thread_finished_main_thread)

    def _on_thread_finished_main_thread(self):
        # let the wizard know that our complete state has changed
        self.completeChanged.emit()

    def isComplete(self):
        return self._thread_success
