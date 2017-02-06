# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

# system modules
import sys
import logging

# local modules
import flexbase

# setup logging
################################################################################
logger = logging.getLogger('sgtk.photoshop')


def log_debug(msg, *args, **kwargs):
    logger.debug(msg, *args, **kwargs)


def log_error(msg, *args, **kwargs):
    logger.error(msg, *args, **kwargs)


def log_exception(msg, *args, **kwargs):
    logger.exception(msg, *args, **kwargs)


# setup default exception handling to log
def logging_excepthook(type, value, tb):
    logger.exception("Uncaught exception", exc_info=(type, value, tb))
    sys.__excepthook__(type, value, tb)
sys.execpthook = logging_excepthook


# setup actionscript integration
################################################################################
def clear_panel():
    flexbase.requestClearPanel()


def set_message(message):
    flexbase.requestSetMessage(message)


def add_button(label, callback):
    flexbase.requestAddButton(label, callback)


def RemoteObject(cls, *args, **kwargs):
    return flexbase.RemoteObject(cls, *args, **kwargs)


def StaticObject(cls, prop):
    return flexbase.requestStatic(cls, prop)


def RemoteClass(cls):
    return flexbase.requestClass(cls)


app = None


# plugin initialization will call the app setup
def initialize_photoshop_application(remote_port, heartbeat_port):
    global app
    try:
        flexbase.setup(remote_port, heartbeat_port)
        app = flexbase.photoshop_instance
        logger.info("Photoshop version is '%s'", app.version)
    except:
        log_exception('error in initializePhotoshopApplication')


################################################################################
# setup photoshop helper functions

def _shouldMaximizeCompatibility():
    """
    Returns if the Maximize Compatibility flag should be set.
    :return True if preference is Ask of Always, False if Never.
    """
    # maximizeCompatibility is actually tri-state: Always, Never and Ask. However, when saving with
    # com.adobe.photoshopdocument.saveAs, the Ask setting is being treated like the Always setting.
    # Therefore, we will mimick this behaviour here. If you ever want to test this for yourself,
    # simply create a new file with two layers, set the compatibility level to Always and do a
    # Shotgun->Save As. Then, set the setting to Never and do a Shotgun->Save As as another name.
    # Finally, switch it to Ask and do a Shotgun->Save As again. Then, load these images as textures
    # in Maya. Only the Ask and Always images will show up properly. The Never one won't work.
    # Note that you have to have at least a second layer on top of the background one. Maya is able
    # to read files that either have the compatibility flag set or that have a single background
    # layer.
    #
    # Note: If you save the image with Never, test in Maya, set the flag to Always and then do a
    # simple save, the file will still not work in Maya. This is because the compatibility setting
    # is apparently set with the file when it is created. Only saving it AS something will set the
    # flag to the current value. This doesn't impact us, but it's important to keep this in mind
    # when validating the above.
    #
    # Also, Maya doesn't support PSBs. :(

    # value is an object, and we can't compare objects, so compare their string representation
    # instead.
    user_setting = app.preferences.maximizeCompatibility.value.toString()
    never_setting = flexbase.requestStatic(
        "com.adobe.photoshop::QueryStateType", "NEVER"
    ).value.toString()
    return user_setting != never_setting


def save_as(document, file_path):
    """
    Saves a photoshop document at the given location.

    :param document: Document to save.
    :param file_path: Path where to save the document.
    """
    file_path_obj = RemoteObject('flash.filesystem::File', file_path)

    if file_path.lower().endswith(".psb"):
        # script listener generates this sequence of statements.
        # var idsave = charIDToTypeID( "save" );
        #     var desc29 = new ActionDescriptor();
        #     var idAs = charIDToTypeID( "As  " );
        #         var desc30 = new ActionDescriptor();
        #         var idmaximizeCompatibility = stringIDToTypeID( "maximizeCompatibility" );
        #         desc30.putBoolean( idmaximizeCompatibility, true );
        #     var idPhteight = charIDToTypeID( "Pht8" );
        #     desc29.putObject( idAs, idPhteight, desc30 );
        #     var idIn = charIDToTypeID( "In  " );
        #     desc29.putPath( idIn, new File( "/Users/boismej/Downloads/Untitled-1 copy.psd" ) );
        # ... // Omitting parameters that don't concern us. We'll use the defaults for these.
        # executeAction( idsave, desc29, DialogModes.NO );
        #
        # Note: There are instances where PSBs are saved using Pht3 instead. Haven't been able to
        # isolate why. Pht3 stands for photoshop35Format according to documentation, but PSBs were
        # introduced in CS1 (aka 8.0). It might be that this value is ignored by Photoshop when the
        # extension is PSB? However, it's not clear why saving an empty canvas sometimes saves with
        # pht8 and sometimes pht3.

        global app
        stringIDToTypeID = app.stringIDToTypeID

        # Descriptor for the maximize compatibility flag.
        compatibility_desc = RemoteObject("com.adobe.photoshop::ActionDescriptor")
        compatibility_desc.putBoolean(stringIDToTypeID("maximizeCompatibility"), _shouldMaximizeCompatibility())

        # Settings for the save as.
        save_as_desc = RemoteObject("com.adobe.photoshop::ActionDescriptor")
        # largeDocumentFormat is the stringID variant of Pht8
        save_as_desc.putObject(stringIDToTypeID("as"), stringIDToTypeID("largeDocumentFormat"), compatibility_desc)
        save_as_desc.putPath(stringIDToTypeID("in"), file_path_obj)

        # Saves the document without a dialog popping up.
        app.executeAction(
            stringIDToTypeID("save"), save_as_desc, flexbase.requestStatic('com.adobe.photoshop.DialogModes', 'NO')
        )
    else:
        # Anything else the user might be saving (psd, tiff, etc), can be saved as is with the Flex
        # API. No options means everything gets saved (layers, coloc profiles, notes, etc) and False
        # means do not save as a copy.
        # http://cssdk.host.adobe.com/sdk/1.5/docs/WebHelp/references/csawlib/com/adobe/photoshop/Document.html#saveAs()
        document.saveAs(file_path_obj, None, False)


################################################################################
# setup gui utilities

def messageBox(text):
    """
    LEGACY -- DO NOT USE.
    """
    try:
        from tank.platform.qt import QtGui, QtCore
        msg = QtGui.QMessageBox()
        msg.setText(text)
        msg.setWindowFlags(msg.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        return msg.exec_()
    except Exception:
        log_exception("messageBox failed")
