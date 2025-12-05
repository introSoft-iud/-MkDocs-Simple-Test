#!/usr/bin/env python3
import os
from canvasapi import Canvas
from bs4 import BeautifulSoup
from pathlib import Path

API_URL = os.environ["CANVAS_URL"]
API_KEY = os.environ["CANVAS_TOKEN"]
COURSE_ID = int(os.environ["CANVAS_COURSE_ID"])

canvas = Canvas(API_URL, API_KEY)
course = canvas.get_course(COURSE_ID)

site_dir = Path("site")
pages_created = 0

print("1. Limpiando páginas antiguas [Docs] (excepto Front Page)...")
for page in course.get_pages():
    if page.title.startswith("[Docs]"):
        if getattr(page, "front_page", False):
            page.edit(wiki_page={"front_page": False})
        page.delete()

print("\n2. Subiendo todas las páginas (incluidas las que están en subcarpetas)...\n")
for html_file in site_dir.rglob("index.html"):  # ← ¡¡Aquí está el truco!!
    rel_path = html_file.relative_to(site_dir).parent  # carpeta relativa
    if rel_path == Path("."):
        url_slug = "inicio-mkdocs"
        title = "[Docs] Inicio"
    else:
        # Ejemplo: carpeta "temario/fisica" → título "[Docs] Temario → Fisica"
        title_parts = [p.capitalize() for p in rel_path.parts]
        title = "[Docs] " + " → ".join(title_parts)
        url_slug = str(rel_path).replace("\\", "/")

    with open(html_file, encoding="utf-8") as f:
        body = f.read()

    soup = BeautifulSoup(body, "html.parser")
    # Corrección mínima de rutas para que CSS/JS/imágenes funcionen
    for tag in soup.find_all(["link", "script", "img", "source"]):
        attr = "href" if tag.has_attr("href") else "src"
        if tag.get(attr) and not tag[attr].startswith(("http", "https", "#", "data:")):
            tag[attr] = "/" + str(rel_path / tag[attr].lstrip("./")).replace("\\", "/")

    body = str(soup)

    try:
        page = course.create_page({
            "title": title,
            "body": body,
            "published": True,
            "url": url_slug,
            "front_page": (url_slug == "inicio-mkdocs")
        })
        print(f"  ✓ {title}  →  /{url_slug}")
        pages_created += 1
    except Exception as e:
        if "already exists" in str(e).lower():
            existing = course.get_page(url_slug)
            existing.edit(wiki_page={"body": body})
            print(f"  ↻ Actualizada: {title}")
        else:
            print(f"  ✗ Error {title}: {e}")

print(f"\n¡Listo! {pages_created} páginas subidas correctamente")
print(f"Ve directo a: {API_URL}/courses/{COURSE_ID}/pages/inicio-mkdocs")