"""
equanimity_client.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import json
import urllib
import httplib2

class test_client(): 
    def __init__(self, ip='127.0.0.1'):
        self.addr = ip + ':8888' #ports will be handled later.
        self.cookie = None
        self.http = httplib2.Http()
        
    def signup(self, u, p):
        url = 'http://' + self.addr + '/auth/signup'
        body = urllib.urlencode({'u': u, 'p': p})
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        return self.http.request(url, 'POST', headers=headers, body=body)
    
    def login(self, u, p):
        url = 'http://' + self.addr + '/auth/login'
        body = urllib.urlencode({'u': u, 'p': p})
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        return self.http.request(url, 'POST', headers=headers, body=body)
    
    def battle(self, method, params, cookie):
        url = 'http://' + self.addr + '/battle/'
        body = json.dumps({"method": method, "params":params, "id":1})
        headers = {'Cookie': cookie}
        return self.http.request(url, 'POST', headers=headers, body=body)
    
    def test_move(self, unit, cookie):
        params = [[unit, 'move', '(2,2)']]
        return self.battle("process_action", params, cookie)
    
    def register(self, cookie):
        params = []
        return self.battle("register", params, cookie)
        
if __name__ == "__main__":
    import sys
    try: 
        t = test_client(sys.argv[1])
    except:
        t = test_client()
    cookie = t.login('atkr', 'atkr')[0]['set-cookie']
    """
    b = t.battle("initial_state", [], cookie)
    print b
    s = json.loads(b[1])['result']['initial_state']
    dude = str(s['units'].keys()[0])
    pos = s['init_locs'][dude]
    pos = (pos[0], pos[1] + 1)
    m = t.battle("process_action", [[dude, 'move', pos]], cookie)
    print m
    """
