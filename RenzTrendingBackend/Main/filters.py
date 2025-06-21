import django_filters
from django_filters import rest_framework as filters
from .models import Product, Category, Color, Size

class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name="sellingPrice", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="sellingPrice", lookup_expr='lte')
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all(), method='filter_by_category',field_name='category')
    color = django_filters.ModelChoiceFilter(queryset=Color.objects.all(), method='filter_by_color',field_name='color')
    size = django_filters.ModelChoiceFilter(queryset=Size.objects.all(), method='filter_by_size',field_name='size')
    ordering = filters.OrderingFilter(
        fields=(
            ('name', 'name'),
            ('sellingPrice', 'sellingPrice'),
            ('stock', 'stock'),
        ),
        field_labels={
            'name': 'Name',
            'sellingPrice': 'Price',
            'stock': 'Stock',
        }
    )

    class Meta:
        model = Product
        fields = ['name', 'min_price', 'max_price', 'category', 'color', 'size']

    def filter_by_category(self, queryset, name, value):
        return queryset.filter(category=value)

    def filter_by_color(self, queryset, name, value):
        return queryset.filter(color=value)

    def filter_by_size(self, queryset, name, value):
        return queryset.filter(size__in=self.data.getlist('size')).distinct()

