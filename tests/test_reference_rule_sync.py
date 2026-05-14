import unittest

from reference_rule_sync import decide_image_reading_plan


class ImageReadingPlanTests(unittest.TestCase):
    def test_small_document_uses_full_render(self):
        plan = decide_image_reading_plan(
            {"enabled": True, "max_full_pages": 120, "max_chunked_pages": 500},
            page_count=80,
            key_pages=[{"page": 10}],
        )

        self.assertEqual(plan["mode"], "full")
        self.assertEqual(plan["ranges"], [(1, 80)])

    def test_medium_document_uses_chunked_full_render(self):
        plan = decide_image_reading_plan(
            {"enabled": True, "max_full_pages": 120, "max_chunked_pages": 500, "chunk_size": 100},
            page_count=250,
            key_pages=[],
        )

        self.assertEqual(plan["mode"], "chunked_full")
        self.assertEqual(plan["ranges"], [(1, 100), (101, 200), (201, 250)])

    def test_large_document_uses_selective_render(self):
        plan = decide_image_reading_plan(
            {"enabled": True, "max_full_pages": 120, "max_chunked_pages": 500, "front_matter_pages": 8},
            page_count=900,
            key_pages=[{"page": 30}, {"page": 900}, {"page": 901}, {"page": "bad"}],
        )

        self.assertEqual(plan["mode"], "selective")
        self.assertEqual(plan["ranges"], [(1, 8), (30, 30), (900, 900)])

    def test_unknown_page_count_defers_full_render(self):
        plan = decide_image_reading_plan(
            {"enabled": True, "unknown_page_count_strategy": "defer_full"},
            page_count=None,
            key_pages=[{"page": 4}],
        )

        self.assertEqual(plan["mode"], "deferred")
        self.assertEqual(plan["ranges"], [(4, 4)])


if __name__ == "__main__":
    unittest.main()

