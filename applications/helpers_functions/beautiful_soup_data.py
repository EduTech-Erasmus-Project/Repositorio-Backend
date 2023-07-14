from itertools import count
from PIL import Image
from bs4 import BeautifulSoup
import os
import magic
import requests
from io import BytesIO


def read_html_files(directory):
    """Lectura de archivos html del objeto de aprendizaje

    :param srt directory: Directorio raiz donde se encuentra los archivos del objeto de aprendizaje

    :return : tuple(str[], str[], boolean)

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
    """
    Genera un objeto de BeautifulSoup para realizar web scraping
    :param html_doc:
    :return BeautifulSoup Data:
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
    """
    Exatraccion de los parrafos de cada pagina html,
    se crea un ID unico, para identificar cada elemento

    :param str aux_text: contiene el codigo html de la pagina
    :param int page_id: id de la pagina
    :param str file: directorio de la pagina
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
    count_img_tag = aux_text.find_all("img");

    return len(count_img_tag)


def web_scraping_video(aux_text):
    count_video_tag = aux_text.find_all("video");
    count_iframe_tag = aux_text.find_all("iframe");
    count_sum_iframe_video = len(count_video_tag) + len(count_iframe_tag)

    return count_sum_iframe_video


def web_scraping_audio(aux_text):
    count_audio_tag = aux_text.find_all("audio");

    return len(count_audio_tag)


def oeradapt_adapted(class_soup):
    if len(class_soup) != 0:
        for class_soup_item in class_soup:
            if class_soup_item == 'oeradapter-edutech':
                return True
    return False


def look_for_class_oeradap(field_index_url):
    soup_index = generateBeautifulSoupFile(field_index_url)
    class_soup = soup_index.body.get('class', [])
    is_adapted = oeradapt_adapted(class_soup)
    return is_adapted


def read_html_files_data(directory):
    """Lectura de archivos html del objeto de aprendizaje
    :param srt directory: Directorio raiz donde se encuentra los archivos del objeto de aprendizaje
    :return : tuple(str[], str[], boolean)
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

            """
            Condiciones para buscar una url 
            para no unir con la ruta base del proyecto 
            """
            flag_img_url = False
            img = None
            if cadena_src.find('https://') == 0 or cadena_src.find('http://') == 0:
                try:
                    object_img['src'] = tag.get(attribute_img)
                    flag_img_url = True
                except Exception as e:
                    object_img['src'] = ''
            else:
                object_img['src'] = os.path.join(file['path_base'], tag.get(attribute_img))

            if object_img['src'] == '':
                continue

            array_split_src = object_img['src'].split('.')
            len_string_img = len(array_split_src)
            if array_split_src[len_string_img-1] == 'svg' or array_split_src[len_string_img-1] == 'raw':
                continue

            if flag_img_url:
                try:
                    response = requests.get(object_img['src'])
                    img = Image.open(BytesIO(response.content))
                except Exception as e:
                    continue
            else:
                img = Image.open(object_img['src'])
                object_img['src'] = os.path.join(url_host, tag.get(attribute_img))

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
    if (witdh > 250 and height > 160) and (witdh < 600 and height < 510):
        return True
    return False


def check_meets_the_width_height_filter_2(witdh, height):
    if (witdh > 400 and height > 310) and (witdh < 600 and height < 510):
        return True
    return False


def exist_object_in_list(object, list):
    if object in list:
        return True
    return False


def generaye_array_paths_img(path_origin, url_host):
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
