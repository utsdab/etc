# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from sgtk.platform.qt import QtGui
from sgtk.platform.qt import QtCore

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunModel = shotgun_model.ShotgunModel


class ProjectModel(ShotgunModel):
    """ Simple Project model to pull down Toolkit projects and their thumbnails """
    DISPLAY_NAME_ROLE = QtCore.Qt.UserRole + 101
    PROJECT_ID_ROLE = QtCore.Qt.UserRole + 102

    def __init__(self, parent):
        ShotgunModel.__init__(self, parent, download_thumbs=True)

        # load the missing project thumbnail
        self._missing_thumbnail_project = \
            QtGui.QPixmap(":/tk-framework-adminui/setup_project/missing_thumbnail_project.png")

        # and load the data from Shotgun
        filters = [
            ["archived", "is_not", True],
            ["tank_name", "is_not", None],
            ["name", "is_not", "Template Project"],
        ]

        ShotgunModel._load_data(
            self,
            entity_type="Project",
            filters=filters,
            hierarchy=["name"],
            fields=["name", "id"],
            order=[{"field_name": "name", "direction": "asc"}],
        )

        self._refresh_data()

    def _populate_item(self, item, sg_data):
        item.setData(sg_data.get("name") or "No Name", self.DISPLAY_NAME_ROLE)
        item.setData(sg_data.get("id"), self.PROJECT_ID_ROLE)

    def _populate_default_thumbnail(self, item):
        item.setIcon(self._missing_thumbnail_project)

    def _populate_thumbnail(self, item, field, path):
        thumb = QtGui.QPixmap(path)
        item.setIcon(thumb)
