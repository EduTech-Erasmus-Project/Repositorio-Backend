"""Helpers de parsing y conteo sobre OAs basados en HTML.

Este módulo recorre los archivos extraídos de un objeto de aprendizaje para:

- contar párrafos, imágenes, audio y video
- construir una galería resumida de imágenes validas
- detectar si un OA fue adaptado con OER Adapt o generado con eXeLearning

La implementación es heredada y mezcla lectura de archivos locales con acceso
opcional a imágenes remotas cuando el `src` apunta a una URL completa.
"""

from itertools import count
from PIL import Image
from bs4 import BeautifulSoup
import os
import magic
import requests
from io import BytesIO


def read_html_files(directory):
    """Recorre el OA y cuenta recursos multimedia y bloques de texto largos.

    Ignora archivos `website_*.html`, que en este proyecto suelen corresponder
    a páginas auxiliares generadas por herramientas externas.

    :param srt directory: Directorio raíz donde se encuentra los archivos del objeto de aprendizaje
    :return: Cantidad total de párrafos, imágenes, audios y videos.

    """

    root_dirs = list()
    count_general_paragaph = 0
    count_general_img = 0
    count_general_video = 0
    count_general_audio = 0
    extent = "website_"
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):

                if (file.find(extent) == -1):
                    root_dirs.append(root)
                    aux = os.path.join(root, file);
                    soup_data = generateBeautifulSoupFile(aux)

                    # Se envia el archivo a que se convierta en Beautiful Suop Data
                    total_paragraph = web_scraping_p(soup_data)
                    total_img = web_scraping_img(soup_data)
                    total_audio = web_scraping_audio(soup_data)
                    total_video = web_scraping_video(soup_data)

                    # Contadores para cada numero de programas
                    count_general_paragaph += total_paragraph
                    count_general_img += total_img
                    count_general_video += total_video
                    count_general_audio += total_audio

    return count_general_paragaph, count_general_img, count_general_audio, count_general_video


def generateBeautifulSoupFile(html_doc):
    """Abre un archivo HTML con detección básica de encoding y retorna un soup.

    Usa `python-magic` para inferir la codificación y cae a UTF-8 cuando el
    detector responde `binary`. El parser se mantiene en `html.parser` por
    compatibilidad con el resto de los helpers del módulo.
    """

    blob = open(html_doc, 'rb').read()
    m = magic.Magic(mime_encoding=True)
    encoding = m.from_buffer(blob)
    if encoding == 'binary':
        encoding = 'utf-8'

    with open(html_doc, encoding=encoding) as file:
        # try:
        soup_data = BeautifulSoup(file, "html.parser")
        file.close()
        return soup_data


def web_scraping_p(aux_text):
    """Cuenta bloques de texto suficientemente largos para análisis del OA.

    :param str aux_text: contiene el código html de la pagina
    """
    length_text = 200
    count_paragrahp = 0
    for p_text in aux_text.find_all("p"):
        if p_text.string:
            if len(p_text.string) >= length_text:
                count_paragrahp += 1

    for p_text in aux_text.find_all('span'):
        if p_text.string:
            if len(p_text.string) >= length_text:
                count_paragrahp += 1

    for p_text in aux_text.find_all('li'):
        if p_text.string:
            if len(p_text.string) >= length_text:
                count_paragrahp += 1

    return count_paragrahp


def web_scraping_img(aux_text):
    """Cuenta etiquetas `img` en una página HTML ya parseada."""
    count_img_tag = aux_text.find_all("img");

    return len(count_img_tag)


def web_scraping_video(aux_text):
    """Cuenta recursos de video sumando etiquetas `video` e `iframe`."""
    count_video_tag = aux_text.find_all("video");
    count_iframe_tag = aux_text.find_all("iframe");
    count_sum_iframe_video = len(count_video_tag) + len(count_iframe_tag)

    return count_sum_iframe_video


def web_scraping_audio(aux_text):
    """Cuenta etiquetas `audio` en una página HTML ya parseada."""
    count_audio_tag = aux_text.find_all("audio");

    return len(count_audio_tag)


def oeradapt_adapted(class_soup):
    """Detecta la marca CSS que identifica contenido adaptado con OER Adapt."""
    if len(class_soup) != 0:
        for class_soup_item in class_soup:
            if class_soup_item == 'oeradapter-edutech':
                return True
    return False


def look_for_class_oeradap(field_index_url):
    """Abre el index del OA y verifica si fue adaptado con OER Adapt."""
    soup_index = generateBeautifulSoupFile(field_index_url)
    class_soup = soup_index.body.get('class', [])
    is_adapted = oeradapt_adapted(class_soup)
    return is_adapted


def read_html_files_data(directory):
    """Lista archivos HTML candidatos junto con su ruta base.

    Este helper sirve como insumo para la extracción de imágenes y descarta los
    archivos `website_` que no forman parte del contenido principal.

    :param srt directory: Directorio raiz donde se encuentra los archivos del objeto de aprendizaje
    :return: Lista de diccionarios con `path_field` y `path_base`.
    """

    files_vect = []
    root_dirs = list()
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".html"):
                root_dirs.append(root)
                aux = os.path.join(root, file);
                if aux.count('website_') != 1:
                    files_vect.append(
                        {
                            "path_field": aux,
                            "path_base": root
                        }
                    )
    return files_vect


def web_scraping_img_fields(aux_text, file, url_host):
    """Extrae imágenes candidatas para galería a partir de una página HTML.

    Soporta rutas locales y URLs remotas, intenta abrir la imagen para obtener
    dimensiones reales y filtra por tamaños que el proyecto considera útiles
    para representación visual del OA.
    """
    tag_identify = "img"
    attribute_img = "src"
    attribute_alt = "alt"
    text_alt = ""
    inf_array_img = []
    object_img = {
        "src": '',
        "alt": '',
    }
    cont = 0
    for tag in aux_text.find_all(tag_identify):
        if tag.get(attribute_img) != '':
            cadena_src = tag.get(attribute_img)

            # Detecta cuando el `src` ya es una URL remota para no unirlo con la base local.
            if cadena_src is None:
                continue

            cadena_src = cadena_src.strip()

            # Los paquetes eXe incluyen bloques JSON ocultos con HTML serializado.
            # Cuando BeautifulSoup parsea ese texto como HTML, aparecen "img" falsas
            # con rutas escapadas como \\"../content/resources/archivo.gif\\".
            # Esas rutas no forman parte del DOM visible del OA y no deben abrirse
            # como archivos locales para la galeria de previsualizacion.
            if '\\"' in cadena_src or cadena_src.startswith('"') or cadena_src.endswith('"'):
                continue

            flag_img_url = False
            img = None
            if cadena_src.find('https://') == 0 or cadena_src.find('http://') == 0:
                try:
                    object_img['src'] = cadena_src
                    flag_img_url = True
                except Exception as e:
                    object_img['src'] = ''
            else:
                object_img['src'] = os.path.join(file['path_base'], cadena_src)

            if object_img['src'] == '':
                continue

            array_split_src = object_img['src'].split('.')
            len_string_img = len(array_split_src)
            if array_split_src[len_string_img-1] == 'svg' or array_split_src[len_string_img-1] == 'raw' \
                        or array_split_src[len_string_img-1] == 'webp':
                continue
            if flag_img_url:
                try:
                    response = requests.get(object_img['src'], timeout=5)
                    response.raise_for_status()
                    img = Image.open(BytesIO(response.content))
                except Exception as e:
                    continue
            else:
                if not os.path.exists(object_img['src']):
                    continue
                try:
                    img = Image.open(object_img['src'])
                except (FileNotFoundError, OSError):
                    continue
                object_img['src'] = os.path.join(url_host, cadena_src)
            width = img.width
            height = img.height

            if tag.get(attribute_alt) is not None:
                object_img[attribute_alt] = tag.get(attribute_alt)
                if check_meets_the_width_height_filter_2(width, height):
                    if exist_object_in_list(object_img, inf_array_img) == False:
                        inf_array_img.append(object_img)
            else:
                object_img[attribute_alt] = text_alt
                if check_meets_the_width_height_filter_2(width, height):
                    if exist_object_in_list(object_img, inf_array_img) == False:
                        inf_array_img.append(object_img)

    return inf_array_img


# mayor a 600
def check_meets_the_width_height(witdh, height):
    """Filtro legacy de dimensiones mínimas y máximas para imágenes."""
    if (witdh > 250 and height > 160) and (witdh < 600 and height < 510):
        return True
    return False


def check_meets_the_width_height_filter_2(witdh, height):
    """Filtro mas estricto de dimensiones usado al construir la galeria final."""
    if (witdh > 400 and height > 310) and (witdh < 600 and height < 510):
        return True
    return False


def exist_object_in_list(object, list):
    """Evita duplicar objetos de imagen dentro de la colección final."""
    if object in list:
        return True
    return False


def generaye_array_paths_img(path_origin, url_host):
    """Construye una galería resumida de hasta 10 imágenes válidas del OA."""
    direcciones = read_html_files_data(path_origin)
    array_paths = []
    for file in direcciones:
        aux_file = generateBeautifulSoupFile(file['path_field'])
        array_paths_web_scraping = web_scraping_img_fields(aux_file, file, url_host)
        if len(array_paths_web_scraping) > 0:
            for object_paths in array_paths_web_scraping:
                if len(array_paths) < 10:
                    array_paths.append(object_paths)
                else:
                    break
    return array_paths


def verify_that_oa_was_made_exelearning(path_imsmanifest):
    """Detecta si el `imsmanifest` pertenece a un paquete generado por eXeLearning.

    Mantiene el parser HTML heredado aunque el archivo sea XML. Esa decisión
    explica los warnings de BeautifulSoup vistos en runtime y conviene
    conservarla hasta que se revise el impacto de cambiar a parser XML.
    """
    soup_data = None
    with open(path_imsmanifest, encoding="utf-8") as file:
        # try:
        soup_data = BeautifulSoup(file, "html.parser")
        file.close()
    imsmanifest = soup_data
    ims_identifier = imsmanifest.find('manifest')['identifier']
    if ims_identifier[0:3] == "eXe":
        return True
    return False
