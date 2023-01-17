import json
import sys
import unittest

from model.dmdata.socket import DmdataSocketData

# To mitigate not being found
sys.path.insert(0, "../")

from internal.dmdata import DMDataFetcher

dmdata = DMDataFetcher(testing=True)


class TestJMAParse(unittest.TestCase):
    def test_xml(self):
        with open("./assets/dmdata/test_eew1.json", "r", encoding="utf-8") as f:
            raw = json.loads(f.read())
            f.close()
        parsed = DmdataSocketData.parse_obj(raw)
        dmdata.parse_data_message(parsed)
