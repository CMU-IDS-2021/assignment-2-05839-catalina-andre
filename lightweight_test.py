import streamlit as st
import pandas as pd
import altair as alt

from sklearn.cluster import DBSCAN, KMeans
from sklearn.manifold import TSNE

from vega_datasets import data


def clustering_visual(df):
    feature_matrix = df.select_dtypes(include='number').to_numpy(na_value=0)
    clustering = KMeans().fit(feature_matrix)
    tsne_embed = TSNE().fit_transform(feature_matrix)

    tsne_df = pd.DataFrame({
        'tsne_x': tsne_embed[:, 0],
        'tsne_y': tsne_embed[:, 1],
        'cluster': clustering.labels_})
    return tsne_df


st.title("Let's analyze some Social Mobility Data 📊.")


@st.cache  # add caching so we load the data only once
def load_data():
    # Load the social mobility data from Opportunity Insights
    return pd.read_csv("health_ineq_online_table_12.csv", encoding="ISO-8859-1")


@st.cache
def load_counties():
    return alt.topo_feature(data.us_10m.url, 'counties')


df = load_data()

st.write("Let's look at the raw data in a Pandas Data Frame.")

st.write(df)

counties = load_counties()

counties_map = alt.Chart(counties).mark_geoshape().encode(
    tooltip=["hhinc00:Q", 'county_name:N', 'statename:N'],
    color='hhinc00:Q'
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(df, 'cty', ['hhinc00', 'county_name', 'statename'])
).project(
    type='albersUsa'
).properties(
    width=700,
    height=500
)

states = alt.topo_feature(data.us_10m.url, 'states')

states_map = alt.Chart(states).mark_geoshape(
    stroke="black",
    strokeWidth=1.5
).properties(
    width=700,
    height=500
)

st.write(counties_map + states_map)

# Observed Relationships in the data (generally at the state level seems to be appropriate for exploration
"""
cs_educ_ba (graduated from college) - cs_fam_wkidsinglemom (single mom)
rel_tot (percent religious) - cs_fam_wkidsinglemom (single mom)
cs_elf_ind_man (proportion working in manufacturing) - cs_educ_ba (graduated from college)
cs_educ_ba (graduated from college) - cs_labforce (labor force participation)
cs_educ_ba (graduated from college) - hhinc00 (household income)
cs_educ_ba (graduated from college) - poor_share (share of pop in poverty)
cs_educ_ba (graduated from college) - tuition (cost of tuition) (interesting b/c no relationship)
subcty_exp_pc (local gov't spending) - taxrate (local government tax rate)
cs_born_foreign (share of pop foreign born) - crime_total (local crime rate) (no relationship observed)
dropout_r (high school dropouts) - crime_total (crime rate) (some states have strong relationship, others not so much)

General Ideas for a story to tell with the Data:
- Confronting Stereotypes
  - explore and share if this data supports stereotypes about health, education, crime, etc.
  - one interesting one to consider is surrounding percentage of foreign born data
    - less crime, lower obesity, fewer single moms, less smoking, fewer high school dropouts
      generally are moving to areas others are moving away from, 
- Why are they leaving?
  - Consider areas people are migrating away from and show how those areas differ the most from
    areas people are staying in or moving to
  - again misconceptions could be interesting, like considering household income, home value, crime,
    education, etc.
- Which features are correlated?
  - Can make a SPLOM of select features -- either we curate these manually or programatically (i.e. try to fit line/curve to pair-plots)
  - Can let users select multiple features from a list (maybe with checkboxes)
- Which counties are most similar to each other?
  - Conjecture: this will not align with states: i.e. counties containing large cities will probably be more similar.
  - Might be too much for this homework, but we could maybe run clustering algortihms using these features.

Our design in greater detail:
- A single map showing the entire US with charts showing aggregate statistics on the right
  or maybe under the main plot (configurable displays, but maybe only show set combinations)
- The ability to compare two states with a choropleth display of the state's outline and a
  selected feature to compare more broadly.
    - sub-plots below compare the states more directly in different areas.
- Can guide a viewer through a story to expose differences between the Northeast and Southeast,
  mid-west and south-west, and/or the pacific north-west.
  A map from state to region can be found here: https://github.com/cphalpert/census-regions/blob/master/us%20census%20bureau%20regions%20and%20divisions.csv.

"""
