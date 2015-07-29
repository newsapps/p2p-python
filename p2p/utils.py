import iso8601
import re
import pytz
from datetime import datetime
from dateutil.parser import parse

_slugify_strip_re = re.compile(r'[^\w\s./-]')
_slugify_hyphenate_re = re.compile(r'[-./\s]+')
_iso8601_full_date = re.compile(r'^\d{4}-\d{2}-\d{2}.\d{2}:\d{2}.*$')
_iso8601_part_date = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    From Django's "django/template/defaultfilters.py".
    """
    import unicodedata
    if not isinstance(value, unicode):
        value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(_slugify_strip_re.sub('', value).strip().lower())
    return _slugify_hyphenate_re.sub('-', value)


def dict_to_qs(dictionary):
    """
    Takes a dictionary of query parameters and returns a query string
    that the p2p API will handle.
    """
    qs = list()

    for k, v in dictionary.items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                if type(v2) in (str, unicode, int, float, bool):
                    qs.append("%s[%s]=%s" % (k, k2, v2))
                elif type(v2) in (list, tuple):
                    for v3 in v2:
                        qs.append("%s[%s][]=%s" % (k, k2, v3))
                elif type(v2) == dict:
                    for k3, v3 in v2.items():
                        qs.append("%s[%s][%s]=%s" % (k, k2, k3, v3))
                else:
                    raise TypeError
        elif type(v) in (str, unicode, int, float, bool):
            qs.append("%s=%s" % (k, v))
        elif type(v) in (list, tuple):
            for v2 in v:
                qs.append("%s[]=%s" % (k, v2))
        else:
            raise TypeError

    return "&".join(qs)


def parse_response(resp):
    """
    Recurse through a dictionary from an API call, and fix weird values,
    convert date strings to objects, etc.
    """
    if type(resp) in (str, unicode):
        if resp in ("null", "Null"):
            # Null value as a string
            return None
        elif (
            _iso8601_full_date.match(resp) is not None or
            _iso8601_part_date.match(resp) is not None
        ):
            # Date as a string
            return parsedate(resp)
    elif type(resp) is dict:
        # would use list comprehension, but that makes unnecessary copies
        for k, v in resp.items():
            resp[k] = parse_response(v)
    elif type(resp) is list:
        # would use list comprehension, but that makes unnecessary copies
        for i in range(len(resp)):
            resp[i] = parse_response(resp[i])

    return resp


def parse_request(data):
    """
    Recurse through a dictionary meant for a request payload, make json- and
    p2p-friendly.
    """
    if type(data) is datetime:
        return formatdate(data)
    elif type(data) is dict:
        # would use list comprehension, but that makes unnecessary copies
        for k, v in data.items():
            data[k] = parse_request(v)
    elif type(data) is list:
        # would use list comprehension, but that makes unnecessary copies
        for i in range(len(data)):
            data[i] = parse_request(data[i])

    return data


def formatdate(d=datetime.utcnow()):
    try:
        return d.astimezone(pytz.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    except (ValueError, AttributeError):
        return d.strftime('%Y-%m-%dT%H:%M:%SZ')


def parsedate(d):
    if _iso8601_full_date.match(d) is not None:
        return iso8601.parse_date(d).replace(tzinfo=pytz.utc)
    else:
        return parse(d)
