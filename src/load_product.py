
import logging
from pathlib import Path

from api_client import clean_products
from db_connection import get_connection


# Create the logs folder automatically
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "pipeline.log"


# Configure logging to save messages in a file and terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def load_products():
    connection = None
    cursor = None

    try:
        logger.info("Pipeline started.")
        logger.info(
            "Products received for processing: %s",
            len(clean_products),
        )

        connection = get_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO products (
                id,
                title,
                category,
                price,
                "discountPercentage",
                rating,
                stock,
                brand,
                "availabilityStatus"
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                category = EXCLUDED.category,
                price = EXCLUDED.price,
                "discountPercentage" = EXCLUDED."discountPercentage",
                rating = EXCLUDED.rating,
                stock = EXCLUDED.stock,
                brand = EXCLUDED.brand,
                "availabilityStatus" = EXCLUDED."availabilityStatus";
        """

        for product in clean_products:
            cursor.execute(
                query,
                (
                    product["id"],
                    product["title"],
                    product["category"],
                    product["price"],
                    product["discountPercentage"],
                    product["rating"],
                    product["stock"],
                    product["brand"],
                    product["availabilityStatus"],
                ),
            )

        connection.commit()

        cursor.execute("SELECT COUNT(*) FROM products;")
        total_products = cursor.fetchone()[0]

        logger.info("Database load completed successfully.")
        logger.info("Products processed: %s", len(clean_products))
        logger.info("Products currently in database: %s", total_products)

    except Exception:
        if connection is not None:
            connection.rollback()

        logger.exception("Pipeline failed.")
        raise

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

        logger.info("Pipeline finished.")


if __name__ == "__main__":
    load_products()
