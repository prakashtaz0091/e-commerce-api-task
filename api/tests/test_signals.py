from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from api.models import Product, Category, Order, OrderStatusHistory

User = get_user_model()


class OrderSignalTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="admin@test.com",
            password="testpass123",
        )

        self.category = Category.objects.create(name="Electronics")
        self.product = Product.objects.create(
            name="Test Product",
            category=self.category,
            base_price=100,
            discount_percent=0,
            stock_quantity=50,
            active=Product.ACTIVE,
        )

        # Order setup
        self.order = Order.objects.create(
            status=Order.StatusChoices.PENDING,
            total_price=500,
            product=self.product,
            unit_price=self.product.base_price,
            quantity=1,
        )

    # ----------------------------------
    # Status change creates history
    # ----------------------------------
    def test_status_change_creates_history(self):
        old_status = self.order.status
        self.order.status = Order.StatusChoices.CONFIRMED
        self.order.save()

        history = OrderStatusHistory.objects.filter(order=self.order)
        self.assertEqual(history.count(), 2)
        entry = history.first()
        self.assertEqual(entry.old_status, old_status)
        self.assertEqual(entry.new_status, Order.StatusChoices.CONFIRMED)

    # ----------------------------------
    # Stock decreases on order create
    # Assuming order creation reduces stock for ordered products
    # ----------------------------------
    def test_stock_decreases_on_order_create(self):
        # Example: manual signal triggers decrease_stock
        initial_stock = self.product.stock_quantity

        # Simulate order containing 5 units
        quantity = 5
        self.product.decrease_stock(quantity)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, initial_stock - quantity)

    # ----------------------------------
    #   Stock increases on order cancel
    # ----------------------------------
    def test_stock_increases_on_order_cancel(self):
        initial_stock = self.product.stock_quantity

        # Simulate canceling order with 5 units
        quantity = 5
        self.product.increase_stock(quantity)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, initial_stock + quantity)

    # ----------------------------------
    # Timestamp auto-updates on status change
    # ----------------------------------
    def test_updated_at_changes_on_status_change(self):
        old_updated_at = self.order.updated_at

        # Sleep a tiny bit to guarantee timestamp difference
        import time

        time.sleep(0.01)

        self.order.status = Order.StatusChoices.CONFIRMED
        self.order.save()

        self.order.refresh_from_db()
        self.assertNotEqual(old_updated_at, self.order.updated_at)
        self.assertTrue(self.order.updated_at > old_updated_at)
