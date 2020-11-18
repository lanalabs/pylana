import json
import unittest

from pylana import create_api


class TestModelsAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        with open('./tests/config.json') as f:
            cls.credentials = json.load(f)
        cls.api = create_api(verify=True, **cls.credentials)

    def test_list(self):
        self.assertIsInstance(self.api.list_user_models(), list)

    def test_describe(self):
        model = self.api.describe_model('Incident.*')
        self.assertIsInstance(model.get('id'), str)

        with self.assertRaises(Exception):
            _ = self.api.describe_model('never-ever-matches-a-model')

    def test_get_model_id(self):
        model_id = self.api.get_model_id('^Incident-Example$')
        self.assertIsInstance(model_id, str)

        with self.assertRaises(Exception):
            self.api.get_model_id('not-an-existing-model')

    def test_get_model_ids(self):
        model_ids = self.api.get_model_ids()
        self.assertGreater(len(model_ids), 0)

        model_ids = self.api.get_model_ids(contains='not-an-existing-name-pattern')
        self.assertEqual(len(model_ids), 0)

    def test_get_model_xml(self):
        self.assertIsInstance(self.api.get_model_xml("Incident.*"), str)

    def test_upload_model_from_file(self):
        r = self.api.upload_model(
            "pylana-File-Example", "./tests/data/m2c_target.bpmn"
        )
        # inconsistent api response, resource creation should be 201
        msg = "failed to upload model from file"
        self.assertEqual(r.status_code, 200, msg)

    def test_upload_model_from_string(self):
        with open("./tests/data/m2c_target.bpmn") as f:
            r = self.api.upload_model(
                "pylana-String-Example", model=f.read()
            )
        # inconsistent api response, resource creation should be 201
        msg = "failed to upload model from string"
        self.assertEqual(r.status_code, 200, msg)

    def test_upload_model_from_binary_string(self):

        with open("./tests/data/m2c_target.bpmn", "rb") as f:
            r = self.api.upload_model(
                "pylana-String-Binary-Example", model=f.read()
            )
        # inconsistent api response, resource creation should be 201
        msg = "failed to upload model from string"
        self.assertEqual(r.status_code, 200, msg)

    def test_connect_and_disconnect_model(self):
        log_id = self.api.get_log_id("^Incident_Management.csv$")
        model_id = self.api.get_model_id("^Incident-Example$")

        r_connect = self.api.connect_model(log_id, model_id)
        msg = "failed to connect model to log"
        self.assertEqual(r_connect.status_code, 200, msg)
        self.assertEqual(
            self.api.get_model_id_connected_to_log(log_id=log_id),
            model_id, msg)

        r_disconnect = self.api.disconnect_model(log_id, model_id)

        msg = "failed to disconnect model from log"
        self.assertEqual(r_disconnect.status_code, 200)
        self.assertIsNone(
            self.api.get_model_id_connected_to_log(log_id=log_id), msg)

    def test_share_and_unshare_model(self):
        info = self.api.get_model_sharing_information("^Incident-Example$")
        msg = "failed to get model sharing information"
        self.assertCountEqual(
            info.keys(), ['lastUpdated', 'organizationIds', 'userIds'], msg
        )

        r_share = self.api.share_model(contains="^Incident-Example$")
        msg = "failed to share model"
        self.assertEqual(r_share.status_code, 200, msg)
        self.assertEqual(r_share.json()
                         .get("sharing", dict())
                         .get("numSuccesses"), 1, msg)

        r_unshare = self.api.unshare_model(contains="^Incident-Example$")
        msg = "failed to share mdoel"
        self.assertEqual(r_unshare.status_code, 200, msg)
        self.assertEqual(r_unshare.json()
                         .get("unsharing", dict())
                         .get("numSuccesses"), 1, msg)

    # the z character ensures that this is the last test to be executed
    def test_z_delete_models(self):
        resps = self.api.delete_models(contains='^pylana.*')
        for status_code in [r.status_code for r in resps]:
            self.assertEqual(status_code, 200)
