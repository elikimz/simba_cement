from fastapi import APIRouter, Depends
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_async_db
from app.models import Product
from fastapi.responses import Response

router = APIRouter()

@router.get("/sitemap.xml", include_in_schema=False)
async def get_sitemap(db: AsyncSession = Depends(get_async_db)):
    base_url = "https://simba-cement.com"
    
    # Static pages
    static_urls = [
        f"{base_url}/",
        f"{base_url}/cart",
        f"{base_url}/blog",
    ]
    
    # Dynamic product pages
    result = await db.execute(select(Product.id).order_by(Product.created_at.desc()))
    product_ids = result.scalars().all()
    product_urls = [f"{base_url}/product/{pid}" for pid in product_ids]
    
    all_urls = static_urls + product_urls
    
    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url in all_urls:
        sitemap_content += f'    <url>\n'
        sitemap_content += f'        <loc>{url}</loc>\n'
        sitemap_content += f'        <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n'
        sitemap_content += f'        <changefreq>daily</changefreq>\n'
        sitemap_content += f'        <priority>0.8</priority>\n'
        sitemap_content += f'    </url>\n'
    
    sitemap_content += '</urlset>'
    
    return Response(content=sitemap_content, media_type="application/xml")
