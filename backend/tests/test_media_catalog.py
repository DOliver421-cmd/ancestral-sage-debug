import unittest

import routers.media as media


class _Cursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    async def to_list(self, *args, **kwargs):
        return self.docs


class _Products:
    def __init__(self, docs):
        self.docs = docs

    def find(self, *args, **kwargs):
        return _Cursor(self.docs)


class _Db:
    def __init__(self, docs):
        self.media_products = _Products(docs)


class MediaCatalogTests(unittest.IsolatedAsyncioTestCase):
    async def test_catalog_is_browsable_without_a_token(self):
        previous_db = media.db
        media.db = _Db([
            {
                "_id": "internal-id",
                "id": "mp_1",
                "title": "A First-Party Guide",
                "owner_name": "M.O.R.E. Help Center",
                "type": "pdf",
                "published": True,
                "file_url": "/api/media/file/file-1",
            }
        ])
        try:
            products = await media.list_media_products(None)
        finally:
            media.db = previous_db

        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["id"], "mp_1")
        self.assertNotIn("_id", products[0])
        self.assertEqual(products[0]["seller_display_name"], "M.O.R.E. Help Center")
        self.assertEqual(products[0]["product_type"], "pdf")

    async def test_optional_auth_does_not_require_a_token(self):
        self.assertIsNone(await media._optional_current_user(None))


if __name__ == "__main__":
    unittest.main()
