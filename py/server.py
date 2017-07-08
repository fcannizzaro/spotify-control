import webbrowser
import _thread

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from .api import api
from .utils import store
import sublime

AUTH = 'https://accounts.spotify.com/authorize/?client_id=da88d740c9ef4bf29a439171efba509f&response_type=code&redirect_uri=http://localhost:9999/callback&scope=user-read-playback-state user-modify-playback-state user-library-read'

class Server(BaseHTTPRequestHandler):

    def do_GET(self):

        query = parse_qs(urlparse(self.path).query)
        spotify = api()
        
        if 'code' in query:
            store(spotify.authorize(query['code'][0]), True)
            spotify.reload()
            restart()
            _thread.start_new_thread(sublime.message_dialog, ('Spotify <--> Sublime Text',))

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><body><script>window.close()</script>Spotify <--> Sublime Text</body></html>", "utf-8"))
            
    def log_message(self, format, *args):
        return

def start():
    res = sublime.yes_no_cancel_dialog('Authorize "sublimify" on spotify.')
    if res == sublime.DIALOG_YES:
        server = HTTPServer(('localhost', 9999), Server)
        webbrowser.open(AUTH)
        server.serve_forever()

def listen(plugin_loaded):
    global restart
    restart = plugin_loaded
    _thread.start_new_thread(start, ())