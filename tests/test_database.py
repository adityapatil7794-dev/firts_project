
import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from db_connection import get_connection


class TestDatabaseIntegration(unittest.TestCase):

    def test_database_connection(self):
        connection = get_connection()

        try:
            self.assertIsNotNone(connection)

            cursor = connection.cursor()
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()

            self.assertEqual(result[0], 1)
            cursor.close()
        finally:
            connection.close()

    def test_products_table_contains_194_products(self):
        connection = get_connection()

        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM products;")
            result = cursor.fetchone()

            self.assertEqual(result[0], 194)
            cursor.close()
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
