# SearchEngine-IRWA_2025

## Description:

This subject explores techniques for retrieving and analyzing information from large-scale data sources, particularly the web. It combines information retrieval (IR) principles with web data mining to address challenges like search engine design, data extraction, and user behavior analysis.

---

## Group Information

**Group Members:**

- Carla Núñez
- Julia Pérez
- Jan Prats

---

## Functions

### PART 1.1 — Data Preparation

#### **`build_terms(line: string) -> list[str]`**
Cleans and tokenizes a text string by:
- Converting to lowercase  
- Removing punctuation and stopwords  
- Applying tokenization
- Applying stemming  

#### **`combine_product_details(details_list: list[dict]) -> str`**
Concatenates the values of product_details (list of dictionaries) into a single string.

---

## Output: Part 1.1 — Data Preparation

Once the preprocessing functions were defined, we applied them to all product entries in the dataset.  
The goal of this step is to systematically clean and tokenize the textual content of each product (title and description), storing the processed tokens for subsequent analysis.

### Example — Before and After Preprocessing

**=== Original Product ===**  
Title      : Solid Women Multicolor Track Pants

Description: Yorker trackpants made from 100% rich combed cotton giving it a rich look.Designed for Comfort,Skin friendly fabric,itch-free waistband & great for all year round use Proudly made in India

**=== After Preprocessing ===**  
Title Tokens      : ['solid', 'women', 'multicolor', 'track', 'pant']

Description Tokens: ['yorker', 'trackpant', 'made', '100', 'rich', 'comb', 'cotton', 'give', 'rich', 'look', 'design', 'comfort', 'skin', 'friendli', 'fabric', 'itch', 'free', 'waistband', 'great', 'year', 'round', 'use', 'proudli', 'made', 'india']

---
## Output: Part 1.2 — Exploratory Data Analysis

### **Word Cloud**
The visualization highlights the most frequent words, including **“men,” “women,” “shirt,” “round,” “neck,” “fit,” “slim,”** and **“solid.”**  
This indicates that the dataset primarily focuses on apparel products, especially tops and shirts.

---

### **Histogram of Selling Prices**
Selling prices show a **right-skewed distribution**, where most products are priced **below €1,000**, with only a few extending to higher price ranges.

---

### **Histogram of Average Ratings**
Most ratings fall between **3.5 and 4 out of 5**, suggesting that users generally find these products **satisfactory or above average**.

---

### **Bar Chart of Top Brands**
A small number of brands such as **ECKO Uni**, **Free Authority**, **ARBO**, and **REEB** represent a large portion of the dataset,  
while many other brands appear infrequently.

---

### **Bar Chart of Top Categories**
The **“Clothing and Accessories”** category dominates the dataset, followed by **“Footwear”** and smaller categories like **“Bags, Wallets & Belts”** and **“Toys.”**

---

### **Bar Chart of Out-of-Stock Products**
Most products are **available**, while only a small portion are **currently out of stock**.
