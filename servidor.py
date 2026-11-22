from datetime import datetime
import difflib
import html
import os
import re
import time
from bson import ObjectId
from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)

# Clave secreta necesaria para manejar las sesiones de usuario
app.secret_key = "tu_clave_secreta_super_segura"

CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HORARIO_ATENCION_TEXTO = (
    "🗓️ Horario de atención\n"
    "🌅 Lunes a Viernes: 7:00 a.m. - 9:00 p.m.\n"
    "🎉 Sábados: 8:00 a.m. - 10:00 p.m.\n"
    "🌤️ Domingos: 8:00 a.m. - 9:00 p.m."
)

MENSAJE_FUERA_DE_CAFE = (
    "☕ Lo siento, por ahora solo puedo ayudarte con temas relacionados al café,"
    " nuestras bebidas, platillos o información de Aroma & Café."
)

CATALOGO_GALERIA_OFICIAL = [
    (
        "Pastel de chocolate: Suave y esponjoso pastel elaborado con chocolate"
        " de alta calidad. Una deliciosa porción de pastel con un intenso"
        " sabor a chocolate que complementa cualquier café.",
        "pa.jpg",
    ),
    (
        "Baguette: Pan crujiente relleno de ingredientes frescos. Preparado"
        " diariamente con ingredientes seleccionados para garantizar el mejor"
        " sabor crujiente.",
        "ba.jpg",
    ),
    (
        "Croissant de Jamón y Queso: Pan hojaldrado con mantequilla, relleno"
        " de jamón de pavo y queso gouda derretido. Una opción calientita,"
        " hojaldrada y crujiente ideal para el desayuno o la tarde.",
        "croissant.jpg",
    ),
    (
        "Panini de Pollo al Pesto: Pechuga de pollo a la plancha, queso"
        " mozzarella, jitomate deshidratado y pesto en ciabatta. Tostado a la"
        " perfección con un toque aromático de albahaca y aceite de oliva.",
        "panini.jpg",
    ),
    (
        "Bagel de Salmón: Bagel de ajonjolí con queso crema a las finas"
        " hierbas, salmón ahumado y pepino. Frescura y elegancia en cada"
        " mordisco con finas láminas de salmón de alta calidad.",
        "bagel.jpg",
    ),
    (
        "Club Sandwich Clásico: Tres capas con pavo, tocino crujiente, queso"
        " americano, lechuga, jitomate y papas. El sándwich tradicional por"
        " excelencia, abundante y acompañado de papas crujientes.",
        "club.jpg",
    ),
    (
        "Toast de Aguacate: Pan de masa madre, puré de aguacate, pepitas,"
        " chile en hojuelas y dos huevos pochados. Nutritivo, moderno y"
        " delicioso, coronado con huevos pochados preparados al momento.",
        "toast.jpg",
    ),
    (
        "Chilaquiles con Pollo: Totopos bañados en salsa verde o roja, pollo"
        " deshebrado, crema y queso fresco. El toque mexicano reconfortante que"
        " nunca falla para empezar el día con energía.",
        "chilaquiles.jpg",
    ),
    (
        "Ensalada César con Pollo: Lechuga romana, tiras de pollo a la"
        " parrilla, crotones de ajo y aderezo César cremoso. Una opción"
        " ligera, fresca y crujiente con pechuga de pollo asada al momento.",
        "ensalada.jpg",
    ),
    (
        "Waffles con Frutos Rojos: Waffle dorado por fuera y suave por dentro,"
        " servido con fresas, zarzamoras y miel. Dulces, esponjosos y"
        " acompañados de una colorida selección de frutos rojos frescos.",
        "waffle.jpg",
    ),
    (
        "Café Espresso: Café intenso y aromático preparado con granos"
        " seleccionados. Una taza de espresso recién preparado, con un sabor"
        " fuerte y un aroma que despierta los sentidos.",
        "exp.jpg",
    ),
    (
        "Capuchino clásico: Deliciosa combinación de espresso, leche"
        " vaporizada y espuma cremosa. Nuestro capuchino destaca por su cremosa"
        " espuma y el equilibrio perfecto entre café y leche.",
        "capu.jpg",
    ),
    (
        "Chocomilk: Bebida dulce y refrescante elaborada con leche y"
        " chocolate. Ideal para quienes prefieren una bebida suave y dulce,"
        " perfecta para cualquier momento del día.",
        "choco.jpg",
    ),
    (
        "Latte de Vainilla o Caramelo: Espresso combinado con leche caliente"
        " vaporizada y jarabe suave de vainilla o caramelo. Una caricia dulce y"
        " reconfortante para acompañar tus tardes.",
        "latte.jpg",
    ),
    (
        "Chai Tea Latte: Té negro concentrado con especias aromáticas (canela,"
        " cardamomo, jengibre) y leche. Exóticas especias orientales"
        " perfectamente integradas con una textura cremosa.",
        "chai.jpg",
    ),
    (
        "Iced Caramel Macchiato: Leche fría con hielo, vainilla, coronada con"
        " shot de espresso y espiral de caramelo. Refrescante, dulce y con el"
        " balance exacto de cafeína fría.",
        "iced.jpg",
    ),
    (
        "Matcha Latte Helado: Té matcha ceremonial batido con leche de tu"
        " elección, hielo y endulzante natural. Todo el poder antioxidante del"
        " té verde japonés en una presentación fría y cremosa.",
        "matcha.jpg",
    ),
    (
        "Frappuccino Moka: Bebida helada a punto de granizado con espresso,"
        " leche, chocolate, hielo y crema batida. Un frappé indulgente y"
        " cremoso con notas intensas de chocolate y café.",
        "frappe.jpg",
    ),
    (
        "Smoothie de Frutos Rojos: Licuado denso de fresas, moras y arándanos"
        " congelados mezclados con yogur griego. Una explosión frutal, cremosa"
        " y llena de frescura natural.",
        "smoothie.jpg",
    ),
    (
        "Tisana Frutal Fría: Infusión refrescante de frutas deshidratadas"
        " (frutos del bosque y jamaica) con hielo. Libre de cafeína, frutal,"
        " colorida y sumamente refrescante.",
        "tisana.jpg",
    ),
]

MAPA_IMAGENES_GALERIA = {
    "pastel de chocolate": "pa.jpg",
    "baguette": "ba.jpg",
    "croissant de jamón y queso": "croissant.jpg",
    "panini de pollo al pesto": "panini.jpg",
    "bagel de salmón": "bagel.jpg",
    "club sandwich clásico": "club.jpg",
    "toast de aguacate": "toast.jpg",
    "chilaquiles con pollo": "chilaquiles.jpg",
    "ensalada césar con pollo": "ensalada.jpg",
    "waffles con frutos rojos": "waffle.jpg",
    "café espresso": "exp.jpg",
    "capuchino clásico": "capu.jpg",
    "chocomilk": "choco.jpg",
    "latte de vainilla o caramelo": "latte.jpg",
    "chai tea latte": "chai.jpg",
    "iced caramel macchiato": "iced.jpg",
    "matcha latte helado": "matcha.jpg",
    "frappuccino moka": "frappe.jpg",
    "smoothie de frutos rojos": "smoothie.jpg",
    "tisana frutal fría": "tisana.jpg",
}


# --- CONEXIÓN A MONGODB ATLAS ---
client_db = MongoClient(
    "mongodb://jfcharliee1125_db_user:bqt3ve2VARr-PjN@ac-fswlmxg-shard-00-00.yxxfzf9.mongodb.net:27017,ac-fswlmxg-shard-00-01.yxxfzf9.mongodb.net:27017,ac-fswlmxg-shard-00-02.yxxfzf9.mongodb.net:27017/aroma_cafe?ssl=true&replicaSet=atlas-7rnzw2-shard-0&authSource=admin&retryWrites=true&w=majority"
)
db = client_db["aroma_cafe"]
coleccion_pedidos = db["pedidos"]
coleccion_comentarios = db["comentarios"]
coleccion_promociones = db["promociones"]


# --- CACHÉ DE SITIO ---
_cache_sitio = {"texto": "", "timestamp": 0}


def quitar_palabra_agregar(texto):
  if not texto:
    return ""
  limpio = re.sub(r"\bagregar\b", "", texto, flags=re.I)
  limpio = re.sub(r"\s{2,}", " ", limpio).strip(" -–:|·")
  return limpio.strip()


def _ruta_archivo(*partes):
  return os.path.join(BASE_DIR, *partes)


def extraer_texto_html(ruta_archivo):
  try:
    ruta_real = (
        ruta_archivo
        if os.path.isabs(ruta_archivo)
        else _ruta_archivo(ruta_archivo)
    )
    if not os.path.exists(ruta_real):
      return ""
    with open(ruta_real, "r", encoding="utf-8") as f:
      contenido = f.read()
    contenido = re.sub(
        r"<(script|style|nav|footer).*?>.*?</\1>",
        "",
        contenido,
        flags=re.S | re.I,
    )
    contenido = re.sub(
        r"</?(p|div|section|article|h[1-6]|li|tr|br|hr|button)[^>]*>",
        "\n",
        contenido,
        flags=re.I,
    )
    texto = re.sub(r"<[^>]+>", " ", contenido)
    texto = html.unescape(texto)

    lineas_limpias = []
    ruido_nav = (
        "Inicio Nosotros Menú Galería Servicios Contacto Carrito Iniciar Sesión"
    )
    frases_estado_ignorar = (
        "cafetería cerrada en este momento",
        "los pedidos se encuentran temporalmente deshabilitados",
        "verificando horario",
    )
    for linea in texto.splitlines():
      limpia = quitar_palabra_agregar(re.sub(r"\s+", " ", linea).strip())
      if not limpia or len(limpia) < 2:
        continue
      if limpia == ruido_nav:
        continue
      if any(f in limpia.lower() for f in frases_estado_ignorar):
        continue
      lineas_limpias.append(limpia)

    return "\n".join(lineas_limpias)
  except Exception:
    return ""


def _es_ruido_producto(texto_linea):
  baja = quitar_palabra_agregar(texto_linea).lower().strip()
  if not baja:
    return True
  palabras_ruido = {
      "aroma & café | menú",
      "preparados para ti",
      "nuestro menú",
      (
          "explora nuestras categorías, elige tus especialidades y agrégalas al"
          " carrito (máximo 20 artículos en total)."
      ),
      "añadir",
      "carrito",
      "ordenar",
      "ver más",
      "ver mas",
  }
  if baja in palabras_ruido:
    return True
  if re.fullmatch(
      r"[\W_]*(añadir|carrito|ordenar)[\W_]*", baja, flags=re.I
  ):
    return True
  if baja.startswith("🔴") or baja.startswith("🍽️") or baja.startswith("☕"):
    if len(baja) < 25 and ("menú" in baja or "categoría" in baja):
      return True
  return False


def _clasificar_categoria_producto(nombre, descripcion, categoria_actual):
  texto = f"{nombre} {descripcion}".lower()

  palabras_platillo = [
      "pastel",
      "rebanada",
      "croissant",
      "bagel",
      "baguette",
      "ciabatta",
      "chapata",
      "sándwich",
      "sandwich",
      "panini",
      "toast",
      "torta",
      "chilaquiles",
      "ensalada",
      "waffle",
      "waffles",
      "hotcake",
      "hot cake",
      "galleta",
      "brownie",
      "cheesecake",
      "pay",
      "pie",
      "platillo",
      "platillos",
      "postre",
      "mollete",
      "crepa",
      "taco",
      "bowl",
  ]
  if any(p in texto for p in palabras_platillo):
    return "platillo"

  palabras_bebida = [
      "café",
      "cafe",
      "latte",
      "capuchino",
      "cappuccino",
      "americano",
      "espresso",
      "expreso",
      "moka",
      "mocha",
      "macchiato",
      "frappuccino",
      "frappé",
      "frappe",
      "smoothie",
      "tisana",
      "chocomilk",
      "té",
      "te ",
      "matcha",
      "chocolate caliente",
      "jugo",
      "limonada",
      "malteada",
      "bebida",
      "bebidas",
      "cold brew",
      "chai",
      "agua",
      "refresco",
      "infusión",
      "infusion",
  ]
  if any(p in texto for p in palabras_bebida):
    return "bebida"

  return categoria_actual or "platillo"


def _emoji_por_producto(nombre, descripcion, tipo, indice):
  t = f"{nombre} {descripcion}".lower()
  if tipo == "platillo":
    if "pastel" in t or "chocolate" in t or "brownie" in t:
      return "🍫"
    if "baguette" in t or "pan" in t or "ciabatta" in t:
      return "🥖"
    if "croissant" in t:
      return "🥐"
    if "panini" in t or "sandwich" in t or "sándwich" in t:
      return "🥪"
    if "bagel" in t:
      return "🥯"
    if "aguacate" in t or "toast" in t:
      return "🥑"
    if "chilaquiles" in t or "taco" in t:
      return "🌮"
    if "ensalada" in t:
      return "🥗"
    if "waffle" in t or "hotcake" in t:
      return "🧇"
    varios_plat = ["🍽️", "🧁", "🥧", "🥞", "🥙"]
    return varios_plat[indice % len(varios_plat)]
  else:
    if "frappuccino" in t or "frappé" in t or "frappe" in t or "helado" in t:
      return "🧊"
    if "matcha" in t or "té" in t or "chai" in t or "tisana" in t:
      return "🍵"
    if "smoothie" in t or "frutos rojos" in t or "jugo" in t:
      return "🍓"
    if "chocomilk" in t or "moka" in t or "mocha" in t:
      return "🥛"
    if "macchiato" in t or "caramel" in t:
      return "🍯"
    varios_beb = ["☕", "🫖", "🥤", "🧋", "🫗"]
    return varios_beb[indice % len(varios_beb)]


def extraer_productos_separados(limite_total=20):
  texto_menu = extraer_texto_html("templates/menu.html")
  if not texto_menu:
    return {"platillos": [], "bebidas": []}

  lineas = [l.strip() for l in texto_menu.splitlines() if l.strip()]
  platillos = []
  bebidas = []
  categoria_seccion = None
  candidatos_texto = []
  ultima_desc = ""

  for linea in lineas:
    linea = quitar_palabra_agregar(linea)
    if not linea:
      continue
    baja = linea.lower()

    if "bebida" in baja and len(baja) <= 35 and "$" not in baja:
      categoria_seccion = "bebida"
      continue
    if (
        any(k in baja for k in ["platillo", "alimento", "comida", "postre"])
        and len(baja) <= 35
        and "$" not in baja
    ):
      categoria_seccion = "platillo"
      continue

    if _es_ruido_producto(linea):
      continue

    precio_match = re.search(
        r"\$\s*\d+(?:[.,]\d+)?\s*(?:mxn)?", linea, flags=re.I
    )
    if precio_match:
      precio_txt = re.sub(r"\s+", " ", precio_match.group(0)).strip().upper()
      if "MXN" not in precio_txt:
        precio_txt = f"{precio_txt} MXN"

      antes_precio = quitar_palabra_agregar(
          linea[: precio_match.start()].strip(" -–:|·")
      )
      nombre_prod = ""
      if antes_precio and not _es_ruido_producto(antes_precio):
        nombre_prod = antes_precio
      else:
        for cand in reversed(candidatos_texto):
          cand_limpio = quitar_palabra_agregar(cand)
          if cand_limpio and not re.match(
              r"^descripci[oó]n\s*:", cand_limpio, flags=re.I
          ):
            nombre_prod = cand_limpio
            break

      if nombre_prod and not _es_ruido_producto(nombre_prod):
        desc_limpia = quitar_palabra_agregar(
            re.sub(r"^descripci[oó]n\s*:\s*", "", ultima_desc, flags=re.I)
        )
        tipo = _clasificar_categoria_producto(
            nombre_prod, desc_limpia, categoria_seccion
        )
        item = {
            "nombre": nombre_prod,
            "precio": precio_txt,
            "descripcion": desc_limpia,
            "tipo": tipo,
        }
        total_actual = len(platillos) + len(bebidas)
        if total_actual < limite_total:
          if tipo == "bebida":
            bebidas.append(item)
          else:
            platillos.append(item)

      candidatos_texto = []
      ultima_desc = ""
      if (len(platillos) + len(bebidas)) >= limite_total:
        break
      continue

    if re.match(r"^descripci[oó]n\s*:", linea, flags=re.I):
      ultima_desc = linea
    else:
      candidatos_texto.append(linea)

  return {"platillos": platillos, "bebidas": bebidas}


def _formatear_lista_vertical(items, tipo):
  lineas = []
  for idx, prod in enumerate(items):
    nombre = quitar_palabra_agregar(prod["nombre"])
    desc = quitar_palabra_agregar(prod.get("descripcion", ""))
    em = _emoji_por_producto(nombre, desc, tipo, idx)
    item_txt = f"{em} {nombre} — {prod['precio']}"
    if desc:
      item_txt += f": {desc}"
    lineas.append(item_txt)
  return "\n".join(lineas)


def formatear_solo_platillos(platillos):
  if not platillos:
    return "🍽️ Platillos\n✨ No hay platillos registrados por el momento."
  return f"🍽️ Platillos\n{_formatear_lista_vertical(platillos, 'platillo')}"


def formatear_solo_bebidas(bebidas):
  if not bebidas:
    return "🥤 Bebidas\n✨ No hay bebidas registradas por el momento."
  return f"🥤 Bebidas\n{_formatear_lista_vertical(bebidas, 'bebida')}"


def formatear_productos_general(datos_prod):
  platillos = datos_prod.get("platillos", [])
  bebidas = datos_prod.get("bebidas", [])

  bloque_platillos = (
      _formatear_lista_vertical(platillos, "platillo")
      if platillos
      else "✨ Sin platillos registrados."
  )
  bloque_bebidas = (
      _formatear_lista_vertical(bebidas, "bebida")
      if bebidas
      else "✨ Sin bebidas registradas."
  )

  return f"🍽️ Platillos\n{bloque_platillos}\n\n\n🥤 Bebidas\n{bloque_bebidas}"


def _normalizar_leetspeak(texto):
  tabla = str.maketrans({
      "0": "o",
      "1": "i",
      "3": "e",
      "4": "a",
      "5": "s",
      "7": "t",
      "@": "a",
  })
  return texto.translate(tabla)


def _es_consulta_sobre_cafe(texto_norm):
  palabras_cafe = [
      "cafe",
      "café",
      "cafetera",
      "cafeteras",
      "cafeteria",
      "cafetería",
      "espresso",
      "expreso",
      "capuchino",
      "cappuccino",
      "latte",
      "americano",
      "moka",
      "mocha",
      "macchiato",
      "frappuccino",
      "frappe",
      "frappé",
      "grano",
      "granos",
      "tostado",
      "molido",
      "barista",
      "aroma",
      "creo el cafe",
      "creó el café",
      "descubrio el cafe",
      "descubrió el café",
      "invento la cafetera",
      "inventó la cafetera",
      "historia del cafe",
      "historia del café",
      "kaldi",
      "arabica",
      "arábica",
      "robusta",
      "cafeina",
      "cafeína",
  ]
  return any(p in texto_norm for p in palabras_cafe)


def _extraer_archivo_static(src_raw, nombre_prod=""):
  limpio = html.unescape(str(src_raw or "")).strip()
  m_fn = re.search(
      r"""filename\s*=\s*['"]([^'"]+)['"]""", limpio, flags=re.I
  )
  if m_fn:
    arch = m_fn.group(1).strip().strip("/")
    if arch and not arch.startswith("{"):
      return arch

  m_ext = re.search(
      r"""([a-zA-Z0-9_-]+\.(?:jpg|jpeg|png|webp|gif))""",
      limpio,
      flags=re.I,
  )
  if m_ext:
    return m_ext.group(1).strip()

  clave_prod = re.sub(r"\s+", " ", (nombre_prod or "").lower()).strip()
  if clave_prod in MAPA_IMAGENES_GALERIA:
    return MAPA_IMAGENES_GALERIA[clave_prod]

  return ""


def obtener_galeria_con_imagenes(limite=20):
  candidatos_html = [
      _ruta_archivo("templates", "galeria.html"),
      _ruta_archivo("galeria.html"),
  ]
  items = []
  emojis = [
      "🍫",
      "🥖",
      "🥐",
      "🥪",
      "🥯",
      "🍔",
      "🥑",
      "🌮",
      "🥗",
      "🧇",
      "☕",
      "🫖",
      "🥛",
      "🍯",
      "🍵",
      "🧊",
      "🍓",
      "🍹",
      "🧁",
      "🥤",
  ]

  ruta_gal = next((p for p in candidatos_html if os.path.exists(p)), None)

  if ruta_gal:
    with open(ruta_gal, "r", encoding="utf-8") as f:
      html_gal = f.read()

    for m_li in re.finditer(
        r"<li[^>]*>(.*?)</li>", html_gal, flags=re.S | re.I
    ):
      inicio_siguiente = len(html_gal)
      m_next = re.search(
          r"(?:<li[^>]*>|</ul>)", html_gal[m_li.end() :], flags=re.I
      )
      if m_next:
        inicio_siguiente = m_li.end() + m_next.start()

      fragmento_despues = html_gal[m_li.end() : inicio_siguiente]
      img_m = re.search(
          r'<img[^>]+src=["\']([^"\']+)["\']', fragmento_despues, flags=re.I
      )
      if not img_m:
        continue

      texto_li = quitar_palabra_agregar(
          re.sub(
              r"\s+",
              " ",
              html.unescape(re.sub(r"<[^>]+>", " ", m_li.group(1))),
          ).strip()
      )
      if ":" in texto_li:
        partes_li = texto_li.split(":", 1)
        nombre_prod = partes_li[0].strip()
        desc_corta = partes_li[1].strip()
      else:
        nombre_prod = texto_li
        desc_corta = ""

      p_m = re.search(
          r"<p[^>]*>(.*?)</p>", fragmento_despues, flags=re.S | re.I
      )
      desc_extra = ""
      if p_m:
        desc_extra = quitar_palabra_agregar(
            re.sub(
                r"\s+",
                " ",
                html.unescape(re.sub(r"<[^>]+>", " ", p_m.group(1))),
            ).strip()
        )

      descripciones = []
      if desc_corta:
        descripciones.append(desc_corta)
      if (
          desc_extra
          and desc_extra.lower() not in " ".join(descripciones).lower()
      ):
        descripciones.append(desc_extra)

      texto_item = (
          f"{nombre_prod}: {' '.join(descripciones)}"
          if descripciones
          else nombre_prod
      )
      if not texto_item:
        continue

      nombre_arch = _extraer_archivo_static(img_m.group(1), nombre_prod)
      if not nombre_arch:
        continue

      items.append((texto_item, f"/static/{nombre_arch}"))
      if len(items) >= limite:
        break

  if not items:
    for desc_item, nombre_arch in CATALOGO_GALERIA_OFICIAL[:limite]:
      items.append((desc_item, f"/static/{nombre_arch}"))

  salida = [
      "📷 Galería Fotográfica",
      (
          "✨ Descubre a través de nuestra galería el sabor y la calidad de cada"
          " una de nuestras especialidades:"
      ),
  ]
  for i, (desc_item, ruta_img) in enumerate(items):
    em = emojis[i % len(emojis)]
    salida.append(f"{em} {desc_item}")
    salida.append(f"[IMG: {ruta_img}]")
  return "\n".join(salida)


def formatear_lineas_en_lista(texto_html, max_lineas=8, emojis=None):
  emojis = emojis or ["📌", "✨", "🌿", "⭐", "🎯", "💡", "🔖", "🗂️"]
  lineas = [
      quitar_palabra_agregar(l.strip())
      for l in (texto_html or "").splitlines()
      if len(quitar_palabra_agregar(l.strip())) > 2
  ]
  seleccion = lineas[:max_lineas]
  if not seleccion:
    return ""
  return "\n".join(
      f"{emojis[i % len(emojis)]} {item}" for i, item in enumerate(seleccion)
  )


def obtener_contexto_sitio():
  ahora = time.time()
  if _cache_sitio["texto"] and (ahora - _cache_sitio["timestamp"] < 300):
    return _cache_sitio["texto"]

  archivos = [
      "templates/index.html",
      "templates/nosotros.html",
      "templates/menu.html",
      "templates/galeria.html",
      "templates/servicios.html",
      "templates/contacto.html",
  ]
  partes = []
  for archivo in archivos:
    txt = extraer_texto_html(archivo)
    if txt:
      partes.append(f"[{archivo}]:\n{txt[:1400]}")

  resultado = "\n\n".join(partes)
  _cache_sitio["texto"] = resultado
  _cache_sitio["timestamp"] = ahora
  return resultado


def obtener_contexto_promociones():
  try:
    hoy = datetime.now().strftime("%Y-%m-%d")
    promos = list(coleccion_promociones.find({}, {"_id": False}))
    activas = []
    emojis_p = ["⚡", "🎁", "🏷️", "💥", "🌟"]
    for i, p in enumerate(promos):
      f_ini = str(p.get("fechaInicio", ""))
      f_fin = str(p.get("fechaFin", ""))
      if (not f_ini or hoy >= f_ini) and (not f_fin or hoy <= f_fin):
        titulo = quitar_palabra_agregar(p.get("titulo", "Promoción"))
        precio = p.get("precio", "")
        sub = quitar_palabra_agregar(
            p.get("subtitulo") or p.get("etiqueta") or ""
        )
        em = emojis_p[i % len(emojis_p)]
        detalle = f"{em} {titulo}"
        if precio != "":
          detalle += f" — ${precio} MXN"
        if sub:
          detalle += f" ({sub})"
        activas.append(detalle)
    if activas:
      return "🎁 Promociones activas hoy\n" + "\n".join(activas)
    return (
        "🎁 Promociones activas hoy\n💤 Por el momento no hay promociones"
        " nuevas registradas para hoy."
    )
  except Exception as e:
    print("[AVISO PROMOS]:", e)
    return "🎁 Promociones activas hoy\n⚠️ No disponibles en este momento."


def limpiar_markdown_basico(texto):
  texto = quitar_palabra_agregar(texto)
  texto = re.sub(r"<br\s*/?>", "\n", texto, flags=re.I)
  texto = re.sub(r"\*+", "", texto)
  texto = re.sub(r"^#+\s*", "", texto, flags=re.M)
  texto = re.sub(r"-{3,}", "", texto)
  texto = re.sub(r"\n{3,}", "\n\n", texto)
  return texto.strip()


def es_consulta_mejores_productos(texto_norm):
  if "mejor" in texto_norm or "mejores" in texto_norm:
    if any(
        w in texto_norm
        for w in [
            "producto",
            "productos",
            "platillo",
            "platillos",
            "bebida",
            "bebidas",
            "cafe",
            "café",
            "menu",
            "menú",
            "recomienda",
            "recomiendan",
        ]
    ):
      return True
  return any(
      f in texto_norm
      for f in [
          "que me recomiendas",
          "qué me recomiendas",
          "que recomiendan",
          "qué recomiendan",
          "lo mas pedido",
          "lo más pedido",
          "estrella de la casa",
      ]
  )


def corregir_palabras_clave_con_typo(texto_norm):
  texto_leet = _normalizar_leetspeak(texto_norm)
  palabras_clave = [
      "menu",
      "producto",
      "productos",
      "platillo",
      "platillos",
      "bebida",
      "bebidas",
      "galeria",
      "fotos",
      "promocion",
      "promociones",
      "oferta",
      "ofertas",
      "descuento",
      "descuentos",
      "pago",
      "pagos",
      "tarjeta",
      "transferencia",
      "efectivo",
      "servicio",
      "servicios",
      "informes",
      "eventos",
      "entrega",
      "entregas",
      "envio",
      "envios",
      "domicilio",
      "delivery",
      "pickup",
      "pedido",
      "pedidos",
      "nosotros",
      "contacto",
      "telefono",
      "correo",
      "ubicacion",
      "direccion",
      "horario",
      "horarios",
      "hola",
      "buenas",
  ]
  tokens = texto_leet.split()
  corregidos = []
  for tok in tokens:
    if tok in palabras_clave:
      corregidos.append(tok)
      continue
    if len(tok) >= 3:
      coincidencias = difflib.get_close_matches(
          tok, palabras_clave, n=1, cutoff=0.72
      )
      if coincidencias:
        corregidos.append(coincidencias[0])
        continue
    corregidos.append(tok)
  return " ".join(corregidos)


def contiene_saludo(texto_norm):
  patrones_saludo = [
      r"\bhola\b",
      r"\bhoa\b",
      r"\bbuenas\b",
      r"\bbuenos dias\b",
      r"\bbuenos días\b",
      r"\bbuenas tardes\b",
      r"\bbuenas noches\b",
      r"\bhey\b",
      r"\bque tal\b",
      r"\bqué tal\b",
      r"\bholi\b",
  ]
  return any(re.search(p, texto_norm) for p in patrones_saludo)


def responder_rapido_de_pagina(mensaje):
  t_crudo = re.sub(r"[^\w\sáéíóúñ]", "", mensaje.lower().strip())
  t_crudo = re.sub(r"\s+", " ", t_crudo)
  t_leet = _normalizar_leetspeak(t_crudo)

  if not t_leet:
    return "💬 Escribe un mensaje para ayudarte."

  if re.fullmatch(r"[a-z0-9]{1,2}", t_leet) and t_leet not in {"menu"}:
    return "❓ Mensaje no válido."

  t = corregir_palabras_clave_con_typo(t_leet)

  if es_consulta_mejores_productos(t):
    datos_prod = extraer_productos_separados(limite_total=20)
    if datos_prod.get("platillos") or datos_prod.get("bebidas"):
      return (
          "🌟 Especialidades y menú de Aroma & Café\n"
          f"{formatear_productos_general(datos_prod)}"
      )
    return (
        "🌟 Especialidades de Aroma & Café\n"
        "☕ Capuchino clásico, Latte de Vainilla o Caramelo y Frappuccino Moka\n"
        "🥐 Croissant de Jamón y Queso, Toast de Aguacate y Pastel de"
        " chocolate"
    )

  # 1) Horarios
  if any(
      k in t
      for k in [
          "horario",
          "horarios",
          "abren",
          "cierran",
          "a que hora",
          "a qué hora",
          "hora de atencion",
          "hora de atención",
      ]
  ):
    return HORARIO_ATENCION_TEXTO

  # 2) Ubicación
  if any(
      k in t
      for k in [
          "ubicacion",
          "ubicación",
          "donde estan",
          "dónde están",
          "direccion",
          "dirección",
      ]
  ):
    return (
        "🗺️ Ubicación\n"
        "🏛️ Av. de los Aromas #125, Colonia Café Dorado, Ciudad del Sabor,"
        " México."
    )

  # 3) Contacto
  if any(
      k in t
      for k in [
          "contacto",
          "telefono",
          "teléfono",
          "correo",
          "instagram",
          "redes",
      ]
  ):
    return (
        "☎️ Contacto\n"
        "📱 Teléfono: (555) 789-4521\n"
        "✉️ Correo: contacto@aromaycafe.com\n"
        "📸 Redes sociales: Página de Instagram"
    )

  # 4) Métodos de pago
  if any(
      k in t
      for k in [
          "metodo de pago",
          "método de pago",
          "metodos de pago",
          "métodos de pago",
          "como pagar",
          "cómo pagar",
          "pagar con tarjeta",
          "tarjeta",
          "transferencia",
          "efectivo",
          "forma de pago",
          "formas de pago",
          "pago",
          "pagos",
      ]
  ):
    return (
        "🏦 Métodos de pago\n"
        "💵 Efectivo (en tienda o al recibir tu pedido)\n"
        "💳 Tarjeta de débito y crédito\n"
        "🔄 Transferencia bancaria\n"
        "🛒 Elige tu opción al confirmar tu orden en Carrito."
    )

  # 5) Servicios e Informes
  if any(
      k in t
      for k in [
          "pickup",
          "pick up",
          "delivery",
          "domicilio",
          "entrega",
          "entregas",
          "envio",
          "envío",
          "envios",
          "envíos",
          "servicio",
          "servicios",
          "informes",
          "evento",
          "eventos",
          "pedido",
          "pedidos",
          "carrito",
      ]
  ):
    return (
        "🛎️ Servicios e Informes\n"
        "🛋️ Consumo en Local: Espacio cálido, música ambiental, Wi-Fi gratuito"
        " y atención para trabajar, leer o charlar.\n"
        "🛵 Pedidos a Domicilio / Para Llevar (Informes):\n"
        "🏃 Pick-up: Ordena en línea y pasa a recoger sin filas.\n"
        "📦 A domicilio: Radio de 5 km alrededor de la sucursal, entrega"
        " estimada de 30 a 45 minutos y empaque térmico.\n"
        "📞 Teléfono: (555) 789-4521\n"
        "🥂 Eventos Privados (Informes):\n"
        "🎶 Espacio exclusivo, catering con barista en vivo y equipo de"
        " sonido/proyector.\n"
        "👥 10 a 15 personas: $2,500 MXN (3 hrs, barra libre"
        " espresso/capuchino y charola de postres).\n"
        "👥 16 a 25 personas: $4,200 MXN (4 hrs, barra de bebidas, postres y"
        " mini baguettes gourmet).\n"
        "👥 26 a 35 personas: $6,500 MXN (4 hrs, cierre parcial, baristas en"
        " vivo, menú completo y sonido).\n"
        "📩 Informes: contacto@aromaycafe.com o (555) 789-4521"
    )

  # 6) Promociones
  if any(
      k in t
      for k in [
          "promo",
          "promocion",
          "promoción",
          "promociones",
          "oferta",
          "ofertas",
          "descuento",
          "descuentos",
      ]
  ):
    return obtener_contexto_promociones()

  # 7) Galería
  if any(k in t for k in ["galeria", "galería", "fotos", "fotografias"]):
    return obtener_galeria_con_imagenes(limite=20)

  # 8) Bebidas / Platillos / Productos en general
  pide_bebidas = any(k in t for k in ["bebida", "bebidas"])
  pide_platillos = any(k in t for k in ["platillo", "platillos"])
  pide_general_menu = any(
      k in t
      for k in [
          "producto",
          "productos",
          "menu",
          "menú",
          "carta",
          "precio",
          "precios",
          "cuanto cuesta",
          "cuánto cuesta",
          "que venden",
          "qué venden",
          "que hay",
          "qué hay",
      ]
  )

  if pide_bebidas and not pide_platillos and not pide_general_menu:
    datos_prod = extraer_productos_separados(limite_total=20)
    return formatear_solo_bebidas(datos_prod.get("bebidas", []))

  if pide_platillos and not pide_bebidas and not pide_general_menu:
    datos_prod = extraer_productos_separados(limite_total=20)
    return formatear_solo_platillos(datos_prod.get("platillos", []))

  if pide_general_menu or (pide_bebidas and pide_platillos):
    datos_prod = extraer_productos_separados(limite_total=20)
    if datos_prod.get("platillos") or datos_prod.get("bebidas"):
      return formatear_productos_general(datos_prod)
    ctx_menu = extraer_texto_html("templates/menu.html")
    lista_menu = formatear_lineas_en_lista(
        ctx_menu,
        max_lineas=20,
        emojis=["🥐", "☕", "🥪", "🍵", "🍰"],
    )
    if lista_menu:
      return f"📋 Menú\n{lista_menu}"
    return "📖 Consulta nuestro menú completo en la sección Menú."

  # 9) Nosotros
  if any(
      k in t
      for k in [
          "quienes somos",
          "quiénes somos",
          "nosotros",
          "acerca de",
          "historia de la cafeteria",
          "historia de la cafetería",
      ]
  ):
    ctx_nos = extraer_texto_html("templates/nosotros.html")
    lista_nos = formatear_lineas_en_lista(
        ctx_nos,
        max_lineas=7,
        emojis=["🌱", "🤎", "🔥", "✨", "🏡", "🤝", "☕"],
    )
    if lista_nos:
      return f"🌱 Nosotros\n{lista_nos}"
    return "🏡 Conoce más sobre nosotros en la sección Nosotros."

  # 10) Saludos
  if contiene_saludo(t):
    return (
        "👋 ¡Hola! Bienvenido a Aroma & Café\n"
        "📋 Menú (Platillos y Bebidas)\n"
        "🌟 Mejores productos\n"
        "🎁 Promociones activas\n"
        "🏦 Métodos de pago\n"
        "🛎️ Servicios e informes\n"
        "📷 Galería\n"
        "🗺️ Ubicación, ☎️ contacto y 🗓️ horarios"
    )

  return None


# --- RUTAS PARA LAS VISTAS HTML PRINCIPALES ---


@app.route("/")
@app.route("/index.html")
def inicio():
  return render_template("index.html")


@app.route("/menu")
@app.route("/menu.html")
def menu():
  return render_template("menu.html")


@app.route("/ordenar")
@app.route("/ordenar.html")
def ordenar():
  return render_template("ordenar.html")


@app.route("/admin")
@app.route("/admin.html")
def admin():
  return render_template("admin.html")


@app.route("/contacto")
@app.route("/contacto.html")
def contacto():
  return render_template("contacto.html")


@app.route("/servicios")
@app.route("/servicios.html")
def servicios():
  return render_template("servicios.html")


@app.route("/galeria")
@app.route("/galeria.html")
def galeria():
  return render_template("galeria.html")


@app.route("/nosotros")
@app.route("/nosotros.html")
def nosotros():
  return render_template("nosotros.html")


@app.route("/ia")
def ia():
  return render_template("ia.html")


# --- RUTA PARA EL CHATBOT (RESPUESTAS MANUALES) ---


@app.route("/api/chat", methods=["POST"])
def chat():
  datos = request.get_json(silent=True) or {}
  mensaje_usuario = str(datos.get("mensaje", "")).strip()

  if not mensaje_usuario:
    return (
        jsonify({"respuesta": "💬 Escribe un mensaje para ayudarte."}),
        200,
    )

  respuesta_pagina = responder_rapido_de_pagina(mensaje_usuario)
  if respuesta_pagina:
    return (
        jsonify({"respuesta": limpiar_markdown_basico(respuesta_pagina)}),
        200,
    )

  t_norm = _normalizar_leetspeak(
      re.sub(
          r"\s+",
          " ",
          re.sub(r"[^\w\sáéíóúñ]", "", mensaje_usuario.lower().strip()),
      )
  )

  if _es_consulta_sobre_cafe(t_norm):
    respuesta_cafe = (
        "☕ Cultura y café en Aroma & Café\n"
        "🌱 Preparamos nuestras bebidas con granos seleccionados y recetas"
        " cuidadas en cada taza.\n"
        "📋 Escribe Menú, Platillos, Bebidas, Galería, Promociones,"
        " Servicios, Métodos de pago, Ubicación, Contacto o Horarios para ver"
        " los detalles."
    )
    return jsonify({"respuesta": limpiar_markdown_basico(respuesta_cafe)}), 200

  return jsonify({"respuesta": MENSAJE_FUERA_DE_CAFE}), 200


# --- RUTA DE AUTENTICACIÓN (LOGIN) ---


@app.route("/api/login", methods=["POST"])
def login():
  data = request.get_json()
  correo = data.get("correo")
  password = data.get("password")

  if correo == "amorycafe@gmail.com" and password == "lara2026":
    return jsonify({
        "exito": True,
        "rol": "admin",
        "mensaje": "Bienvenido Administrador",
    })
  elif correo == "matutino@gmail.com" and password == "matutino2026":
    return jsonify({
        "exito": True,
        "rol": "encargado",
        "turno": "Matutino",
        "mensaje": "Bienvenido Encargado Matutino",
    })
  elif correo == "vespertino@gmail.com" and password == "vespertino2026":
    return jsonify({
        "exito": True,
        "rol": "encargado",
        "turno": "Vespertino",
        "mensaje": "Bienvenido Encargado Vespertino",
    })
  elif correo == "marketing@gmail.com" and password == "market2026":
    return jsonify({
        "exito": True,
        "rol": "marketing",
        "mensaje": "Bienvenido al panel de marketing",
    })

  return jsonify({"exito": False, "mensaje": "Credenciales incorrectas"}), 401


# --- RUTAS DE PEDIDOS ---


@app.route("/api/guardar-pedido", methods=["POST"])
def guardar_pedido():
  datos = request.json
  if not datos:
    return jsonify({"error": "No se recibieron datos"}), 400

  datos["estado"] = "Pendiente"

  if "metodoPago" not in datos or not datos["metodoPago"]:
    datos["metodoPago"] = "Efectivo"

  coleccion_pedidos.insert_one(datos)
  return jsonify({"mensaje": "¡Pedido guardado con éxito!"}), 200


@app.route("/api/pedidos", methods=["GET"])
def obtener_pedidos():
  pedidos = list(coleccion_pedidos.find({}, {"_id": False}))
  return jsonify(pedidos)


@app.route("/api/pedidos/<folio>", methods=["PUT"])
def actualizar_estado(folio):
  datos = request.json
  nuevo_estado = datos.get("estado")

  if not nuevo_estado:
    return jsonify({"error": "No se proporcionó el nuevo estado"}), 400

  resultado = coleccion_pedidos.update_one(
      {"folio": folio}, {"$set": {"estado": nuevo_estado}}
  )

  if resultado.matched_count == 0:
    return jsonify({"error": "Pedido no encontrado"}), 404

  return jsonify({"mensaje": "Estado actualizado con éxito"}), 200


@app.route("/api/pedidos/<folio>/pago", methods=["PUT"])
def actualizar_pago(folio):
  datos = request.json
  nuevo_pago = datos.get("metodoPago")

  if not nuevo_pago:
    return jsonify({"error": "No se proporcionó el método de pago"}), 400

  resultado = coleccion_pedidos.update_one(
      {"folio": folio}, {"$set": {"metodoPago": nuevo_pago}}
  )

  if resultado.matched_count == 0:
    return jsonify({"error": "Pedido no encontrado"}), 404

  return jsonify({"mensaje": "Método de pago actualizado con éxito"}), 200


@app.route("/api/pedidos/completados", methods=["DELETE"])
def eliminar_completados():
  resultado = coleccion_pedidos.delete_many(
      {"estado": {"$regex": "^completado$", "$options": "i"}}
  )
  return (
      jsonify({
          "mensaje": (
              f"Se eliminaron {resultado.deleted_count} pedidos completados."
          )
      }),
      200,
  )


# --- RUTAS DE COMENTARIOS Y CALIFICACIONES ---


@app.route("/api/comentarios", methods=["POST"])
def guardar_comentario():
  datos = request.json
  if not datos or "comentario" not in datos:
    return jsonify({"error": "No se recibió el comentario"}), 400

  correo_usuario = (
      datos.get("correo")
      or session.get("user_email")
      or "usuario desconocido"
  )

  nuevo_comentario = {
      "correo": correo_usuario,
      "comentario": datos.get("comentario"),
      "calificacion": int(datos.get("calificacion", 5)),
      "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
  }

  coleccion_comentarios.insert_one(nuevo_comentario)
  return jsonify({"mensaje": "¡Comentario guardado con éxito!"}), 200


@app.route("/api/comentarios", methods=["GET"])
def obtener_comentarios():
  comentarios = list(coleccion_comentarios.find().sort("_id", -1))
  for c in comentarios:
    c["_id"] = str(c["_id"])
  return jsonify(comentarios)


@app.route("/api/comentarios/<id>", methods=["DELETE"])
def eliminar_comentario(id):
  try:
    resultado = coleccion_comentarios.delete_one({"_id": ObjectId(id)})
    if resultado.deleted_count == 0:
      return jsonify({"error": "Comentario no encontrado"}), 404
    return jsonify({"mensaje": "Comentario eliminado con éxito"}), 200
  except Exception as e:
    return jsonify({"error": str(e)}), 400


@app.route("/api/comentarios/eliminar-multiples", methods=["POST"])
def eliminar_multiples_comentarios():
  datos = request.json
  ids = datos.get("ids", [])

  if not ids:
    return jsonify({"error": "No se seleccionaron comentarios"}), 400

  try:
    object_ids = [ObjectId(id_str) for id_str in ids]
    resultado = coleccion_comentarios.delete_many({"_id": {"$in": object_ids}})
    return (
        jsonify({
            "mensaje": (
                f"Se eliminaron {resultado.deleted_count} comentarios"
                " correctamente."
            )
        }),
        200,
    )
  except Exception as e:
    return jsonify({"error": str(e)}), 400


@app.route("/api/comentarios/<id>/responder", methods=["POST"])
def responder_comentario(id):
  datos = request.json
  respuesta_texto = datos.get("respuesta")

  if not respuesta_texto:
    return jsonify({"error": "La respuesta no puede estar vacía"}), 400

  try:
    resultado = coleccion_comentarios.update_one(
        {"_id": ObjectId(id)}, {"$set": {"respuesta": respuesta_texto}}
    )
    if resultado.matched_count == 0:
      return jsonify({"error": "Comentario no encontrado"}), 404
    return jsonify({"mensaje": "Respuesta guardada con éxito"}), 200
  except Exception as e:
    return jsonify({"error": str(e)}), 400


# --- RUTAS DE PROMOCIONES DINÁMICAS ---


@app.route("/api/promociones", methods=["GET"])
def obtener_promociones():
  promociones = list(coleccion_promociones.find())
  for p in promociones:
    p["_id"] = str(p["_id"])
  return jsonify(promociones)


@app.route("/api/promociones", methods=["POST"])
def guardar_promocion():
  datos = request.json
  if not datos:
    return jsonify({"error": "No se recibieron datos de la promoción"}), 400

  resultado = coleccion_promociones.insert_one(datos)
  return (
      jsonify({
          "mensaje": "¡Promoción guardada en MongoDB con éxito!",
          "id": str(resultado.inserted_id),
      }),
      200,
  )


@app.route("/api/promociones/<id>", methods=["DELETE"])
def eliminar_promocion(id):
  try:
    resultado = coleccion_promociones.delete_one({"_id": ObjectId(id)})
    if resultado.deleted_count == 0:
      return jsonify({"error": "Promoción no encontrada"}), 404
    return jsonify({"mensaje": "Promoción eliminada con éxito"}), 200
  except Exception as e:
    return jsonify({"error": str(e)}), 400


# --- RUTA COMODÍN PARA CUALQUIER OTRA VISTA HTML ADICIONAL ---


@app.route("/<path:pagina>")
def cargar_pagina_generica(pagina):
  if not pagina.endswith(".html"):
    pagina += ".html"
  try:
    return render_template(pagina)
  except Exception:
    return render_template("index.html")


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)