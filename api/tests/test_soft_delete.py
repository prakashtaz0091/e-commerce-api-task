from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

from api.models import Product, Category, Order

User = get_user_model()


class SoftDeleteAPITest(APITestCase):

    def setUp(self):
        # Authenticated user
        self.user = User.objects.create_user(
            username="admin@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(self.user)

        # Product setup
        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Soft Delete Test Product",
            category=self.category,
            base_price=100,
            discount_percent=0,
            stock_quantity=10,
            active=Product.ACTIVE,
        )

        self.order = Order.objects.create(
            status=Order.StatusChoices.PENDING,
            total_price=500,
            product=self.product,
            unit_price=self.product.base_price,
            quantity=1,
        )

        # URLs
        self.product_url = reverse("product-detail", args=[self.product.id])
        self.product_list_url = reverse("product-list")

        self.category_url = reverse("category-detail", args=[self.category.id])
        self.category_list_url = reverse("category-list")

        self.order_url = reverse("order-detail", args=[self.order.id])
        self.order_list_url = reverse("order-list")

    # -------------------------------
    # Product soft delete
    # -------------------------------
    def test_soft_delete_product(self):
        response = self.client.delete(self.product_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.product.refresh_from_db()
        self.assertTrue(self.product.delete_status)

        response = self.client.get(self.product_list_url)
        ids = [item["id"] for item in response.data["results"]]
        self.assertNotIn(str(self.product.id), ids)

        # Optional: all_objects still accessible
        product_in_db = Product.all_objects.get(id=self.product.id)
        self.assertIsNotNone(product_in_db)

    # -------------------------------
    # Category soft delete
    # -------------------------------
    def test_soft_delete_category(self):
        response = self.client.delete(self.category_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.category.refresh_from_db()
        self.assertTrue(self.category.delete_status)

        response = self.client.get(self.category_list_url)
        ids = [item["id"] for item in response.data["results"]]
        self.assertNotIn(str(self.category.id), ids)

        # Optional: all_objects still accessible
        category_in_db = Category.all_objects.get(id=self.category.id)
        self.assertIsNotNone(category_in_db)

    # -------------------------------
    # Order soft delete
    # -------------------------------
    def test_soft_delete_order(self):
        response = self.client.delete(self.order_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.order.refresh_from_db()
        self.assertTrue(self.order.delete_status)

        response = self.client.get(self.order_list_url)
        ids = [item["id"] for item in response.data["results"]]
        self.assertNotIn(str(self.order.id), ids)

        # Optional: all_objects still accessible
        order_in_db = Order.all_objects.get(id=self.order.id)
        self.assertIsNotNone(order_in_db)
