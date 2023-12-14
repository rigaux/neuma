# Outils de mesure de différence et de qualité

On reprend le code de Francesco, lui-même amélioré par Greg Chapman (https://github.com/gregchapman-dev/musicdiff).

## Installation

Créer un environnement avec *a minima* python3.10. Installer les packages 

```
pip3 install -r requirements.txt
``

L'utilitaire doit être dans le chemin ``PYTHONPATH``.

```
export PYTHONPATH=./musicdiff
```

On doit alors pouvoir l'exécuter 

```
python3 musicdiff/musicdiff -h
```


Essayer sur les jeux de test

```
python3 musicdiff/musicdiff/ data/invention1.mei data/invention2.mei 
```

On obtient un affichage PDF (déclenché par music21) des deux partitions, avec les différences mises en évidence. 
