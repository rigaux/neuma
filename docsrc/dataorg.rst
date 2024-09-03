.. _chap-dataorg:

#################
Data organization
#################

The main objects managed in Neuma are *corpus(es)* and *opus(es)*. They 
implement a data organization comparable to the classical
concepts of *folders* and *files* in a computer. A *corpus*
is a container. Its content consists of either opuses or (sub)corpuses,
or both. An *opus* is a musical work, such as, e.g., The Goldberg variations
or The New World Symphony. Thus, data in Neuma is essentially
a hierarchy,  rooted at as pseudo-corpus named *all*, where internal nodes
are corpuses, and leaves are opuses. Both corpuses
and opus are described by textual meta-data.

A third, important type of object is called *Source*. A source is
any digital document that represents an information about an opus. 
A source is typically a file that encodes the music in a format such as
MusicXML or MEI. A source can also be an audio file, and textbook, an
external document that refers to the opus, etc. 

Finally, an opus can be annotated. Annotations express a statement
(the *body*) about an opus or one of its sources (the *target*).

Let's now explain these concepts in details.

***************
Corpus and Opus
***************

As explained above, a corpus is a contained, whereas an opus
gathers a set of information about a musical work. In Neuma, objects
of both types receive a unique and immutable reference when they are
created. Since this reference is essential for further data 
management tasks, this is the first aspect to address.

Managing references
===================


Each object, whether *corpus* or *opus*, is identified by a unique Neuma *reference*. 
A (global) reference
represents a path from the top-level corpus to the object, 
and takes the following form:

.. code-block:: text
   
       all:ref2:...:refN
         
Each *refi* is the *local* reference. The top-level corpus
reference is *all*, hence all pathes begin with ``all:``.
The first *n-1* references are local *corpus* reference (since
internal nodes of the hierarchy consist of corpuses). 
The last reference is either a corpus local
reference of an opus local reference, depending of the 
object referred to.

Let's take some examples:

  - the corpus *Composers*, with local reference ``composers``, located
    below the top-level corpus, has ``all:composers`` as its global reference;
  - the corpus *Monteverdi*, with local reference ``monteverdi``, located
    below the *Composers* corpus, has ``all:composers:monteverdi`` as its global reference;
  - the opus *Madrigal XII*,  with local reference ``madrigal12``, located
    below the *Monteverdi* corpus, has ``all:composers:monteverdi:madrigal12`` as 
    its global reference.

(Global) reference are therefore quite similar to  absolute paths in a file system. Although the
choice of reference string is free, there are some good practices highly
recommended:

  - use short, and if possibly meaningful, identifiers, u
  - allways use lowercase strings,
  - never us special characters, and preferably avoid accents.

Initially, Neuma proposes the root corpus, and a few pre-defined corpuses 
(children of the root) for generic 
activities. They are shown on the welcome page of Neuma
(:numref:`initialCorpus`).

.. _initialCorpus:
.. figure:: ./figures/initialCorpus.png       
        :width: 90%
        :align: center
   
        The root (initial) corpus

The complete list of corpuses, along with some stats of their opuses,
is shown at http://neuma.huma-num.fr/home/collecti

******************
Exploring corpuses
******************

By clicking on a corpus's icon, one obtain a page that 
details the corpus content. Let's examine first the case
of a "container" corpus, e.g., a corpus that contains
sub-corpus. Examine :numref:`exploringCorpus` below,
showing the page dedicated to corpus ``all:composers``.

.. _exploringCorpus:
.. figure:: ./figures/exploringCorpus.png       
        :width: 90%
        :align: center
   
        A corpus with sub-corpuses

Each corpus consists first of some general informations:

  - a title, in short and detailed form. The short form is 
    used for navigation purposes: see the breadcrumb at the top of the page
  - a description, also in short and detailed forms.
  - a licence, that applies to all the corpuses contents
  - a cover image, used as an icon in lists
  - and finally, the list of sub-corpuses or opuses.
  
It turns out that ``all:composers`` consists only of sub-corpuses,
one for each composer.

.. _exploringCorpus2:
.. figure:: ./figures/exploringCorpus2.png       
        :width: 90%
        :align: center
   
        A corpus with opuses

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
