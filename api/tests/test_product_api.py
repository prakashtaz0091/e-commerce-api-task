from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from api.models import Category, Product


class ProductAPITests(TestCase):
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

        # Create product linked to child category
        self.product = Product.objects.create(
            name="Advanced Accessory 130",
            code="PRD-94845",
            description="Professional-grade advanced accessory 130 with advanced features",
            category=self.child_category,
            base_price=Decimal("527.96"),
            discount_percent=0,
            stock_quantity=165,
        )

    def test_list_products_includes_nested_category(self):
        """API should return products with category including parent_category"""
        response = self.client.get("/api/products/?page=1", format="json")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("results", data)
        self.assertGreater(len(data["results"]), 0)

        product_data = data["results"][0]

        # Check product fields
        self.assertEqual(product_data["name"], self.product.name)
        self.assertEqual(product_data["code"], self.product.code)

        # Check category nested info
        category_data = product_data["category"]
        self.assertEqual(category_data["id"], str(self.child_category.id))
        self.assertEqual(category_data["name"], self.child_category.name)
        self.assertEqual(category_data["parent_category"], str(self.parent_category.id))
