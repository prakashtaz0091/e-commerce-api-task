from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Prefetch
from django.db.models import F, ExpressionWrapper, DecimalField
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from .filters import ProductFilter

from .models import Category, Product, Order
from .serializers import (
    CategorySerializer,
    CategoryListSerializer,
    CategoryCreateUpdateSerializer,
    ProductSerializer,
    ProductUpdateSerializer,
    OrderSerializer,
    OrderReadSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category CRUD operations with nested subcategories
    """

    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "id"

    def get_queryset(self):
        """
        Optimize queries with prefetch_related for nested categories
        Only return non-deleted categories
        """
        queryset = Category.objects.filter(
            delete_status=Category.DELETE_STATUS_NOT_DELETED
        )

        # Prefetch children recursively for better performance
        children_prefetch = Prefetch(
            "children",
            queryset=Category.objects.filter(
                delete_status=Category.DELETE_STATUS_NOT_DELETED, active=Category.ACTIVE
            ),
        )

        return queryset.prefetch_related(children_prefetch)

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == "list":
            return CategoryListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return CategoryCreateUpdateSerializer
        return CategorySerializer

    def list(self, request, *args, **kwargs):
        """
        GET /api/categories/
        List all parent categories (parent_category=null) with nested subcategories
        """
        # Only get root/parent categories
        queryset = self.get_queryset().filter(parent_category__isnull=True)

        # Optional: filter by active status
        active_filter = request.query_params.get("active")
        if active_filter is not None:
            queryset = queryset.filter(active=int(active_filter))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        GET /api/categories/{id}/
        Get single category with all nested subcategories
        """
        instance = self.get_object()
        serializer = CategorySerializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        POST /api/categories/
        Create a new category
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Return full category data with nested structure
        instance = serializer.instance
        response_serializer = CategorySerializer(instance)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        PUT/PATCH /api/categories/{id}/
        Update a category
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return full category data with nested structure
        response_serializer = CategorySerializer(instance)
        return Response(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /api/categories/{id}/
        Soft delete a category (set delete_status=1)
        Also soft delete all child categories recursively
        """
        instance = self.get_object()

        # Soft delete the category and all its children
        self._soft_delete_recursive(instance)

        return Response(
            {"message": "Category and its subcategories deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )

    def _soft_delete_recursive(self, category):
        """Recursively soft delete category and all children"""
        # Soft delete current category
        category.delete_status = Category.DELETE_STATUS_DELETED
        category.save()

        # Recursively soft delete all children
        for child in category.children.filter(
            delete_status=Category.DELETE_STATUS_NOT_DELETED
        ):
            self._soft_delete_recursive(child)


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "id"

    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
    ]
    filterset_class = ProductFilter
    ordering_fields = ["final_price_db", "name"]
    ordering = ["name"]

    def get_queryset(self):
        return (
            Product.objects.filter(
                active=Product.ACTIVE,
            )
            .annotate(
                final_price_db=ExpressionWrapper(
                    F("base_price") * (100 - F("discount_percent")) / 100,
                    output_field=DecimalField(max_digits=10, decimal_places=2),
                )
            )
            .select_related("category")
        )

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProductUpdateSerializer
        return ProductSerializer

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "id"

    def get_queryset(self):
        return Order.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return OrderSerializer

        return OrderReadSerializer
