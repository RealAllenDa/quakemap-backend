import base64
import datetime
import gzip
import json
import os
import sys
import unittest
from os.path import join, isfile

# To mitigate not being found
sys.path.insert(0, "../")
os.environ["ENV"] = "testing"

from model.dmdata.generic import DmdataMessageTypes
from sdk import relpath
from starlette.testclient import TestClient
from main import app
from model.dmdata.socket import DmdataSocketData, DmdataSocketDataHead
from internal.dmdata import DMDataFetcher

client = TestClient(app)
dmdata = DMDataFetcher()

mocked_dmdata_socket = DmdataSocketData(
    version="1.0",
    id="TESTING",
    classification="TESTING",
    passing=[],
    head=DmdataSocketDataHead(type=DmdataMessageTypes.eew_forecast, author="TEST", time=datetime.datetime.now(),
                              test=False, xml=True),
    format="xml",
    compression="gzip",
    encoding="base64",
    body=""
)


class TestJMAParse(unittest.TestCase):
    def test_message(self):
        json_files = [join(relpath("./assets/dmdata"), f)
                      for f in os.listdir(relpath("./assets/dmdata"))
                      if isfile(join(relpath("./assets/dmdata"), f))]
        for i in json_files:
            with open(i, "r", encoding="utf-8") as f:
                raw = json.loads(f.read())
                f.close()
            parsed = DmdataSocketData.parse_obj(raw)
            dmdata.parse_data_message(parsed)

    def test_xml_eew_forecasts(self):
        forecast_files = [join(relpath("./assets/eew_forecast"), f)
                          for f in os.listdir(relpath("./assets/eew_forecast"))
                          if isfile(join(relpath("./assets/eew_forecast"), f))]
        for i in forecast_files:
            print(f"Parsing {i}")
            with open(i, encoding="utf-8") as f:
                content = f.read()
                f.close()
            mocked_dmdata_socket.head.type = DmdataMessageTypes.eew_forecast
            message = base64.b64encode(gzip.compress(content.encode(encoding="utf-8"))).decode(encoding="utf-8")
            mocked_dmdata_socket.body = message
            dmdata.parse_data_message(mocked_dmdata_socket)

            from internal.modules_init import module_manager
            eew_info = module_manager.get_module_info("eew_info")
            self.assertIsNotNone(eew_info)
            print(eew_info)

    def test_xml_eew_warnings(self):
        warning_files = [join(relpath("./assets/eew_warning"), f)
                         for f in os.listdir(relpath("./assets/eew_warning"))
                         if isfile(join(relpath("./assets/eew_warning"), f))]
        for i in warning_files:
            print(f"Parsing {i}")
            with open(i, encoding="utf-8") as f:
                content = f.read()
                f.close()
            mocked_dmdata_socket.head.type = DmdataMessageTypes.eew_warning
            message = base64.b64encode(gzip.compress(content.encode(encoding="utf-8"))).decode(encoding="utf-8")
            mocked_dmdata_socket.body = message
            dmdata.parse_data_message(mocked_dmdata_socket)

            from internal.modules_init import module_manager
            eew_info = module_manager.get_module_info("eew_info")
            self.assertIsNotNone(eew_info)
            print(eew_info)

    def test_xml_tsunami_warnings(self):
        warning_files = [join(relpath("./assets/tsunami_expectation"), f)
                         for f in os.listdir(relpath("./assets/tsunami_expectation"))
                         if isfile(join(relpath("./assets/tsunami_expectation"), f))]
        for i in warning_files:
            print(f"Parsing {i}")
            with open(i, encoding="utf-8") as f:
                content = f.read()
                f.close()
            mocked_dmdata_socket.head.type = DmdataMessageTypes.tsunami_warning
            message = base64.b64encode(gzip.compress(content.encode(encoding="utf-8"))).decode(encoding="utf-8")
            mocked_dmdata_socket.body = message
            dmdata.parse_data_message(mocked_dmdata_socket)

            from internal.modules_init import module_manager
            tsunami_expectation_info = module_manager.classes.get("tsunami").tsunami_expectation_info
            self.assertIsNotNone(tsunami_expectation_info)
            print(tsunami_expectation_info)

    def test_xml_tsunami_watches(self):
        warning_files = [join(relpath("./assets/tsunami_watch"), f)
                         for f in os.listdir(relpath("./assets/tsunami_watch"))
                         if isfile(join(relpath("./assets/tsunami_watch"), f))]
        for i in warning_files:
            print(f"Parsing {i}")
            with open(i, encoding="utf-8") as f:
                content = f.read()
                f.close()
            mocked_dmdata_socket.head.type = DmdataMessageTypes.tsunami_info
            message = base64.b64encode(gzip.compress(content.encode(encoding="utf-8"))).decode(encoding="utf-8")
            mocked_dmdata_socket.body = message
            dmdata.parse_data_message(mocked_dmdata_socket)

            from internal.modules_init import module_manager
            tsunami_expectation_info = module_manager.classes.get("tsunami").tsunami_expectation_info
            tsunami_watch_info = module_manager.classes.get("tsunami").tsunami_obs_info
            self.assertIsNotNone(tsunami_watch_info)
            print(tsunami_watch_info)
            self.assertIsNotNone(tsunami_expectation_info)
            print(tsunami_expectation_info)


if __name__ == '__main__':
    unittest.main()
