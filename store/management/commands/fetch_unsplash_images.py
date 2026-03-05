import json
import urllib.parse
import urllib.request
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from store.models import Product


class Command(BaseCommand):
    help = "Fetch product images from Unsplash API and assign to products."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Replace existing images too (default only fills missing images).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max number of products to process (0 = all).",
        )

    def handle(self, *args, **options):
        access_key = getattr(settings, "UNSPLASH_ACCESS_KEY", "").strip()
        if not access_key:
            raise CommandError(
                "UNSPLASH_ACCESS_KEY missing. Set env var first, then rerun."
            )

        force = options["force"]
        limit = int(options["limit"] or 0)

        queryset = Product.objects.all().order_by("id")
        if not force:
            queryset = queryset.filter(image="")
        if limit > 0:
            queryset = queryset[:limit]

        products_dir = Path(settings.MEDIA_ROOT) / "products"
        products_dir.mkdir(parents=True, exist_ok=True)

        processed = 0
        updated = 0
        failed = 0

        for product in queryset:
            processed += 1
            try:
                image_url = self._search_unsplash_image(product.name, access_key)
                if not image_url:
                    self.stdout.write(self.style.WARNING(f"Skip: {product.name} (no image found)"))
                    continue

                filename = f"{product.slug or f'product-{product.id}'}-unsplash.jpg"
                relative_path = f"products/{filename}"
                absolute_path = products_dir / filename

                self._download_image(image_url, absolute_path)

                product.image = relative_path
                product.save(update_fields=["image"])
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"Updated: {product.name}"))
            except Exception as exc:
                failed += 1
                self.stdout.write(self.style.ERROR(f"Failed: {product.name} -> {exc}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Unsplash sync complete"))
        self.stdout.write(f"Processed: {processed}")
        self.stdout.write(f"Updated: {updated}")
        self.stdout.write(f"Failed: {failed}")

    def _search_unsplash_image(self, query, access_key):
        params = urllib.parse.urlencode(
            {
                "query": query,
                "page": 1,
                "per_page": 1,
                "orientation": "squarish",
                "content_filter": "high",
            }
        )
        url = f"https://api.unsplash.com/search/photos?{params}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Client-ID {access_key}",
                "Accept-Version": "v1",
            },
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))

        results = payload.get("results") or []
        if not results:
            return None

        urls = results[0].get("urls") or {}
        return urls.get("regular") or urls.get("small") or urls.get("thumb")

    def _download_image(self, image_url, output_path):
        req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
        output_path.write_bytes(data)
