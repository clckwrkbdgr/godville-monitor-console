import os
import gettext

def get_config_file(*args):
    xdg_config_dir = os.environ.get('XDG_CONFIG_HOME')
    if not xdg_config_dir:
        xdg_config_dir = os.path.join(os.path.expanduser("~"), ".config")
    app_config_dir = os.path.join(xdg_config_dir, "pygod")
    os.makedirs(app_config_dir, exist_ok=True)
    return os.path.join(app_config_dir, "pygod.ini")

def get_data_dir(*args):
    xdg_data_dir = os.environ.get('XDG_DATA_HOME')
    if not xdg_data_dir:
        xdg_data_dir = os.path.join(os.path.expanduser("~"), ".local", "share")
    app_data_dir = os.path.join(xdg_data_dir, "pygod")
    os.makedirs(app_data_dir, exist_ok=True)
    return app_data_dir

def get_log_dir():
    data_dir = os.environ.get('XDG_LOG_HOME')
    if not data_dir:
        data_dir = os.path.join(os.path.expanduser("~"), ".local", "log")
    logdir = os.path.join(data_dir, "pygod")
    os.makedirs(logdir, exist_ok=True)
    return logdir

def unquote_string(string):
    if string.startswith('"') and string.endswith('"'):
        string = string[1:-1]
    # Apparently 'unicode_escape' returns string with corrupted utf-8 encoding.
    return bytes(string, "utf-8").decode('unicode_escape').encode("latin1").decode("utf-8")

# I18N
translate = gettext.translation('pygod', get_data_dir(), fallback=True)
tr = translate.gettext # this function should be used to mark all translatable strings.
translate.install()
