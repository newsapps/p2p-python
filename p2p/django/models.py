from django.db import models
from django.utils.encoding import smart_str
from django.utils import text

from datetime import datetime
from iso8601 import parse_date, ParseError

from newsapps.p2p import get_connection

import logging
log = logging.getLogger(__name__)


p2p = get_connection()


def keyword_safe(d):
    """
    Given a dict, convert all of its keys to something safe for keywords.
    Mostly replace '-' with '_'.
    """
    return dict((smart_str(k.replace('-', '_'), strings_only=True),
                smart_str(v, strings_only=True))
        for k, v in d.items())


def convert_iso8601_dates(d):
    """
    Given a content item dict, convert iso8601 date
    fields to valid date/time format and return the modified dict.
    """
    for k, v in d.iteritems():
        try:
            if parse_date(v):
                d[k] = p2p.parsedate(v)
        except ParseError:
            pass
    return d


class Collection(models.Model):
    """
    An collection in p2p
    """
    name = models.CharField(blank=True, null=True, max_length=80)
    code = models.CharField(max_length=200, unique=True)
    types = models.CharField(blank=True, max_length=200,
            default='story/htmlstory/storylink/photogallery')
    last_updated = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name, verbose_name_plural = "Collection", "Collections"

    def __unicode__(self):
        if self.name:
            return unicode(self.name)
        else:
            return unicode(self.code)

    def update(self):
        """
        Load content items from this collection
        """
        collection_dict = p2p.get_fancy_collection(self.code)

        if len(collection_dict) == 0:
            return False

        # Delete all the existing relations between this collection
        # and any content items.
        content_items = ContentItemMembership.objects.filter(collection=self)
        content_items.delete()

        order = 1
        for ci in collection_dict['items']:
            ci = convert_iso8601_dates(keyword_safe(ci['content_item']))
            try:
                content_item = ContentItem.objects.get(slug=ci['slug'])

                diff = False
                for k, v in ci.items():
                    if not v == getattr(content_item, k):
                        diff = True
                        setattr(content_item, k, v)

                if diff:
                    log.info('Update ContentItem %s' % content_item.slug)
                    content_item.save()
                else:
                    log.debug('Skip ContentItem %s' % content_item.slug)

            except ContentItem.DoesNotExist:
                content_item = ContentItem.objects.create(**ci)
                log.debug('Create ContentItem %s' % content_item.slug)

            ContentItemMembership.objects.get_or_create(
                    collection=self, content_item=content_item, order=order)
            order += 1

        # record when we updated this collection
        self.last_updated = datetime.now()
        self.save()


class ContentItem(models.Model):
    """
    Represents a content item from p2p
    """
    id = models.IntegerField(blank=True, primary_key=True)

    # Date
    expire_time = models.DateTimeField(blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)
    last_modified_time = models.DateTimeField(blank=True, null=True)
    publish_time = models.DateTimeField(blank=True, null=True)
    live_time = models.DateTimeField(blank=True, null=True)
    display_time = models.DateTimeField(blank=True, null=True)

    # Text
    altheadline = models.TextField(blank=True, null=True)
    mobile_title = models.TextField(blank=True, null=True)
    source_name = models.TextField(blank=True, null=True)
    seodescription = models.TextField(blank=True, null=True)
    exclusivity = models.TextField(blank=True, null=True)
    content_type_group_code = models.TextField(blank=True, null=True)
    byline = models.TextField(blank=True, null=True)
    dateline = models.TextField(blank=True, null=True)
    brief = models.TextField(blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    undated = models.TextField(blank=True, null=True)
    is_opinion = models.TextField(blank=True, null=True)
    column_title = models.TextField(blank=True, null=True)
    columnist_blog = models.TextField(blank=True, null=True)
    columnist_id = models.TextField(blank=True, null=True)
    columnist_email = models.TextField(blank=True, null=True)
    columnist_facebook = models.TextField(blank=True, null=True)
    columnist_name = models.TextField(blank=True, null=True)
    columnist_twitter = models.TextField(blank=True, null=True)
    titleline = models.TextField(blank=True, null=True)
    ad_exclusion_category = models.TextField(blank=True, null=True)
    product_affiliate_code = models.TextField(blank=True, null=True)
    content_item_state_code = models.TextField(blank=True, null=True)
    content_item_type_code = models.TextField(blank=True, null=True)
    deckheadline = models.TextField(blank=True, null=True)
    seo_keyphrase = models.TextField(blank=True, null=True)
    mobile_highlights = models.TextField(blank=True, null=True)
    subheadline = models.TextField(blank=True, null=True)
    source_code = models.TextField(blank=True, null=True)
    ad_keywords = models.TextField(blank=True, null=True)
    seotitle = models.TextField(blank=True, null=True)

    # URLs
    canonical_url = models.URLField(blank=True, null=True)
    web_url = models.URLField(blank=True, null=True)
    seo_redirect_url = models.URLField(blank=True, null=True)
    thumbnail_url = models.URLField(blank=True, null=True)
    alt_thumbnail_url = models.URLField(blank=True, null=True)
    columnist_thumbnail_url = models.URLField(blank=True, null=True)
    columnist_alt_thumbnail_url = models.URLField(blank=True, null=True)

    # Other
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=200)

    collections = models.ManyToManyField(
            Collection, through='ContentItemMembership')

    class Meta:
        ordering = ['collections__name', 'contentitemmembership__order']
        verbose_name, verbose_name_plural = "Content Item", "Content Items"
        
    def save(self, *args, **kwargs):
        self.brief = text.truncate_html_words(self.body, 30)
        super(ContentItem, self).save(*args, **kwargs)

    def __unicode__(self):
        return unicode(self.title)

    @models.permalink
    def get_absolute_url(self):
        return ('p2p_content_item', [self.slug])


class ContentItemMembership(models.Model):
    collection = models.ForeignKey(Collection)
    content_item = models.ForeignKey(ContentItem)
    order = models.IntegerField()


########################
# Signals
########################

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save)
def update_collection(sender, **kwargs):
    # check if this is a new Collection object
    if sender == Collection and kwargs['created']:
        kwargs['instance'].update()
