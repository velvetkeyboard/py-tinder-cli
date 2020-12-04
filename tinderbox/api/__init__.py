from .base import *


class AllMatches(TinderApiEndpoint):
    '''
    No messages yet
    '''
    path = '/v2/matches?locale=en&count=60&message=0&is_tinder_u=false'


class AllMatchesIceBreaked(TinderApiEndpoint):
    '''
    No messages yet
    '''
    path = '/v2/matches?locale=en&count=60&message=1&is_tinder_u=false'


class MessageEndpoint(TinderApiEndpoint):
    path = '/user/matches/{match_id}?locale=en'


class MatchMessages(TinderApiEndpoint):
    # &page_token=MjAyMC0xMS0yMVQxOTozOToyOC4xOTNa
    path = '/v2/matches/{match_id}/messages?locale=en&count=100'


class TravelEndpoint(TinderApiEndpoint):
    '''
    payload:
        {"lat":51.5073509,"lon":-0.1277583}
    '''
    path = '/passport/user/travel?locale=en'


class LikeEndpoint(TinderApiEndpoint):
    path = '/like/{uid}'


class RecommendationsEndpoint(TinderApiEndpoint):
    path = '/v2/recs/core'