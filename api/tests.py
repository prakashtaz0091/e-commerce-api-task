from django.test import TestCase
from api.models import Category, Product
from decimal import Decimal

from django.core.exceptions import ValidationError


class CategoryModelTests(TestCase):
    def setUp(self):
        self.parent_category = Category.objects.create(
            name="Electronics", description="Parent category"
        )

        self.child_category = Category.objects.create(
            name="Mobile Phones", parent_category=self.parent_category
        )

        self.grandchild_category = Category.objects.create(
            name="Smartphones", parent_category=self.child_category
        )

    def test_parent_category_creation(self):
        """Parent category should be created without a parent"""
        self.assertIsNone(self.parent_category.parent_category)
        self.assertEqual(self.parent_category.name, "Electronics")

    def test_child_category_creation_with_parent(self):
        """Child category should correctly reference its parent"""
        self.assertIsNotNone(self.child_category.parent_category)
        self.assertEqual(self.child_category.parent_category, self.parent_category)

    def test_grand_child_category_creation_with_grand_parent(self):
        """Grand child cateogry should correctly referece it's parent and grand parent"""
        self.assertEqual(self.grandchild_category.parent_category, self.child_category)
        self.assertEqual(
            self.grandchild_category.parent_category.parent_category,
            self.parent_category,
        )


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
