# Repositorio de Objetos de Aprendizaje (ROA) 

Este proyecto es la parte Backend del <a href="https://repositorio.edutech-project.org/#/">Repositorio de Objetos de Aprendizaje</a>.

## Empezar 🚀

Estas instrucciones te permitirán obtener una copia del proyecto en funcionamiento en tu máquina local para propósitos de desarrollo y pruebas.

<ul>
 <li>
  <a href="https://github.com/EduTech-Erasmus-Project/Repositorio-Frontend.git">Frontend repositorio de objetos de aprendizaje (ROA)</a>
 </li>
</ul>

### Pre-requisitos 📋

Instalación de Python 3

- Linux

```
sudo apt-get install python3-pip

```

   Observar la version de python que se instalo

```
python3 -V
```

- Windows

   Descargar del siguiente enlace

   https://www.python.org/downloads/

Entorno virtual 

```
python3 -m venv ejemplo-env
```

## Instalación 🔧

- Instalar requerimientos 

```
pip install –r requirements.txt 
``` 

### Configuracion de la base de datos

PostgreSQL

- Instalación Windows

  https://www.postgresql.org/
  
 - Instalación Linux

```
sudo apt-get -y install postgresql
```

## Ejecución de proyecto 

Para la ejecucucion del proyecto situarse a la altura del archivo manage.py

```
python manage.py makemigrations
```

```
python manage.py migrate
```

```
python manage.py runserver
```

