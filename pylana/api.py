"""
generic api requests including authorization
"""

from typing import Optional

import requests

from pylana.decorators import handle_response, expect_json
from pylana.structures import User


def _create_authorization_header(token: str) -> dict:
    return {"Authorization": f"API-Key {token}"}


@expect_json
@handle_response
def get_user_information(url, token, **kwargs) -> dict:
    headers = {**_create_authorization_header(token),
               **kwargs.pop('headers', dict())}
    r = requests.get(url + '/api/users/by-token', headers=headers,
                     **kwargs)
    r.raise_for_status()
    return r


def get_user(url, token, **kwargs) -> User:
    user_info = get_user_information(url, token, **kwargs)
    return User(user_id=user_info.get('id'),
                organization_id=user_info.get('organizationId'),
                api_key=user_info.get('apiKey'),
                role=user_info.get('role'))


# TODO consider certificate passing for TLS
# TODO consider letting kwargs replace authentication header
class API:
    """An api for a specific user at a Lana deployment.

    All required information to make authenticated requests to the api are
    passed during construction and stored. Named request methods are
    provided as wrappers around requests library methods, that add required
    header fields. Additional headers to the requests library methods can be
    passed as keyword arguments.

    When constructed a request to the lana api is made in order to
    retrieve user information.

    Attributes:
        url (str):
            A string denoting the URL of the lana api, including the
            application root.
        user:
            A User dataclass encapsulating the user of the api information.
        headers:
            A dictionary representing the authorization header used for every
            request by default.
    """

    # TODO document
    def __init__(self, scheme: str, host: str, token: str,
                 port: Optional[int] = None,
                 application_root: Optional[str] = None, **kwargs):
        """Construct a configured LANA api.

        Args:
            scheme:
                A string denoting the scheme of the api URL.
            host:
                A string denoting the lana api host.
            token:
                A string denoting the user authentication token without the
                preceding "API-Key".
            port:
                (optional) A string or integer denoting the port of the
                lana api.
            application_root:
                (optional) A string denoting the application root. Only required
                if your lana api is placed outside the URL root, e.g. "/lana-api"
                instead of "/". Has to start with a slash.
            **kwargs:
                Keyword arguments to pass to requests for the initial
                request retrieving user information.
        """

        self.url = (f'{scheme}://{host}'
                    + (f':{port}' if port else '')
                    + (f':{application_root}'
                       if application_root else '').replace('//', '/')
                    ).strip('/')
        self.user = get_user(self.url, token, **kwargs)
        self.headers = _create_authorization_header(token)

    def _request(self, method, route, headers=None, additional_headers=None,
                 **kwargs):
        headers = {**self.headers, **(additional_headers or dict()),
                   **(headers or dict())}
        return requests.request(method, self.url + route, headers=headers,
                                **kwargs)

    @handle_response
    def get(self, route, additional_headers=None, **kwargs):
        return self._request('GET', route, additional_headers, **kwargs)

    @handle_response
    def put(self, route, additional_headers=None, **kwargs):
        return self._request('PUT', route, additional_headers, **kwargs)

    @handle_response
    def post(self, route, additional_headers=None, **kwargs):
        return self._request('POST', route, additional_headers, **kwargs)

    @handle_response
    def patch(self, route, additional_headers=None, **kwargs):
        return self._request('PATCH', route, additional_headers, **kwargs)

    @handle_response
    def delete(self, route, additional_headers=None, **kwargs):
        return self._request('DELETE', route, additional_headers, **kwargs)
