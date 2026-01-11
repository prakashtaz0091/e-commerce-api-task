from django.test import TestCase
from api.models import Category, Product, Order
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
