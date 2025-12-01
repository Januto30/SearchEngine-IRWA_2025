# SearchEngine-IRWA_2025

**Repository:** [SearchEngine-IRWA_2025](https://github.com/yourusername/SearchEngine-IRWA_2025)  
**Course:** Information Retrieval and Web Analytics (IRWA) – 2025  
**Environments:**
- Part 1/2/3: Google Colab (Python 3)
- Part 4: Visual Studio Code (Python 3)

## Project Overview:
This repository contains the implementation of the **IRWA 2025 Final Project**, an incremental development of a **Retrieval-Augmented Generation (RAG)** system.  
The objective is to build a **custom search engine** implementing different text processing, indexing, ranking, and RAG techniques across four parts:

| Part | Topic  |  Delivery Date |
|------|--------|----------------|
| 1 | Text Processing & Exploratory Data Analysis | 24/10/2025 |
| 2 | Indexing & Evaluation | 02/11/2025 |
| 3 | Ranking & Filtering | 20/11/2025 |
| 4 | RAG, User Interface & Web Analytics | 04/12/2025 |

All parts are implemented in a Jupyter notebook (Python3), tagged in GitHub as `IRWA-2025-part-N`, while Part 4 is developed separately in Visual Studio Code using Python and the Flask web framework.

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
├── IRWA-2025-part-3/
│ ├── IRWA_2025_part_3.ipynb
│ ├── IRWA-2025-u214970-u213927-u214026-part-3.pdf
│ └── data/
│   ├──  fashion_products_dataset.json
│   └──  validation_labels.csv
├── IRWA-2025-part-4/
│ ├── IRWA-2025-u214970-u213927-u214026-part-4.pdf
│ ├── myapp/
│ ├── project_progress/
│ ├── static/
│ ├── templates/
│ ├── .gitignore
│ ├── LICENSE
│ ├── README.md
│ ├── requirements.txt
│ └── web_app.py
│
└── README.md
```

---

## 🚀 How to Run on Google Colab (applicable for Part 1/2/3)

All notebooks are designed for **Google Colab**, so no local setup is required.

1. Open the corresponding notebook (`IRWA_2025_part_N.ipynb`) on GitHub.  
   - Click **"Open in Colab"** or copy the notebook link into [Colab](https://colab.research.google.com/).  
2. Mount your Google Drive when prompted.  
3. Verify that the dataset folder (`/data/`) is correctly located in your Drive or repository.

   ⚠️ Important:
      Paths to the data files (e.g., /content/drive/MyDrive/...) may vary depending on your personal Google Drive structure.
      You might need to modify the path variables at the beginning of the notebook to point to your actual data location.
      Example:
      ``` DATA_PATH = "/content/drive/MyDrive/IRWA_2025/data/fashion_products_dataset.json"```

6. Run all cells sequentially (Runtime → Run all).  
7. The notebook will automatically install any missing libraries at the beginning (using `!pip install ...`).  

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

## 📙 Part 3 – Ranking & Filtering 

**Objective:**
Experiment with different ranking algorithms to sort documents by relevance for conjunctive queries.

**Main Steps:**
- Implement three ranking methods:
- TF-IDF + cosine similarity for classical term-based scoring
- BM25 for probabilistic relevance scoring
- Custom score combining relevance signals such as ratings, stock availability, price, and discounts
- Apply word2vec + cosine similarity to represent queries and documents as averaged word vectors and rank accordingly
- Compare ranking outcomes across methods and analyze their advantages and limitations

**Output:**
Top-k ranked documents per query, precision and recall metrics, and a comparison of ranking performance across TF-IDF, BM25, and the custom score.

---

## 📒 Part 4 – RAG, User Interface & Web Analytics

**Objective:**
Give our search engine a user interface (UI) and apply some web analytics to it.

**Main Steps:**
- Extend the provided Flask web framework with a proper search page, results page, and document details view.
- Connect the UI to a unified search() function that calls the optimized ranking algorithms.
- Enhance the baseline RAG component with improved prompts, metadata usage, and LLM-based result summarization.
- Add analytics tracking for queries, clicks, sessions, dwell time, and user context.
- Store analytics data in memory using a simple schema and present insights in an analytics dashboard.

**Output:**
A Web application for entering the search query, displaying the search results, and collecting usage statistics.

---

## Group Information

**Group Members:**

- Carla Núñez
- Julia Pérez
- Jan Prats

---



