.. _chap-analysis:
   

########
Analysis
########

The chapter describes all the operations that produce analytic features from
corpora and opera.


***************
Analytic models
***************

An analysis is run with respect to an *analytic model*. Essentially, such a model
is a forest of concepts, and each concept has a specific semantics. For 
instance:

  - in the *counterpoint* analytic model, one finds a taxonomy of dissonances
    found in Medieval/Renaissance counterpoint.
  - in the *quality* analytic model, one finds a forest of quality measures
    such as metadata issues, rendering issues, etc.
    
Defining analytic models
========================

An analytic model is defined in an XML file, located in ``static/analytic_models``.
The following is an excerpt of the ``quality_model.xml`` document.

.. code-block:: xml

    <?xml version="1.0" encoding="utf-8" ?>

    <analytic_model id="quality">
        <name>Quality</name>
        <description>Quality measures
        </description>

    
        <!-- Tree of concepts -->
        <concepts>
            <concept id="content">
                <name>Music content issues</name>
                <description>
                    Quality issues related to the content of the score, and
                    not to its rendering
                </description>
                <concepts>
                    <concept id="structure">
                       ...
                    </concept>
                     <concept id="voice">
                    ...
                    </concept>
                    <concept id="lyrics">
                        <name>Lyrics issues</name>
                        <description>
                            Issues related to lyrics (if any) and their
                            relationship to music
                        </description>
                        <concepts>
                          <concept id="invalidlyrics">
                            <name>Invalid lyrics encoding</name>
                            <description>
                                The lyrics text contains invalid characters.
                            </description>
                           </concept>
                        </concepts>
                 </concept>
            </concepts>
        </concept>
      </concepts>
    </analytic_model>

Each concept has an id, a name (displayed in interfaces) and a description
(used in tooltips windows). The id has to be unique.

A model has to be imported in the database. This is done by running the following
command.

.. code-block:: bash

     python3 manage.py setup_neuma

A concept has also a semantic: it associates some meaning to some elements
in a music score (usually a note). For instance, a ``missing lyrics`` concept
associated to a note tells that the note should have a syllable, and that 
this syllable is missing.

Running an analysis means discovering all the meanings of the elements
of a score with respect to the concepts of an analytic model. This
produces *annotations*.
 
Annotations
===========

An annotation stores the list of associations between scores elements
and concepts of an analytic model. An annotation is stored in table ``Annotation``
and is produced by a procedure (usually a Python function) that implements
the meaning of each concept.

Here is a basic example of such a function. It identifies missing lyrics
in a voice.

.. code-block:: python

    @staticmethod
    def missing_lyrics(opus, voice):
        """ Missing lyrics metrics"""
        
        for event in voice.m21_stream.notes:
            if not event.hasLyrics():
                try:
                    db_concept = AnalyticConcept.objects.get(code=AC_QUAL_MISSING_LYRICS)
                    annot = Annotation(opus=opus, ref=event.id, 
                               analytic_concept=db_concept, 
                               fragment= json.dumps([event.id]))
                    annot.save()
                except AnalyticConcept.DoesNotExist:
                    print ("Unknown concept : " + AC_QUAL_MISSING_LYRICS)
        return

So the function looks at events (notes, chords, rests, etc.) and determines, for each,
if it matches to concept (here, missing lyrics). If yes, an annotation
is created with:
 
  - The Opus 
  - The concept 
  - The fragment qualified by the concept, i.e., the list if event ids
    That together matches the concept meaning
  - The id of a specific event in the fragment, that will be used to display the concept
    in a graphic representation.
  
Ids are taken from the MEI file. 

The code refers to a ``AC_QUAL_MISSING_LYRICS`` constant: this is the id of the
concept, declared in ``/scorelib/analytic_concepts.py``. This id must match
the id of the concept in the XML file: see above.

Cookbook
========

In order to define a new concept, you must:

  - describe it in the the corresponding XML analytic model file;
  - insert in the DB with ``python3 manage.py setup_neuma``;
  - declare the concept id in ``/scorelib/analytic_concepts.py``;
  - last, but no least, implement the concept semantic as a Python function 
    (in general).
    
Finally the function call has to be put in the analytic workflow
of the model. These workflow are in ``lib/workflow/Workflow.py``.

For the quality model, the workflow is specifically found in ``/quality//lib/Processor.py``.


    
.. note:: A REST call can be used to obtain the forest of concepts
     for a model. In JSON:
   
     .. code-block:: bash
     
       curl http://neuma.huma-num.fr/rest/analysis/models/quality/concepts/json/
       
    or in Latex
    
     .. code-block:: bash
     
         curl http://neuma.huma-num.fr/rest/analysis/models/quality/concepts/latex/
    
*******************
Similarity measures
*******************

Measures
========

Evaluation of similarity is based on a measure. The list of measures is put in a DB
table called ``SimMeasure`` that can be edited, via the ``/neumadmin`` interface. Insert
at least one measure, called ``pitches``.


Building a measure matrix
=========================

A matrix of similarities can be built for all the opera of a corpus thanks
to the following command:

.. code-block:: bash

      python3 manage.py scan_corpus -a cptdist -c <corpus_id> 

Par exemple:

.. code-block:: bash

      python3 manage.py scan_corpus -a cptdist -c psautiers:godeau1658 
      
One matrix is produced for each of the similarity measures found in table ``SimMeasure``. 


**********
Clustering
**********

