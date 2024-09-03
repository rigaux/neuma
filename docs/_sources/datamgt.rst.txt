.. _chap-datamgt:

###############
Data management
###############

*****************
Managing corpuses
*****************

By clicking to the "Management", one obtain the forms shown on Figure :ref:`manageCorpus`. 

.. _manageCorpus:
.. figure:: ./figures/manageCorpus.png       
        :width: 90%
        :align: center
   
        Managing a corpus and its sub-corpuses

The following actions are 
proposed

  - Editing the corpus, to change its description
  - Adding a sub-corpus
  - Adding a zip file containing a list of opuses to import in the corpus
  - Importing a zip file
  
Editing corpuses
================

The *Edit corpus* form is shown on Figure :ref:`editCorpus`. Note that it is automatically 
produced by Django from the schema. This form can be used for creating and 
editing (modifying) corpuses.

.. _editCorpus:
.. figure:: ./figures/editCorpus.png       
        :width: 90%
        :align: center
   
        Corpus form 
        
Fields:

 - title, for the main page of the corpus
 - short title, used for lists and links
 - description
 - short description (a few lines) 
 - ``isPublic``: a corpus can be either *Public* (not access restrictions) or *Private*. In the
    latter case it is shown only to users with access grants.
 - Parent corpus: each corpus has a unique parent. Choose the parent from the list
 - Reference code: this is the *global* reference code, for instance ``composers:bach:chorals``
   for the ``chorals`` corpus, child of ``bach``, itself child of ``composers``. **Be very careful**
   when entering the reference, because its is essential to ensure the consistency of 
   navigation and searches in Neuma.
 - The cover is an image that illustrates the corpus.

Access rights on corpuses
=========================

Neuma is implemented with the Django framework, which proposes an automatically
generated interface for administrating data. Among these administration tasks, 
*access rights management* is used to protect corpuses and opuses.

In the admin page of a corpus, a link located in the top-right corner gives
access to the permissions form. Links are defined per user: first choose the
user as shown on Figure  :numref:`droits_specif_user`. 

.. _droits_specif_user:
.. figure:: ./figures/droits_specif_user.png
   :width: 100%
   :align: center
   
   Choosing the user for permissions
   
One obtains the form of Figure :numref:`droits_specif`. 

.. _droits_specif:
.. figure:: ./figures/droits_specif.png
   :width: 100%
   :align: center
   
   Access rights form

The following rights can be given to the user:
 
 - *Read*: allows to inspect the corpus. This is only relevant for non-public corpuses, 
   the public corpuses are, by definition, acessible (in read mode) for everybody. 
 - *Write*: rights to modify a corpus, add sub-corpuses and import opuses. 
 - *Delete*: there is no function to delete a corpus from the Neuma interface. This right is therefore
    ignored.
    
Commands on corpuses
====================

A set of Django commands is available on the command line to apply actions to either a
corpus (and its set of opera) or to a single corpus. 

All these command can be run from the ``scorelib`` root directory via the `` manage.py`` script. 
The general syntax is:

.. code-block:: bash

    python3 manage.py <command_name> <options>

For corpuses, the command is ``scan_corpus``. It always take an option ``-c`` with the reference 
of the corpus
(for instance ``composers:monteverdi``) and a ``-a`` action with the specific action to carry out.
For instance the following command builds and index for the psautiers corpus.

.. code-block:: bash

    python3 manage.py scan_corpus -c psautiers -a index

Here is the list of available actions:


  - ``mei``: this action converts the MusicXML file of each opus to an MEI file.
     The MEI XSLT conversion stylesheet is used and taken from the ``scripts`` directory.  See 
     the github repository for details: 
     https://github.com/music-encoding/encoding-tools/releases/tag/v3.0.0

     .. code-block:: bash
   
          python3 manage.py scan_corpus -c <corpus_ref> -a mei
      
  - ``index``: this actions extracts descriptors from each opus of a corpus, and 
    stores these descriptors in the ``Descriptor`` table. Descriptors are then sent
    to ElasticSearch 

    .. code-block:: bash
   
        python3 manage.py scan_corpus -c <corpus_ref> -a index
      

***************
Managing opuses
***************

Like corpuses, opuses cn be edited via the Django admin form. This form can be accessed, for
connected users with access rights, thanks to a small pen displayed left of the opus title.

However, in general opuses are managed in batches. The main procedure consists in importing
(and exporting) Zip files containing opuses contents. 

For data exchanges, all infos related to an opus are gathered in two files

 - The score, either a MusicXML (and its compressed variant) or MEI 
 - (Optional) metadata sotred in a Json file.
 
For XML files (scores), three extensions are accepted:  'xml' for MusicXML, 'mxl' 
for compressed MusicXML, and 'mei' for MEI.
     
Both files are named accoding to the (local) reference of the opus, for instance 
``bwv333.xml`` for the MusicXML file of choral BWV333, and ``bwv333.json`` for metadata.
The Json file is optional: if absent, the import procedure attempts to extract metadata from
the XML file. 

Upload files
============

.. note:: In the ``data`` directory of Neuma, you will find that Zip files ready to be imported.

For import/export, opuses are gathered in Zip files. In order to create such a file, proceed as follows

  - create a directory (its name is not important), say ``myImport``;
  - put the opuses files in this directory. It is essential to respect the naming
    rules explained above. 
  - compress the directory as a zip file, e.g., ``myImport.zip``.
    
**Be careful with opus references**: the file names (without extension)
define the local reference of an opus inside its corpus. if, for instance,
one imports in a corpus ``psautiers:godeau1656``, then a file 
``mynopus.xml`` will be imported in the corpus with (globl) reference 
``psautiers:godeau1656:monopus``.

Opus references cannot be modified after import.  **Use a consistent naming scheme,
in lowercase, as short as possible**. Note that opuses are sorted
on their (local) reference whenever a corpus is displayed. This must be anticipated
if order is important. For instance,  
``opus_1``  appears before ``opus_2`` in alphanumeric order, ,
but the latter  appears *after* ``opus_12``. Use padding 0 to obtain a correct sorting,
such as ``opus_01``,
``opus_02``, `òpus_12`` (in case two  positions are enough).

Inserting upload files
======================

In the *Management* tab of a corpus, a form allows to upload a zip file. You must supply
a sort description of the Zip content, and the Zip file itself. 

Once uploaded, Zip files appear in a list, left of the *Management* tab. Note the ID of a
file which is required to trigger its insertion.

The Django admin form gives additional access to upload files (deletion, replacement, etc.)

Importing opuses
================

In order to bulkload the content of a ZIP file, run the following command:

.. code-block:: bash

    python3 manage.py import_zip -u <upload_id>
 
This function can be run in asynchronous mode with:

.. code-block:: bash

    python3 manage.py import_zip -u <upload_id> -a 1
