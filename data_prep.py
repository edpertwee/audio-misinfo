# Script to clean raw Talkwalker podcast data

import pandas as pd
import numpy as np
from datetime import datetime


# Read in dataset matching exact phrase "polio vaccin*"
df1 = pd.read_excel("./data/raw/polio_vaccin_20220823_20220923.xlsx")
df2 = pd.read_excel("./data/raw/polio_vaccin_20220924_20221031.xlsx")
polio_vaccin = pd.concat([df1, df2], ignore_index=True)

# Read in dataset containing keywords "polio AND vaccin*"
df3 = pd.read_excel("./data/raw/polio_AND_vaccin_20220823_20220923.xlsx")
df4 = pd.read_excel("./data/raw/polio_AND_vaccin_20220924_20221031.xlsx")
polio_and_vaccin = pd.concat([df3, df4], ignore_index=True)

# Print the shape of the DataFrames
print("Exact phrase search results (rows, columns): "
      + str(polio_vaccin.shape))
print("Keyword search results (rows, columns): "
      + str(polio_and_vaccin.shape))

# Merge datasets and create indicator column to show which dataset
# each entry came from
combined = polio_and_vaccin.merge(
    polio_vaccin.drop_duplicates(), on=['url','title'],
    how='left', indicator=True)
polio_and_vaccin["match"] = combined["_merge"]

# Print the shape of the final dataset
print("Final dataset (rows, columns): " + str(polio_and_vaccin.shape))

# Give each entry a unique identifier
polio_and_vaccin['unique_id'] = np.arange(polio_and_vaccin.shape[0])
polio_and_vaccin['unique_id'] = polio_and_vaccin['unique_id']+1

# Remove duplicate columns (based on column values)
print("Number of columns to be removed:")
print(len(polio_and_vaccin.T[polio_and_vaccin.T.duplicated()]))
print("List of columns to be removed:")
print(polio_and_vaccin.T[polio_and_vaccin.T.duplicated()].index.values)
polio_and_vaccin = polio_and_vaccin.T.drop_duplicates().T

# Remove other columns unncessary for analysis
cols_to_drop = ["display_url", "lang", "source_type", "post_type",
                "tags_internal", "entity_urls", "matched_profile",
                "pagemonitoring_sitemon_siteid",
                "article_extended_attributes.facebook_shares",
                "extra_article_attributes.world_data.continent",
                "extra_article_attributes.world_data.country",
                "extra_article_attributes.world_data.country_code",
                "extra_article_attributes.world_data.region",
                "extra_article_attributes.world_data.city",
                "extra_article_attributes.world_data.longitude",
                "extra_article_attributes.world_data.latitude",
                "extra_author_attributes.id",
                "extra_author_attributes.id"]

polio_and_vaccin.drop(columns = cols_to_drop, inplace=True)

# Set remaining column names to be human readable
polio_and_vaccin.columns = [
    col.replace('extra_source_attributes.', '') 
    for col in polio_and_vaccin.columns]
polio_and_vaccin.columns = [
    col.replace('source_extended_attributes.', '') 
    for col in polio_and_vaccin.columns]
polio_and_vaccin.columns = [
    col.replace('world_data.', '') 
    for col in polio_and_vaccin.columns]

polio_and_vaccin.rename(
    columns = {"title": "episode_title",
               "images.url": "image_url",
               "source_extended_attributes.alexa_pageviews": "alexa_pageviews",
               "extra_author_attributes.name": "author_names",
               "extra_author_attributes.gender": "author_gender",
               "name": "podcast_name"},
    inplace = True)

# Reorder columns for convenience
polio_and_vaccin = polio_and_vaccin.loc[:,['unique_id', 'url', 'podcast_name',
                                           'episode_title', 'author_names',
                                           'title_snippet', 'content_snippet', 
                                           'content', 'match',
                                           'continent', 'country',
                                           'country_code', 'region', 'city', 
                                           'longitude', 'latitude',
                                           'nsfw_level', 'sentiment',
                                           'cluster_id', 'author_gender',
                                           'alexa_pageviews',
                                           'alexa_unique_visitors',
                                           'word_count', 
                                           'indexed', 'published',
                                           'search_indexed', 'domain_url',
                                           'host_url', 'image_url']]

# Annotate rows based on relevance (whether contain exact phrase 
# "polio vaccin*" or keywords polio AND vaccin* only)
polio_and_vaccin["match"].replace({"left_only": "keywords only",
                                  "both": "exact phrase"}, inplace=True)

# Save pre-processed data to Excel file
now = datetime.now()
datetime_string = now.strftime("%Y%m%d_%H%M%S")

output = polio_and_vaccin.to_excel(
    "./data/clean/polio_vaccine_podcasts_"+datetime_string+".xlsx",
    index = False)