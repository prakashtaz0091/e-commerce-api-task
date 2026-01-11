from rest_framework import serializers
from .models import Category, Product, Order, OrderStatusHistory
from django.db import transaction
from django.db.models import F


class CategorySerializer(serializers.ModelSerializer):
    """Recursive serializer for nested categories"""

    sub_categories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "description",
            "image_url",
            "parent_category",
            "active",
            "sub_categories",
        ]
        read_only_fields = ["id"]

    def get_sub_categories(self, obj):
        """Recursively serialize child categories"""
        # Only include active, non-deleted subcategories
        children = obj.children.filter(
            delete_status=Category.DELETE_STATUS_NOT_DELETED, active=Category.ACTIVE
        )
        return CategorySerializer(children, many=True).data


class CategoryListSerializer(serializers.ModelSerializer):
    """Serializer for listing only parent categories"""

    sub_categories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "description",
            "image_url",
            "parent_category",
            "active",
            "sub_categories",
        ]

    def get_sub_categories(self, obj):
        """Get only direct children (not nested deeper)"""
        children = obj.children.filter(
            delete_status=Category.DELETE_STATUS_NOT_DELETED, active=Category.ACTIVE
        )
        return CategorySerializer(children, many=True).data


class CategoryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating categories"""

    class Meta:
        model = Category
        fields = ["id", "name", "description", "image_url", "parent_category", "active"]
        read_only_fields = ["id"]

    def validate_parent_category(self, value):
        """Ensure parent category exists and is not deleted"""
        if value and value.delete_status == Category.DELETE_STATUS_DELETED:
            raise serializers.ValidationError(
                "Cannot assign a deleted category as parent."
            )
        return value

    def validate(self, data):
        """Prevent circular references"""
        parent = data.get("parent_category")
        instance = self.instance

        if parent and instance:
            # Check if trying to set a child as parent (circular reference)
            current = parent
            while current:
                if current.id == instance.id:
                    raise serializers.ValidationError(
                        {
                            "parent_category": "Cannot create circular category reference."
                        }
                    )
                current = current.parent_category

        return data


class CategorySerializerForProduct(serializers.ModelSerializer):
    """Serializer for listing only parent categories"""

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "parent_category",
        ]


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for products"""

    category = CategorySerializerForProduct()
    discount_amount = serializers.SerializerMethodField()
    final_price = serializers.FloatField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        exclude = ["delete_status"]

    def get_discount_amount(self, obj):
        return obj.base_price - obj.final_price


class ProductUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating products"""

    class Meta:
        model = Product
        exclude = ["delete_status"]


class ProductSerializerForOrder(serializers.ModelSerializer):
    """Serializer for products in order"""

    class Meta:
        model = Product
        fields = ["id", "name", "code"]


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        exclude = ["delete_status", "status_changed_at"]

    def create(self, validated_data):
        product = validated_data["product"]
        quantity = validated_data["quantity"]

        with transaction.atomic():
            updated = Product.objects.filter(
                id=product.id, stock_quantity__gte=quantity
            ).update(stock_quantity=F("stock_quantity") - quantity)

            if updated == 0:
                raise serializers.ValidationError({"quantity": "Not enough stock."})

            order = Order.objects.create(**validated_data)

        return order


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_new_status_display")

    class Meta:
        model = OrderStatusHistory
        fields = [
            "new_status",
            "status_display",
            "created_at",
            "changed_by",
            "change_source",
        ]


class OrderReadSerializer(serializers.ModelSerializer):

    product = ProductSerializerForOrder()
    status_display = serializers.CharField(source="get_status_display")
    timeline = OrderStatusHistorySerializer(
        many=True, read_only=True, source="status_history"
    )

    class Meta:
        model = Order
        exclude = ["delete_status"]
