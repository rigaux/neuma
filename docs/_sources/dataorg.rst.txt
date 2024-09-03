.. _chap-dataorg:

#################
Data organization
#################

The main objects managed in Neuma are *corpus(es)* and *opus(es)*. They 
implement a data organization comparable to the classical
concepts of *folders* and *files* in a computer. A *corpus*
is a container. Its content consists of either 
opuses or (sub)corpuses. An *opus* is a musical work, such as, e.g., The Goldberg variations
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

As explained above, a corpus is a container, whereas an opus
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

The hierarchy of corpuses
=========================

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
details the corpus content. 

Sub-corpuses
============

Let's examine first the case
of a "folder" corpus, e.g., a corpus that contains
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

Note also that each corpus has a unique parent. By clicking
on the parent's icon, one can move up one level in the hierarchy.

Opus containers
===============

It turns out that ``all:composers`` consists only of sub-corpuses,
one for each composer. For a corpus consisting of opuses, a 
list is shown with a music score incipit (:numref:`exploringCorpus`, showing
the first opuses of corpus ``all:airs:cdc``).

.. _exploringCorpus2:
.. figure:: ./figures/exploringCorpus2.png       
        :width: 90%
        :align: center
   
        A corpus with opuses

Each opus in the list is shown with a title, the composer (if known)
and the corpus it belongs to. By clicking of the title, one can access
to the page that details the opus.

***************
The Opus object
***************

An Opus gathers a set of information related to a musical work,
including  *digital score* in XML format (MusicXML or MEI). 
:numref:`opus_page` shows how this information is displayed in the
web page dedicated to an opus. 

.. _opus_page:
.. figure:: ./figures/opus_page.png       
        :width: 90%
        :align: center
   
        A page showing an Opus

Metadata
========

Score
=====

Sources
=======

Features
========

Annotations
===========



