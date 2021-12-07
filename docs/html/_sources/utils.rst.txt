.. _chap-utils:
   

#########
Utilities
#########


***********
Translation
***********

Based on the standard Django system. All the texts in Neuma are initially in English, from which
translations can be created.


Creation
========

First, run the ``makemessages`` process. Example
for French:

.. code-block:: bash

    django-admin makemessages --locale=fr

    
This creates a new translation file ``django.po``  in ``locale/fr/LC_MESSAGES``. Edit
this file (in UTF-8) and supply the translations. The format is straightfoward. Then
compile the messages with

.. code-block:: bash

     django-admin compilemessages

That's it! This creates a ``.mo`` file, the one that needs to be distributed.

Updates
=======

Same process. Beware: any change, even minor, in the initial text will generate
a new entry in the translation file. It seems that the old one is never deleted, though.



