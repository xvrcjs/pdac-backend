from django.conf import settings
from redis import from_url
from uuid import UUID
from settings.middlewares import get_request


cache = from_url(settings.CACHES['default']['LOCATION']) if settings.REDIS_ENABLED else None
CHUNK_SIZE = 5000

def clear_cache(key_pattern):
    """
    Clears all cache entries by a key pattern
    :param key_pattern: str
    :return: None
    """
    cursor = '0'
    while cursor != 0:
        cursor, keys = cache.scan(cursor=cursor, match=key_pattern, count=CHUNK_SIZE)
        if keys:
            cache.delete(*keys)
    get_request().cache_cleared = True


def clear_user_cache(user):
    """
    Clears all cache entries for a given user
    :param user: User instance
    :return: None
    """

    clear_cache(f'*:{user.pk}')

def clear_account_cache(account):
    """
    Clears cache entry for a given account
    :param account: Account instance
    :return: None
    """

    clear_cache(f'*:account:{account.user_id}')
