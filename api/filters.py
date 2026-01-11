import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(
        field_name="final_price_db",
        lookup_expr="gte",
        label="Minimum final price",
    )
    max_price = django_filters.NumberFilter(
        field_name="final_price_db",
        lookup_expr="lte",
        label="Maximum final price",
    )

    in_stock = django_filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Product
        fields = [
            "category",
            "min_price",
            "max_price",
            "in_stock",
        ]

    def filter_in_stock(self, queryset, name, value):
        if value is True:
            return queryset.filter(stock_quantity__gt=0)
        if value is False:
            return queryset.filter(stock_quantity=0)
        return queryset
