from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Prefetch
from .models import Category
from .serializers import (
    CategorySerializer,
    CategoryListSerializer,
    CategoryCreateUpdateSerializer,
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
