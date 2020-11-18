"""
dashboard management api requests
"""

from typing import List

from requests import Response

from pylana.decorators import warn_for_interface_deprecation
from pylana.resources import ResourceAPI


class DashboardAPI(ResourceAPI):

    def list_dashboards(self, **kwargs) -> List[dict]:
        """
        List all dashboards available to the user.
        
        Args:
            **kwargs:
                Keyword arguments passed to requests functions.
            
        Returns: 
            A list of strings denoting dashboard names.
        """
        return self.list_resources('v2/dashboards', **kwargs)

    def get_dashboard_ids(self, contains: str = '.*', **kwargs) \
            -> List[str]:
        """
        List ids of dashboard pages with matching names.

        Args:
           contains:  
                A string denoting a regular expression
                matched against the dashboard titles.
            **kwargs: 
                Keyword arguments passed to requests functions.
            
        Returns:
            A list of strings denoting the ids of the dashboard pages.
        """
        return self.get_resource_ids('v2/dashboards', contains, **kwargs)

    def get_dashboard_id(self, contains: str, **kwargs) -> str:
        """
        Get dashboard id with matching name.

        Args:
            contains:  
                A string denoting a regular expression
                matched against the dashboard name.
            **kwargs: 
                Keyword arguments passed to requests functions.
            
        Returns: 
            A string denoting the id of the dashboard page.

        Raises:
            Exception:
                None or more than one dashboard name matches the
                regular expression.
        """
        return self.get_resource_id('v2/dashboards', contains, **kwargs)

    # TODO json lacks sharing options
    def create_dashboard(self, name: str, items: List[dict], 
                         is_active: bool = False, **kwargs) -> Response:
        """
        Create a dashboard with a list of dashboard items.

        Args:
            name:  
                A string denoting the dashboard name.
            items:
                A list of dicts denoting the dashboard items (referenced as
                charts in LANA Process Mining)
            is_active:
                A boolean denoting if the dashboard should be set
                as the last one selected by the user.
            **kwargs: 
                Keyword arguments passed to requests functions.
            
        Returns:
            The requests response of the lana api call.
        """
        request_data = {'title': name,
                        'items': items,
                        'isActive': is_active}

        return self.create_resource('v2/dashboards/', json=request_data, **kwargs)

    def describe_dashboard(self, contains: str = None,
                           dashboard_id: str = None, **kwargs) -> dict:
        """
        Get dashboard metadata.

        Args:
            contains: 
                A string denoting a regular expression
                matched against the dashboard name. 
                Matching several names raises an exception.
            dashboard_id: 
                A string denoting the id of the dashboard page.
            **kwargs: 
                Keyword arguments passed to requests functions.
            
        Returns:
            A dictionary with the dashboard data.
        """
        return self.describe_resource('v2/dashboards', contains, dashboard_id, 
                                      **kwargs)
    
    def describe_dashboard_items(self, contains: str = None,
                                 dashboard_id: str = None, **kwargs) \
            -> List[dict]:
        """
        Get dashboard item metadata.

        Args:
            contains: 
                A string denoting a regular expression
                matched against the dashboard name. 
                Matching several names raises an exception.
            dashboard_id: 
                A string denoting the id of the dashboard page.
            **kwargs: 
                Keyword arguments passed to requests functions.
            
        Returns:
            A list with the dashboard items as dicts (items are referenced as
            charts in LANA Process Mining)
        """
        dashboard = self.describe_dashboard(contains, dashboard_id, **kwargs)
        
        return dashboard["items"]

    def delete_dashboard(self, dashboard_id: str, **kwargs) \
            -> Response:
        """
        Delete a dashboard by its id.
        
        Args:
            dashboard_id: 
                A string denoting the id of the dashboard page.
            **kwargs: 
                Keyword arguments passed to requests functions.

        Returns:
            The requests response of the lana api call.
        """
        return self.delete_resource('v2/dashboards', dashboard_id,
                                    **kwargs)

    def delete_dashboards(self, contains: str = None,
                          ids: List[str] = None, **kwargs) -> \
            List[Response]:
        """
        Delete dashboards with matching names.

        Args:
            contains: 
                A string denoting a regular expression. 
                It is ignored when ids are passed.
            ids: 
                A list of strings denoting ids of dashboard pages.
            **kwargs:
                Keyword arguments passed to requests functions.
                
        Returns:
            A list of request responses of the calls to the lana api.
        """
        return self.delete_resources('v2/dashboards', contains, ids,
                                     **kwargs)

    # TODO consider sharing by names
    @warn_for_interface_deprecation
    def share_dashboard(self, dashboard_id: str, organization_ids: List[str],
                        **kwargs) -> Response:
        """
        Share a dashboard with organizations by ids.
        Args:
            dashboard_id:
                A string denoting the id of the dashboard page.
            organization_ids:
                A list of strings denoting ids of organizations to share with.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            The requests response of the lana api call.
        """
        return self.put(
            f"/api/v2/dashboards/{dashboard_id}/sharing",
            json={"shareWithOrganizations": organization_ids},
            **kwargs)

    @warn_for_interface_deprecation
    def unshare_dashboard(self, dashboard_id: str, organization_ids: List[str],
                          **kwargs) -> Response:
        """
        Unshare a dashboard with organizations by ids.

        Args:
            dashboard_id:
                A string denoting the id of the dashboard page.
            organization_ids:
                A list of strings denoting ids of organizations to unshare the
                dashboard with.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            The requests response of the lana api call.
        """
        return self.put(
            f"/api/v2/dashboards/{dashboard_id}/sharing",
            json={"unshareWithOrganizations": organization_ids},
            **kwargs)

    def connect_dashboard(self, log_id, dashboard_id, **kwargs) \
            -> Response:
        """
        Connect a dashboard with a log by their ids.
        
        Args:
            log_id: 
                A string denoting the id of the log in LANA.
            dashboard_id:
                A string denoting the id of the dashboard page.
            **kwargs: 
                Keyword arguments passed to requests functions.

        Returns:
            The requests response of the lana api call.
        """
        dct = {'log_id': log_id, 'dashboard_id': dashboard_id}
        return self.connect_resources(dct, **kwargs)
