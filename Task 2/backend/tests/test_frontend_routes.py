import unittest

from fastapi.testclient import TestClient

from app.main import app


class FrontendRoutesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_serves_dashboard_root(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("OptiVue", response.text)

    def test_serves_static_js_asset(self) -> None:
        response = self.client.get("/js/api.js")
        self.assertEqual(response.status_code, 200)
        self.assertIn("BackendAPI", response.text)


if __name__ == "__main__":
    unittest.main()
