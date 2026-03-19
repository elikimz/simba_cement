from fastapi import APIRouter, Depends
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_async_db
from app.models import Product, Category
from fastapi.responses import Response

router = APIRouter()

@router.get("/sitemap.xml", include_in_schema=False)
async def get_sitemap(db: AsyncSession = Depends(get_async_db)):
    base_url = "https://www.simbacementwholesalesdistributor.co.ke"
    
    # Static pages
    static_urls = [
        (f"{base_url}/", "1.0", "weekly"),
        (f"{base_url}/cart", "0.8", "weekly"),
        (f"{base_url}/blog", "0.8", "weekly"),
        (f"{base_url}/contact", "0.8", "monthly"),
    ]
    
    # Dynamic category pages
    result = await db.execute(select(Category.id).order_by(Category.id))
    category_ids = result.scalars().all()
    category_urls = [(f"{base_url}/category/{cid}", "0.9", "weekly") for cid in category_ids]
    
    # Dynamic product pages
    result = await db.execute(select(Product.id).order_by(Product.created_at.desc()))
    product_ids = result.scalars().all()
    product_urls = [(f"{base_url}/product/{pid}", "0.8", "daily") for pid in product_ids]
    
    all_urls = static_urls + category_urls + product_urls
    
    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url, priority, changefreq in all_urls:
        sitemap_content += f'    <url>\n'
        sitemap_content += f'        <loc>{url}</loc>\n'
        sitemap_content += f'        <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n'
        sitemap_content += f'        <changefreq>{changefreq}</changefreq>\n'
        sitemap_content += f'        <priority>{priority}</priority>\n'
        sitemap_content += f'    </url>\n'
    
    sitemap_content += '</urlset>'
    
    return Response(content=sitemap_content, media_type="application/xml")
