import os
import sys

import tank

def setup(launcher, context):
    extra_configs = launcher.get_setting("extra", {})

    # Get the path to the python executable
    python_setting = {"darwin": "mac_python_path", "win32": "windows_python_path"}[sys.platform]
    python_path = extra_configs.get(python_setting) or sys.executable
    if not python_path:
        raise tank.TankError("Your photoshop app launch config is missing the extra setting %s" % python_setting)

    # get the path to extension manager
    manager_setting = { "darwin": "mac_extension_manager_path",
                        "win32": "windows_extension_manager_path" }[sys.platform]
    manager_path = extra_configs.get(manager_setting)
    if not manager_path:
        raise tank.TankError("Your photoshop app launch config is missing the extra setting %s!" % manager_setting)
    os.environ["SGTK_PHOTOSHOP_EXTENSION_MANAGER"] = manager_path

    # make sure the extension is up to date
    try:
        import photoshop_extension_manager
        photoshop_extension_manager.update()
    except Exception, e:
        raise tank.TankError("Could not run the Adobe Extension Manager. Please double check your "
                        "Shotgun Pipeline Toolkit Photoshop Settings. Error Reported: %s" % e)

    # Store data needed for bootstrapping Toolkit in env vars. Used in startup/menu.py
    os.environ["SGTK_PHOTOSHOP_PYTHON"] = python_path
    os.environ["SGTK_PHOTOSHOP_BOOTSTRAP"] = os.path.join(os.path.dirname(__file__), "engine_bootstrap.py")

    # add our startup path to the photoshop init path
    startup_path = os.path.abspath(os.path.join(launcher._get_app_specific_path("photoshop"), "startup"))
    tank.util.append_path_to_env_var("PYTHONPATH", startup_path)