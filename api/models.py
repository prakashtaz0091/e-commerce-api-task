import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class SoftDeleteUUIDModel(models.Model):
    DELETE_STATUS_NOT_DELETED = 0
    DELETE_STATUS_DELETED = 1

    DELETE_STATUS_CHOICES = (
        (DELETE_STATUS_NOT_DELETED, "Not Deleted"),
        (DELETE_STATUS_DELETED, "Deleted"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delete_status = models.IntegerField(
        choices=DELETE_STATUS_CHOICES,
        default=DELETE_STATUS_NOT_DELETED,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CategoryManager(models.Manager):
    """Custom manager for Category with soft delete support"""

    def get_queryset(self):
        """Override to exclude soft-deleted by default"""
        return (
            super()
            .get_queryset()
            .filter(delete_status=SoftDeleteUUIDModel.DELETE_STATUS_NOT_DELETED)
        )

    def active(self):
        """Get only active categories"""
        return self.get_queryset().filter(active=Category.ACTIVE)

    def parents(self):
        """Get only parent categories (no parent)"""
        return self.get_queryset().filter(parent_category__isnull=True)

    def with_deleted(self):
        """Include soft-deleted records"""
        return super().get_queryset()


class Category(SoftDeleteUUIDModel):
    ACTIVE = 1
    INACTIVE = 0

    ACTIVE_CHOICES = (
        (ACTIVE, "Active"),
        (INACTIVE, "Inactive"),
    )

    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True, null=True)

    parent_category = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
        db_index=True,
    )

    image_url = models.URLField(blank=True, null=True)

    active = models.IntegerField(
        choices=ACTIVE_CHOICES,
        default=ACTIVE,
        db_index=True,
    )

    # Managers
    objects = CategoryManager()
    all_objects = models.Manager()  # Access all records including deleted

    class Meta:
        db_table = "categories"
        indexes = [
            models.Index(fields=["active", "delete_status"]),
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name

    def soft_delete(self):
        """Soft delete this category"""
        self.delete_status = self.DELETE_STATUS_DELETED
        self.save()

    def restore(self):
        """Restore a soft-deleted category"""
        self.delete_status = self.DELETE_STATUS_NOT_DELETED
        self.save()

    def get_all_children(self):
        """Get all descendant categories recursively"""
        children = []
        for child in self.children.all():
            children.append(child)
            children.extend(child.get_all_children())
        return children

    def get_ancestors(self):
        """Get all ancestor categories"""
        ancestors = []
        current = self.parent_category
        while current:
            ancestors.append(current)
            current = current.parent_category
        return ancestors

    @property
    def is_parent(self):
        """Check if this category has children"""
        return self.children.exists()

    @property
    def depth(self):
        """Get the depth level of this category in the hierarchy"""
        return len(self.get_ancestors())


class ProductManager(models.Manager):
    """Custom manager for Product with soft delete support"""

    def get_queryset(self):
        """Override to exclude soft-deleted by default"""
        return (
            super()
            .get_queryset()
            .filter(delete_status=SoftDeleteUUIDModel.DELETE_STATUS_NOT_DELETED)
        )

    def active(self):
        """Get only active categories"""
        return self.get_queryset().filter(active=Product.ACTIVE)

    def with_deleted(self):
        """Include soft-deleted records"""
        return super().get_queryset()


class Product(SoftDeleteUUIDModel):
    ACTIVE = 1
    INACTIVE = 0

    ACTIVE_CHOICES = (
        (ACTIVE, "Active"),
        (INACTIVE, "Inactive"),
    )

    name = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=50, unique=True)

    description = models.TextField()

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        db_index=True,
    )

    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    discount_percent = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    stock_quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
    )

    active = models.IntegerField(
        choices=ACTIVE_CHOICES,
        default=ACTIVE,
        db_index=True,
    )

    # Managers
    objects = ProductManager()
    all_objects = models.Manager()  # Access all records including deleted

    class Meta:
        db_table = "products"
        indexes = [
            models.Index(fields=["active", "delete_status"]),
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def discounted_price(self):
        return self.base_price * (100 - self.discount_percent) / 100


class OrderManager(models.Manager):
    """Custom manager for Order with soft delete support"""

    def get_queryset(self):
        """Override to exclude soft-deleted by default"""
        return (
            super()
            .get_queryset()
            .filter(delete_status=SoftDeleteUUIDModel.DELETE_STATUS_NOT_DELETED)
        )


class Order(SoftDeleteUUIDModel):
    STATUS_PENDING = 0
    STATUS_CONFIRMED = 10
    STATUS_PROCESSING = 20
    STATUS_SHIPPED = 30
    STATUS_DELIVERED = 40
    STATUS_CANCELLED = 50

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    order_code = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        db_index=True,
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="orders",
        db_index=True,
    )

    quantity = models.IntegerField(validators=[MinValueValidator(1)])

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )

    status_changed_at = models.DateTimeField(null=True, blank=True)

    # Managers
    objects = OrderManager()
    all_objects = models.Manager()  # Access all records including deleted

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.order_code:
            self.order_code = f"ORD-{uuid.uuid4().hex[:10].upper()}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_code


class OrderStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="status_history",
        db_index=True,
    )

    old_status = models.IntegerField(
        null=True, blank=True, choices=Order.STATUS_CHOICES
    )
    new_status = models.IntegerField(choices=Order.STATUS_CHOICES)

    changed_by = models.CharField(max_length=100, null=True, blank=True)

    change_source = models.CharField(
        max_length=20,
        choices=(
            ("api", "API"),
            ("admin", "Admin"),
            ("system", "System"),
        ),
        db_index=True,
    )

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_status_history"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.order_code}: {self.old_status} → {self.new_status}"
