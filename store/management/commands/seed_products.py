from django.core.management.base import BaseCommand
from store.models import Product, Category
from django.utils.text import slugify
import random

class Command(BaseCommand):
    help = 'Seed database with categories and products (PKR)'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data')
        parser.add_argument('--count', type=int, default=0, help='Number of random products to generate')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting seed command...'))

        usd_to_pkr = 350  # conversion rate

        # Clear existing data
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Product.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Database cleared!'))

        # Categories
        categories_data = ['Electronics', 'Mobiles', 'Laptops', 'Watches', 'Clothes', 'Shoes', 'Accessories']
        categories = {}

        for cat_name in categories_data:
            cat, created = Category.objects.get_or_create(
                name=cat_name,
                slug=slugify(cat_name),
                defaults={'is_active': True}
            )
            categories[cat_name] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created category: {cat_name}'))

        # Static products
        products_data = [
            ('iPhone 15 Pro', 'Mobiles', 1299.99*usd_to_pkr, 1199.99*usd_to_pkr, 15),
            ('Samsung S24', 'Mobiles', 1199.99*usd_to_pkr, 1099.99*usd_to_pkr, 20),
            ('MacBook Pro', 'Laptops', 2499.99*usd_to_pkr, 2299.99*usd_to_pkr, 10),
            ('HP Pavilion', 'Laptops', 899.99*usd_to_pkr, 799.99*usd_to_pkr, 22),
            ('Rolex Watch', 'Watches', 8999.99*usd_to_pkr, 8499.99*usd_to_pkr, 2),
            ('Apple Watch', 'Watches', 429.99*usd_to_pkr, 399.99*usd_to_pkr, 35),
            ('Men T-Shirt', 'Clothes', 29.99*usd_to_pkr, 24.99*usd_to_pkr, 100),
            ('Women Dress', 'Clothes', 59.99*usd_to_pkr, 49.99*usd_to_pkr, 75),
            ('Nike Shoes', 'Shoes', 159.99*usd_to_pkr, 139.99*usd_to_pkr, 45),
            ('Adidas Shoes', 'Shoes', 189.99*usd_to_pkr, 169.99*usd_to_pkr, 38),
            ('Leather Wallet', 'Accessories', 29.99*usd_to_pkr, 24.99*usd_to_pkr, 85),
            ('Sunglasses', 'Accessories', 39.99*usd_to_pkr, 29.99*usd_to_pkr, 70),
            ('Smart TV', 'Electronics', 699.99*usd_to_pkr, 649.99*usd_to_pkr, 25),
            ('Headphones', 'Electronics', 79.99*usd_to_pkr, 69.99*usd_to_pkr, 40),
        ]

        created_count = 0
        for name, cat, price, disc_price, stock in products_data:
            prod, created = Product.objects.get_or_create(
                name=name,
                slug=slugify(name),
                defaults={
                    'category': categories[cat],
                    'price': round(price, 2),
                    'discounted_price': round(disc_price, 2),
                    'stock_quantity': stock,
                    'description': f'High quality {name}',
                    'is_active': True
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  Created: {name}'))

        # Random products
        if options['count'] > 0:
            self.generate_random(options['count'], categories, usd_to_pkr)

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('SEEDING COMPLETE!'))
        self.stdout.write(f'Categories: {Category.objects.count()}')
        self.stdout.write(f'Products: {Product.objects.count()}')
        self.stdout.write(f'New: {created_count}')
        self.stdout.write('='*50)

    def generate_random(self, count, categories, usd_to_pkr):
        names = ['Premium', 'Deluxe', 'Pro', 'Elite', 'Essential', 'Luxury']
        types = ['Gadget', 'Device', 'Accessory', 'Kit', 'Bundle', 'Pack']

        for i in range(count):
            name = f"{random.choice(names)} {random.choice(types)} {random.randint(100,999)}"
            cat = random.choice(list(categories.values()))
            price = round(random.uniform(10, 1000) * usd_to_pkr, 2)

            Product.objects.create(
                name=name,
                slug=slugify(name + str(random.randint(1000,9999))),
                category=cat,
                price=price,
                discounted_price=round(price * 0.9, 2),
                stock_quantity=random.randint(5, 50),
                description=f'Random product {i+1}',
                is_active=True
            )
        self.stdout.write(self.style.SUCCESS(f'  Generated {count} random products'))