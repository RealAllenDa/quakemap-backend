import unittest

from pydantic import BaseModel

from sdk import *
# noinspection PyProtectedMember
from sdk import VerifyFailedException


class ComplexType(BaseModel):
    test: str


class _TestYamlModel2(BaseModel):
    test2: str


class TestYamlModel(BaseModel):
    test: _TestYamlModel2


class TestSDK(unittest.TestCase):
    def test_todo(self):
        with self.assertRaises(VerifyFailedException) as exc:
            todo()
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Use before todo!: todo!.")

    def test_verify_none(self):
        with self.assertRaises(VerifyFailedException) as exc:
            verify_none([])
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Variable is none.")
        with self.assertRaises(VerifyFailedException) as exc:
            verify_none(None)
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: Variable is none.")
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
        self.assertEqual(exc.exception.__str__(), "VERIFY failed: "
                                                  "Type mismatch: {'test': '123'} is <class 'dict'>, "
                                                  "which should be <class 'test_sdk.ComplexType'>.")

    def test_open_file(self):
        # TODO: Fail test
        handle = open_file("./assets/test.txt", "w")
        self.assertIsNotNone(handle)
        handle.write("TEST")
        handle.close()
        handle2 = open_file("./assets/test.txt")
        self.assertIsNotNone(handle2)
        self.assertEqual(handle2.read(), "TEST")
        handle2.close()

    def test_yaml_to_model(self):
        content = yaml_to_model("./assets/test.yaml", TestYamlModel)
        self.assertEqual(content, TestYamlModel(test=_TestYamlModel2(test2='123')))


if __name__ == '__main__':
    unittest.main()
