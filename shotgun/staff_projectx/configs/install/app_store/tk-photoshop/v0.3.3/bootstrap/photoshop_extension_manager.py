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
import re
import sys
import subprocess
import ConfigParser

CURRENT_EXTENSION = "1.1.1"
CURRENT_ZXP_PATH = os.path.normpath(os.path.join(__file__, "..", "..", "SgTkPhotoshopEngine.zxp"))

VERSION_BEFORE_RENAME = "0.1.2"
EXTENSION_NAME = "Shotgun Photoshop Engine"

ENV_VAR = "SGTK_PHOTOSHOP_EXTENSION_MANAGER"


# platform specific alert with no dependencies
def msgbox(msg, button="Sorry!"):
    if sys.platform == "win32":
        import ctypes
        MessageBox = ctypes.windll.user32.MessageBoxA
        MessageBox(None, msg, "Shotgun", 0)
    elif sys.platform == "darwin":
        os.system("""osascript -e 'tell app "System Events" to activate'""")
        os.system("""osascript -e 'tell app "System Events" to display dialog "%s" with icon caution buttons "%s!"'""" % (msg, button))


def update():
    # Upgrade if the installed version is out of date
    config = _get_config()
    installed_version = config.get("Adobe Extension", "installed_version")

    try:
        extension_manager = os.environ[ENV_VAR]
    except KeyError:
        raise ValueError("Could not open extension manager from env var %s" % ENV_VAR)
    version = _guess_extension_manager_version(extension_manager)

    if _version_cmp(CURRENT_EXTENSION, installed_version) > 0:
        if _version_cmp(VERSION_BEFORE_RENAME, installed_version) >= 0:
            uninstall_old = True
        else:
            uninstall_old = False
        if version == "CC":
            msgbox("Welcome to the Shotgun Photoshop engine!\n"
                   "\n"
                   "The Shotgun Photoshop extension must be installed before using "
                   "the integration.\n"
                   "\n"
                   "Adobe Extension Manager will now automatically install the "
                   "extension, which may take a minute.\n"
                   "\n"
                   "Photoshop CC will launch after the install and be ready to "
                   "use with Shotgun Pipeline Toolkit.", "Got it")
        elif uninstall_old:
            msgbox("A new Shotgun Photoshop extension is available.\n\n"
                "Adobe Extension Manager will run twice, once to remove the old extension "
                "and again to install the new one.", button="Got it")
        else:
            msgbox("A new Shotgun Photoshop extension is available.\n\n"
                "Adobe Extension Manager will now run to install the new version.",
                button="Got it")
        _upgrade_extension(uninstall_old)


def tag(version):
    config = _get_config()
    config.set("Adobe Extension", "installed_version", version)
    _save_config(config)


# - Internal -------------------------------------------------------------------
_APPNAME = "com.shotgunsoftware.SgTkPhotoshopEngine"
_CSIDL_LOCAL_APPDATA = 28


def _get_config():
    # Setup defaults
    config = ConfigParser.SafeConfigParser()
    config.add_section("Adobe Extension")
    config.set("Adobe Extension", "installed_version", "0.0.0")

    # Load the actual config
    config_fname = _get_conf_fname()
    if os.path.exists(config_fname):
        config.read(config_fname)

    return config


def _save_config(config):
    # Create directory for config file if it does not exist
    config_fname = _get_conf_fname()
    config_dir = os.path.dirname(config_fname)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    # Save out the updated config
    fp = open(config_fname, "wb")
    try:
        config.write(fp)
    finally:
        fp.close()


def _get_conf_fname():
    if "TK_PHOTOSHOP_EXTENSION_TRACKER" in os.environ:
        # Allow overriding of the file location so that if a studio is managing
        # the extension machine wide they can avoid having the first invocation
        # of the engine for an artist trigger an extension install.
        return os.environ["TK_PHOTOSHOP_EXTENSION_TRACKER"]
    if sys.platform == "win32":
        return _get_win_fname()
    elif sys.platform == "darwin":
        return _get_osx_fname()
    else:
        raise ValueError("unsupported platform: %s" % sys.platform)


def _get_osx_fname():
    try:
        extension_manager = os.environ[ENV_VAR]
    except KeyError:
        raise ValueError("Could not open extension manager from env var %s" % ENV_VAR)
    version = _guess_extension_manager_version(extension_manager)

    folder = os.path.join(os.path.expanduser('~/Library/Application Support/'), _APPNAME)
    return os.path.join(folder, "Extension_%s.ini" % version)


def _get_win_fname():
    import ctypes

    bfr = ctypes.create_unicode_buffer(1024)
    ctypes.windll.shell32.SHGetFolderPathW(None, _CSIDL_LOCAL_APPDATA, None, 0, bfr)

    # Fix to get short path name when invalid unicode is used
    needs_fix = False
    for c in bfr:
        if ord(c) > 255:
            needs_fix = True
            break
    if needs_fix:
        fix_bfr = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(bfr.value, fix_bfr, 1024):
            bfr = fix_bfr

    folder = bfr.value

    try:
        extension_manager = os.environ[ENV_VAR]
    except KeyError:
        raise ValueError("Could not open extension manager from env var %s" % ENV_VAR)
    version = _guess_extension_manager_version(extension_manager)

    return os.path.join(folder, "%s_%s.ini" % (_APPNAME, version))


def _version_cmp(left, right):
    def normalize(v):
        return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]
    return cmp(normalize(left), normalize(right))


def _upgrade_extension(uninstall = False):
    # Grab path to extension manager
    try:
        extension_manager = os.environ[ENV_VAR]
    except KeyError:
        raise ValueError("Could not open extension manager from env var %s" % ENV_VAR)

    version = _guess_extension_manager_version(extension_manager)
    if version == "CC":
        _upgrade_cc(extension_manager, uninstall)
    elif version == "CS6":
        _upgrade_cs6(extension_manager, uninstall)
    else:
        raise NotImplementedError("Unsupported version of extension manager: %s" % version)


def _upgrade_cs6(extension_manager, uninstall):
    cmd = _guess_extension_manager_command(extension_manager)

    if uninstall:
        if sys.platform == "darwin":
            product = "Photoshop CS6"
        elif sys.platform == "win32":
            product = "Photoshop CS6 64"

        args = [cmd, "-remove", 'product="%s"' % product, 'extension="%s"' % EXTENSION_NAME]
        _call_cmd(args)

    # install the extension
    args = [cmd, "-install", 'zxp="%s"' % CURRENT_ZXP_PATH]
    _call_cmd(args)


def _upgrade_cc(extension_manager, uninstall):
    cmd = _guess_extension_manager_command(extension_manager)

    if sys.platform == "darwin":
        arg_prefix = "--"
    elif sys.platform == "win32":
        arg_prefix = "/"

    if uninstall:
        # CC supports getting a list of installed extensions
        args = [cmd, arg_prefix + "list", "all"]
        (ret, lines) = _call_cmd(args)

        # make sure we have valid output
        found = False
        for line in lines:
            split = [word.strip() for word in line.split(" ") if word.strip()]
            # each line is 'Status' 'Name', 'Version', status and version have no spaces
            extension_name = " ".join(split[1:-1])
            if extension_name == EXTENSION_NAME:
                found = True
                break

        # only call uninstall if the extension is actually installed
        if found:
            args = [cmd, arg_prefix + "remove", EXTENSION_NAME]
            (ret, lines) = _call_cmd(args)

    # install the extension
    args = [cmd, arg_prefix + "install", CURRENT_ZXP_PATH]
    _call_cmd(args)


def _call_cmd(args):
    # Note: Tie stdin to a PIPE as well to avoid this python bug on windows
    # http://bugs.python.org/issue3905
    try:
        process = subprocess.Popen(args,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process.stdin.close()

        # Popen.communicate() doesn't play nicely if the stdin pipe is closed
        # as it tries to flush it causing an 'I/O error on closed file' error
        # when run from a terminal
        #
        # to avoid this, lets just poll the output from the process until
        # it's finished
        output_lines = []
        while True:
            line = process.stdout.readline()
            if not line:
                break
            output_lines.append(line)
        ret = process.poll()
    except StandardError:
        import traceback
        ret = True
        output_lines = traceback.format_exc().split()
        output_lines.append("%s" % args)

    if ret:
        # Return value of Extension manager is not reliable, so just warn
        print "WARNING: Extension manager returned a non-zero value."
        print "%s" % args
        print "\n".join(output_lines)

    return (ret, output_lines)


def _guess_extension_manager_command(extension_manager):
    if sys.platform == "darwin":
        # CC introduced a managment command
        cmd = os.path.join(extension_manager, "Contents", "MacOS", "ExManCmd")
        if os.path.exists(cmd):
            return cmd

        # Default is the name of the bundle
        try:
            bundle_name = os.path.basename(extension_manager).split('.')[0]
            cmd = os.path.join(extension_manager, "Contents", "MacOS", bundle_name)
            if os.path.exists(cmd):
                return cmd
        except:
            raise ValueError("Expected path to Extension manager bundle (ending in .app).  Got %s." % extension_manager)
    elif sys.platform == "win32":
        # Try CC command name
        cmd = os.path.join(os.path.dirname(extension_manager), "ExManCmd.exe")
        if os.path.exists(cmd):
            return cmd

        cmd = os.path.join(os.path.dirname(extension_manager), "XManCommand.exe")
        if os.path.exists(cmd):
            return cmd
    else:
        raise NotImplementedError("unsupported platform: %s" % sys.platform)

    # Couldn't find the command to run
    raise ValueError("Could not figure out extension manager cmd: %s" % extension_manager)


def _guess_extension_manager_version(extension_manager):
    if sys.platform == "darwin":
        try:
            bundle_name = os.path.basename(extension_manager).split('.')[0]
            return bundle_name.split()[-1]
        except:
            raise ValueError("Expected path to Extension manager bundle (ending in .app).  Got %s." % extension_manager)
    elif sys.platform == "win32":
        # Try CC command name
        cmd = os.path.join(os.path.dirname(extension_manager), "ExManCmd.exe")
        if os.path.exists(cmd):
            return "CC"

        cmd = os.path.join(os.path.dirname(extension_manager), "XManCommand.exe")
        if os.path.exists(cmd):
            return "CS6"
    else:
        raise NotImplementedError("unsupported platform: %s" % sys.platform)

    raise ValueError("Could not figure out extension manager version: %s" % extension_manager)
