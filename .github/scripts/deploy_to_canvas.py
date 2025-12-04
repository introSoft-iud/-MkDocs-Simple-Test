#!/usr/bin/env python3
import os
import re
from canvasapi import Canvas
from bs4 import BeautifulSoup
from pathlib import Path

# Configuración
API_URL = os.environ["CANVAS_URL"]
API_KEY = os.environ["CANVAS_TOKEN"]
COURSE_ID = int(os.environ["CANVAS_COURSE_ID"])

canvas = Canvas(API_URL, API_KEY)
course = canvas.get_course(COURSE_ID)

site_dir = Path("site")
pages_created = 0

# Limpiar páginas antiguas que empiecen con [MkDocs]
print("Eliminando páginas antiguas del sitio MkDocs...")
for page in course.get_pages():
    if page.title.startswith("[MkDocs]"):
        page.delete()
        print(f"  Eliminada: {page.title}")

# Subir todas las páginas del build
for html_file in site_dir.rglob("*.html"):
    rel_path = html_file.relative_to(site_dir)
    url_slug = str(rel_path.parent / html_file.stem).replace("\\", "/")
    if url_slug == "index":  # página de inicio
        url_slug = "inicio-mkdocs"
    
    title = "[MkDocs] " + " → ".join(rel_path.parts[:-1]).replace("index", "Inicio")
    if title == "[MkDocs] ":
        title = "[MkDocs] Inicio"

    with open(html_file, encoding="utf-8") as f:
        body = f.read()

    # Corregir rutas relativas de CSS/JS/imágenes
    soup = BeautifulSoup(body, "html.parser")
    base_url = f"https://{API_URL.split('//')[1]}courses/{COURSE_ID}/file_ref/"
    
    for tag in soup.find_all(["link", "script", "img"]):
        attr = "href" if tag.has_attr("href") else "src"
        if tag.get(attr) and tag[attr] and not tag[attr].startswith(("http", "https", "#")):
            # Para CSS/JS/imágenes, subimos como archivos a Canvas y linkeamos
            # Pero para simplicidad inicial, ajustamos a rutas relativas (puedes expandir esto)
            tag[attr] = tag[attr].lstrip('./')  # Simplificado; para prod, sube assets primero

    body = str(soup)

    # Crear o actualizar la página en Canvas
    try:
        page = course.create_page({
            "title": title,
            "body": body,
            "published": True,
            "front_page": (url_slug == "inicio-mkdocs")
        })
        print(f"  Creada: {title}")
        pages_created += 1
    except Exception as e:
        print(f"  Error en {title}: {e}")
        # Si falla, intenta actualizar si existe
        try:
            existing_page = course.get_page_by_title(title)
            existing_page.update(body=body)
            print(f"  Actualizada: {title}")
        except:
            print(f"  No se pudo crear/actualizar: {title}")

print(f"\n¡Listo! {pages_created} páginas desplegadas en Canvas")
print(f"Ve a: {API_URL}/courses/{COURSE_ID}")