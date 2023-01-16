"""
 HomeNetwork Python SDK unittest suite
 Licensed under GPL.
 2022-2023 Allen Da.
 Current Version - 1.1
"""
import json
import random
import sys
import unittest

# To mitigate sdk not being found
sys.path.insert(0, "../")

from pydantic import BaseModel

from sdk import *
# noinspection PyProtectedMember
from sdk import VerifyFailedException

JSONP_TEST_STRING = f"callback_{random.randbytes(16)}" + '({"test": "works"})'


class ComplexType(BaseModel):
    test: str


class _TestYamlModel2(BaseModel):
    test2: str


class TestYamlModel(BaseModel):
    test: _TestYamlModel2


class TestSDKAssert(unittest.TestCase):
    def test_todo(self):
        with self.assertRaises(VerifyFailedException) as exc:
            todo()
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: todo!.")

    def test_verify_none(self):
        with self.assertRaises(VerifyFailedException) as exc:
            verify_none([])
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Variable is none or false.")
        with self.assertRaises(VerifyFailedException) as exc:
            verify_none(None)
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Variable is none or false.")
        verify_none("test")
        verify_none(["1", "2"])
        verify_none({"content": "test"})

    def test_verify_not_used(self):
        with self.assertRaises(VerifyFailedException) as exc:
            verify_not_used("test")
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Use before declaration: test.")

    def test_verify_type(self):
        temp = ComplexType(test="123")
        verify_type(123, int)
        verify_type("123", str)
        verify_type(["1", "2"], list)
        verify_type(("1", "2"), tuple)
        verify_type({"1": "2"}, dict)
        verify_type(temp, ComplexType)
        with self.assertRaises(VerifyFailedException) as exc:
            verify_type({"test": "123"}, ComplexType)
        self.assertTrue("VERIFY failed: "
                        "Type mismatch: {'test': '123'} is <class 'dict'>, "
                        "which should be" in exc.exception.__str__())


class TestSDKFile(unittest.TestCase):
    def test_open_file(self):
        handle = open_file("./assets/test.txt", "w")
        self.assertIsNotNone(handle)
        handle.write("TEST")
        handle.close()

        handle2 = open_file("./assets/test.txt")
        self.assertIsNotNone(handle2)
        self.assertEqual(handle2.read(), "TEST")
        handle2.close()

        handle_fail = open_file("./assets/random_should_not_exist.txt", "r")
        self.assertIsNone(handle_fail)

    def test_read_json(self):
        with self.assertRaises(VerifyFailedException) as exc:
            _ = read_json("./assets/random_should_not_exist.txt", "r")
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Variable is none or false.")

        handle_fail_json = read_json("./assets/test.txt")
        self.assertIsNone(handle_fail_json)

        handle = read_json("./assets/test.json")
        self.assertEqual(handle, {"test": "It works!"})

    def test_read_csv(self):
        fields = ("test", "test2")
        with self.assertRaises(VerifyFailedException) as exc:
            _ = read_csv("./assets/random_should_not_exist.txt", fields)
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Variable is none or false.")

        # NOTE: When parsing malformed files, it should NEVER error out.
        # It would only return garbage data.
        handle_fail_csv = read_csv("./assets/test.txt", fields)
        self.assertEqual(handle_fail_csv, [{'test': 'TEST', 'test2': None}])

        handle = read_csv("./assets/test.csv", fields)
        self.assertEqual(handle, [{'test': 'test', 'test2': 'test2'}, {'test': 'it', 'test2': 'works'}])


class TestSDKMisc(unittest.TestCase):
    def test_relpath(self):
        path_test = relpath("./assets/test.txt")

        test_handle = open_file("./assets/test.txt", "r+")
        self.assertIsNotNone(test_handle)
        test_content = test_handle.read()
        test_handle.close()

        path_test_handle = open_file(path_test, "r+")
        self.assertIsNotNone(path_test_handle)
        path_test_content = path_test_handle.read()
        path_test_handle.close()

        self.assertEqual(test_content, path_test_content)

    def test_func_timer(self):
        @func_timer
        def dummy():
            self.assertTrue(True)

        @func_timer(log_func=print)
        def dummy2():
            self.assertTrue(True)

        self.assertTrue(hasattr(dummy, "__wrapped__"))
        dummy()

        self.assertTrue(hasattr(dummy2, "__wrapped__"))
        dummy2()

    def test_parse_jsonp(self):
        parsed_json_str = parse_jsonp(JSONP_TEST_STRING)
        print(parsed_json_str)
        parsed_json = json.loads(parsed_json_str)
        self.assertEqual(parsed_json, {"test": "works"})

        with self.assertRaises(VerifyFailedException) as exc:
            _ = parse_jsonp("INVALID_JSONP")
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Use before Invalid JSONP: JSONP.")

    def test_generate_list(self):
        a = False
        self.assertEqual(generate_list(a), [])
        a = "1"
        self.assertEqual(generate_list(a), ["1"])
        a = {"1": "2"}
        self.assertEqual(generate_list(a), [{"1": "2"}])
        # NOTE: Intentional behavior parsing tuple.
        a = (1, 2,)
        self.assertEqual(generate_list(a), [(1, 2)])
        a = [1, 2]
        self.assertEqual(generate_list(a), [1, 2])


class TestSDKConversion(unittest.TestCase):
    def test_yaml_to_model(self):
        content = yaml_to_model("./assets/test.yaml", TestYamlModel)
        self.assertEqual(content, TestYamlModel(test=_TestYamlModel2(test2='123')))


if __name__ == '__main__':
    unittest.main()
