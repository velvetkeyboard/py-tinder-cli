import time
import yaml
from tinderbox.api import *


class BaseEntity(object):
    def __init__(self, data):
        self.data = data


class Recomendation(BaseEntity):

    def get_number(self):
        return self.data['s_number']

    def get_id(self):
        return self.data['user']['_id']

class Message(object):

    def __init__(self, data):
        self.data = data
    
    def get_id(self):
        return self.data['_id']

    def get_content(self):
        return self.data['message']

    def get_sent_date(self):
        return self.data['sent_date']

    def get_sender_id(self):
        return self.data['from']
    
    def get_destinatary_id(self):
        return self.data['to']


class Match(object):

    def __init__(self, data, credential):
        self.data = data
        self.credential = credential

    def get_name(self):
        return self.data['person']['name']

    def get_id(self):
        return self.data["_id"]

    def get_number(self):
        print(self.data)
        return self.data["person"]["s_number"]

    def send_msg(self, text):
        payload = {
            "userId": self.data["_id"][:24],
            "otherId": self.data["_id"][-24:],
            "tempMessageId": "0.7496613406628272",  # TODO Do we really need this one?
            "matchId": self.data["_id"],
            # "match": self.data,  # TODO Do we really need this one?
            "sessionId": "a78c13fe-1342-4d06-aaab-d91d6e704128",
            "message": text
        }
        return MessageEndpoint(
            credential=self.credential,
            match_id=self.data["_id"],
            ).post(json_data=payload)

    def unmatch(self):
        resp = MessageEndpoint(credential=self.credential, match_id=self.get_id()).delete()


class Tinder(object):

    def __init__(self, cfg_path):
        self.cfg = yaml.safe_load(open(cfg_path, 'r'))
        self.credential = XAuthTokenCredential(token=self.cfg['auth']['token'])

    def like(self, recs):
        for rec in recs:
            uid = rec.get_id()
            s_number = rec.get_number()
            time.sleep(self.cfg['like']['delay'])
            yield uid, LikeEndpoint(credential=self.credential, uid=uid)\
                    .post(json_data={"s_number": s_number})

    def get_recommendations(self):
        resp = RecommendationsEndpoint(credential=self.credential).get()
        return [Recomendation(rec) for rec in resp.json().get('data', {}).get('results', [])]

    def all_matches(self):
        ret = self.all_matches_no_messages_yet()
        resp = AllMatchesIceBreaked(credential=self.credential, page_token='').get()
        ret += [Match(match, self.credential) for match in resp.json()['data']['matches']]
        return ret

    def all_engaged_matches(self):
        resp = AllMatchesIceBreaked(credential=self.credential, page_token='').get()
        ret = [Match(match, self.credential) for match in resp.json()['data']['matches']]
        return ret

    def all_matches_no_messages_yet(self):
        resp = AllMatches(credential=self.credential, page_token='').get()
        return [Match(match, self.credential) for match in resp.json()['data']['matches']]

    def get_last_msg(self, match_id):
        resp = MatchMessages(credential=self.credential, match_id=match_id).get()
        return [Message(msg) for msg in resp.json()['data']['messages']]

    def change_location(self, lat, lon):
        resp = TravelEndpoint(credential=self.credential).post(json_data={'lat': lat, 'lon': lon})
        return resp
