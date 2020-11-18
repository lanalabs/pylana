"""
resource management api requests
"""

import re
from typing import List, Union

from requests import Response

from pylana.api import API
from pylana.decorators import expect_json


def extract_resource_id(resource):
    """
    Extract resource id.

    We currently have two ways of naming resource ids, "id" and "pageId". We
    only have "pageId" in case "id" is missing.
    """
    return resource.get('id') or resource.get('pageId')


def filter_resource_ids(resources: List[dict], contains: str) -> List[str]:
    """
    Filter a list of resources by matching a regex against their names.
    """
    return [
        extract_resource_id(resource)
        for resource in resources
        if re.compile(contains).search(
            resource.get('name') or resource.get('title')
        )
    ]


class ResourceAPI(API):

    @expect_json
    def list_resources(self, kind: str, **kwargs) -> list:
        """
        Lists all resources of a kind.

        Args:
            kind:
                A string denoting the resource type.
            **kwargs:
                Keyword arguments passed to requests functions.
        """
        return self.get(f'/api/{kind}', **kwargs)

    def get_resource_ids(self, kind: str, contains: str, **kwargs) -> List[str]:
        """
        Get ids of resource with names are matched by regular expression

        Args:
            kind:
                A string denoting the resource type.
            contains:
                A string denoting a regular expression matched against the resource
                names.
            **kwargs:
                Keyword arguments passed to requests functions.

        Returns:
            a list of strings representing resource ids
        """
        return filter_resource_ids(
            self.list_resources(kind, **kwargs),
            contains)

    def get_resource_id(self, kind: str, contains: str, **kwargs) -> str:
        """
        Get id of a resource by its name

        name needs to be unique or an exception is raised
        """
        resource_ids = self.get_resource_ids(kind, contains, **kwargs)

        try:
            [resource_id] = resource_ids
        except ValueError as e:
            raise Exception(
                f'Found {len(resource_ids)} resources with the pattern {contains}')

        return resource_id

    @expect_json
    def describe_resource(self, kind: str, contains: str = None, resource_id: str = None, **kwargs) -> dict:
        """
        get description of resource

        Args:
            kind: resource type name
            resource_id: The id of the log, takes precedence over contains
            contains: a regex matching the resource's name, matching several names raises an exception

        Returns:

        """
        resource_id = resource_id or self.get_resource_id(kind, contains, **kwargs)
        return self.get(f'/api/{kind}/{resource_id}')

    @expect_json
    def create_resource(self, kind: str, json: Union[list, dict, str], **kwargs):
        return self.post(f'/api/{kind}', json=json, **kwargs)

    def delete_resource(self, kind, id_: str, **kwargs) -> Response:
        """
        delete a log by its id
        """
        return self.delete(f'/api/{kind}/{id_}', **kwargs)

    def delete_resources(self, kind: str, contains: str = None, ids: List[str] = None, **kwargs) -> List[Response]:
        """
        deletes one or multiple logs matching the passed regular expression
        """
        ids = ids or self.get_resource_ids(kind, contains, **kwargs)
        return [self.delete_resource(kind, id_) for id_ in ids]

    def connect_resources(self, dct, **kwargs) -> Response:
        return self.post('/api/v2/resource-connections', json=dct, **kwargs)

    def connect_working_schedule(self, log_id, working_schedule_id, **kwargs):
        dct = {'log_id': log_id, 'working_schedule_id': working_schedule_id}
        return self.connect_resources(dct, **kwargs)

    def share_resource(self, kind: str, resource_id: str, **kwargs):
        return self.put(
            f"/api/v2/{kind}/{resource_id}/sharing",
            json={"shareWithOrganizations": [self.user.organization_id],
                  "unshareWithOrganizations": []},
            **kwargs
            )

    def unshare_resource(self, kind: str, resource_id: str, **kwargs):
        return self.put(
            f"/api/v2/{kind}/{resource_id}/sharing",
            json={"shareWithOrganizations": [],
                  "unshareWithOrganizations": [self.user.organization_id]},
            **kwargs
            )
