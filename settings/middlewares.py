from datetime import datetime
from django.apps import apps
from django.http import Http404
from logging import getLogger
from pytz import UTC
from threading import local
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from jwt import decode

from common.utils import datetime_now, is_running_commands

logger = getLogger(__name__)

def log_request(request, response):
    if not response:
        logger.info('%s to %s by %s -> 404' % (
            request.method, request.path, get_request_by()
        ))
    elif response.status_code >= 500:
        logger.error('%s to %s by %s -> %s' % (
            request.method, request.path, get_request_by(), response.status_code
        ))
    elif response.status_code >= 400:
        logger.warning('%s to %s by %s -> %s' % (
            request.method, request.path, get_request_by(), response.status_code
        ))
    elif settings.DEBUG:
        logger.debug('%s to %s by %s -> %s' % (
            request.method, request.path, get_request_by(), response.status_code
        ))

#SCOPE
_request_scope = local()

def clear_request_scope():
    _request_scope.__dict__.clear()
    _request_scope.token_type = None
    _request_scope.token_expires_in = 0
    _request_scope.user = None
    _request_scope.account = None
    _request_scope.at = None
    _request_scope.ip = None
    _request_scope.origin = None
    _request_scope.cache_cleared = False


# TOKENS
def get_user_with_token(token):
    # Decode token
    try:
        token_claims = decode(
            token,
            settings.JWT_SECRET,
            algorithms=['HS256'],
            **({'audience': _request_scope.origin} if settings.JWT_AUD_CHECK else {})
        )
    except Exception as err:
        try: logger.warning('Invalid Token: %s -> %s' % (err, decode(token, options={'verify_signature': False})))
        except: logger.warning('Invalid Token: %s' % (err))
        return None
    # Account
    if token_claims['type'] == 'user':
        # Get Account
        get_account = apps.get_model('users.Account').objects.select_related('user').filter(
            user_id=token_claims['sub'],
            user__email=token_claims['email'],
            is_active=True,
        ).first
        _request_scope.account = cache.get_or_set(
            f'account:{token_claims["sub"]}',
            get_account
        ) if settings.REDIS_ENABLED else get_account()

        if not _request_scope.account:
            return None
        # Get token type and expiration
        _request_scope.token_type = token_claims['type']
        _request_scope.token_expires_in = int(token_claims['exp'] - _request_scope.at.timestamp())
        # Get User
        _request_scope.user = _request_scope.account.user
        # Return User
        return _request_scope.user

    return None

def get_refresh_token(token):
    return apps.get_model('users.UserRefreshToken').objects.select_related(
        'user',
    ).filter(
        token=token,
        aud=_request_scope.origin,
        exp__gte=_request_scope.at,
    ).first() or cache.get(f'refresh_token:{token}') if settings.REDIS_ENABLED else None

def get_user_with_refresh_token(token):
    # Get Refresh Token
    refresh_token = get_refresh_token(token)
    if not refresh_token:
        return [None, None]
    # Get Account
    _request_scope.account = refresh_token.account
    # Get token type and expiration
    _request_scope.token_type = 'account'
    _request_scope.token_expires_in = settings.JWT_ACCESS_EXP * 60 * 60 # Hours to seconds
    # Get User
    _request_scope.user = _request_scope.account.user
    # Save to cache for 5s (prevent logging out on parallel requests)
    if settings.REDIS_ENABLED:
        cache.set(f'refresh_token:{token}', refresh_token, 5)
    # Return User
    return [_request_scope.user, refresh_token]

# MIDDLEWARE
class RequestScopeMiddleware:
    
    def __init__(self, get_response):

        self.get_response = get_response

    def __call__(self, request):

        # Clear current request
        clear_request_scope()

        in_admin = False

        # Authentication flags
        auth_will_logout = False
        auth_will_refresh = False

        # Get at
        _request_scope.at = datetime_now()

        # Get from
        # Will get HTTP_X_FORWARDED_FOR at index -3, as -2 is CloudFront and -1 is Elastic Load Balancer
        _request_scope.ip = \
            request.META.get('HTTP_X_FORWARDED_FOR','').split(',')[-3:][0].strip() or \
            request.META.get('REMOTE_ADDR', '')
        _request_scope.origin = \
            request.META.get('HTTP_ORIGIN', '') or \
            '/'.join(request.META.get('HTTP_REFERER', '').split('/')[:3]) or \
            _request_scope.ip
        # API CALLS
        if request.path.startswith('/api/') or request.path.startswith('/auth/'):
            # Get user with token in Authorization
            authorization = request.META.get('HTTP_AUTHORIZATION', \
                request.META.get('HTTP_X_AWS_SQSD_ATTR_AUTHORIZATION', '')).split()
            if authorization.__len__() == 2 and authorization[0] == 'Bearer':
                token = authorization[1]
                request.user = get_user_with_token(token)
                # Check user
                if not request.user:
                    request.user = AnonymousUser()
                    auth_will_logout = True

            # Get user with token in Cookies
            elif 'token' in request.COOKIES:
                token = request.COOKIES['token']
                request.user = get_user_with_token(token)
                # Check user
                if not request.user:
                    request.user = AnonymousUser()
                    auth_will_logout = True

            # Get user with refresh_token in Cookies
            elif 'refresh_token' in request.COOKIES:
                [request.user, refresh_token] = get_user_with_refresh_token(request.COOKIES['refresh_token'])
                # Check user
                if not request.user:
                    request.user = AnonymousUser()
                    auth_will_logout = True
                else:
                    auth_will_refresh = True

            # Clear user if missing Authorization
            else:
                request.user = AnonymousUser()

        # ADMIN PAGE
        elif request.user.is_authenticated: # Do not get AnonymousUser as it has no custom functions and properties
            in_admin = True
            # Get User
            _request_scope.user = request.user
        # Store last access
        if _request_scope.user:
            _request_scope.user.update_last_access()

        # Save current request to request variable
        request.scope = _request_scope

        # Process view
        try:
            response = self.get_response(request)
        except Http404:
            log_request(request, None)
            return None

        # Log
        log_request(request, response)

        # Check authentication flags
        if auth_will_logout or response.status_code == 401:
            # Clear cookies
            return delete_cookies(response)
        if auth_will_refresh:
            # Create token
            [token, token_exp] = _request_scope.user.create_token()
            # Create refresh_token
            [refresh_token, refresh_token_exp] = refresh_token.refresh()
            # Create cookies
            return create_cookies(response, token, token_exp, refresh_token, refresh_token_exp)

        # Cache Scope
        if settings.REDIS_ENABLED and not _request_scope.cache_cleared and _request_scope.user:
            cache.set(
                f'user:{_request_scope.user.pk}',
                _request_scope.user
            )
        return response


# COOKIES
def create_cookies(response, token, token_exp, refresh_token=None, refresh_token_exp=None):
    response.set_cookie(
        'token',
        token,
        expires=token_exp.strftime('%a, %d %b %Y %H:%M:%S GMT') if token_exp else None,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite='None'
    )
    if refresh_token and refresh_token_exp:
        response.set_cookie(
            'refresh_token',
            refresh_token,
            expires=refresh_token_exp.strftime('%a, %d %b %Y %H:%M:%S GMT') if refresh_token_exp else None,
            httponly=True,
            secure=settings.SECURE_COOKIES,
            samesite='None'
        )
    else:
        response.set_cookie(
            'refresh_token',
            '',
            expires='Thu, 01 Jan 1970 00:00:01 GMT',
            httponly=True,
            secure=settings.SECURE_COOKIES,
            samesite='None'
        )

    return response

def delete_cookies(response):
    response.set_cookie(
        'token',
        '',
        expires='Thu, 01 Jan 1970 00:00:01 GMT',
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite='None'
    )
    response.set_cookie(
        'refresh_token',
        '',
        expires='Thu, 01 Jan 1970 00:00:01 GMT',
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite='None'
    )

    return response


# FUNCTIONS FOR OTHERS MODULES
def get_request():

    return _request_scope

def get_request_token_type():

    return getattr(_request_scope, 'token_type', None)

def get_request_token_expires_in():

    return getattr(_request_scope, 'token_expires_in', 0)


def get_request_account():

    return getattr(_request_scope, 'user', None)

def get_request_at():
    if not getattr(_request_scope, 'at', None):
        _request_scope.at = datetime_now()

    return _request_scope.at

def get_request_by():
    if not getattr(_request_scope, 'user', None):
        _request_scope.user = apps.get_model('users.User').objects.filter(
            pk=settings.SYSTEM_USER_UUID if is_running_commands() else settings.ANONYMOUS_USER_UUID
        ).first()

    return _request_scope.user

def get_request_from():

    return getattr(_request_scope, 'ip', None)

def get_request_origin():

    return getattr(_request_scope, 'origin', None)
