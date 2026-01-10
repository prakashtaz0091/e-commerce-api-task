"""
Management command to seed the database with test products

USAGE:
    python manage.py seed_products                          # Create 50 random products
    python manage.py seed_products --count 100              # Create 100 random products
    python manage.py seed_products --clear                  # Clear all products first
    python manage.py seed_products --realistic              # Create realistic e-commerce products
    python manage.py seed_products --clear --realistic      # Clear and create realistic
    python manage.py seed_products --categories-only        # Only create products for existing categories
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from api.models import (
    Product,
    Category,
)
import random


class Command(BaseCommand):
    help = "Seed the database with test products"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=50,
            help="Number of products to create (default: 50)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing products before seeding",
        )
        parser.add_argument(
            "--realistic",
            action="store_true",
            help="Create realistic e-commerce products instead of random ones",
        )
        parser.add_argument(
            "--categories-only",
            action="store_true",
            help="Only create products for existing categories (skip category creation)",
        )

    def handle(self, *args, **options):
        count = options["count"]
        clear = options["clear"]
        realistic = options["realistic"]
        categories_only = options["categories_only"]

        if clear:
            self.stdout.write("Clearing existing products...")
            Product.all_objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✓ All products cleared"))

        # Check if categories exist
        if not Category.objects.exists():
            if categories_only:
                self.stdout.write(
                    self.style.ERROR(
                        "✗ No categories found. Run: python manage.py seed_categories --realistic"
                    )
                )
                return
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "⚠ No categories found. Creating categories first..."
                    )
                )
                # Create basic categories
                self._create_basic_categories()

        if realistic:
            self.create_realistic_products()
        else:
            self.create_random_products(count)

        self.stdout.write(self.style.SUCCESS(f"\n✓ Successfully seeded products!"))

    def _create_basic_categories(self):
        """Create minimal categories for products"""
        categories = ["Electronics", "Clothing", "Books", "Sports", "Home & Kitchen"]
        for cat_name in categories:
            Category.objects.get_or_create(
                name=cat_name,
                defaults={
                    "description": f"{cat_name} products",
                    "active": Category.ACTIVE,
                },
            )
        self.stdout.write("  ✓ Created basic categories")

    def _generate_product_code(self, prefix="PRD"):
        """Generate unique product code"""
        while True:
            code = f"{prefix}-{random.randint(10000, 99999)}"
            if not Product.objects.filter(code=code).exists():
                return code

    @transaction.atomic
    def create_realistic_products(self):
        """Create realistic e-commerce products"""

        self.stdout.write("Creating realistic e-commerce products...")

        # Product templates by category
        products_data = {
            "Electronics": {
                "Mobile Phones": [
                    (
                        "iPhone 15 Pro Max",
                        "Premium flagship smartphone with A17 Pro chip",
                        1199.99,
                        5,
                    ),
                    (
                        "Samsung Galaxy S24 Ultra",
                        "Top Android phone with S Pen",
                        1299.99,
                        8,
                    ),
                    (
                        "Google Pixel 8 Pro",
                        "Pure Android experience with AI features",
                        999.99,
                        10,
                    ),
                    ("OnePlus 12", "Flagship killer with great value", 799.99, 12),
                    ("Xiaomi 14 Pro", "Powerful camera phone", 699.99, 15),
                ],
                "Laptops": [
                    (
                        'MacBook Pro 16"',
                        "Professional laptop with M3 Max chip",
                        2499.99,
                        5,
                    ),
                    ("Dell XPS 15", "Premium Windows laptop", 1899.99, 8),
                    ("HP Spectre x360", "Convertible ultrabook", 1599.99, 10),
                    ("Lenovo ThinkPad X1 Carbon", "Business laptop", 1799.99, 7),
                    ("ASUS ROG Zephyrus G14", "Gaming laptop", 1699.99, 12),
                ],
                "Tablets": [
                    ('iPad Pro 12.9"', "Professional tablet with M2 chip", 1099.99, 8),
                    ("Samsung Galaxy Tab S9+", "Premium Android tablet", 899.99, 10),
                    ("iPad Air", "Mid-range Apple tablet", 599.99, 5),
                    (
                        "Microsoft Surface Pro 9",
                        "Windows tablet/laptop hybrid",
                        999.99,
                        12,
                    ),
                ],
                "Audio": [
                    (
                        "Sony WH-1000XM5",
                        "Premium noise-cancelling headphones",
                        399.99,
                        15,
                    ),
                    (
                        "Apple AirPods Pro 2",
                        "Premium true wireless earbuds",
                        249.99,
                        10,
                    ),
                    (
                        "Bose QuietComfort 45",
                        "Comfortable noise-cancelling headphones",
                        329.99,
                        12,
                    ),
                    ("JBL Flip 6", "Portable Bluetooth speaker", 129.99, 20),
                ],
            },
            "Clothing": {
                "Men's Clothing": [
                    ("Classic Oxford Shirt", "Premium cotton dress shirt", 79.99, 15),
                    ("Slim Fit Chinos", "Versatile casual pants", 89.99, 20),
                    ("Leather Jacket", "Genuine leather biker jacket", 299.99, 10),
                    ("Running Shoes", "Lightweight athletic shoes", 129.99, 25),
                    ("Polo Shirt", "Classic cotton polo", 49.99, 15),
                ],
                "Women's Clothing": [
                    ("Floral Summer Dress", "Lightweight cotton dress", 89.99, 20),
                    ("Silk Blouse", "Elegant office wear", 119.99, 15),
                    ("Yoga Pants", "High-waist athletic leggings", 69.99, 25),
                    ("Leather Handbag", "Designer style handbag", 199.99, 10),
                    ("Cashmere Sweater", "Luxury soft sweater", 149.99, 12),
                ],
            },
            "Books": {
                "Fiction": [
                    (
                        "The Midnight Library",
                        "Bestselling contemporary fiction",
                        14.99,
                        0,
                    ),
                    ("Project Hail Mary", "Science fiction thriller", 16.99, 5),
                    ("Where the Crawdads Sing", "Mystery drama novel", 15.99, 10),
                    (
                        "The Seven Husbands of Evelyn Hugo",
                        "Historical fiction",
                        13.99,
                        0,
                    ),
                ],
                "Non-Fiction": [
                    ("Atomic Habits", "Self-improvement bestseller", 16.99, 0),
                    ("Sapiens", "Brief history of humankind", 18.99, 5),
                    ("Educated", "Memoir by Tara Westover", 15.99, 0),
                    ("Thinking, Fast and Slow", "Psychology and economics", 17.99, 10),
                ],
            },
            "Sports & Outdoors": {
                "Exercise & Fitness": [
                    ("Yoga Mat Premium", "Non-slip exercise mat", 39.99, 20),
                    ("Adjustable Dumbbells Set", "5-52.5 lbs per dumbbell", 299.99, 15),
                    ("Resistance Bands Set", "Complete workout bands", 24.99, 25),
                    ("Foam Roller", "Muscle recovery tool", 29.99, 15),
                ],
                "Outdoor Recreation": [
                    ("4-Person Camping Tent", "Waterproof family tent", 179.99, 10),
                    ("Hiking Backpack 40L", "Durable trekking backpack", 89.99, 15),
                    ("Sleeping Bag", "All-season sleeping bag", 69.99, 20),
                    ("Portable Camp Stove", "Compact camping stove", 49.99, 12),
                ],
            },
            "Home & Kitchen": {
                "Kitchen Appliances": [
                    ("KitchenAid Stand Mixer", "Professional stand mixer", 379.99, 10),
                    ("Ninja Blender", "High-powered blender", 99.99, 15),
                    ("Instant Pot Duo", "Multi-function pressure cooker", 89.99, 20),
                    ("Espresso Machine", "Semi-automatic espresso maker", 299.99, 8),
                ],
                "Furniture": [
                    ("Modern Sectional Sofa", "5-seater L-shaped sofa", 1299.99, 5),
                    ("Dining Table Set", "Table with 6 chairs", 799.99, 10),
                    ("Queen Size Bed Frame", "Upholstered platform bed", 499.99, 8),
                    ("Office Desk", "Ergonomic work desk", 299.99, 12),
                ],
            },
        }

        total_created = 0

        # Create products
        for category_name, subcategories in products_data.items():
            # Try to find the category
            try:
                parent_category = Category.objects.get(name=category_name)
            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ Category "{category_name}" not found, skipping...'
                    )
                )
                continue

            for subcategory_name, products in subcategories.items():
                # Try to find subcategory, fallback to parent
                try:
                    category = Category.objects.get(
                        name=subcategory_name, parent_category=parent_category
                    )
                except Category.DoesNotExist:
                    category = parent_category

                for product_name, description, price, discount in products:
                    # Generate stock quantity
                    stock = random.randint(10, 100)

                    # Determine if active (95% active)
                    active = (
                        Product.ACTIVE if random.random() < 0.95 else Product.INACTIVE
                    )

                    product = Product.objects.create(
                        name=product_name,
                        code=self._generate_product_code(),
                        description=description,
                        category=category,
                        base_price=Decimal(str(price)),
                        discount_percent=discount,
                        stock_quantity=stock,
                        active=active,
                    )

                    total_created += 1
                    discount_info = f" ({discount}% off)" if discount > 0 else ""
                    self.stdout.write(
                        f"  ✓ Created: {product.name} - ${price}{discount_info} in {category.name}"
                    )

        self.stdout.write(f"\nCreated {total_created} realistic products")

    @transaction.atomic
    def create_random_products(self, count):
        """Create random products for testing"""

        self.stdout.write(f"Creating {count} random products...")

        # Get all categories
        categories = list(Category.objects.all())
        if not categories:
            self.stdout.write(self.style.ERROR("✗ No categories available"))
            return

        # Product name templates
        adjectives = [
            "Premium",
            "Deluxe",
            "Professional",
            "Basic",
            "Advanced",
            "Ultra",
            "Standard",
            "Economy",
            "Luxury",
            "Budget",
            "Essential",
            "Pro",
            "Elite",
            "Ultimate",
            "Classic",
        ]

        nouns = [
            "Widget",
            "Gadget",
            "Device",
            "Tool",
            "Item",
            "Product",
            "Equipment",
            "Accessory",
            "Component",
            "System",
            "Kit",
            "Set",
            "Bundle",
            "Pack",
            "Unit",
        ]

        created_count = 0

        for i in range(count):
            # Generate product details
            name = f"{random.choice(adjectives)} {random.choice(nouns)} {random.randint(100, 999)}"
            category = random.choice(categories)
            base_price = Decimal(str(round(random.uniform(9.99, 999.99), 2)))
            discount = random.choice(
                [0, 0, 0, 5, 10, 15, 20, 25]
            )  # Most products no discount
            stock = random.randint(0, 200)
            active = Product.ACTIVE if random.random() < 0.9 else Product.INACTIVE

            # Generate description
            descriptions = [
                f"High-quality {name.lower()} for everyday use",
                f"Professional-grade {name.lower()} with advanced features",
                f"Affordable {name.lower()} perfect for beginners",
                f"Top-rated {name.lower()} with excellent reviews",
                f"Durable {name.lower()} built to last",
            ]
            description = random.choice(descriptions)

            try:
                product = Product.objects.create(
                    name=name,
                    code=self._generate_product_code(),
                    description=description,
                    category=category,
                    base_price=base_price,
                    discount_percent=discount,
                    stock_quantity=stock,
                    active=active,
                )

                created_count += 1

                if created_count % 10 == 0:
                    self.stdout.write(
                        f"  ✓ Created {created_count}/{count} products..."
                    )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Error creating product: {e}"))

        self.stdout.write(f"\nCreated {created_count} random products")

        # Summary statistics
        total_products = Product.objects.count()
        active_products = Product.objects.filter(active=Product.ACTIVE).count()
        total_value = sum(
            p.base_price * p.stock_quantity for p in Product.objects.all()
        )

        self.stdout.write(f"\n📊 Summary:")
        self.stdout.write(f"  Total products: {total_products}")
        self.stdout.write(f"  Active products: {active_products}")
        self.stdout.write(f"  Total inventory value: ${total_value:,.2f}")
