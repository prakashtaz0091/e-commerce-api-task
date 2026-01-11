"""
Management command to seed the database with test orders

USAGE:
    python manage.py seed_orders                          # Create 100 random orders
    python manage.py seed_orders --count 200              # Create 200 random orders
    python manage.py seed_orders --clear                  # Clear all orders first
    python manage.py seed_orders --realistic              # Create realistic order history
    python manage.py seed_orders --status delivered       # Only create delivered orders
    python manage.py seed_orders --days 30                # Orders from last 30 days
    python manage.py seed_orders --clear --realistic      # Clear and create realistic
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from api.models import (
    Order,
    Product,
)
import random


class Command(BaseCommand):
    help = "Seed the database with test orders"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Number of orders to create (default: 100)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing orders before seeding",
        )
        parser.add_argument(
            "--realistic",
            action="store_true",
            help="Create realistic order history with proper status progression",
        )
        parser.add_argument(
            "--status",
            type=str,
            choices=[
                "pending",
                "confirmed",
                "processing",
                "shipped",
                "delivered",
                "cancelled",
            ],
            help="Create orders with specific status only",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Create orders within last N days (default: 90)",
        )

    def handle(self, *args, **options):
        count = options["count"]
        clear = options["clear"]
        realistic = options["realistic"]
        status_filter = options["status"]
        days = options["days"]

        if clear:
            self.stdout.write("Clearing existing orders...")
            Order.all_objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✓ All orders cleared"))

        # Check if products exist
        if not Product.objects.exists():
            self.stdout.write(
                self.style.ERROR(
                    "✗ No products found. Run: python manage.py seed_products --realistic"
                )
            )
            return

        if realistic:
            self.create_realistic_orders(days)
        else:
            self.create_random_orders(count, status_filter, days)

        self.stdout.write(self.style.SUCCESS(f"\n✓ Successfully seeded orders!"))

    def _get_random_past_datetime(self, days):
        """Generate random datetime within the last N days"""
        now = timezone.now()
        start_date = now - timedelta(days=days)
        random_seconds = random.randint(0, int((now - start_date).total_seconds()))
        return start_date + timedelta(seconds=random_seconds)

    def _get_status_progression_time(self, created_at, status):
        """Calculate realistic status change time based on order creation"""
        if status == Order.STATUS_PENDING:
            return None

        # Realistic time delays between statuses
        delays = {
            Order.STATUS_CONFIRMED: timedelta(minutes=random.randint(5, 60)),
            Order.STATUS_PROCESSING: timedelta(hours=random.randint(1, 24)),
            Order.STATUS_SHIPPED: timedelta(days=random.randint(1, 3)),
            Order.STATUS_DELIVERED: timedelta(days=random.randint(3, 7)),
            Order.STATUS_CANCELLED: timedelta(hours=random.randint(1, 48)),
        }

        return created_at + delays.get(status, timedelta(hours=1))

    @transaction.atomic
    def create_realistic_orders(self, days):
        """Create realistic order history with proper status progression"""

        self.stdout.write(f"Creating realistic order history for last {days} days...")

        # Get active products with stock
        products = list(
            Product.objects.filter(active=Product.ACTIVE, stock_quantity__gt=0)
        )

        if not products:
            self.stdout.write(self.style.ERROR("✗ No active products with stock found"))
            return

        # Status distribution (realistic e-commerce percentages)
        status_distribution = [
            (Order.STATUS_DELIVERED, 60),  # 60% delivered
            (Order.STATUS_SHIPPED, 15),  # 15% shipped
            (Order.STATUS_PROCESSING, 10),  # 10% processing
            (Order.STATUS_CONFIRMED, 5),  # 5% confirmed
            (Order.STATUS_PENDING, 5),  # 5% pending
            (Order.STATUS_CANCELLED, 5),  # 5% cancelled
        ]

        # Calculate number of orders per status
        total_orders = 150  # Realistic number for demo
        orders_by_status = []

        for status, percentage in status_distribution:
            count = int(total_orders * percentage / 100)
            orders_by_status.extend([status] * count)

        random.shuffle(orders_by_status)

        created_count = 0
        total_revenue = Decimal("0.00")

        for status in orders_by_status:
            product = random.choice(products)

            # Realistic quantity distribution
            if product.base_price > 500:  # Expensive items
                quantity = random.randint(1, 2)
            elif product.base_price > 100:  # Mid-range
                quantity = random.randint(1, 3)
            else:  # Cheap items
                quantity = random.randint(1, 5)

            # Calculate prices
            unit_price = product.discounted_price
            total_price = unit_price * quantity

            # Generate creation time
            created_at = self._get_random_past_datetime(days)

            # Calculate status change time
            status_changed_at = self._get_status_progression_time(created_at, status)

            # Create order
            order = Order.objects.create(
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                status=status,
                status_changed_at=status_changed_at,
            )

            # Manually set created_at to simulate historical data
            Order.objects.filter(id=order.id).update(created_at=created_at)

            created_count += 1

            # Add to revenue if delivered
            if status == Order.STATUS_DELIVERED:
                total_revenue += total_price

            if created_count % 25 == 0:
                self.stdout.write(f"  ✓ Created {created_count} orders...")

        self.stdout.write(f"\nCreated {created_count} realistic orders")
        self._print_statistics(total_revenue)

    @transaction.atomic
    def create_random_orders(self, count, status_filter, days):
        """Create random orders for testing"""

        self.stdout.write(f"Creating {count} random orders...")

        # Get active products
        products = list(Product.objects.filter(active=Product.ACTIVE))

        if not products:
            self.stdout.write(self.style.ERROR("✗ No active products found"))
            return

        # Status mapping
        status_map = {
            "pending": Order.STATUS_PENDING,
            "confirmed": Order.STATUS_CONFIRMED,
            "processing": Order.STATUS_PROCESSING,
            "shipped": Order.STATUS_SHIPPED,
            "delivered": Order.STATUS_DELIVERED,
            "cancelled": Order.STATUS_CANCELLED,
        }

        created_count = 0
        total_revenue = Decimal("0.00")

        for i in range(count):
            product = random.choice(products)

            # Random quantity (1-10)
            quantity = random.randint(1, 10)

            # Calculate prices
            unit_price = product.discounted_price
            total_price = unit_price * quantity

            # Determine status
            if status_filter:
                status = status_map[status_filter]
            else:
                # Random status with weighted distribution
                status = random.choices(
                    [
                        Order.STATUS_DELIVERED,
                        Order.STATUS_SHIPPED,
                        Order.STATUS_PROCESSING,
                        Order.STATUS_CONFIRMED,
                        Order.STATUS_PENDING,
                        Order.STATUS_CANCELLED,
                    ],
                    weights=[50, 20, 10, 10, 5, 5],  # Weights favor completed orders
                    k=1,
                )[0]

            # Generate creation time
            created_at = self._get_random_past_datetime(days)

            # Calculate status change time
            status_changed_at = self._get_status_progression_time(created_at, status)

            try:
                # Create order
                order = Order.objects.create(
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                    status=status,
                    status_changed_at=status_changed_at,
                )

                # Manually set created_at
                Order.objects.filter(id=order.id).update(created_at=created_at)

                created_count += 1

                # Add to revenue if delivered
                if status == Order.STATUS_DELIVERED:
                    total_revenue += total_price

                if created_count % 25 == 0:
                    self.stdout.write(f"  ✓ Created {created_count}/{count} orders...")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Error creating order: {e}"))

        self.stdout.write(f"\nCreated {created_count} random orders")
        self._print_statistics(total_revenue)

    def _print_statistics(self, total_revenue):
        """Print order statistics"""

        total_orders = Order.objects.count()

        # Status breakdown
        status_counts = {
            "Pending": Order.objects.filter(status=Order.STATUS_PENDING).count(),
            "Confirmed": Order.objects.filter(status=Order.STATUS_CONFIRMED).count(),
            "Processing": Order.objects.filter(status=Order.STATUS_PROCESSING).count(),
            "Shipped": Order.objects.filter(status=Order.STATUS_SHIPPED).count(),
            "Delivered": Order.objects.filter(status=Order.STATUS_DELIVERED).count(),
            "Cancelled": Order.objects.filter(status=Order.STATUS_CANCELLED).count(),
        }

        # Calculate average order value
        orders = Order.objects.all()
        if orders:
            avg_order_value = sum(o.total_price for o in orders) / len(orders)
        else:
            avg_order_value = Decimal("0.00")

        self.stdout.write(f"\n📊 Order Statistics:")
        self.stdout.write(f"  Total orders: {total_orders}")
        self.stdout.write(f"  Total revenue (delivered): ${total_revenue:,.2f}")
        self.stdout.write(f"  Average order value: ${avg_order_value:,.2f}")

        self.stdout.write(f"\n📈 Status Breakdown:")
        for status_name, count in status_counts.items():
            percentage = (count / total_orders * 100) if total_orders > 0 else 0
            self.stdout.write(f"  {status_name}: {count} ({percentage:.1f}%)")

        # Recent orders
        recent = Order.objects.order_by("-created_at")[:5]
        if recent:
            self.stdout.write(f"\n🕐 Recent Orders:")
            for order in recent:
                self.stdout.write(
                    f"  {order.order_code} - {order.product.name} - "
                    f"${order.total_price} - {order.get_status_display()}"
                )
