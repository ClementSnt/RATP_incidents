# Imports
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm
import torch
import re
import unicodedata
import spacy
import nltk
from nltk.corpus import stopwords

# Import des données
df = pd.read_csv('historique_incidents.csv', sep=';')
causes_uniques = df['origine incident'].dropna().unique().tolist()
print(f"Nombre de causes uniques : {len(causes_uniques)}")

# clean avec Stopwords et spaCy
nltk.download('stopwords')
STOPWORDS = set(stopwords.words('french'))
nlp = spacy.load("fr_core_news_sm", disable=["parser", "ner"])

def nettoyer_texte(texte):
    """Nettoyage et lemmatisation simple"""
    if not isinstance(texte, str):
        return ""
    texte = texte.lower()
    texte = ''.join(c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn')
    texte = re.sub(r'[^a-z\s]', ' ', texte)
    mots = [mot for mot in texte.split() if len(mot) > 2]
    return " ".join(mots)

causes_nettoyees = [nettoyer_texte(c) for c in tqdm(causes_uniques, desc="Nettoyage")]

# Modèle CamemBERT
model = SentenceTransformer("dangvantuan/sentence-camembert-large")

# Clusters et mots-clés pour aider le modèle a faire des clusters pertinents
themes = {
    "voyageur": ["voyageur", "individu", "personne", "malaise", "chute",
                 "affluence", "retard voyageur", "présence quai"],
    
    "incivilite": ["agression", "altercation", "bagarre", "acte", "caillassage",
                   "vandalisme", "bagage", "colis suspect", "signal alarme", "oublie","dégradation"],

    "travaux": ["travaux", "chantier", "maintenance programmée",
                "modernisation", "renouvellement"],

    "infrastructure": ["signalisation", "caténaire", "défaillance", "défaut matériel",
                        "aiguillage", "voie", "système", "équipement", "infrastructure",
                        "incident", "intervention", "perturbation", "panne train",
                        "retard technique", "incident d’exploitation","dysfonctionnement","défaut","défaillance"],

    "accident": ["accident", "heurt", "collision", "choc", "suicide", "animal heurté"],

    "operationnel": ["exploitation", "régulation", "retard", "gestionnaire réseau",
                     "manque de rame", "conducteur", "personnel", "grève",
                     "mouvement social", "plan de transport"],

    "externe": ["manifestation", "concert", "météo", "neige", "intempéries", "tempête",
                "préfecture", "animal", "fête", "jeux", "arbre", "cérémonie",
                "autoroute", "inondation", "orage", "vent violent", "canicule"]
}



# Step 0 : vectorisation des mots-clés par thème
theme_keyword_embeddings = {}
for theme, kw_list in themes.items():
    kw_clean = [nettoyer_texte(kw) for kw in kw_list]
    theme_keyword_embeddings[theme] = model.encode(kw_clean, convert_to_tensor=True)

# Étape 1 : attribution lexicale vectorisée
assigned_themes_lex = []
threshold_lex = 0.4  # seuil pour la similarité avec mots-clés => assez bas volontairement pour favoriser l'attribution à un cluster sinon trop restrictif et trop de données dans "autres", d'autant que les autres mots des motifs peuvent diluer

cause_embeddings = model.encode(causes_nettoyees, convert_to_tensor=True)

for emb in tqdm(cause_embeddings, desc="Étape 1 : Attribution lexicale"):
    sims_theme = {}
    for theme, kw_embs in theme_keyword_embeddings.items():
        sim = util.cos_sim(emb, kw_embs).max().item()
        sims_theme[theme] = sim
    best_theme = max(sims_theme, key=sims_theme.get)
    if sims_theme[best_theme] >= threshold_lex:
        assigned_themes_lex.append(best_theme)
    else:
        assigned_themes_lex.append(None)
      
# Étape 2 : attribution sémantique pour les non attribués

# Embeddings moyens par thème (cause déjà attribuées) => comme les clusters commencent à être déjà fournis plus pertinent

theme_mean_embeddings = {}
for theme in themes.keys():
    idx_theme = [i for i, t in enumerate(assigned_themes_lex) if t == theme]
    if idx_theme:
        theme_mean_embeddings[theme] = cause_embeddings[idx_theme].mean(dim=0)
    else:
        theme_mean_embeddings[theme] = theme_keyword_embeddings[theme].mean(dim=0)

assigned_themes_sem = []
threshold_sem = 0.4  # Pareil assez bas volontairement mêmes raisons

for i, theme in enumerate(assigned_themes_lex):
    if theme is not None:
        assigned_themes_sem.append(theme)
        continue
    emb = cause_embeddings[i]
    sims = {t: util.cos_sim(emb, theme_mean_embeddings[t]).item() for t in themes.keys()}
    best_theme = max(sims, key=sims.get)
    if sims[best_theme] >= threshold_sem:
        assigned_themes_sem.append(best_theme)
    else:
        assigned_themes_sem.append("autres")  # Étape 3 : garde-fou, on met tout dans autres 

# Résultat final
mapping_df = pd.DataFrame({
    "cause_originale": causes_uniques,
    "cause_nettoyee": causes_nettoyees,
    "theme_final": assigned_themes_sem
})

# Affichage complet des clusters 
for theme in sorted(mapping_df["theme_final"].unique()):
    subset = sorted(mapping_df[mapping_df["theme_final"] == theme]["cause_originale"].tolist())
    print(f"Thème : {theme} ({len(subset)} causes)")
    for c in subset:
        print(f" - {c}")

# Export CSV
mapping_df.to_csv("mapping.csv", index=False)
