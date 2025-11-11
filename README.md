# 🚇 RATP Incidents - NLP Classifier

🔗 **[Accéder au dashboard interactif](https://ratp-incidents.streamlit.app/))**

## 🎯 Objectif du projet

Les objectifs de ce projet sont de :
1. Regrouper et classer automatiquement les problèmes sur toutes les lignes de la RATP (technique, accident, travaux, incivilité, etc.) à l'aide d'un modèle NLP.
2. Analyser les fréquences par ligne, par heure, par mois, etc. afin d’identifier les périodes et types d’incidents les plus fréquents.

Ce travail permet également de distinguer les incidents directement imputables à la RATP (pannes, problèmes techniques et opérationnels) de ceux qui sont plus externes/indépendants (accidents, événements externes, intempéries, manifestations...).


## Contenu du projet

Le projet se compose de deux volets :

### 1. 🧠 Modèle NLP de classification
J'ai réalisé deux étapes pour cette partie :
- 1 : classification semi-supervisée avec mots-clés à la main pour commencer pour regrouper les incidents en clusters cohérents
- 2 : passage au NLP automatique qui va attribuer aux causes restantes un cluster en se basant sur la similarité sémantique avec les causes déjà attribuées à la partie 1. Le modèle apprend des catégories déjà définies et généralise pour les nouveaux incidents.

J'ai retenu 7 grandes familles de problème ici :
- Voyageurs : malaises, incidents voyageurs dont la cause n'est pas clairement indiquée, affluence exceptionnelle...
- Incivilités : altercations, agressions, etc mais aussi oublis de bagages.
- Externes : causes indépendantes de la RATP, événnement, manifestation, animaux sur les voies, intempéries, etc.
- Travaux
- Accidents : choc, accident
- Infrastructures : tout ce qui est relatif aux pannes, incidents techniques, défauts électriques ou informatiques
- Opérationnel : retard, cause liés aux conducteurs, grêves/mouvement social, régulations, etc.


### 2. 📈 Dashboard interactif Streamlit
Une application Streamlit permet d’explorer les résultats de classification et de visualiser les incidents selon plusieurs dimensions :
  - Lignes RATP (métro, RER, tram…)
  - Types d’incidents (souvent retirer les travaux pour plus de cohérence) 
  - Mois/année sélectionnés
  
    
- **Type de visualisations :**
  - Line plot comparatif entre lignes (nombre d’incidents ou durée totale en fonction de la tickbox)
  - Histogramme empilé par mois et type d’incident
  - Bar plot des % de jours ayant des incidents pour voir les jours les plus concernés s'il y en a
  - Heatmap pour avoir les heures les plus "problèmatiques"

