import re

UNQUERYABLE_PATTERN = re.compile('\.[a-zA-Z]+$')
QUERY_PATTERN = re.compile('/\d+(/\d+x\d+)?$')


def get_body(content_dict):
    """
    Get the content item body or caption, whatever it's called
    """
    content_item = find_content_item(content_dict)

    if content_item.get('body', False):
        body = content_item['body'] or ''
    elif content_item.get('caption', False):
        body = content_item['caption'] or ''
    elif content_item.get('short_description', False):
        body = content_item['short_description'] or ''
    else:
        body = ''

    return br_to_p(strip_runtime_tags(body))


def get_brief(content_dict, words=60):
    """
    Get the abstract or brief for an item, or make one to length 'words' from
    the body
    """
    if content_dict.get('abstract', False):
        return content_dict['abstract']
    else:
        content_item = find_content_item(content_dict)

    if content_item.get('body', False):
        brief = content_item['body'] or ''
    elif content_item.get('caption', False):
        brief = content_item['caption'] or ''
    elif content_item.get('short_description', False):
        brief = content_item['short_description'] or ''
    else:
        brief = ''

    return truncate_words(
        strip_tags(br_to_space(brief)), words)


def get_headline(content_dict):
    """
    Get the headline for this item
    """
    if content_dict.get('headline', False):
        return content_dict['headline']
    else:
        content_item = find_content_item(content_dict)

    return content_item['title']


def get_url(content_dict):
    """
    Get the p2p url for this item, or if it's a link, get the link url
    """
    content_item = find_content_item(content_dict)

    link_types = ('hyperlink', 'storylink')
    if (
        'content_item_type_code' in content_item and
        content_item['content_item_type_code'] in link_types
    ):
        return content_item['url'] if 'url' in content_item else ""
    else:
        return content_item['web_url']


def get_thumb_url(content_dict, size, ratio=None):
    """
    Find a thumbnail url in the content item dictionary and adjust the size
    and ratio parameters before returning the url. Pass 'None' for size to get
    a url without any size or ratio params.
    """
    content_item = find_content_item(content_dict)

    # If image_url already contains query, replace it; otherwise, append query.
    if (
        'photo_services_url' in content_item and
        content_item['photo_services_url']
    ):
        image_url = content_item['photo_services_url']
    elif (
        'alt_thumbnail_url' in content_item and
        content_item['alt_thumbnail_url']
    ):
        image_url = content_item['alt_thumbnail_url']
    elif 'thumbnail_url' in content_item and content_item['thumbnail_url']:
        image_url = content_item['thumbnail_url']
    else:
        return ""

    # If image_url ends in .jpg or any other filename, can't use query with it
    if UNQUERYABLE_PATTERN.search(image_url):
        return image_url

    if size is None:
        query = ''
    elif ratio is None:
        query = str(size)
    else:
        query = '/'.join([str(size), ratio])

    if QUERY_PATTERN.search(image_url):
        ret = QUERY_PATTERN.sub('/' + query, image_url)
    else:
        ret = '/'.join([image_url.rstrip('/'), query])
    return ret.rstrip('/')


def get_byline(content_dict):
    """
    Get the byline for this item
    """
    if 'byline' in content_dict:
        return content_dict['byline']
    else:
        return find_content_item(content_dict)['byline']


def get_time(content_dict):
    if content_dict.get('display_time', False):
        return content_dict['display_time']
    elif 'content_item' in content_dict:
        if content_dict['content_item'].get('display_time', False):
            return content_dict['content_item']['display_time']
        elif content_dict['content_item'].get('create_time', False):
            return content_dict['content_item']['create_time']
    else:
        return content_dict['create_time']


def get_featured_related_item(content_dict):
    """
    Look through related items to find the first photo, gallery or video
    """
    content_item = find_content_item(content_dict)
    feature_types = (
        'embeddedvideo', 'photogallery', 'photo', 'premiumvideo')

    for item in content_item['related_items']:
        if item['content_item_type_code'] in feature_types:
            return item


def find_content_item(content_dict):
    if 'content_item' in content_dict:
        return content_dict['content_item']
    else:
        return content_dict


def br_to_space(text):
    return re.sub(r'<br[^>]*?>\s*?(&nbsp;)?\s*?<br[^>]*?>', ' ', text)


def split_paragraphs(value):
    """
    Take a block of text and return an array of paragraphs. Only works if
    paragraphs are denoted by <p> tags and not double <br>.
    Use `br_to_p` to convert text with double <br>s to <p> wrapped paragraphs.
    """
    value = re.sub(r'</p>\s*?<p>', u'</p>\n\n<p>', value)
    paras = re.split('\n{2,}', value)
    return paras


def br_to_p(value):
    """
    Converts text where paragraphs are separated by two <br> tags to text
    where the paragraphs are wrapped by <p> tags.
    """
    value = re.sub(r'<br\s*?/?>\s*?(&nbsp;)?\s*?<br\s*?/?>', u'\n\n', value)
    paras = re.split('\n{2,}', value)
    paras = [u'<p>%s</p>' % p.strip() for p in paras if p]
    paras = u'\n\n'.join(paras)
    paras = re.sub(r'</p\s*?>\s*?</p\s*?>', u'</p>', paras)
    paras = re.sub(r'<p\s*?>\s*?<p\s*?>', u'<p>', paras)
    paras = re.sub(r'<p\s*?>\s*?(&nbsp;)?\s*?</p\s*?>', u'', paras)
    return paras


def section_heads(value):
    """
    Search through a block of text and replace <p><b>text</b></p>
    with <h4>text</h4>
    """
    value = re.sub(r'<p>\s*?<b>([^<]+?)</b>\s*?</p>', u'<h4>\\1</h4>', value)
    return value


def strip_runtime_tags(value):
    return re.sub(r'</?runtime:[^>]*?>', '', value)


def truncate_words(content, words=60, suffix='...'):
    word_list = re.split('\s+', force_unicode(content))
    if len(word_list) <= words:
        return content
    return u' '.join(word_list[:words]) + force_unicode(suffix)


# http://stackoverflow.com/questions/2584885/strip-tags-python
def strip_tags(value):
    """Returns the given HTML with all tags stripped."""
    return re.sub(r'<[^>]*?>', '', force_unicode(value))


# http://www.codigomanso.com/en/2010/05/una-de-python-force_unicode/
def force_unicode(s, encoding='utf-8', errors='ignore'):
    """
    Returns a unicode object representing 's'. Treats bytestrings using the
    'encoding' codec.
    """
    if s is None:
        return ''

    try:
        if not isinstance(s, basestring,):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                try:
                    s = unicode(str(s), encoding, errors)
                except UnicodeEncodeError:
                    if not isinstance(s, Exception):
                        raise
                    # If we get to here, the caller has passed in an Exception
                    # subclass populated with non-ASCII data without special
                    # handling to display as a string. We need to handle this
                    # without raising a further exception. We do an
                    # approximation to what the Exception's standard str()
                    # output should be.
                    s = ' '.join(
                        [force_unicode(arg, encoding, errors) for arg in s])
        elif not isinstance(s, unicode):
            # Note: We use .decode() here, instead of unicode(s, encoding,
            # errors), so that if s is a SafeString, it ends up being a
            # SafeUnicode at the end.
            s = s.decode(encoding, errors)
    except UnicodeDecodeError, e:
        if not isinstance(s, Exception):
            raise UnicodeDecodeError(s, *e.args)
        else:
            # If we get to here, the caller has passed in an Exception
            # subclass populated with non-ASCII bytestring data without a
            # working unicode method. Try to handle this without raising a
            # further exception by individually forcing the exception args
            # to unicode.
            s = ' '.join([force_unicode(arg, encoding, errors) for arg in s])
    return s
