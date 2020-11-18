"""
All functional parts of the API are combined in the class LanaAPI2.

The name will be changed to LanaAPI as soon as we phase out the
eponymous legacy API.
"""

from pylana.aggregation import AggregationAPI
from pylana.dashboards import DashboardAPI
from pylana.logs import LogsAPI
from pylana.models import ModelsAPI
from pylana.resources import ResourceAPI
from pylana.shiny_dashboards import ShinyDashboardAPI
from pylana.users import UsersAPI


class LanaAPI2(LogsAPI, ModelsAPI, ShinyDashboardAPI, DashboardAPI, UsersAPI,
               AggregationAPI, ResourceAPI):
    """The Python API for Lana process Mining.

    It allows programmatic management of all lana resources.

    All required information to make authenticated requests to the api are
    passed during construction and stored. Named request methods are
    provided as wrappers around requests library methods, that add required
    header fields. Additional headers to the requests library methods can be
    passed as keyword arguments.

    Attributes:
        url (str):
            The base url of the api (scheme, host and port).
        user (User):
            A User dataclass encapsulating the user of the api information.
        headers (dict):
            The authorization header used for every request by default.
    """
    pass
