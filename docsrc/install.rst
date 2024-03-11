.. _chap-install:
   

############
Installation
############

Neuma is essentially a web application developped in Python with the Django framework
(https://www.djangoproject.com/). It relies on a Postgres relational DB for storage, 
and on an ElasticSearch server for search operations.

The full code can be downloaded from a SVN repository, currently 
https://gforge.cnam.fr/svn/vertigo_svn/scorelib/app/scorelib.

Download the code. The root directory of the project is named ``scorelib``. Most of the commands
given below can be run from this directory through the ``manage.py``  script. The general
form is

.. code-block:: bash

    python3 manage.py <command> <options>

.. note:: If you do not know Django, 
   as a technical user, you should probably spend some time to run the initial
   tutorial at https://www.djangoproject.com/.

***********
Environment
***********

Python/Django
=============

You need a Python3 environment, with a recent version of Django. 

.. note:: At the time of writing, we use Django 3.1

Follow the standard instructions for installing Django. It should not be more
difficult that 

.. code-block:: bash

     pip3 install django
     

Neuma depends on many Python packages. We use Conda (https://docs.conda.io/en/latest/) 
to manage these dependencies. You should be able to install them in one shot thanks to the followng command:

.. code-block:: bash 

     conda env create -f environment.yml

One mandatory step is the creation of a Django administration user:

.. code-block:: bash

    python3 manage.py createsuperuser

Enter the nameand password of the super-user for django. For instance (used  in the following): 
``djadmin / djadmin``.


Postgres
========

Install the lastest version of Postgres (see https://www.postgresql.org/). 
A nice client interface to enter commands is pgAdmin (https://www.pgadmin.org/). 

Then
create a Postgres database named ``scorelib``, and a user with all privileges on this DB. For instance:

.. code-block:: sql
  
     create database scorelib
     create user neumadmin with encrypted password 'neuma';
     grant all privileges on database scorelib to neumadmin

Choose the names and passwords at your convenience of course. They must be
reported in the database configuration dictionary located 
in the ``scorelib/local_settings.py`` file. .

.. code-block:: python

    DATABASES = {
     'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'neuma',
        'USER': 'neumadmin',
        'PASSWORD': 'neuma',
        'HOST': 'localhost',
        'PORT': '',
        }
    }
 
The database schema is automatically created and maintained by Django. In principle, you
just have to run:

.. code-block:: bash

      python3 manage.py migrate
     
.. important:: Do not change, *ever*, the  ``settings.py`` configuration file. Everything
   pertaining to your *local* configuration has to be put in ``scorelib/local_settings.py``. Values
   stored there override the default one in ``settings.py``. Be sure to preserve this file
   in you environment : do not release it it the SVN repository; keep a safe copy somewhere.
 
ElasticSearch
=============

Install ElasticSearch, standard, from https://www.elastic.co/fr/products/elasticsearch. Run
an Elasticsearch server somewhere. A simple choice for a dev environment is to install ElasticSearch
locally, and run a single node from the command line

.. code-block:: bash

    ./bin/elasticsearch

That's all. The server runs on ``localhost``, port 9200. Check it by accessing the
Url http://localhost:9200.

Be sure to report the correct values in ``scorelib/local_settings.py``.

.. code-block:: python

     ELASTIC_SEARCH = {"host": "localhost", 
                       "port": 9200, 
                       "index": "scorelib"}

In principle, you should never have to worry about directly 
inspecting the index. If you want to do so,
install the client such as Kibana or Cerebro (https://github.com/lmenezes/cerebro). Being
able to send HTTP requests with ``curl`` might also prove to be useful 


Redit
=====

Neuma uses Celery for running large tasks in the background. Celery
itself uses Redit. Just install an instance, with Docker or
any other utility.

Celery
======

Finally we must run the Celery worker. In development environment,
run as follows:

.. code-block:: 

	celery -A scorelib worker --loglevel=INFO




Neuma setup
===========

Now some objects must be created in Neuma. This can be done by running the ``setup_neuma``  command as follows:

.. code-block:: bash

      python3 manage.py setup_neuma
      
This creates some mandatory objects in the DB. 

.. note:: This is a first example of a ``command`` run in a terminal. Several such command
  are provided and documented in Chapter :ref:`chap-commands`.

Does it work?
=============

Launch the Django app.

.. code-block:: bash

     python3 manage.py runserver
     
And Neuma should be accessible at http://localhost:8000.


.. _neumaLogin:
.. figure:: ./figures/neumaLogin.png       
        :width: 90%
        :align: center
   
        Login to neuma with the Django superuser 

Félicitations ! It works. You can connect to Neuma with the super user account created for Django (Neuma
relies on the Django authentication system). Figure :ref:`neumaLogin`.

The next step is to load data.

