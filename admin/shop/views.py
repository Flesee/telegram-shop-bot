from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.contrib import messages
from .models import Category, Product, Order, OrderItem

def index(request):
    """Главная страница"""
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)[:8]
    return render(request, 'shop/index.html', {
        'categories': categories,
        'products': products,
    })

class CategoryListView(ListView):
    """Список категорий"""
    model = Category
    template_name = 'shop/category_list.html'
    context_object_name = 'categories'

class CategoryDetailView(DetailView):
    """Детальная информация о категории"""
    model = Category
    template_name = 'shop/category_detail.html'
    context_object_name = 'category'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = self.object.products.filter(available=True)
        return context

class ProductDetailView(DetailView):
    """Детальная информация о товаре"""
    model = Product
    template_name = 'shop/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'

@login_required
def order_list(request):
    """Список заказов"""
    orders = Order.objects.all()
    return render(request, 'shop/order_list.html', {
        'orders': orders,
    })

@login_required
def order_detail(request, order_id):
    """Детальная информация о заказе"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'shop/order_detail.html', {
        'order': order,
    })

@login_required
def order_update_status(request, order_id):
    """Обновление статуса заказа"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Order.STATUS_CHOICES):
            order.status = status
            order.save()
            messages.success(request, f'Статус заказа #{order.id} обновлен на "{order.get_status_display()}"')
        else:
            messages.error(request, 'Некорректный статус заказа')
        
        return redirect('shop:order_detail', order_id=order.id)
    
    return render(request, 'shop/order_update_status.html', {
        'order': order,
        'statuses': Order.STATUS_CHOICES,
    })
