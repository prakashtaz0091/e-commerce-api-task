from django.test import TestCase
from api.models import Category, Product
from decimal import Decimal

from django.core.exceptions import ValidationError


class ProductDiscountPercentTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics",
        )

        self.base_payload = {
            "name": "Test Product",
            "code": "TP-001",
            "description": "Test description",
            "category": self.category,
            "base_price": Decimal("100.00"),
            "stock_quantity": 10,
        }

    def test_product_creation_with_valid_discount_percent(self):
        """Product should be created when discount_percent is between 0 and 100"""
        product = Product(
            **self.base_payload,
            discount_percent=20,
        )

        # full_clean triggers model validators
        product.full_clean()
        product.save()

        self.assertEqual(product.discount_percent, 20)
        self.assertEqual(product.discounted_price, Decimal("80.00"))

    def test_product_creation_with_zero_discount(self):
        """discount_percent = 0 should be valid"""
        product = Product(
            **self.base_payload,
            discount_percent=0,
        )

        product.full_clean()
        product.save()

        self.assertEqual(product.discounted_price, Decimal("100.00"))

    def test_product_creation_with_full_discount(self):
        """discount_percent = 100 should be valid"""
        product = Product(
            **self.base_payload,
            discount_percent=100,
        )

        product.full_clean()
        product.save()

        self.assertEqual(product.discounted_price, Decimal("0.00"))

    def test_product_creation_with_negative_discount_percent_should_fail(self):
        """Negative discount_percent should raise ValidationError"""
        product = Product(
            **self.base_payload,
            discount_percent=-1,
        )

        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_product_creation_with_discount_percent_greater_than_100_should_fail(self):
        """discount_percent > 100 should raise ValidationError"""
        product = Product(
            **self.base_payload,
            discount_percent=101,
        )

        with self.assertRaises(ValidationError):
            product.full_clean()
