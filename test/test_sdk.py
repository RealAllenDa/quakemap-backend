"""
 HomeNetwork Python SDK unittest suite
 Licensed under GPL.
 2022-2023 Allen Da.
 Current Version - 1.2.1
"""
import json
import random
import sys
import unittest
from io import StringIO
from unittest.mock import patch

# To mitigate sdk not being found
sys.path.insert(0, "../")

from pydantic import BaseModel

from sdk import *
# noinspection PyProtectedMember
from sdk import VerifyFailedException

JSONP_TEST_STRING = f"callback_{random.getrandbits(16)}" + '({"test": "works"})'


class ComplexType(BaseModel):
    test: str


class IncorrectTestJsonModel(BaseModel):
    test_incorrect: str


class _TestYamlModel2(BaseModel):
    test2: str


class ForTestYamlModel(BaseModel):
    test: _TestYamlModel2


class IncorrectTestYamlModel(BaseModel):
    incorrect: str


class TestSDKAssert(unittest.TestCase):
    def test_todo(self):
        """This test includes:
        - normal -> VerifyFailedException
        """
        with self.assertRaises(VerifyFailedException) as exc:
            todo()
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: todo!.")

    def test_verify_none(self):
        """This test includes:
        - empty list -> VerifyFailedException
        - literal None -> VerifyFailedException
        - str -> None
        - list -> None
        - dict -> None
        """
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
        """This test includes:
        - normal -> VerifyFailedException
        """
        with self.assertRaises(VerifyFailedException) as exc:
            verify_not_used("test")
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Use before declaration: test.")

    def test_verify_type(self):
        """This test includes:
        - int/int -> None
        - str/str -> None
        - list/list -> None
        - tuple/tuple -> None
        - dict/dict -> None
        - ComplexType/ComplexType -> None
        - dict/ComplexType -> VerifyFailedException
        """
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
        """This test includes:
        - writing an existing file -> None
        - reading/verifying an existing file -> None
        - opening an nonexistent file -> (Returns None) None
        """
        handle = open_file(relpath("./assets/test.txt"), "w")
        self.assertIsNotNone(handle)
        handle.write("TEST")
        handle.close()

        handle2 = open_file(relpath("./assets/test.txt"))
        self.assertIsNotNone(handle2)
        self.assertEqual(handle2.read(), "TEST")
        handle2.close()

        handle_fail = open_file(relpath("./assets/random_should_not_exist.txt"), "r")
        self.assertIsNone(handle_fail)

    def test_read_json(self):
        """This test includes:
        - reading an nonexistent json -> VerifyFailedException
        - reading an incorrect json -> (Returns None) None
        - reading an existing json -> None
        """
        with self.assertRaises(VerifyFailedException) as exc:
            _ = read_json(relpath("./assets/random_should_not_exist.txt"), "r")
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Variable is none or false.")

        handle_fail_json = read_json(relpath("./assets/test.txt"))
        self.assertIsNone(handle_fail_json)

        handle = read_json(relpath("./assets/test.json"))
        self.assertEqual(handle, {"test": "It works!"})

    def test_read_csv(self):
        """This test includes:
        - reading an nonexistent csv -> VerifyFailedException
        - reading an incorrect csv -> (Returns garbage data) None
        - reading an existing csv -> None
        """
        fields = ("test", "test2")
        with self.assertRaises(VerifyFailedException) as exc:
            _ = read_csv(relpath("./assets/random_should_not_exist.txt"), fields)
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Variable is none or false.")

        # NOTE: When parsing malformed files, it should NEVER error out.
        # It would only return garbage data.
        handle_fail_csv = read_csv(relpath("./assets/test.txt"), fields)
        self.assertEqual(handle_fail_csv, [{'test': 'TEST', 'test2': None}])

        handle = read_csv(relpath("./assets/test.csv"), fields)
        self.assertEqual(handle, [{'test': 'test', 'test2': 'test2'}, {'test': 'it', 'test2': 'works'}])


class TestSDKMisc(unittest.TestCase):
    def test_relpath(self):
        """This test includes:
        - opening, reading an existing file -> None
        """
        path_test = relpath("./assets/test.txt")

        path_test_handle = open_file(path_test, "r+")
        self.assertIsNotNone(path_test_handle)
        path_test_content = path_test_handle.read()
        path_test_handle.close()
        self.assertIsNotNone(path_test_content)

    def test_func_timer(self):
        """This test includes:
        - timing a function without log_func -> None
        - timing a function with log_func -> None
        """

        @func_timer
        def dummy():
            self.assertTrue(True)

        @func_timer(log_func=print)
        def dummy2():
            self.assertTrue(True)

        self.assertTrue(hasattr(dummy, "__wrapped__"))
        dummy()

        self.assertTrue(hasattr(dummy2, "__wrapped__"))
        with patch("sys.stdout", new=StringIO()) as fake:
            dummy2()
            self.assertIn("dummy2 => ", fake.getvalue().strip())

    def test_parse_jsonp(self):
        """This test includes:
        - parsing a jsonp string -> None
        - parsing an invalid jsonp string -> VerifyFailedException
        """
        parsed_json_str = parse_jsonp(JSONP_TEST_STRING)
        print(parsed_json_str)
        parsed_json = json.loads(parsed_json_str)
        self.assertEqual(parsed_json, {"test": "works"})

        with self.assertRaises(VerifyFailedException) as exc:
            _ = parse_jsonp("INVALID_JSONP")
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Use before Invalid JSONP: JSONP.")

    def test_generate_list(self):
        """This test includes:
        - boolean -> []
        - str -> str
        - dict -> list[dict]
        - tuple -> list[tuple]
        - list -> list
        """
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
        """This test includes:
        - parsing a yaml -> None
        - parsing an nonexistent yaml -> VerifyFailedException
        - parsing an incorrect yaml -> VerifyFailedException
        - parsing a yaml with incorrect model -> VerifyFailedException
        """
        content = yaml_to_model(relpath("./assets/test.yaml"), ForTestYamlModel)
        self.assertEqual(content, ForTestYamlModel(test=_TestYamlModel2(test2='123')))

        with self.assertRaises(VerifyFailedException) as exc:
            _ = yaml_to_model(relpath("./assets/do_not_exist.yaml"), ForTestYamlModel)
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Variable is none or false.")

        with self.assertRaises(VerifyFailedException) as exc:
            _ = yaml_to_model(relpath("./assets/test.json"), ForTestYamlModel)
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Variable is none or false.")

        with self.assertRaises(VerifyFailedException) as exc:
            _ = yaml_to_model(relpath("./assets/test.yaml"), IncorrectTestYamlModel)
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Variable is none or false.")

    def test_json_to_model(self):
        """This test includes:
        - parsing a json -> None
        - parsing an nonexistent json -> VerifyFailedException
        - parsing an incorrect json -> VerifyFailedException
        - parsing a json with incorrect model -> (Returns None) None
        """
        content = json_to_model(relpath("./assets/test.json"), ComplexType)
        self.assertEqual(content, ComplexType(test="It works!"))

        with self.assertRaises(VerifyFailedException) as exc:
            _ = json_to_model(relpath("./assets/do_not_exist.json"), ComplexType)
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Variable is none or false.")

        with self.assertRaises(VerifyFailedException) as exc:
            _ = json_to_model(relpath("./assets/test.yaml"), ComplexType)
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Variable is none or false.")

        content = json_to_model(relpath("./assets/test.json"), IncorrectTestJsonModel)
        self.assertIsNone(content)

    def test_obj_to_model(self):
        """This test includes:
        - parsing an object -> None
        - parsing an incorrect object -> (Returns None) None
        - parsing an object with incorrect model -> (Returns None) None
        """
        test = {
            "test": "It works!"
        }
        content = obj_to_model(test, ComplexType)
        self.assertEqual(content, ComplexType(test="It works!"))

        test_incorrect = {
            "test_incorrect": "It didn't work."
        }
        content = obj_to_model(test_incorrect, ComplexType)
        self.assertIsNone(content)

        content = obj_to_model(test, IncorrectTestJsonModel)
        self.assertIsNone(content)


if __name__ == '__main__':
    unittest.main()
