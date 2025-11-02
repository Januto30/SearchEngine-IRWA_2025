# SearchEngine-IRWA_2025

**Repository:** [SearchEngine-IRWA_2025](https://github.com/yourusername/SearchEngine-IRWA_2025)  
**Course:** Information Retrieval and Web Analytics (IRWA) – 2025  
**Environment:** Google Colab (Python 3)

## Project Overview:
This repository contains the implementation of the **IRWA 2025 Final Project**, an incremental development of a **Retrieval-Augmented Generation (RAG)** system.  
The objective is to build a **custom search engine** implementing different text processing, indexing, ranking, and RAG techniques across four parts:

| Part | Topic  |  Delivery Date |
|------|--------|----------------|
| 1 | Text Processing & Exploratory Data Analysis | 24/10/2025 |
| 2 | Indexing & Evaluation | 02/11/2025 |
| 3 | Ranking & Filtering | 20/11/2025 |
| 4 | RAG, User Interface & Web Analytics | 29/11/2025 |

Each part is developed in a separate Jupyter notebook (in Python3), tagged in GitHub as `IRWA-2025-part-N`.

---

## 🗂️ Repository Structure
```
SearchEngine-IRWA_2025/
│
├── IRWA-2025-part-1/
│ ├── IRWA_2025_part_1.ipynb
│ ├── IRWA-2025-u214970-u213927-u214026-part-1.pdf
│ └── data/
│   ├──  fashion_products_dataset.json
│   └──  validation_labels.csv
├── IRWA-2025-part-2/
│ ├── IRWA_2025_part_2.ipynb
│ ├── IRWA-2025-u214970-u213927-u214026-part-2.pdf
│ └── data/
│   ├──  fashion_products_dataset.json
│   └──  validation_labels.csv
├── IRWA-2025-part-3/  #to be implemented
├── IRWA-2025-part-4/  #to be implemented
│
└── README.md
```

---

## 🚀 How to Run on Google Colab

All notebooks are designed for **Google Colab**, so no local setup is required.

1. Open the corresponding notebook (`IRWA_2025_part_N.ipynb`) on GitHub.  
   - Click **"Open in Colab"** or copy the notebook link into [Colab](https://colab.research.google.com/).  
2. Mount your Google Drive when prompted.  
3. Verify that the dataset folder (`/data/`) is correctly located in your Drive or repository.  
4. Run all cells sequentially (Runtime → Run all).  
5. The notebook will automatically install any missing libraries at the beginning (using `!pip install ...`).  

Each notebook produces outputs (tables, visualizations, evaluation metrics) directly within the Colab environment.

---

## 📘 Part 1 – Text Processing & Exploratory Data Analysis

**Objective:**  
Prepare and analyze the dataset `fashion_products_dataset.json`.

**Main Steps:**
- Load and inspect dataset  
- Text cleaning and normalization  
- Tokenization, stopword removal, stemming, and lemmatization (NLTK)  
- Word frequency analysis and visualizations (WordClouds, histograms)  
- Export preprocessed data for later parts  

**Output:**  
`preprocessed_fashion_products.csv` stored under `/data/`.

---

## 📗 Part 2 – Indexing & Evaluation

**Objective:**  
Implement indexing structures and evaluate retrieval performance.

**Main Steps:**
- Build inverted indexes from the preprocessed data  
- Apply term-weighting schemes (TF, TF-IDF)  
- Implement query matching functions  
- Evaluate retrieval quality using validation labels  
- Compute precision, recall, and F1-score  

**Output:**  
Evaluation metrics and retrieved document tables displayed in the notebook.

---

## 📙 Part 3 – Ranking & Filtering *(to be added)*
 

---

## 📒 Part 4 – RAG, User Interface & Web Analytics *(to be added)*

---

## Group Information

**Group Members:**

- Carla Núñez
- Julia Pérez
- Jan Prats

---
