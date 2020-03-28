import os
import sys
import json
import random
import requests
import logging
from datetime import datetime

LOGLEVEL = os.environ.get("TINDER_LOGLEVEL", "INFO")
logging.basicConfig(level=LOGLEVEL)
logger = logging.getLogger("Tinder API")


class Endpoint(object):
    domain = ''
    path = ''
    params = {}
    headers = {}

    def __init__(self, *args, **kwargs):
        self.path_vars = kwargs

    def get_domain(self):
        return self.domain

    def get_path(self):
        if self.path_vars:
            return self.path.format(**self.path_vars)
        return self.path

    def get_url(self):
        return "{}{}".format(self.get_domain(), self.get_path())

    def get_params(self):
        return self.params

    def get_headers(self):
        return self.headers

    def request(self, http_method, *args, **kwargs):
        verb = http_method
        url = self.get_url()
        params = {}
        params.update(kwargs.get("params", {}))
        params.update(self.get_params())
        # params = self.credential.get_params()
        headers = {}
        # headers = self.credential.get_headers()
        headers.update(kwargs.get("headers", {}))
        headers.update(self.get_headers())
        data = kwargs.get("data", {})
        logger.debug("HTTP - {} - Request - URL {}".format(verb, url))
        logger.debug("HTTP - {} - Request - Params {}".format(verb, params))
        logger.debug("HTTP - {} - Request - Headers {}".format(verb, headers))
        # exit(0)
        fn = getattr(requests, verb)
        if data:
            data = json.dumps(data)
            resp = fn(url=url, headers=headers, params=params, data=data, verify=True)
        else:
            resp = fn(url=url, headers=headers, params=params, verify=True)
        logger.debug(
            "HTTP - {} - Response - status code - {}".format(
                verb, resp.status_code
                )
        )
        logger.debug(
            "HTTP - {} - Response - content - {}".format(verb, resp.content)
        )
        return resp

    def get(self, *args, **kwargs):
        return self.request("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request("post", *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.request("patch", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request("delete", *args, **kwargs)


class BaseAuthSmsEndpoint(Endpoint):
    domain = 'https://api.gotinder.com'
    headers = {
        'user-agent': 'Tinder/11.4.0 (iPhone; iOS 12.4.1; Scale/2.00)',
        'content-type': 'application/json'
    }


class AuthSmsSend(BaseAuthSmsEndpoint):

    path = '/v2/auth/sms/send'
    params = {
        'auth_type': 'sms'
    }


class AuthSmsValidate(BaseAuthSmsEndpoint):
    path = '/v2/auth/sms/validate'
    params = {
        'auth_type': 'sms'
    }


class AuthLoginSms(BaseAuthSmsEndpoint):
    path = '/v2/auth/login/sms'


class ApiEndpoint(Endpoint):
    domain = 'https://api.gotinder.com'
    headers = {
        'app_version': '6.9.4',
        'platform': 'ios',
        'content-type': 'application/json',
        'User-agent': 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0',
        'X-Auth-Token': None,
    }
    api_token = None

    def get_headers(self):
        headers = super(ApiEndpoint, self).get_headers()
        if not self.api_token:
            self.api_token = self.get_api_token()
        headers['X-Auth-Token'] = self.api_token
        return headers

    def get_api_token(self):
        with open('tinder_token.txt', 'r') as f:
            self.api_token = f.read()
        return self.api_token


class MatchesEndpoint(ApiEndpoint):
    path = '/v2/matches'
    params = {
        'count': 60,
        'is_tinder_u': 'false',
        'locale': 'en',
        'message': 0,
    }

    def get_headers(self):
        headers = super(MatchesEndpoint, self).get_headers()
        headers['x-supported-image-formats'] = 'webp,jpeg'
        return headers


class UserMatchesEndpoint(ApiEndpoint):
    path = '/user/matches/{match_id}'


class TinderTokenSms(object):

    def __init__(self, phone_number):
        self.phone_number = phone_number

    def send_otp_code(self):
        data = {
            'phone_number': self.phone_number,
        }
        endpoint = AuthSmsSend()
        resp = endpoint.post(data=data, verify=False)
        logger.info(f'status_code = {resp.status_code}')
        if resp.json()["data"]['sms_sent']:
            return True

    def get_refresh_token(self, otp_code):
        data = {
            'otp_code': otp_code,
            'phone_number': self.phone_number,
        }
        endpoint = AuthSmsValidate()
        resp = endpoint.post(data=data, verify=False)
        logger.info(f'status_code = {resp.status_code}')
        if resp.json()['data']['validated']:
            return resp.json()['data']['refresh_token']

    def get_api_token(self, otp_code):
        refresh_token = self.get_refresh_token(otp_code)
        data = {
            'refresh_token': refresh_token,
        }
        endpoint = AuthLoginSms()
        resp = endpoint.post(data=data, verify=False)
        return resp.json()['data']['api_token']


def get_all_matches():
    matches = []

    # Never Messaged
    page_token = None
    endpoint = MatchesEndpoint()
    while True:
        resp = endpoint.get(params={'page_token': page_token})
        matches += resp.json()['data']['matches']
        page_token = resp.json()['data'].get('next_page_token')
        if not page_token:
            break

    # Messaged Once
    page_token = None
    endpoint = MatchesEndpoint()
    endpoint.params['message'] = 1
    while True:
        resp = endpoint.get(params={'page_token': page_token})
        matches += resp.json()['data']['matches']
        page_token = resp.json()['data'].get('next_page_token')
        if not page_token:
            break

    return matches


TEMPLATE = '''
{}


༼つ◕_◕༽つ
'''
LAST_PICKUP = ''
def send_msg(match_id, text):
    text = TEMPLATE.format(text)
    endpoint = UserMatchesEndpoint(match_id=match_id)
    resp = endpoint.post(data={'message': text})
    return resp

def get_pickup_line(lang):
    global LAST_PICKUP
    with open(f'pickup_lines_{lang}.txt', 'r') as f:
        pickup_lines = f.read().split('\n')
    ret = ''
    while True:
        ret = random.choice(pickup_lines)
        if ret != LAST_PICKUP:
            LAST_PICKUP = ret
            break
    print('picked up > ', ret)
    return ret


if __name__ == '__main__':
    if sys.argv[1] == 'auth':
        print(sys.argv)
        tts = TinderTokenSms(sys.argv[2])
        tts.send_otp_code()
        otp_code = input('SMS Code > ')
        api_token = tts.get_api_token(otp_code)
        with open('tinder_token.txt', 'w') as f:
            f.write(api_token)

    elif sys.argv[1] == 'matches':
        if sys.argv[2] == 'list':
            for match in get_all_matches():
                print('{} - {} - {}'.format(
                    match['id'],
                    match['last_activity_date'],
                    match['person']['name'],
                ))
        elif sys.argv[2] == 'unmatch':
            if sys.argv[3] == 'idles':
                now = datetime.now()
                print('Unmatching idles ...')
                for match in get_all_matches():
                    if len(match['messages']):
                        sent_date = match['messages'][0]['sent_date']
                        sent_date = datetime.strptime(sent_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                        delta = now - sent_date
                        if delta.days >= 1:
                            print('{} - {} - {} -> {} = {}'.format(
                                match['id'],
                                match['last_activity_date'],
                                match['person']['name'],
                                sent_date,
                                delta.days,
                            ))
                            endpoint = UserMatchesEndpoint(match_id=match['id'])
                            resp = endpoint.delete()
            else:
                match_id = sys.argv[3]
                endpoint = UserMatchesEndpoint(match_id=match_id)
                resp = endpoint.delete()
                print(resp.json())

    elif sys.argv[1] == 'msg':
        if sys.argv[2] == 'coldopen':
            for match in get_all_matches():
                if sys.argv[3] == 'pickup':
                    text = get_pickup_line('br')
                else:
                    text = sys.argv[3]
                if not len(match['messages']):
                    send_msg(match['id'], text)

        elif sys.argv[2] == 'all':
            for match in get_all_matches():
                send_msg(match['id'], sys.argv[3])
        elif sys.argv[2] == 'id':
            send_msg(sys.argv[3], sys.argv[4])
        else:
            for match in get_all_matches():
                print('Checking... ', match['person']['name'])
                if match['person']['name'] == sys.argv[2]:
                    send_msg(match['id'], sys.argv[3])
                    break

        if sys.argv[2] == 'pickup':
            for match in get_all_matches():
                send_msg(match['id'], text)
                break
