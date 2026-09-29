# Document de Passation (Handoff) — Pâtisserie Studio

> **Application** : Pâtisserie Studio — Catalogue Automatique  
> **Version** : 1.2.0 (Maintenance Complète, Tests Automatisés & Cartographie Graphify)  
> **Auteur / Équipe** : Antigravity AI (Google DeepMind Agentic Coding)  
> **Dernière Maintenance** : 29 Septembre 2026  


---

## 📌 1. Vue d'Ensemble & Objectif du Projet

**Pâtisserie Studio** est une solution web et mobile complète conçue pour automatiser la création de catalogues de produits pâtissiers à partir de captures d'écran brutes (issues de WhatsApp, Instagram, Facebook ou galeries photos).

### Problème résolu :
Les captures d'écran mobiles contiennent des barres d'état, des textes de chat, des boutons ("Envoyer un message") et des éléments d'interface parasite. L'application extrait automatiquement le rectangle de la photo du produit, sauvegarde le visuel propre dans un dossier par catégorie, extrait automatiquement les prix (ex: `15 000 FCFA`), met à jour un registre Excel central et permet l'exportation en ZIP.

---

## 🏷️ 2. Moteur d'Extraction Automatique du Prix (Nouveau !)

L'application intègre un moteur d'analyse Regex intelligent capable d'extraire automatiquement les montants en FCFA / Francs :
- **Entrée dans la catégorie** : si vous saisissez `"Gâteau d'anniversaire à 15000 francs"`, le système :
  1. Nettoie le nom de la catégorie : `"Gâteau d'anniversaire"`
  2. Formate et enregistre le prix : `"15 000 FCFA"`
  3. Nomme le dossier de stockage de façon propre : `gateau_danniversaire`
- **Champ Prix Dédié** : un champ optionnel *"Prix (ex: 15 000 FCFA)"* est également disponible lors de la création de la catégorie.
- **Badges et Registre Excel** : le prix est affiché sous forme de badge vert sur les cartes produits, les pilules de catégories, et inscrit dans la colonne **`Prix`** du registre `catalogue_global.xlsx`.

---

## 🛠️ 3. Architecture & Technologies Utilisées

| Composant | Technologie | Rôle / Description |
| :--- | :--- | :--- |
| **Backend API** | Python 3.11 + FastAPI | Traitement asynchrone, endpoints REST et gestion d'exportation |
| **Gestionnaire de dépendances** | `uv` (Fast Python Package Installer) | Environnement virtuel ultra-rapide et reproductible |
| **Base de Données** | SQLite 3 | Stockage des catégories (avec champ `price`), captures brutes et produits traités |
| **Moteur d'Image & Prix** | OpenCV + PIL + Regex | Détection de texture gradient, rognage automatique, extraction du prix |
| **Détourage AI** | `rembg` (U2-Net ONNX) | Option de suppression d'arrière-plan avec canal alpha RGBA |
| **Générateur Excel** | `openpyxl` | Génération du registre `catalogue_global.xlsx` (colonnes: Catégorie, Nom Fichier, Prix, Chemin, Date) |
| **Archivage** | Standard `zipfile` Python | Compression dynamique des sous-dossiers de catégories en `.zip` |
| **Frontend UI** | HTML5 / Vanilla JS / Tailwind CSS | Interface studio 100% responsive PC & Mobile avec badges de prix |

---

## 🚀 4. Fonctionnalités Clés Livrées

1. **✂️ Rognage Intelligent de Produit (Mode par défaut)**
2. **🏷️ Détection & Gestion des Prix (FCFA / Francs)**
3. **🪄 Détourage AI Optionnel (`rembg`)**
4. **📱 Synchronisation & Interface 100% Responsive Mobile**
5. **📊 Registre Excel Central Automatique avec colonne `Prix`**
6. **📦 Exportation ZIP par Catégorie & Global**
7. **🗑️ Galerie Interactives, Lightbox & Nettoyage en 1 Clic**

---

## 📁 5. Arborescence du Projet

```text
Automatisation/
├── app/
│   ├── config.py              # Chemins de base et constantes du projet
│   ├── db.py                  # Schéma SQLite avec support des prix & regex extraction
│   ├── main.py                # Point d'entrée FastAPI, routage et fichiers statiques
│   ├── routes/
│   │   ├── categories.py      # REST API: CRUD des catégories avec prix
│   │   ├── upload.py          # REST API: Téléversement des captures d'écran brutes
│   │   ├── process.py         # REST API: Rognage, statut temps réel & suppression
│   │   └── export.py          # REST API: Téléchargements ZIP et Excel
│   ├── services/
│   │   ├── processor.py       # Moteur OpenCV + PIL + rembg + extraction de prix
│   │   ├── excel.py           # Service openpyxl avec colonne Prix
│   │   └── exporter.py        # Service d'archivage zipfile
│   ├── static/
│   │   └── js/app.js          # Client JS avec rendu des prix
│   └── templates/
│       └── index.html         # Dashboard studio responsive
├── uploads_bruts/             # Stockage des captures d'écran brutes par catégorie
├── catalogue_final/           # Stockage des visuels propres et du registre Excel
│   └── catalogue_global.xlsx
└── HANDOFF.md                 # Le présent document de passation
```

---

## 💻 6. Guide de Démarrage

```bash
cd /Users/farelviaho/Desktop/Automatisation
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### URLs d'accès :
- **Sur votre PC** : 👉 `http://localhost:8000`
- **Sur votre Téléphone** : 👉 `http://192.168.1.73:8000`
