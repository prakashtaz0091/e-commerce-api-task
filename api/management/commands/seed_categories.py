"""
Management command to seed the database with test categories

INSTALLATION:
1. Create this file at: your_app/management/commands/seed_categories.py
2. Update line 24: Change 'your_app' to your actual app name (e.g., 'products', 'inventory')
3. Run: python manage.py seed_categories --realistic

USAGE:
    python manage.py seed_categories                    # Create 5 random parent categories
    python manage.py seed_categories --count 10         # Create 10 random parent categories
    python manage.py seed_categories --clear            # Clear all categories first
    python manage.py seed_categories --realistic        # Create realistic e-commerce categories
    python manage.py seed_categories --clear --realistic  # Clear and create realistic
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Category
import random


class Command(BaseCommand):
    help = "Seed the database with test categories"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=5,
            help="Number of parent categories to create (default: 5)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing categories before seeding",
        )
        parser.add_argument(
            "--realistic",
            action="store_true",
            help="Create realistic e-commerce categories instead of random ones",
        )

    def handle(self, *args, **options):
        count = options["count"]
        clear = options["clear"]
        realistic = options["realistic"]

        if clear:
            self.stdout.write("Clearing existing categories...")
            Category.all_objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✓ All categories cleared"))

        if realistic:
            self.create_realistic_categories()
        else:
            self.create_random_categories(count)

        self.stdout.write(self.style.SUCCESS(f"\n✓ Successfully seeded categories!"))

    @transaction.atomic
    def create_realistic_categories(self):
        """Create realistic e-commerce category structure"""

        self.stdout.write("Creating realistic e-commerce categories...")

        # Define realistic category structure
        categories_data = {
            "Electronics": {
                "description": "Electronic devices and gadgets",
                "subcategories": {
                    "Mobile Phones": {
                        "description": "Smartphones and feature phones",
                        "subcategories": [
                            "Smartphones",
                            "Feature Phones",
                            "Phone Accessories",
                        ],
                    },
                    "Laptops": {
                        "description": "Notebook computers",
                        "subcategories": [
                            "Gaming Laptops",
                            "Business Laptops",
                            "Ultrabooks",
                        ],
                    },
                    "Tablets": {
                        "description": "Tablet computers",
                        "subcategories": ["iPad", "Android Tablets", "Windows Tablets"],
                    },
                    "Audio": {
                        "description": "Audio devices",
                        "subcategories": ["Headphones", "Speakers", "Earbuds"],
                    },
                    "Cameras": {
                        "description": "Photography equipment",
                        "subcategories": ["DSLR", "Mirrorless", "Action Cameras"],
                    },
                },
            },
            "Clothing": {
                "description": "Fashion and apparel",
                "subcategories": {
                    "Men's Clothing": {
                        "description": "Clothing for men",
                        "subcategories": ["Shirts", "Pants", "Jackets", "Shoes"],
                    },
                    "Women's Clothing": {
                        "description": "Clothing for women",
                        "subcategories": ["Dresses", "Tops", "Skirts", "Shoes"],
                    },
                    "Kids' Clothing": {
                        "description": "Clothing for children",
                        "subcategories": ["Boys", "Girls", "Infants"],
                    },
                },
            },
            "Home & Kitchen": {
                "description": "Home essentials and kitchen items",
                "subcategories": {
                    "Furniture": {
                        "description": "Home furniture",
                        "subcategories": ["Sofas", "Tables", "Chairs", "Beds"],
                    },
                    "Kitchen Appliances": {
                        "description": "Kitchen appliances",
                        "subcategories": ["Blenders", "Microwaves", "Coffee Makers"],
                    },
                    "Home Decor": {
                        "description": "Decorative items",
                        "subcategories": ["Wall Art", "Lamps", "Cushions"],
                    },
                },
            },
            "Books": {
                "description": "Books and reading materials",
                "subcategories": {
                    "Fiction": {
                        "description": "Fiction books",
                        "subcategories": [
                            "Mystery",
                            "Romance",
                            "Science Fiction",
                            "Fantasy",
                        ],
                    },
                    "Non-Fiction": {
                        "description": "Non-fiction books",
                        "subcategories": ["Biography", "History", "Self-Help"],
                    },
                    "Educational": {
                        "description": "Educational books",
                        "subcategories": ["Textbooks", "Reference", "Test Prep"],
                    },
                },
            },
            "Sports & Outdoors": {
                "description": "Sports equipment and outdoor gear",
                "subcategories": {
                    "Exercise & Fitness": {
                        "description": "Fitness equipment",
                        "subcategories": ["Yoga", "Weights", "Cardio Equipment"],
                    },
                    "Outdoor Recreation": {
                        "description": "Outdoor activities",
                        "subcategories": ["Camping", "Hiking", "Cycling"],
                    },
                    "Team Sports": {
                        "description": "Team sports equipment",
                        "subcategories": ["Football", "Basketball", "Cricket"],
                    },
                },
            },
        }

        # Create categories
        for parent_name, parent_data in categories_data.items():
            parent = Category.objects.create(
                name=parent_name,
                description=parent_data["description"],
                image_url=f'https://example.com/images/{parent_name.lower().replace(" ", "-")}.jpg',
                active=Category.ACTIVE,
            )
            self.stdout.write(f"  ✓ Created parent: {parent_name}")

            # Create subcategories
            for sub_name, sub_data in parent_data.get("subcategories", {}).items():
                if isinstance(sub_data, dict):
                    subcategory = Category.objects.create(
                        name=sub_name,
                        description=sub_data.get("description", ""),
                        parent_category=parent,
                        active=Category.ACTIVE,
                    )
                    self.stdout.write(f"    ✓ Created subcategory: {sub_name}")

                    # Create nested subcategories
                    for nested_name in sub_data.get("subcategories", []):
                        Category.objects.create(
                            name=nested_name,
                            description=f"{nested_name} products",
                            parent_category=subcategory,
                            active=Category.ACTIVE,
                        )
                        self.stdout.write(f"      ✓ Created nested: {nested_name}")

        # Show summary
        total = Category.objects.count()
        parents = Category.objects.filter(parent_category__isnull=True).count()
        self.stdout.write(f"\nCreated {total} categories ({parents} parents)")

    @transaction.atomic
    def create_random_categories(self, count):
        """Create random categories for testing"""

        self.stdout.write(f"Creating {count} random parent categories...")

        parent_names = [
            "Electronics",
            "Clothing",
            "Books",
            "Sports",
            "Home & Garden",
            "Toys",
            "Beauty",
            "Automotive",
            "Food",
            "Health",
            "Music",
            "Movies",
            "Games",
            "Office",
            "Pet Supplies",
            "Jewelry",
            "Crafts",
            "Industrial",
            "Travel",
            "Baby Products",
        ]

        subcategory_templates = [
            "Premium {}",
            "Budget {}",
            "Luxury {}",
            "Everyday {}",
            "Professional {}",
            "Beginner {}",
            "Advanced {}",
            "Standard {}",
        ]

        created_parents = []

        # Create parent categories
        for i in range(min(count, len(parent_names))):
            parent = Category.objects.create(
                name=parent_names[i],
                description=f"All about {parent_names[i].lower()}",
                image_url=f"https://example.com/images/{parent_names[i].lower()}.jpg",
                active=Category.ACTIVE,
            )
            created_parents.append(parent)
            self.stdout.write(f"  ✓ Created: {parent.name}")

            # Create 2-5 subcategories for each parent
            num_subcategories = random.randint(2, 5)
            for j in range(num_subcategories):
                template = random.choice(subcategory_templates)
                subcategory = Category.objects.create(
                    name=template.format(parent.name),
                    description=f"{template.format(parent.name)} products",
                    parent_category=parent,
                    active=random.choice(
                        [Category.ACTIVE, Category.ACTIVE, Category.INACTIVE]
                    ),
                )
                self.stdout.write(f"    ✓ Created subcategory: {subcategory.name}")

                # Randomly create nested subcategories (30% chance)
                if random.random() < 0.3:
                    nested = Category.objects.create(
                        name=f"Specialized {subcategory.name}",
                        description=f"Specialized products for {subcategory.name}",
                        parent_category=subcategory,
                        active=Category.ACTIVE,
                    )
                    self.stdout.write(f"      ✓ Created nested: {nested.name}")

        # Show summary
        total = Category.objects.count()
        parents = Category.objects.filter(parent_category__isnull=True).count()
        self.stdout.write(f"\nCreated {total} categories ({parents} parents)")
