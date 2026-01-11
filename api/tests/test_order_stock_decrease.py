from django.test import TestCase
from api.models import Category, Product, Order
from decimal import Decimal


class OrderStockDecreaseTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics")

        self.product = Product.objects.create(
            name="Phone",
            code="PH-001",
            description="Test product",
            category=self.category,
            base_price=Decimal("100.00"),
            stock_quantity=10,
        )

    def test_order_creation_decreases_product_stock(self):
        """Creating an order should decrease product stock quantity"""
        initial_stock = self.product.stock_quantity

        Order.objects.create(
            product=self.product,
            quantity=3,
            unit_price=Decimal("100.00"),
            total_price=Decimal("300.00"),
        )

        self.product.refresh_from_db()

        self.assertEqual(self.product.stock_quantity, initial_stock - 3)
