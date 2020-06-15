#!/usr/bin/env bash


#export MAYA_LOCATION="/Applications/Autodesk/maya2019/Maya.app/Contents"
#export PYTHONPATH="/Applications/Autodesk/maya2019/Maya.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python2.7/site-packages":${PYTHONPATH}

#export PYTHONHOME="/Applications/Autodesk/maya2019/Maya.app/Contents/Frameworks/Python.framework/Versions/Current"
#export DYLD_LIBRARY_PATH="/Applications/Autodesk/maya2019/Maya.app/Contents/MacOS:${DYLD_LIBRARY_PATH}"
#export DYLD_FRAMEWORK_PATH="/Applications/Autodesk/maya2019/Maya.app/Contents/Frameworks:${DYLD_FRAMEWORK_PATH}"
#export MAYA_NO_BUNDLE_RESOURCES="1"
#export QT_PLUGIN_PATH="/Applications/Autodesk/maya2017/qt-plugins"
#export PYTHONPATH="/Applications/Pixar/Tractor-2.3/lib/python2.7/site-packages:${PYTHONPATH}"

/Applications/Autodesk/maya2019/Maya.app/Contents/bin/mayapy "$@"
#/Applications/Autodesk/maya2017/Maya.app/Contents/bin/mayapy "$@"
#/Applications/Autodesk/maya2017/Maya.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python "$@"
#$PYTHONHOME/Resources/Python.app/Contents/MacOS/Python "$@"

#  To set up the environment for a Python interpreter
#  Add the site-packages directory of Maya to your PYTHONPATH environment variable, or add
# it to sys.path inside of Python once the interpreter is initialized (but before Maya is initialized).
# This directory is:
# Windows: ../Python/Lib/site-packages
# Mac OS X: ../files/Maya.app/Contents/Frameworks/Python.framework/Versions/Current/lib/python2.4/site-packages
# Linux: ../files/lib/python2.4/site-packages
# Set the MAYA_LOCATION environment variable to point to Maya's install location, so that Maya can find its resources.
# On Mac OS X, the MAYA_LOCATION must be set to point into the application bundle (that is, ../files/Maya.app/Contents).
# (Linux) Add the lib directory of the Maya distribution to the LD_LIBRARY_PATH so that Python can find the
# shared libraries when importing Maya.
# Tip: On Mac OS X, the mayapy executable is a shell script which can be copied and modified
# to use a different Python installation.
# To set up the environment without the script
# 1. Add ../files/Maya.app/Contents/MacOS to the DYLD_LIBRARY_PATH so that Python can find Maya's shared libraries.
# 2. Add ../files/Maya.app/Contents/Frameworks to the DYLD_FRAMEWORK_PATH so that Python can
# find the frameworks that Maya depends upon.
# 3. Set MAYA_NO_BUNDLE_RESOURCES to some value. This tells Maya to look up resources via MAYA_LOCATION
# rather than by looking in the main bundle. (When Maya is run in batch this way,
# then the main bundle is not Maya's main bundle.)
