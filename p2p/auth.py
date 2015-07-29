import requests
import json
from .adapters import TribAdapter


def authenticate(username=None, password=None, token=None, auth_url=None):

    if username is not None and password is not None:
        # we need the url to request against
        if auth_url is None:
            # First try the environment
            import os
            if 'P2P_AUTH_URL' in os.environ:
                auth_url = os.environ['P2P_AUTH_URL']
            else:
                # then try Django
                try:
                    from django.conf import settings
                    auth_url = settings.P2P_AUTH_URL
                except Exception:
                    pass
                    raise P2PAuthError(
                        "No connection settings available. Please put settings"
                        " in your environment variables or your Django config")

        s = requests.Session()
        s.mount('https://', TribAdapter())
        resp = s.post(
            auth_url,
            params={
                'username': username,
                'password': password,
                'token': token,
            },
            verify=False)

        if not resp.ok:
            if resp.status_code == 403:
                raise P2PAuthError('Incorrect username or password')
            else:
                raise P2PAuthError(resp.content)

        return json.loads(resp.content)['p2p_user']
    else:
        raise NotImplementedError


try:
    from django.contrib.auth.models import User

    class P2PBackend:
        def authenticate(self, username=None, password=None):

            try:
                userinfo = authenticate(username=username, password=password)

                # prefix 'p2p' to the username so it doesn't collide with
                # any other local users. This doesn't change the username
                # that you use for authentication
                local_username = '.'.join(('p2p', userinfo['username']))

                try:
                    user = User.objects.get(username=local_username)

                except User.DoesNotExist:
                    user = User(
                        username=local_username,
                        email=userinfo['email'],
                        first_name=userinfo['first_name'],
                        last_name=userinfo['last_name'])
                    user.set_unusable_password()
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()

                return user
            except P2PAuthError:
                pass

            return None

        def get_user(self, user_id):
            try:
                return User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return None

except ImportError, e:
    pass


class P2PAuthError(Exception):
    pass
