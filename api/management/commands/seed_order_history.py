"""
Management command to seed the database with order status history

USAGE:
    python manage.py seed_order_history                     # Create history for all orders
    python manage.py seed_order_history --clear             # Clear all history first
    python manage.py seed_order_history --order-id UUID     # Create history for specific order
    python manage.py seed_order_history --realistic         # Create realistic progression
    python manage.py seed_order_history --full-history      # Create complete status progression
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from api.models import (
    Order,
    OrderStatusHistory,
)
import random


class Command(BaseCommand):
    help = "Seed the database with order status history"

    # Realistic user names for changed_by field
    USERS = [
        "admin@example.com",
        "john.doe@example.com",
        "jane.smith@example.com",
        "system",
        "warehouse.manager@example.com",
        "shipping.dept@example.com",
        "customer.service@example.com",
    ]

    # Sample IP addresses
    IP_ADDRESSES = [
        "192.168.1.100",
        "192.168.1.101",
        "10.0.0.50",
        "172.16.0.100",
        "203.0.113.42",
        None,  # System changes might not have IP
    ]

    # Status progression mapping
    STATUS_FLOW = {
        Order.STATUS_PENDING: [Order.STATUS_CONFIRMED, Order.STATUS_CANCELLED],
        Order.STATUS_CONFIRMED: [Order.STATUS_PROCESSING, Order.STATUS_CANCELLED],
        Order.STATUS_PROCESSING: [Order.STATUS_SHIPPED, Order.STATUS_CANCELLED],
        Order.STATUS_SHIPPED: [Order.STATUS_DELIVERED, Order.STATUS_CANCELLED],
        Order.STATUS_DELIVERED: [],  # Final state
        Order.STATUS_CANCELLED: [],  # Final state
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing order status history before seeding",
        )
        parser.add_argument(
            "--order-id", type=str, help="Create history for specific order by UUID"
        )
        parser.add_argument(
            "--realistic",
            action="store_true",
            help="Create realistic status progression based on current order status",
        )
        parser.add_argument(
            "--full-history",
            action="store_true",
            help="Create complete status progression for all orders (overrides realistic)",
        )

    def handle(self, *args, **options):
        clear = options["clear"]
        order_id = options["order_id"]
        realistic = options["realistic"]
        full_history = options["full_history"]

        if clear:
            self.stdout.write("Clearing existing order status history...")
            OrderStatusHistory.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✓ All order status history cleared"))

        # Check if orders exist
        if not Order.objects.exists():
            self.stdout.write(
                self.style.ERROR(
                    "✗ No orders found. Run: python manage.py seed_orders --realistic"
                )
            )
            return

        if order_id:
            self.create_history_for_order(order_id, full_history)
        elif full_history:
            self.create_full_history_for_all_orders()
        elif realistic:
            self.create_realistic_history()
        else:
            self.create_simple_history()

        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Successfully seeded order status history!")
        )

    def _get_status_notes(self, old_status, new_status):
        """Generate realistic notes for status changes"""
        notes_map = {
            (None, Order.STATUS_PENDING): [
                "Order created by customer",
                "New order received",
                "Order placed successfully",
            ],
            (Order.STATUS_PENDING, Order.STATUS_CONFIRMED): [
                "Payment confirmed",
                "Payment received and verified",
                "Order payment processed successfully",
            ],
            (Order.STATUS_CONFIRMED, Order.STATUS_PROCESSING): [
                "Order sent to warehouse for processing",
                "Items being picked from warehouse",
                "Order processing started",
            ],
            (Order.STATUS_PROCESSING, Order.STATUS_SHIPPED): [
                "Order shipped via courier",
                "Package handed over to delivery partner",
                "Shipped with tracking number",
            ],
            (Order.STATUS_SHIPPED, Order.STATUS_DELIVERED): [
                "Order delivered successfully",
                "Package delivered to customer",
                "Delivery confirmed by customer",
            ],
            (None, Order.STATUS_CANCELLED): [
                "Order cancelled by customer",
                "Order cancelled - payment failed",
            ],
            (Order.STATUS_PENDING, Order.STATUS_CANCELLED): [
                "Order cancelled by customer before payment",
                "Order cancelled - payment timeout",
            ],
            (Order.STATUS_CONFIRMED, Order.STATUS_CANCELLED): [
                "Order cancelled by customer after payment",
                "Order cancelled - refund initiated",
            ],
            (Order.STATUS_PROCESSING, Order.STATUS_CANCELLED): [
                "Order cancelled - item out of stock",
                "Order cancelled by warehouse - unable to fulfill",
            ],
        }

        key = (old_status, new_status)
        return random.choice(notes_map.get(key, ["Status updated"]))

    def _get_change_source(self, old_status, new_status):
        """Determine realistic change source based on status transition"""
        # Initial order creation
        if old_status is None and new_status == Order.STATUS_PENDING:
            return "api"

        # Customer cancellations
        if new_status == Order.STATUS_CANCELLED and old_status in [
            Order.STATUS_PENDING,
            Order.STATUS_CONFIRMED,
        ]:
            return random.choice(["api", "admin"])

        # System/warehouse operations
        if new_status in [Order.STATUS_PROCESSING, Order.STATUS_SHIPPED]:
            return random.choice(["system", "admin"])

        # Delivery confirmation
        if new_status == Order.STATUS_DELIVERED:
            return "system"

        # Default
        return random.choice(["api", "admin", "system"])

    def _get_changed_by(self, change_source):
        """Get appropriate user based on change source"""
        if change_source == "system":
            return "system"
        return random.choice(self.USERS)

    @transaction.atomic
    def create_history_for_order(self, order_id, full_history=False):
        """Create status history for a specific order"""

        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"✗ Order {order_id} not found"))
            return

        self.stdout.write(f"Creating history for order {order.order_code}...")

        if full_history:
            self._create_full_progression(order)
        else:
            self._create_simple_progression(order)

        history_count = order.status_history.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Created {history_count} history records for {order.order_code}"
            )
        )

    @transaction.atomic
    def create_full_history_for_all_orders(self):
        """Create complete status progression history for all orders"""

        self.stdout.write("Creating full status history for all orders...")

        orders = Order.objects.all()
        total_orders = orders.count()
        created_count = 0
        total_history = 0

        for i, order in enumerate(orders, 1):
            history_count = self._create_full_progression(order)
            total_history += history_count
            created_count += 1

            if created_count % 25 == 0:
                self.stdout.write(
                    f"  ✓ Processed {created_count}/{total_orders} orders..."
                )

        self.stdout.write(
            f"\nCreated {total_history} history records for {created_count} orders"
        )
        self._print_statistics()

    @transaction.atomic
    def create_realistic_history(self):
        """Create realistic status history based on current order status"""

        self.stdout.write("Creating realistic status history for all orders...")

        orders = Order.objects.all()
        total_orders = orders.count()
        created_count = 0
        total_history = 0

        for i, order in enumerate(orders, 1):
            history_count = self._create_simple_progression(order)
            total_history += history_count
            created_count += 1

            if created_count % 25 == 0:
                self.stdout.write(
                    f"  ✓ Processed {created_count}/{total_orders} orders..."
                )

        self.stdout.write(
            f"\nCreated {total_history} history records for {created_count} orders"
        )
        self._print_statistics()

    @transaction.atomic
    def create_simple_history(self):
        """Create basic history (only current status) for all orders"""

        self.stdout.write("Creating simple status history for all orders...")

        orders = Order.objects.all()
        total_orders = orders.count()
        created_count = 0

        for i, order in enumerate(orders, 1):
            # Create only the current status record
            change_source = self._get_change_source(None, order.status)

            OrderStatusHistory.objects.create(
                order=order,
                old_status=None,
                new_status=order.status,
                changed_by=self._get_changed_by(change_source),
                change_source=change_source,
                ip_address=random.choice(self.IP_ADDRESSES),
                notes=self._get_status_notes(None, order.status),
            )

            created_count += 1

            if created_count % 50 == 0:
                self.stdout.write(
                    f"  ✓ Processed {created_count}/{total_orders} orders..."
                )

        self.stdout.write(
            f"\nCreated {created_count} history records for {created_count} orders"
        )
        self._print_statistics()

    def _create_full_progression(self, order):
        """Create complete status progression history for an order"""

        # Define the progression path based on final status
        if order.status == Order.STATUS_DELIVERED:
            progression = [
                (None, Order.STATUS_PENDING),
                (Order.STATUS_PENDING, Order.STATUS_CONFIRMED),
                (Order.STATUS_CONFIRMED, Order.STATUS_PROCESSING),
                (Order.STATUS_PROCESSING, Order.STATUS_SHIPPED),
                (Order.STATUS_SHIPPED, Order.STATUS_DELIVERED),
            ]
        elif order.status == Order.STATUS_CANCELLED:
            # Random cancellation point
            cancel_at = random.choice(
                [Order.STATUS_PENDING, Order.STATUS_CONFIRMED, Order.STATUS_PROCESSING]
            )

            if cancel_at == Order.STATUS_PENDING:
                progression = [
                    (None, Order.STATUS_PENDING),
                    (Order.STATUS_PENDING, Order.STATUS_CANCELLED),
                ]
            elif cancel_at == Order.STATUS_CONFIRMED:
                progression = [
                    (None, Order.STATUS_PENDING),
                    (Order.STATUS_PENDING, Order.STATUS_CONFIRMED),
                    (Order.STATUS_CONFIRMED, Order.STATUS_CANCELLED),
                ]
            else:  # PROCESSING
                progression = [
                    (None, Order.STATUS_PENDING),
                    (Order.STATUS_PENDING, Order.STATUS_CONFIRMED),
                    (Order.STATUS_CONFIRMED, Order.STATUS_PROCESSING),
                    (Order.STATUS_PROCESSING, Order.STATUS_CANCELLED),
                ]
        else:
            # For in-progress orders
            progression = [(None, Order.STATUS_PENDING)]
            current = Order.STATUS_PENDING

            while current != order.status:
                next_status = self._get_next_status_in_flow(current, order.status)
                if next_status is None:
                    break
                progression.append((current, next_status))
                current = next_status

        # Create history records with proper timestamps
        base_time = order.created_at
        history_count = 0

        for i, (old_status, new_status) in enumerate(progression):
            # Calculate realistic time for this status change
            if i == 0:
                created_at = base_time
            else:
                # Add realistic delay
                if new_status == Order.STATUS_CONFIRMED:
                    delay = timedelta(minutes=random.randint(5, 60))
                elif new_status == Order.STATUS_PROCESSING:
                    delay = timedelta(hours=random.randint(1, 24))
                elif new_status == Order.STATUS_SHIPPED:
                    delay = timedelta(days=random.randint(1, 3))
                elif new_status == Order.STATUS_DELIVERED:
                    delay = timedelta(days=random.randint(3, 7))
                elif new_status == Order.STATUS_CANCELLED:
                    delay = timedelta(hours=random.randint(1, 48))
                else:
                    delay = timedelta(hours=1)

                created_at = base_time + delay
                base_time = created_at

            change_source = self._get_change_source(old_status, new_status)

            history = OrderStatusHistory.objects.create(
                order=order,
                old_status=old_status,
                new_status=new_status,
                changed_by=self._get_changed_by(change_source),
                change_source=change_source,
                ip_address=random.choice(self.IP_ADDRESSES),
                notes=self._get_status_notes(old_status, new_status),
            )

            # Update created_at to match progression
            OrderStatusHistory.objects.filter(id=history.id).update(
                created_at=created_at
            )
            history_count += 1

        return history_count

    def _create_simple_progression(self, order):
        """Create simple progression (only to current status)"""

        # Create initial pending record
        change_source = self._get_change_source(None, Order.STATUS_PENDING)

        OrderStatusHistory.objects.create(
            order=order,
            old_status=None,
            new_status=Order.STATUS_PENDING,
            changed_by=self._get_changed_by(change_source),
            change_source=change_source,
            ip_address=random.choice(self.IP_ADDRESSES),
            notes=self._get_status_notes(None, Order.STATUS_PENDING),
        )

        # If current status is not pending, create one more record
        if order.status != Order.STATUS_PENDING:
            change_source = self._get_change_source(Order.STATUS_PENDING, order.status)

            OrderStatusHistory.objects.create(
                order=order,
                old_status=Order.STATUS_PENDING,
                new_status=order.status,
                changed_by=self._get_changed_by(change_source),
                change_source=change_source,
                ip_address=random.choice(self.IP_ADDRESSES),
                notes=self._get_status_notes(Order.STATUS_PENDING, order.status),
            )
            return 2

        return 1

    def _get_next_status_in_flow(self, current_status, target_status):
        """Get the next logical status in the flow towards target"""
        if current_status == Order.STATUS_PENDING:
            return Order.STATUS_CONFIRMED
        elif current_status == Order.STATUS_CONFIRMED:
            return Order.STATUS_PROCESSING
        elif current_status == Order.STATUS_PROCESSING:
            return Order.STATUS_SHIPPED
        elif current_status == Order.STATUS_SHIPPED:
            return Order.STATUS_DELIVERED
        return None

    def _print_statistics(self):
        """Print order status history statistics"""

        total_history = OrderStatusHistory.objects.count()
        total_orders = Order.objects.count()

        # History by change source
        source_counts = {
            "API": OrderStatusHistory.objects.filter(change_source="api").count(),
            "Admin": OrderStatusHistory.objects.filter(change_source="admin").count(),
            "System": OrderStatusHistory.objects.filter(change_source="system").count(),
        }

        # Average history per order
        avg_history = total_history / total_orders if total_orders > 0 else 0

        self.stdout.write(f"\n📊 History Statistics:")
        self.stdout.write(f"  Total history records: {total_history}")
        self.stdout.write(f"  Orders tracked: {total_orders}")
        self.stdout.write(f"  Average history per order: {avg_history:.1f}")

        self.stdout.write(f"\n📈 Change Source Breakdown:")
        for source_name, count in source_counts.items():
            percentage = (count / total_history * 100) if total_history > 0 else 0
            self.stdout.write(f"  {source_name}: {count} ({percentage:.1f}%)")

        # Recent history
        recent = OrderStatusHistory.objects.select_related("order")[:5]
        if recent:
            self.stdout.write(f"\n🕐 Recent Status Changes:")
            for history in recent:
                old_status_name = dict(Order.STATUS_CHOICES).get(
                    history.old_status, "None"
                )
                new_status_name = dict(Order.STATUS_CHOICES).get(history.new_status)
                self.stdout.write(
                    f"  {history.order.order_code}: {old_status_name} → {new_status_name} "
                    f"({history.change_source}) - {history.notes[:50]}"
                )
