import streamlit as st
import pandas as pd
import altair as alt

from sklearn.cluster import DBSCAN, KMeans
from sklearn.manifold import TSNE


@st.cache
def load_geodata():
  return alt.topo_feature(
    "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/united-states/us-albers-counties.json",
    "collection"
  )


@st.cache
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


@st.cache
def load_data():
    # Load the social mobility data from Opportunity Insights
    df = pd.read_csv("health_ineq_online_table_12.csv", encoding = "ISO-8859-1")
    df['fips'] = ['{:05}'.format(num) for num in df.cty]
    return df


def choro_map(geo_data, df, column):
  tooltip_cols = ('name:O', 'state:O')
  chart = alt.Chart(geo_data).mark_geoshape(
  ).encode(
    color=alt.Color('{}:Q'.format(column), scale=alt.Scale(type='log', scheme='greenblue')),
    tooltip=[alt.Tooltip('properties.{}'.format(col), title=col.split(':')[0]) for col in tooltip_cols]
  ).properties(
    width=1000, height=600
  ).transform_lookup(
    lookup='properties.fips',
    from_=alt.LookupData(df, "fips", [column])
  ).project(
    'albersUsa'
  )

  return chart


df = load_data()

st.write("Let's look at the raw data in a Pandas Data Frame.")

st.write(df)

st.write(
    "Whew, that's a lot of columns!  Hmm 🤔, is there some correlation between the population and median house value? "
    "Let's make a scatterplot with [Altair](https://altair-viz.github.io/) to find out!")

picked = alt.selection_single(encodings=["color"], empty="none")

chart = alt.Chart(df).mark_point().encode(
    x=alt.X("cty_pop2000", scale=alt.Scale(zero=False)),
    y=alt.Y("median_house_value", scale=alt.Scale(zero=False)),
    color=alt.condition(picked, "statename:N", alt.value("lightgray"))
).properties(
    width=600, height=400
).interactive().add_selection(picked)

st.write(chart)

st.write(df.median_house_value)


st.write(
    "Yikes, that isn't super helpful, everyone is bunched in the corner and the states are too numerous to be clearly "
    "visible! Maybe we could do some filtering?")


# have to specify y domain, otherwise the plot renders strangely, not sure why
chart = alt.Chart(df).mark_point().encode(
    x=alt.X("cty_pop2000", scale=alt.Scale(type='log')),
    y=alt.Y("median_house_value", scale=alt.Scale(type='log', domain=[1, 10000000])),
    color=alt.condition(picked, "statename:N", alt.value("lightgray"))
).properties(
    width=600, height=400
).interactive().add_selection(picked)

st.write(chart)

st.write('Here is a first attempt at making this plot better by using log scales.',
    'Unfortunately, still a bit crowded...')


# avg all counties for each state, plot that avg as representative
agg_df = df.groupby('statename').mean()
agg_df['statename'] = [name for name, _ in df.groupby('statename')]

chart = alt.Chart(agg_df).mark_point().encode(
    x=alt.X("cty_pop2000", scale=alt.Scale(type='log')),
    y=alt.Y("median_house_value", scale=alt.Scale(type='log', domain=[1, 10000000])),
    color=alt.condition(picked, "statename:N", alt.value("lightgray"))
).properties(
    width=600, height=400
).interactive().add_selection(picked)
st.write(chart)

st.write('This is less crowded and shows that median_house_value & city_pop2000 are not correlated',
    'We should add tooltips so that on hover for each point, you see the state.',
    'Also, instead of having both log-scale and linear scale plots, we can have a checkbox toggle for this')


tsne_df = clustering_visual(df)

chart = alt.Chart(tsne_df).mark_point().encode(
    x=alt.X("tsne_x"),
    y=alt.Y("tsne_y"),
    color=alt.condition(picked, "cluster:N", alt.value("lightgray"))
).properties(
    width=600, height=400
).interactive().add_selection(picked)
st.write(chart)

st.write("What I've done above is running kmeans clustering on all numeric data. We can probably find a better clustering",
"But, the point is to answer 'Which counties are similar? We might find some interesting relationships this way.")

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

counties_data = load_geodata()
st.write(choro_map(counties_data, df, 'pop_density'))