from datetime import datetime
from email.Utils import parsedate
import json
import logging

from django import http

import jingo

from .models import CannedCategory, Tweet
import twitter

log = logging.getLogger('k')


@twitter.auth_wanted
def landing(request):
    """Customer Care Landing page."""

    twitter = request.twitter

    canned_responses = CannedCategory.objects.all()
    tweets = []
    for tweet in Tweet.objects.filter(locale='en')[:10]:
        data = json.loads(tweet.raw_json)
        parsed_date = parsedate(data['created_at'])
        date = datetime(*parsed_date[0:6])
        tweets.append({
            'profile_img': data['profile_image_url'],
            'user': data['from_user'],
            'text': tweet,
            'reply_to': tweet.tweet_id,
            'date': date,
        })

    resp = jingo.render(request, 'customercare/landing.html', {
        'canned_responses': canned_responses,
        'tweets': tweets,
        'authed': twitter.authed,
    })

    return resp

def is_printable(s, coded='utf-8'):
    try: s.decode(codec)
    except UnicodeDecodeError: return False
    else: return True

def is_int(x):
    try: return int(x) == x
    except ValueError: return False

@twitter.auth_required
def twitter_post(request):
    reply_to = request.POST.get('reply_to')
    reply_to_name = request.POST.get('reply_to_name')
    tweet = request.POST.get('tweet')
    content = '@{0} {1} #fxhelp'.format(reply_to_name, tweet)

    if not is_int(reply_to):
        return http.HttpResponseBadRequest('Malformed data.  reply_to must be an integer.')
    elif not is_printable(content):
        return http.HttpResponseBadRequest('Malformed data.  content must be printable.')
    elif len(content) > 140:
        return http.HttpResponseBadRequest('Content length exceeds 140 characters.')
    else:
        try:
            request.twitter.api.update_status(content, reply_to)
        except tweepy.TweepError, e:
            return http.HttpResponseBadRequest(e)
        else:
            return http.HttpResponse()