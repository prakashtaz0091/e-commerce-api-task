from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone


from api.models import Order, OrderStatusHistory
from api.middlewares import get_current_request, get_client_ip


@receiver(pre_save, sender=Order)
def track_order_status_change(sender, instance, **kwargs):
    """
    Capture old status before saving Order.
    Store it on the instance for post_save access.
    """

    # New object → no previous status
    if instance._state.adding:
        instance._old_status = None
        return

    try:
        old_instance = Order.objects.only("status").get(pk=instance.pk)
        instance._old_status = old_instance.status
    except Order.DoesNotExist:
        instance._old_status = None


@receiver(post_save, sender=Order)
def create_order_status_history(sender, instance, created, **kwargs):
    old_status = getattr(instance, "_old_status", None)
    new_status = instance.status

    if old_status == new_status:
        return

    request = get_current_request()

    changed_by = None
    ip_address = None
    change_source = OrderStatusHistory.ChangeSource.SYSTEM

    if request:
        ip_address = get_client_ip(request)

        resolver_match = request.resolver_match
        if resolver_match and resolver_match.app_name == "admin":
            change_source = OrderStatusHistory.ChangeSource.ADMIN
        else:
            change_source = OrderStatusHistory.ChangeSource.API

        if request.user.is_authenticated:
            changed_by = request.user

    OrderStatusHistory.objects.create(
        order=instance,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by,
        change_source=change_source,
        ip_address=ip_address,
    )


@receiver(pre_save, sender=Order)
def update_status_timestamp(sender, instance, **kwargs):
    """
    Automatically update `status_changed_at` when `status` changes.
    """

    # Skip for new objects (optional: or set timestamp on creation)
    if instance._state.adding:
        instance.status_changed_at = timezone.now()
        return

    if hasattr(instance, "_old_status") and instance._old_status != instance.status:
        instance.status_changed_at = timezone.now()


@receiver(post_save, sender=Order)
def update_stock_on_order(sender, instance, created, **kwargs):
    """
    Update stocks
    """

    old_status = getattr(instance, "_old_status", None)
    new_status = instance.status

    # if status changed
    if old_status == new_status:
        return

    product = instance.product
    qty = instance.quantity

    # Decrease stock if order moves to PENDING (or just created)
    if created or (
        old_status != Order.StatusChoices.PENDING
        and new_status == Order.StatusChoices.PENDING
    ):
        product.decrease_stock(qty)

    # Restore stock if order cancelled
    elif (
        new_status == Order.StatusChoices.CANCELLED
        and old_status != Order.StatusChoices.CANCELLED
    ):
        product.increase_stock(qty)
