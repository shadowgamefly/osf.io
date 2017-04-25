import logging
import time

from website.app import init_app
from website.identifiers.utils import get_or_create_identifiers

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def add_identifiers_to_preprints():
    from osf.models import PreprintService

    preprints_without_identifiers = PreprintService.objects.filter(identifiers__isnull=True)
    logger.info('About to add identifiers to {} preprints.'.format(preprints_without_identifiers.count()))


    for preprint in preprints_without_identifiers:
        new_identifiers = get_or_create_identifiers(preprint)
        logger.info('Saving identifier for preprint {}'.format(preprint.node.title))
        preprint.set_preprint_identifiers(new_identifiers)
        preprint.save()
        time.sleep(1)

    logger.info('Finished Adding identifiers to {} preprints.'.format(preprints_without_identifiers.count()))


if __name__ == '__main__':
    init_app(routes=False)
    add_identifiers_to_preprints()