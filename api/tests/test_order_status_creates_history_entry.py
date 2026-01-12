from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

from api.models import Order, OrderStatusHistory, Product, Category

User = get_user_model()


class OrderStatusHistoryAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="admin@test.com",
            password="testpass123",
        )

        self.client.force_authenticate(self.user)

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

        self.order = Order.objects.create(
            status=Order.StatusChoices.PENDING,
            quantity=1,
            unit_price=100,
            total_price=100,
            product=self.product_1,
        )

        self.url = reverse("order-detail", args=[self.order.id])

    def test_update_order_status_creates_history(self):
        payload = {
            "status": Order.StatusChoices.CONFIRMED,
        }

        response = self.client.patch(self.url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh order
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.StatusChoices.CONFIRMED)

        # History validation
        history = OrderStatusHistory.objects.filter(order=self.order)

        self.assertEqual(history.count(), 2)

        entry = history.first()
        self.assertEqual(entry.old_status, Order.StatusChoices.PENDING)
        self.assertEqual(entry.new_status, Order.StatusChoices.CONFIRMED)
        self.assertEqual(entry.changed_by, self.user.username)
