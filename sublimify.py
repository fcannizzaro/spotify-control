import sublime_plugin
import _thread as th
import sublime
import time
from .py.api import api
from .py.server import listen
from .py.utils import settings, store, set_interval

def update():
    status = api().currently_playing()
    if 'device' in status:
        for view in sublime.active_window().views():
            if status['device']:
              view.set_status('spotify', ' [%s] %s ♫ ' % (status['artist'], status['name']))
            else:
                view.set_status('spotify', ' Spotify Closed ♫ ')

def on_track_selected(index):
    if index < 0: return
    tracks = [track['uri'] for track in settings('tracks')]
    th.start_new_thread(api().play, (tracks[index:],))

def repeat_mode(value):
  modes = ['track', 'context', 'off']
  if isinstance(value, str):
    return modes.index(value)
  return modes[value]

def on_repeat_selected(index):
  if index < 0: return
  th.start_new_thread(api().repeat, (repeat_mode(index),))

def refresh_library():

    spotify = api()
    tracks = []
    res = {}

    while True:
        res = spotify.tracks(res['offset'] + 50 if len(res) else 0)
        if not res: break
        tracks += [{key: item['track'][key] for key in ('uri', 'name')} for item in res['items']]
        if not res['next']: break
    
    if len(tracks):
        settings('tracks', tracks)

def run(api):
  
    if not api.access_token:
        return listen(plugin_loaded)

    global updating
    updating = set_interval(update, 3)

    refresh_library()   

class SpotifyFlowCommand(sublime_plugin.TextCommand):

    def exec(self, action):

        spotify = api()

        if action == 'tracks':
          tracks = [track['name'] for track in settings('tracks')]
          self.view.window().show_quick_panel(tracks, on_track_selected)
        
        elif action == 'refresh':
            refresh_library()

        elif action == 'next':
            spotify.next()

        elif action == 'previous':
            spotify.previous()

        elif action == 'shuffle':
          spotify.shuffle(not spotify.status['shuffle'])   

        elif action == 'repeat':
          labels = ['repeat current', 'repeat all', 'no repeat']
          if 'repeat' not in spotify.status: return
          self.view.window().show_quick_panel(labels, on_repeat_selected, selected_index=repeat_mode(spotify.status['repeat']))

        else:

            if 'playing' in spotify.status and spotify.status['playing']:
                spotify.pause()
            else:
                spotify.play()

        update()

    def run(self, edit, action='play/pause'):
        th.start_new_thread(self.exec, (action,))

def plugin_loaded():
    sublime.save_settings('Sublimify.sublime-settings')
    th.start_new_thread(run, (api(),))

def plugin_unloaded():
    if 'updating' in globals():
      updating.cancel()
