# SearchEngine-IRWA_2025

Description:

This subject explores techniques for retrieving and analyzing information from large-scale data sources, particularly the web. It combines information retrieval (IR) principles with web data mining to address challenges like search engine design, data extraction, and user behavior analysis.

Group Information

Group:

Carla Núñez
Julia Pérez
Jan Prats

Functions

PART 1.1: Data preparation

built_terms(line: string): list of strings.

combine_product_details(details_list: list of dictionaries): string

Output Part 1.1 (Data preparation)

Once the preprocessing functions were defined, we applied them to all product entries in the dataset. The goal of this step is to systematically clean and tokenize the textual content of each product (title and description), storing the processed tokens for subsequent analysis. An example of the before and after the preprocessing of a product would be the following:

=== Original Product ===
Title      : Solid Women Multicolor Track Pants
Description: Yorker trackpants made from 100% rich combed cotton giving it a rich look.Designed for Comfort,Skin friendly fabric,itch-free waistband & great for all year round use Proudly made in India
=== After Preprocessing ===
Title Tokens      : ['solid', 'women', 'multicolor', 'track', 'pant']
Description Tokens: ['yorker', 'trackpant', 'made', '100', 'rich', 'comb', 'cotton', 'give', 'rich', 'look', 'design', 'comfort', 'skin', 'friendli', 'fabric', 'itch', 'free', 'waistband', 'great', 'year', 'round', 'use', 'proudli', 'made', 'india']


Output Part 1.2 (Exploratory Data Analysis)

- Word Cloud
From the visualization, the most important words include “men,” “women,” “shirt,” “round,” “neck,” “fit,” “slim,” and “solid.” Indicating that the dataset is heavily focused on apparel products, especially tops and shirts.

- Histogram of Selling Prices
Selling prices have a clear right-skewed distribution, where most products are priced below 1.000 euros, and only a few extend to higher price ranges.

- Histogram of Average Ratings
Most ratings fall between 3.5 and 4 points out of 5, indicating that users generally perceive these products as satisfactory or above average.

- Bar Chart of Top Brands
Only a few brands ( “ECKO Uni,” “Free Authority,” “ARBO,” “REEB”, ..) account for a large portion of the dataset, while many other brands appear infrequently.

- Bar Chart of Top Categories
The plot reveals that the “Clothing and Accessories” category dominates the dataset, followed by much smaller portions of “Footwear” and a few other categories like “Bags, Wallets & Belts” or “Toys.” 

- Bar Chart of Out-of-Stock Products
Most products are available, while only a smaller share is currently out-of-stock.
