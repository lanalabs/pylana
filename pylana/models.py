import io
from typing import List, Union

import requests

from pylana.decorators import expect_json, handle_response
from pylana.resources import ResourceAPI, filter_resource_ids


def stream_model(path: str = None, model: Union[bytes, str] = None):
    if path:
        return open(path, "rb")
    elif model:
        return io.BytesIO(model if type(model) == bytes else model.encode())
    else:
        raise


class ModelsAPI(ResourceAPI):

    @expect_json
    def list_user_models(self, **kwargs) -> List[dict]:
        return self.get(f'/api/users/{self.user.user_id}/process-models',
                        **kwargs)

    def get_model_ids(self, contains: str = ".*", **kwargs) -> List[str]:
        return filter_resource_ids(
            self.list_user_models(**kwargs),
            contains
        )

    def get_model_id(self, contains: str, **kwargs) -> str:
        model_ids = self.get_model_ids(contains, **kwargs)

        try:
            [model_id] = model_ids
        except ValueError as e:
            raise Exception(
                f'Found {len(model_ids)} resources with the pattern {contains}')

        return model_id

    @expect_json
    def describe_model(self, contains: str = None, model_id: str = None,
                       **kwargs) -> dict:
        return self.get(f'/api/process-models/'
                        f'{model_id or self.get_model_id(contains, **kwargs)}')

    def get_model_xml(self, contains: str = None, model_id: str = None,
                      **kwargs) -> str:
        try:
            return \
                self.describe_model(contains, model_id, **kwargs)["modelXML"]
        except KeyError as e:
            raise Exception(
                f"No model found in response (key {e} missing in json)."
            )

    def upload_model(self, name: str, path: str = None, model: str = None,
                     **kwargs) -> requests.Response:
        with stream_model(path, model) as f:
            return self.post(
                "/api/process-models",
                data={"fileName": name},
                files={"file": f},
                **kwargs
            )

    def delete_model(self, model_id: str, **kwargs) -> requests.Response:
        return self.delete_resource("process-models", model_id, **kwargs)

    def delete_models(self, model_ids: str = None, contains: str = None,
                      **kwargs) -> List[requests.Response]:
        return [
            self.delete_model(model_id, **kwargs)
            for model_id
            in (model_ids or self.get_model_ids(contains, **kwargs))
        ]

    def connect_model(self, log_id, model_id, **kwargs):
        dct = {'log_id': log_id, 'model_id': model_id}
        return self.connect_resources(dct, **kwargs)

    def disconnect_model(self, log_id, model_id, **kwargs):
        return self.delete("/api/v2/resource-connections",
                           json={
                               "log_id": log_id,
                               "model_id": model_id
                           }, **kwargs)

    @expect_json
    def get_model_sharing_information(
            self, contains: str = None, model_id: str = None, **kwargs) -> \
            dict:
        return \
            self.get(
                f"/api/v2/model/{model_id or self.get_model_id(contains)}"
                f"/sharing", **kwargs
                     )

    @handle_response
    def share_model(self, contains: str = None, model_id: str = None,
                    **kwargs) -> requests.Response:
        return self.share_resource(
            "model", model_id or self.get_model_id(contains), **kwargs)

    @handle_response
    def unshare_model(self, contains: str = None, model_id: str = None,
                    **kwargs) -> requests.Response:
        return self.unshare_resource(
            "model", model_id or self.get_model_id(contains), **kwargs)
