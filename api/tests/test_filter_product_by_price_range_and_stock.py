from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from api.models import Product, Category


class ProductFilterAPITest(APITestCase):

    def setUp(self):
        self.category = Category.objects.create(name="Electronics")

        self.product_1 = Product.objects.create(
            name="Cheap In Stock",
            code="PRD-001",
            category=self.category,
            base_price=100,
            discount_percent=0,  # final_price = 100
            stock_quantity=10,
            active=Product.ACTIVE,
        )

        self.product_2 = Product.objects.create(
            name="Mid Price In Stock",
            code="PRD-002",
            category=self.category,
            base_price=500,
            discount_percent=10,  # final_price = 450
            stock_quantity=5,
            active=Product.ACTIVE,
        )

        self.product_3 = Product.objects.create(
            name="Expensive Out of Stock",
            code="PRD-003",
            category=self.category,
            base_price=1000,
            discount_percent=20,  # final_price = 800
            stock_quantity=0,
            active=Product.ACTIVE,
        )

        self.url = reverse("product-list")

    def test_filter_products_by_price_range(self):
        response = self.client.get(
            self.url,
            {
                "min_price": 200,
                "max_price": 600,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ids = [item["id"] for item in response.data["results"]]

        self.assertIn(str(self.product_2.id), ids)
        self.assertNotIn(str(self.product_1.id), ids)
        self.assertNotIn(str(self.product_3.id), ids)

    def test_filter_products_in_stock(self):
        response = self.client.get(
            self.url,
            {
                "in_stock": True,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ids = [item["id"] for item in response.data["results"]]

        self.assertIn(str(self.product_1.id), ids)
        self.assertIn(str(self.product_2.id), ids)
        self.assertNotIn(str(self.product_3.id), ids)

    def test_filter_products_by_price_and_stock(self):
        response = self.client.get(
            self.url,
            {
                "min_price": 200,
                "max_price": 600,
                "in_stock": True,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], str(self.product_2.id))
