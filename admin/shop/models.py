from django.db import models
from django.utils import timezone
from django.utils.text import slugify

class Category(models.Model):
    """Модель категории товаров"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Название категории")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Описание")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, 
                              related_name='subcategories', verbose_name="Родительская категория")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    """Модель товара"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", verbose_name="Категория")
    name = models.CharField(max_length=200, verbose_name="Название товара")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    image = models.ImageField(upload_to="products/%Y/%m/", blank=True, null=True, verbose_name="Изображение")
    available = models.BooleanField(default=True, verbose_name="Доступен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ["name"]
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class User(models.Model):
    user_id = models.BigIntegerField(unique=True, verbose_name="ID пользователя Telegram")
    username = models.CharField(max_length=100, blank=True, null=True, verbose_name="Имя пользователя Telegram")
    full_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Полное имя")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефон")
    address = models.TextField(blank=True, null=True, verbose_name="Адрес доставки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.full_name or self.username or self.user_id}"

class CartItem(models.Model):
    user = models.ForeignKey(User, related_name='cart_items', on_delete=models.CASCADE, verbose_name="Пользователь")
    product = models.ForeignKey(Product, related_name='cart_items', on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Элемент корзины"
        verbose_name_plural = "Элементы корзины"
        unique_together = ('user', 'product')
    
    def __str__(self):
        return f"{self.user} - {self.product.name} ({self.quantity})"

class Order(models.Model):
    """Модель заказа"""
    STATUS_CHOICES = (
        ("new", "Новый"),
        ("processing", "В обработке"),
        ("shipped", "Отправлен"),
        ("delivered", "Доставлен"),
        ("cancelled", "Отменен"),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Ожидает оплаты'),
        ('succeeded', 'Оплачен'),
        ('failed', 'Ошибка оплаты'),
        ('refunded', 'Возврат'),
    )
    
    user_id = models.BigIntegerField(verbose_name="ID пользователя Telegram")
    username = models.CharField(max_length=100, blank=True, null=True, verbose_name="Имя пользователя Telegram")
    full_name = models.CharField(max_length=255, verbose_name="Полное имя")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    address = models.TextField(verbose_name="Адрес доставки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new", verbose_name="Статус")
    payment_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID платежа")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name="Статус оплаты")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Общая стоимость")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"Заказ {self.id} от {self.full_name}"
    
    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = sum(item.get_cost() for item in self.items.all())
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    """Модель элемента заказа"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="order_items", verbose_name="Товар")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    
    class Meta:
        verbose_name = "Элемент заказа"
        verbose_name_plural = "Элементы заказа"
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def get_cost(self):
        return self.price * self.quantity 

class FAQ(models.Model):
    question = models.CharField(max_length=255, unique=True, verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")
    keywords = models.TextField(blank=True, null=True, help_text="Ключевые слова, разделенные запятыми", verbose_name="Ключевые слова")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"
        ordering = ["question"]
    
    def __str__(self):
        return self.question[:50] + ('...' if len(self.question) > 50 else '') 
 
class Mailing(models.Model):
    """Модель рассылки"""
    text = models.TextField(verbose_name="Текст рассылки")
    scheduled_at = models.DateTimeField(verbose_name="Запланировано на")
    is_sent = models.BooleanField(default=False, verbose_name="Отправлено")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"Рассылка на {self.scheduled_at}" 