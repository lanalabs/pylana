"""
shiny dashboard management api requests
"""

import json
import os
import re
import zipfile
from typing import List

from requests import Response

from pylana.decorators import warn_for_interface_deprecation
from pylana.resources import ResourceAPI


class ShinyDashboardAPI(ResourceAPI):

    def list_shiny_dashboards(self, **kwargs) -> List[dict]:
        """
        List all shiny dashboards available to the user.
        
        Args:
            **kwargs:
                Keyword arguments passed to requests functions.
            
        Returns: 
            A list of strings denoting shiny dashboard names.
        """
        return self.list_resources('shiny-dashboards', **kwargs)

    def get_shiny_dashboard_ids(self, contains: str = '.*', **kwargs) \
            -> List[str]:
        """
        List shiny dashboard ids with matching names.

        Args:
           contains:  
                A string denoting a regular expression
                matched against the shiny dashboard names.
            **kwargs: 
                Keyword arguments passed to requests functions.
            
        Returns:
            A list of strings denoting shiny dashboard ids.
        """
        return self.get_resource_ids('shiny-dashboards', contains, **kwargs)

    def get_shiny_dashboard_id(self, contains: str, **kwargs) -> str:
        """
        Get shiny dashboard id with matching name.

        Args:
            contains:  
                A string denoting a regular expression
                matched against the shiny dashboard name.
            **kwargs: 
                Keyword arguments passed to requests functions.
            
        Returns: 
            A string denoting the shiny dashboard id.

        Raises:
            Exception:
                None ore more than one shiny dashboard name matches the
                regular expression.
        """
        return self.get_resource_id('shiny-dashboards', contains, **kwargs)

    def describe_shiny_dashboard(self, contains: str = None,
                                 shiny_dashboard_id: str = None, **kwargs) \
            -> dict:
        """
        Get shiny dashboard metadata.

        Args:
            contains: 
                A string denoting a regular expression
                matched against the log name. 
                Matching several names raises an exception.
            shiny_dashboard_id: 
                A string denoting the id of the log.
            **kwargs: 
                Keyword arguments passed to requests functions.
            
        Returns:
            A dictionary denoting the shiny dashboard description.
        """
        return self.describe_resource('shiny-dashboards', contains, shiny_dashboard_id, **kwargs)

    # TODO json lacks sharing options
    def create_shiny_dashboard(self, name: str, **kwargs) -> dict:
        """
        Create a named shiny dashboard.

        Args:
            name: 
                A string denoting the dashboards name.
            **kwargs: 
                Keyword arguments passed to requests functions.

        Returns:
            A dictionary denoting the shiny dashboard metadata.
        """
        return self.create_resource('shiny-dashboards', json={'name': name}, **kwargs)

    def upload_shiny_dashboard(self, dashboard_id: str, file_path: str,
                               **kwargs) -> Response:
        """
        Upload and replace shiny dashboard source code.

        Typical usage example:

        with open('./path_to_dashboard/dashboard.zip', r) as f:
            instance.upload_shiny_dashboard(<dashboard_id>, f)

        Args:
            dashboard_id:
                A string denoting the shiny dashboard.
            file_path:
                A string denoting the ath to the zipped dashboard code.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            The requests response of the lana api call.
        """
        with open(file_path, "rb") as file:
            resp = self.post(f"/api/shiny-dashboards/{dashboard_id}/source",
                             files={'file': file}, **kwargs)
        return resp

    def delete_shiny_dashboard(self, shiny_dashboard_id: str, **kwargs) \
            -> Response:
        """
        Delete a shiny dashboard by its id.
        
        Args:
            shiny_dashboard_id: 
                A string denoting the shiny dashboard.
            **kwargs: 
                Keyword arguments passed to requests functions.

        Returns:
            The requests response of the lana api call.
        """
        return self.delete_resource('shiny-dashboards', shiny_dashboard_id,
                                    **kwargs)

    def delete_shiny_dashboards(self, contains: str = None,
                                ids: List[str] = None, **kwargs) -> \
            List[Response]:
        """
        Delete shiny dashboards by id list of name matching

        Args:
            contains: 
                A string denoting a regular expression. 
                It is ignored when ids are passed.
            ids: 
                A list of strings denoting shiny dashboard ids.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            A list of request responses of the calls to the lana api.
        """
        return self.delete_resources('shiny-dashboards', contains, ids,
                                     **kwargs)

    # TODO consider sharing by names
    def share_shiny_dashboard(self, shiny_dashboard_id: str, organization_ids: List[str],
                              **kwargs) -> Response:
        """
        Share a shiny dashboard with organizations by ids.

        Args:
            shiny_dashboard_id:
                A string denoting the id of the shiny dashboard.
            organization_ids:
                A list of strings denoting ids of organizations to share with.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            The requests response of the lana api call.
        """
        body = {
            "shareWithOrganizations": organization_ids
        }
        return self.patch(f"/api/shiny-dashboards/{shiny_dashboard_id}/sharing",
                          json=body, **kwargs)

    @warn_for_interface_deprecation
    def unshare_shiny_dashboard(self, shiny_dashboard_id: str, organization_ids: List[str],
                                **kwargs) -> Response:
        """
        Unshare a shiny dashboard with organizations by ids.

        Args:
            shiny_dashboard_id:
                A string denoting the id of the shiny dashboard.
            organization_ids:
                A list of strings denoting ids of organizations to unshare the
                shiny dashboard with.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            The requests response of the lana api call.
        """
        body = {
            "unshareWithOrganizations": organization_ids
        }
        return self.patch(f"/api/shiny-dashboards/{shiny_dashboard_id}/sharing",
                          json=body, **kwargs)

    @warn_for_interface_deprecation
    def connect_shiny_dashboard(self, log_id, shiny_dashboard_id, **kwargs) \
            -> Response:
        """
        Connect a shiny dashboard with a log by their ids.
        
        Args:
            log_id: 
                A string denoting the id of the log in LANA.
            shiny_dashboard_id:
                A string denoting the id of the shiny dashboard.
            **kwargs: 
                Keyword arguments passed to requests functions.

        Returns:
            The requests response of the lana api call.
        """
        dct = {'log_id': log_id, 'shiny_dashboard_id': shiny_dashboard_id}
        return self.connect_resources(dct, **kwargs)

    # legacy
    # ------

    def updateDashboardUrl(self, in_file: str, out_file: str, url: str) -> None:
        with open(in_file, 'r+') as f:
            db_string = f.read()
            s = re.sub('lanaUrl <- \".*\"', 'lanaUrl <- ' + '"' + url + '"', db_string)

        with open(out_file, 'w') as out_file:
            out_file.write(s)

    def zipDashboard(self, zip_path: str, dashboard_rmd: str) -> None:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as f:
            f.write(dashboard_rmd, os.path.basename(dashboard_rmd))

    def createShinyDashboard(self, dashboardName: str) -> str:
        body = {"name": dashboardName}
        r = self.post("/api/shiny-dashboards", json=body)
        r_json = json.loads(r.text)
        dashboardId = r_json['id']
        return dashboardId

    def uploadShinyDashboard(self, dashboard: str, dashboardId: str) -> Response:
        file = {'file': open(dashboard, 'rb')}
        return self.post(f"/api/shiny-dashboards/{dashboardId}/source", files=file)

    # Id arguments need to be lists
    def shareDashboard(self, dashboardId: str, userIds: str, projectIds: str, organizationIds: str) -> Response:
        body = {"sharedInformation": {
            "userIds": userIds,
            "projectIds": projectIds,
            "organizationIds": organizationIds
        }}
        return self.patch(f"/api/shiny-dashboards/{dashboardId}", data=body)
