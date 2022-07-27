from itertools import count

from bs4 import BeautifulSoup
import os
import magic

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
                
                if(file.find(extent) == -1):
                    root_dirs.append(root)
                    aux = os.path.join(root, file);
                    soup_data = generateBeautifulSoupFile(aux)

                    #Se envia el archivo a que se convierta en Beautiful Suop Data
                    total_paragraph = web_scraping_p(soup_data)
                    total_img = web_scraping_img(soup_data)
                    total_audio = web_scraping_audio(soup_data)
                    total_video = web_scraping_video(soup_data)

                    #Contadores para cada numero de programas
                    count_general_paragaph += total_paragraph
                    count_general_img += total_img
                    count_general_video += total_video
                    count_general_audio += total_audio

    return count_general_paragaph,count_general_img, count_general_audio, count_general_video




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
