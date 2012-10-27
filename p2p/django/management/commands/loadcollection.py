from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings
from newsapps.p2p.models import Collection, ContentItem

import logging
log = logging.getLogger("newsapps.p2p.loadcollections")


class Command(NoArgsCommand):
    """
    Create and load whichever collections were provided on the command line
    """

    def handle_noargs(self, **options):
        """
        Load collections from settings
        """

        Collection.objects.all().delete()
        ContentItem.objects.all().delete()

        # Fetch collections defined in settings.py
        if hasattr(settings, 'LOAD_COLLECTIONS'):
            for name, code in settings.LOAD_COLLECTIONS:
                # Create the collection if is hasn't been created before
                c, created = Collection.objects.get_or_create(
                        name=name, code=code)

                if created:
                    log.info('New collection: %s' % c)

        # Fetch all collections
        collections = Collection.objects.all()

        # Update collections
        for collection in collections:
            log.info('Updating collection: %s' % collection)
            #collection.update()
