import os
import time
import json
import argparse
import requests
import yaml
from tinderbox import __version__
from tinderbox.api import *
from tinderbox.services import *
from tinderbox.bot import *


def get_config(path):
    with open(path, 'r') as stream:
        return yaml.safe_load(stream)


def travelling(cfg, tinder):
    travel_rounds = cfg['travel']['rounds']
    travel_delay = cfg['travel']['delay']

    for location in cfg['travel']['locations']:
        lat = location['lat']
        lon = location['lon']

        time.sleep(travel_delay)
        resp = tinder.change_location(lat, lon)

        if resp.status_code == 200:
            print(f'Travelling to {location["name"]} for {travel_rounds} rounds')

        counter = 0

        while counter < travel_rounds:
            recs = tinder.get_recommendations()

            if not len(recs):
                # Damn son! So just liked all the available
                # profiles. Move to another location.
                break

            for user_id, resp in tinder.like(recs):
                if resp.status_code == 200:
                    print(f"liked {user_id}")
                # else:  # TODO convert this print to use the logger
                #     print(f"Could not like {user_id} - {resp.status_code} {resp.content}")

                counter += 1


def stationary(cfg, tinder):
    location = cfg['travel']['locations'][0]
    lat = location['lat']
    lon = location['lon']
    resp = tinder.change_location(lat, lon)
    if resp.status_code != 200:
        print(f'Could not set location to {location["name"]} - {resp.status_code} {resp.content}')

    while True:
        for user_id, resp in tinder.like(tinder.get_recommendations()):
            if resp.status_code != 200:
                print(f"Could not like {user_id} - {resp.status_code} {resp.content}")
            else:
                print(f"liked {user_id}")


def like(args):
    modes = {
        'travel': travelling,
        'stationary': stationary,
    }
    while True:
        # Reload everytime for a "hotreload" behavior
        cfg = get_config(args.config)
        tinder = Tinder(args.config)

        try:
            modes[cfg['like']['mode']](cfg, tinder)
        except KeyError:
            print(f"no support for {cfg['like']['mode']} mode")


def msg(args):  # TODO Remove this?
    text = args.text
    match_id = '5fb6f5f165e2560100ffd92c5fb7012783ceae0100631639'
    payload = {
        "userId": match_id[:24],
        "otherId": match_id[24:],
        "tempMessageId": "0.7496613406628272",
        "matchId": match_id,
        "match": {},
        "sessionId": "a78c13fe-1342-4d06-aaab-d91d6e704128",
        "message": text
    }
    resp = MessageEndpoint(match_id=match_id).post(json_data=payload)


def msg_ice_breaker_all(args):
    # cfg = get_config(args.config)
    tinder = Tinder(args.config)
    limit = args.limit
    text = args.text

    while True:
        for i, match in enumerate(tinder.all_matches_no_messages_yet()):
            print(f'Breaking the ice with {match.get_name()} ({match.get_id()[:8]})')
            if text:
                resp = match.send_msg(text)
            else:
                resp = match.send_msg(get_basic_opening())

            if i == limit - 1:
                exit(0)

            time.sleep(5)
        print('Waiting for new matches...')
        time.sleep(60 * 60)


def msg_all(args):
    text = args.text
    limit = args.limit
    tinder = Tinder(TINDER_TOKEN)
    for i, match in enumerate(tinder.all_matches()):
        print(f'Sending "{text}" to {match.get_name()} ({match.get_id()[:8]})', end='')
        if text == 'default':
            resp = match.send_msg(get_basic_opening())
        else:
            resp = match.send_msg(text)
        print(f' ... Sent!')
        if i == (limit - 1):
            break


def last_msg(args):
        match_id = args.match_id
        tinder = Tinder(TINDER_TOKEN)
        for msg in tinder.get_last_msg(match_id):
            who = 'match' if msg.data['to'] != match_id[:24] else 'mself'
            print(f'[{who}] sent "{msg.get_content()}" at {msg.get_sent_date()}')
        

def auto_reply(args):
    tinder = Tinder(TINDER_TOKEN)
    while True:
        for i, match in enumerate(tinder.all_engaged_matches()):
            msg = tinder.get_last_msg(match.get_id())[0]
            last_msg = msg.get_content().lower().strip()
            
            print(f'{i + 1} -> Checking last message from {match.get_name()} ({match.get_id()[:24]})')
            print(f'\tSender {msg.get_sender_id()} | Destinatary {msg.get_destinatary_id()}')

            if msg.get_sender_id() == match.get_id()[:24] and msg.get_destinatary_id() != match.get_id()[:24] and \
                msg.get_sender_id() != '5fb6f5f165e2560100ffd92c':
                print(f'\t "{last_msg}"')

                if last_msg == menu:
                    reply_msg = get_menu()
                else:
                    reply_msg = get_basic_info().get(last_msg)
                    if not reply_msg:
                        reply_msg = get_basic_not_understand()
                    else:
                        reply_msg = reply_msg['value']

                print(f'\tReplying "{msg.get_content()[:20]}" with "{reply_msg[:20]}" to {match.get_name()} ({match.get_id()[:8]})')
                resp = match.send_msg(reply_msg)

        print('Re-checking messages in a couple of minutes')
        time.sleep(30)


def auto_unmatch(args):
    tinder = Tinder(args.config)
    limit = args.limit
    for i, match in enumerate(tinder.all_engaged_matches()):
        print(f'{i + 1} -> Unmatching {match.get_name()} ({match.get_id()[:24]})')
        match.unmatch()
        if i == limit - 1:
            break


def main():
    parser = argparse.ArgumentParser(
        prog='tinderbox',
        description='tinder cli',
        )
    parser.add_argument(
        '-v', '--version', action='version', version=f'{__version__}')

    parser.add_argument(
        '-c', '--config', type=str, default='./tinderbox.yaml')

    sparser = parser.add_subparsers(help='actions help')

    # Liking People!!!!
    # --------------------------------------------------------------------------

    like_parser = sparser.add_parser(
        'like',
        help='like matches',
        )
    like_parser.add_argument(
        '-d',
        '--delay',
        type=int,
        default=10,
        help='delay (secs) for next batch',
        )
    like_parser.set_defaults(func=like)

    # Messaging People
    # --------------------------------------------------------------------------

    msg_parser = sparser.add_parser(
        'msg',
        help='send message to matches',
        )
    msg_parser.add_argument(
        'text',
        type=str,
        help='text to be sent',
        )
    msg_parser.add_argument(
        '-uid',
        type=str,
        help='match uid',
        )
    msg_parser.set_defaults(func=msg)

    # Messaging All People
    # --------------------------------------------------------------------------

    msg_all_parser = sparser.add_parser(
        'msg_all',
        help='send message to all matches',
        )
    msg_all_parser.add_argument(
        'text',
        type=str,
        help='text to be sent',
        )
    msg_all_parser.add_argument(
        '-limit',
        type=int,
        default=0,
        help='how many matches at once',
        )
    msg_all_parser.set_defaults(func=msg_all)

    msg_ice_breaker_parser = sparser.add_parser(
        'icebreaker',
        help='send message to all matches we did not enganged yet',
        )
    msg_ice_breaker_parser.add_argument(
        '-text',
        type=str,
        default='',
        help='how many matches at once',
        )
    msg_ice_breaker_parser.add_argument(
        '-limit',
        type=int,
        default=0,
        help='how many matches at once',
        )
    msg_ice_breaker_parser.set_defaults(func=msg_ice_breaker_all)

    last_msg_parser = sparser.add_parser(
        'last_msg',
        help='send message to all matches we did not enganged yet',
        )
    last_msg_parser.add_argument(
        'match_id',
        type=str,
        help='match id',
        )
    last_msg_parser.set_defaults(func=last_msg)


    auto_reply_parser = sparser.add_parser(
        'auto_reply',
        help='send message to all matches we did not enganged yet',
        )
    auto_reply_parser.set_defaults(func=auto_reply)

    auto_unmatch_parser = sparser.add_parser(
        'auto_unmatch',
        help='unmatch all things',
        )
    auto_unmatch_parser.add_argument(
        '-limit',
        type=int,
        default=0,
        help='how many matches at once',
        )
    auto_unmatch_parser.set_defaults(func=auto_unmatch)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
