.. _chap-datamgt:

###############
Data management
###############

Data management tasks are reserved to the administrators or
to users with an ``editor`` role on the corpus. They can be performed
either via web forms, or by exporting/importing files. 

*********************
Form-based management
*********************

The "management" tab
====================

A user with editor rights on a corpus can access to the corpus management 
function via a "Management" tab. By clicking to this tab, 
one obtains the forms shown on   :numref:`manageCorpus`. 

.. _manageCorpus:
.. figure:: ./figures/manageCorpus.png       
        :width: 90%
        :align: center
   
        Managing a corpus and its sub-corpuses

The following actions are  proposed

  - Editing the corpus, to change or complete its description
  - Adding a sub-corpus
  - Adding a zip file containing a list of opuses to import in the corpus
  - Importing a zip file
  - Exporting the corpus content as a zip file
  
Editing corpuses
================

The *Edit corpus* form is shown on :numref:`editCorpus`. 
This form can be used for creating and 
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

Adding a sub-corpus
===================

A sub-corpus is added with the form shown on :numref:`add_sub_corpus`. All
the fields are mandatory, and in particular an image that serves to illustrate the corpus.

.. _add_sub_corpus:
.. figure:: ./figures/add_sub_corpus.png       
        :width: 90%
        :align: center
   
        Adding a sub-corpus

If the new corpus is not *public*, access rights must be 
specified by an administrator.
    

Adding an Opus
==============

An Opus can be added via a form. However, the preferred method is to
load a set of opuses via a Zip file.

Upload a ZIP file
=================

In the *Management* tab of a corpus, a form allows to upload a zip file. You must supply
a sort description of the Zip content, and the Zip file itself. 

Once uploaded, Zip files appear in a list, left of the *Management* tab. Note the ID of a
file which is required to trigger its insertion.
See the next section for instructions regarding the organization and format.

       
*******************
Importing/exporting
*******************

In general opuses are managed in batches. The main procedure consists in importing
(and exporting) Zip files (called "neumazip" from now on) 
containing opuses contents. Actually such zip files
can contain full subsets of the Neuma collection, including a hierarchy of corpuses.


.. note:: Several examples of neumazips are available on demand.

Organization of neumazips
=========================

The organization of neumazips containing corpus/sub-corpuses/opuses is similar to
that  on your computer, where *directories* play the role of corpuses, and
*files* the role of opuses. The local reference of the corpus is the directory name,
and the files in the directory contain the opuses' description. 

The metadata of the corpus is stored in a JSON file named ``corpus.json``, and
there
are actually *at least* two files for each opus:


 - A MusicXML (and its compressed variant) or MEI file containing the default score
 - A JSON file containing the metadata.

 
.. note:: For XML files (scores), three extensions are accepted:  'xml' for MusicXML, 'mxl' 
   for compressed MusicXML, and 'mei' for MEI.

For a given opus with reference ``xyz``, those files are respectively named
``xyz.xml`` (the extension might be ``mxl`` or ``mei``) and ``xyz.json``.

.. admonition:: Example

   Assume a corpus with reference ``corp`` and two opuses, with 
   respective references ``opA`` and ``opB``. On your computer, it
   corresponds to a directory named ``corp`` with the following files:
   
     - a JSON file ``corpus.json`` containing corpus metadata 
     - a file ``opA.json`` containing opA metadata 
     - a file ``opA.xml`` containing the MusicXML default score for opA
     - a file ``opB.json`` containing opA metadata 
     - a file ``opB.xml`` containing the MusicXML default score for opA
   
   By compressing the directory ``corp``, you obtain a ``corp.zip`` file
   ready to be inserted in and existing corpus of Neuma.
 
**Be careful with  references**: the directory name (without extension)
defines the corpus local referece, and the file names (without extension)
define the local reference of an opus inside its corpus. 

.. admonition:: Example

    If one imports the  corpus ``corp``  in a parent corpus with global reference
    ``all:parent``, the global reference of the new corpus is ``all:parent::corp``,
    and thetwo  opuses get the respective global references ``all:parent::corp:opA`` and ``all:parent::corp:opB``.

Opus references cannot be modified after import.  **Use a consistent naming scheme,
in lowercase, as short as possible**. Note that opuses are sorted
on their (local) reference whenever a corpus is displayed. This must be anticipated
if order is important. For instance,  
``opus_1``  appears before ``opus_2`` in alphanumeric order, ,
but the latter  appears *after* ``opus_12``. Use padding 0 to obtain a correct sorting,
such as ``opus_01``,
``opus_02``, `òpus_12`` (in case two  positions are enough).

Format of metadate JSON files
=============================
