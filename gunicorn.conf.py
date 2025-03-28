# gunicorn.conf.py
# Non logging stuff
# bind = unix:/home/scorelibadmin/scorelib-django/scorelib.sock
workers = 3
# Access log - records incoming HTTP requests
accesslog = "/home/scorelibadmin/scorelib-django/gunicorn.access.log"
# Error log - records Gunicorn server goings-on
errorlog = "/home/scorelibadmin/scorelib-django/gunicorn.error.log"
# Whether to send Django output to the error log 
capture_output = True
# How verbose the Gunicorn error logs should be 
loglevel = "info"
