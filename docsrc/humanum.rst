.. _chap-humanum:

##############################
Appendix: deploying at Humanum
##############################

Contact chez HumaNum:  Joël Marchand, joel.marchand@huma-num.fr
et l'équipe des sysadmins: sysadmin@huma-num.fr.

Une bonne documentation expliquant l'installation: https://realpython.com/django-nginx-gunicorn/#making-your-site-production-ready-with-https

*******
Serveur
*******

On travaille dans une VM Ubuntu, pour le moment 18.04 LTS. Elle dispose de 20Go
d'espace (j'ai enlevé qq Go de backup pour pouvoir installer tensorflow, mais il
reste maintenant 5 Go de libres).


Environnement
=============

Le serveur Web est Nginx, et non apache. Les infos importantes pour Nginx se
trouvent dans ``/etc/nginx/```, notamment dans ``/etc/nginx/sites-available/``
(configurations équivalentes aux *Virtual hosts* d'apache), voir les
``scorelib-webdjango`` et ``scorelib-dev-webdjango`` (avec liens symboliques dans
``/etc/nginx/sites-enabled``. Les logs (access et error) sont dans
``/usr/share/nginx/logs/``.

On a conservé deux applis django, scorelib et scorelib-dev, qui
localement sont résolues avec les noms de domaines scorelib.test et
scorelib-dev.test (cf /etc/hosts), et huma-num nous fournit respectivement les
deux sous-domaines http://neuma.huma-num.fr et http://neuma-dev.huma-num.fr
.

Les fichiers des applis sont dans ``/home/scorelibadmin``, dossiers
``scorelib-django`` et ``scorelib-dev-django``. Donc faire:

.. code-block:: bash

      cd /home/scorelibadmin/scorelib-django

Pour l'appli principale.

Les droits d'accès
sont accordés à l'utilisateur ``scorelibadmin``: **ne pas
en utiliser un autre sous peine de problèmes**. La commande:

.. code-block:: bash

		 sudo chown -R scorelibadmin:scorelibadmin ./*

dans le dossier ``~/scorelib-django`` devrait les résoudre.

Il y a des environnements virtuels pour
les installations de package, penser à faire

.. code-block:: bash

    source env/bin/activate

pour
activer l'environnement quand on travaille en local. On peut ensuite lancer


.. code-block:: bash

     python3 manage.py runserver 0.0.0.0:8080

Attention, dans les fichiers
versionnés, je crois que "0.0.0.0" n'a pas été ajouté au fichier
scorelib/settings.py, de même que "neuma.huma-num.fr", je les ai ajoutés en dur
sur le serveur). Ça permet de tester si les migrations ont bien été faites et si
tous les paquets nécessaires sont présents dans l'environnement virtuel. Là, il
manquait notamment python_log_indenter et tensorflow. Une fois que django a
démarré, on peut le consulter avec une aute connexion sur le serveur avec "links
http://0.0.0.0:8080", par exemple.

Gunicorn
========

Gunicorn se charge ensuite de faire le lien entre une appli wsgi comme django et
le serveur Nginx. Il faut utiliser

.. code-block:: bash

     systemctl restart gunicorn-scorelib nginx

pour relancer gunicorn et nginx. Ou, très radical:

.. code-block:: bash

    systemctl reboot -i

On peut consulter les logs de gunicorn depuis
le dernier boot avec

.. code-block:: bash

      journalctl -u gunicorn-scorelib.service -b --no-pager

Ce ``service systemd`` repose sur une configuration dans
``/etc/systemd/system/gunicorn-scorelib.service``. Il fonctionne avec une "socket
unix", qui se trouve là : ``/home/scorelibadmin/scorelib-django/scorelib.sock``.

Codes d'accès
=============

Voir le fichier dédié.

Neuma est dans ``/home/scorelibadmin/scorelib-django/``.

Une fois connecté dans la VM, pour devenir administrateur (root),
il suffit de faire

.. code-block:: bash

		sudo bash

Le systeme de la VM est Ubuntu 18.04.4 LTS. Cf

.. code-block:: bash

				cat /etc/issue

Ne pas oublier de relancer le serveur XSGI après un déploiement:

.. code-block:: bash

       systemctl restart gunicorn-scorelib-dev gunicorn-scorelib nginx


*************
ElasticSearch
*************

J'ai suivi ce mode d'emploi [1], ce qui permet de redémarrer ElasticSearch comme
un service avec :

.. code-block:: bash

    sudo systemctl restart elasticsearch.service

(les commandes start et stop sont aussi utilisables, évidemment)

La configuration se trouve dans /etc/elasticsearch/elasticsearch.yml (nom du
cluster, nodes, binding sur IP ou port spécifique). On peut ajuster la mémoire
prise par ElasticSearch dans /etc/elasticsearch/jvm.options, en passant "-Xms1g"
à "-Xms512m" (idem pour -Xmx).

********
Postgres
********

Le serveur est installé sur la VM. Le compte d'accès est dans le fichier des infos
sensibles. Créer un pont SSH sur notre machine virtuelle:

.. code-block:: bash

       ssh -L 63333:localhost:5432 scorelibadmin@neuma.huma-num.fr


On peut alors se connecter au serveur postgres sur le port ``localhost:63333``.


Donc, pour se connecter.

.. code-block:: bash

      psql -U user_scorelib -h localhost scorelib --password

Quelques commandes utiles (se connecter sous root avec ``su -``)

.. code-block:: bash

	  systemctl | grep postgres
	  systemctl stop postgresql@14-main.service
      systemctl start postgresql@14-main.service
      systemctl enable postgresql@14-main.service
      systemctl disable postgresql@14-main.service
 
 *****     
 REDIS
 *****
 
 Installé de manière standard sous Unbuntu. Le fichier de configuration
 est `/etc/redis/redis.conf/etc/redis/redis.conf``. Commandes usuelles:
 
 
 .. code-block:: bash
 
     sudo systemctl restart redis.service
	 sudo systemctl disable redis
	 
******
CELERY
******

Il faut créer le fichier de conf et le fichier de services à la main.

Cf https://www.willandskill.se/sv/articles/celery-4-with-django-on-ubuntu-18-04

Le fichier de définition du service est dans 
``/etc/systemd/system/celery.service``,

.. code-block:: python

	[Unit]
	Description=Celery Service
	After=network.target

	[Service]
	Type=forking
	User=celery
	Group=celery
	EnvironmentFile=/etc/conf.d/celery
	WorkingDirectory=/home/scorelibadmin/scorelib-django
	ExecStart=/bin/sh -c '${CELERY_BIN} -A $CELERY_APP multi start $CELERYD_NODES \
    	--pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} \
    	--loglevel="${CELERYD_LOG_LEVEL}" $CELERYD_OPTS'
	ExecStop=/bin/sh -c '${CELERY_BIN} multi stopwait $CELERYD_NODES \
    	--pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} \
    	--loglevel="${CELERYD_LOG_LEVEL}"'
	ExecReload=/bin/sh -c '${CELERY_BIN} -A $CELERY_APP multi restart $CELERYD_NODES \
    	--pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} \
    	--loglevel="${CELERYD_LOG_LEVEL}" $CELERYD_OPTS'
	Restart=always

	[Install]
	WantedBy=multi-user.target

Tandis que le fichier de
configuration est dans ``/etc/conf.d/celery``.

.. code-block:: python

	# Name of nodes to start
	# here we have a single node
	CELERYD_NODES="w1"
	# or we could have three nodes:
	#CELERYD_NODES="w1 w2 w3"

	# Absolute or relative path to the 'celery' command:
	#CELERY_BIN="/usr/bin/celery"
	CELERY_BIN="/home/scorelibadmin/scorelib-django/env/bin/celery"

	# App instance to use
	CELERY_APP="scorelib"

	# How to call manage.py
	CELERYD_MULTI="multi"

	# Extra command-line arguments to the worker
	CELERYD_OPTS="--time-limit=300 --concurrency=8"

	# - %n will be replaced with the first part of the nodename.
	# - %I will be replaced with the current child process index
	#   and is important when using the prefork pool to avoid race conditions.
	CELERYD_PID_FILE="/var/run/celery/%n.pid"
	CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
	CELERYD_LOG_LEVEL="INFO"

	# you may wish to add these options for Celery Beat
	CELERYBEAT_PID_FILE="/var/run/celery/beat.pid"
	CELERYBEAT_LOG_FILE="/var/log/celery/beat.log"

	# Flower configuration options
	FLOWER_PORT=5555
	FLOWER_LOG_PREFIX="/var/log/celery/flower.log"
	FLOWER_LOG_LEVEL="INFO"
	
Pour Flower on crée un fichier flower.service avec le même 
fichier de paramètres.

.. code-bloc:: python
	
	[Unit]
	Description=Flower Celery Service
	After=network.target

	[Service]
	Type=forking
	User=celery
	Group=celery
	EnvironmentFile=/etc/conf.d/celery
	WorkingDirectory=/home/scorelibadmin/scorelib-django
	ExecStart=/bin/sh -c '${CELERY_BIN} -A ${CELERY_APP} flower --port=${FLOWER_PORT} \
  		--log-file-prefix=${FLOWER_LOG_PREFIX} --loglevel=${FLOWER_LOG_LEVEL}'
	ExecStop=/bin/sh -c '${CELERY_BIN} multi stopwait $CELERYD_NODES \
    	--pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} \
    	--loglevel="${CELERYD_LOG_LEVEL}"'
	ExecReload=/bin/sh -c '${CELERY_BIN} -A $CELERY_APP multi restart $CELERYD_NODES \
    	--pidfile=${CELERYD_PID_FILE} --logfile=${CELERYD_LOG_FILE} \
    	--loglevel="${CELERYD_LOG_LEVEL}" $CELERYD_OPTS'
	Restart=always

	[Install]
	WantedBy=multi-user.target

Je n’ai pas ajouté le ``—address`` donc flower est ouvert sur le port 5555
On peut faire un relais:

.. code-block:: bash

	sudo ssh -L 5555:localhost:5555 scorelibadmin@neuma.huma-num.fr
