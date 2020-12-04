from endpoints import Endpoint
from endpoints import Credential


class XAuthTokenCredential(Credential):
    def __init__(self, token):
        self.headers = {
            'x-auth-token': token,
        }


class TinderApiEndpoint(Endpoint):
    domain = 'https://api.gotinder.com'
    headers = {
        'authority': 'api.gotinder.com',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'x-supported-image-formats': 'jpeg',
        'persistent-device-id': '',
        'tinder-version': '2.63.0',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.193 Safari/537.36',
        'content-type': 'application/json',
        'user-session-id': '',
        'accept': 'application/json',
        'app-session-time-elapsed': '-4967862',
        # 'x-auth-token': '',
        'user-session-time-elapsed': '1355273',
        'platform': 'web',
        'app-session-id': ',
        'app-version': '1026300',
        'origin': 'https://tinder.com',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://tinder.com/',
        'accept-language': 'en-US,en;q=0.9,pt;q=0.8',
    }