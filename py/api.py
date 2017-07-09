import urllib
import json
import time

from  urllib.parse import urlencode
from .utils import store, settings, set_interval

ME = 'https://api.spotify.com/v1/me/'
PLAYER = ME + 'player/'

AUTH_HEADERS = {
    "Authorization": "Basic ZGE4OGQ3NDBjOWVmNGJmMjlhNDM5MTcxZWZiYTUwOWY6MWMzZDVlYmJkZTYyNDEwOGE2YWE4OGEyYjMyMjI2YjU="
}

instance = None

class Api():

    def __init__(self):
        self.reload()

    def reload(self):
        self.access_token = settings('access_token')
        self.refresh_token = settings('refresh_token')
        self.expires_in = settings('expires_in') or 0
        self.headers = {'Authorization': 'Bearer %s' % settings('access_token')}
        self.status = {}
        if self.access_token:
            self.currently_playing()

    def request(self, url, headers={}, data=None, method='GET', params={}, parse=False):
        
        # access token verify
        if 'token' not in url and time.time() >= self.expires_in:
            self.refresh()

        if len(params):
            url += '?' + urlencode(params)

        if data:
            
            if not isinstance(data, str):
                data = urlencode(data)           

            data = data.encode('utf-8')
            
        if not len(headers):
            headers = self.headers        

        # cache control
        tracks_req = 'tracks' in url
        etags =  settings('tracks_etags') or {}
        offset = '0'
        
        if tracks_req:            
            offset = str(params['offset'])
            if offset in etags:
                headers['If-None-Match'] = etags[offset]

        # request
        req = urllib.request.Request(url, headers=headers, data=data, method=method)
        
        try:
            
            res = urllib.request.urlopen(req)
            
            if tracks_req:
                etags[offset] = res.getheader('ETag')
                settings('tracks_etags', etags)
            
            res = res.read()
            
            return json.loads(res.decode()) if parse else res.decode()

        except Exception:
            return None

    def refresh(self):   
        payload = { 'refresh_token': self.refresh_token, 'grant_type': 'refresh_token' }
        res = self.request('https://accounts.spotify.com/api/token', headers=AUTH_HEADERS, data=payload, method='POST', parse=True)
        store(res, True)
        self.reload()        
    
    def authorize(self, code):   
        payload = {
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': 'http://localhost:9999/callback'
        }
        return self.request('https://accounts.spotify.com/api/token', headers=AUTH_HEADERS, data=payload, method='POST', parse=True)

    def tracks(self, offset):
        return self.request(ME+'tracks', params={'limit': 50, 'offset': offset}, parse=True)

    def albums(self):
        return self.request(ME+'albums', parse=True)

    def currently_playing(self):
        status = self.request(PLAYER, parse=True)
        if not status: return self.status
        self.status['playing'] = status['is_playing']
        self.status['name'] = status['item']['name']
        self.status['repeat'] = status['repeat_state']
        self.status['shuffle'] = status['shuffle_state']
        self.status['artist'] = status['item']['artists'][0]['name']
        return self.status

    def play(self, uris=[]):
        
        if len(uris): 
            self.request(PLAYER + 'play', data=json.dumps({'uris': uris}), method='PUT')
        else:
            self.request(PLAYER + 'play', method='PUT')
            
        self.status['playing'] = True

    def pause(self):
        self.request(PLAYER + 'pause', method='PUT')
        self.status['playing'] = False

    def next(self):
        self.request(PLAYER + 'next', method='POST')

    def previous(self):
        self.request(PLAYER + 'previous', method='POST')

    def shuffle(self, state):
        self.status['shuffle'] = state
        self.request(PLAYER + 'shuffle', params={'state': state}, method='PUT')

    def repeat(self, state):
        self.status['repeat'] = state
        self.request(PLAYER + 'repeat', params={'state': state}, method='PUT')

def api():
    global instance
    if not instance: instance = Api()
    return instance