from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from api.models import Category


class CategoryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create category hierarchy
        self.grandparent_category = Category.objects.create(name="Sports")
        self.parent_category = Category.objects.create(
            name="Cycling", parent_category=self.grandparent_category
        )
        self.child_category = Category.objects.create(
            name="Mountain Bikes", parent_category=self.parent_category
        )

    def test_list_category_includes_nested_category(self):
        """API should return categories with sub categories nested"""
        response = self.client.get("/api/categories/?page=1", format="json")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("results", data)
        self.assertGreater(len(data["results"]), 0)

        category_data = data["results"][0]

        # Check category fields
        self.assertEqual(category_data["name"], self.grandparent_category.name)

        # Check category nested info
        subcategories = category_data["sub_categories"]
        self.assertGreater(len(subcategories), 0)

        subcategory = subcategories[0]

        self.assertEqual(subcategory["id"], str(self.parent_category.id))
        self.assertEqual(subcategory["name"], self.parent_category.name)

        sub_subcategories = subcategory["sub_categories"]
        self.assertGreater(len(sub_subcategories), 0)

        sub_subcategory = sub_subcategories[0]

        self.assertEqual(sub_subcategory["id"], str(self.child_category.id))
        self.assertEqual(sub_subcategory["name"], self.child_category.name)
