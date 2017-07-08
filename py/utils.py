import threading
import sublime
import time

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

def settings(key=None, value=None):
    preferences = sublime.load_settings('Sublimify.sublime-settings')
    if key and not value:
        return preferences.get(key)
    elif value:
        preferences.set(key, value)
        sublime.save_settings('Sublimify.sublime-settings')
    return preferences

def store(params, auth=False):
    for key in params:
        settings(key,params[key])
    if auth:
        settings('expires_in', int(time.time()) + params['expires_in'])
