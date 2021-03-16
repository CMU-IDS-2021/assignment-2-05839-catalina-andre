import streamlit as st
import pandas as pd
import altair as alt

from sklearn.cluster import DBSCAN, KMeans
from sklearn.manifold import TSNE

from vega_datasets import data


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


@st.cache
def load_data():
    # Load the social mobility data from Opportunity Insights
    df = pd.read_csv("health_ineq_online_table_12.csv", encoding="ISO-8859-1")
    df['fips'] = ['{:05}'.format(num) for num in df.cty]
    return df


@st.cache
def load_counties():
    return alt.topo_feature(data.us_10m.url, 'counties')


def choro_map(geo_data, df, column, scale):
    tooltip_cols = ('properties.name:O', 'properties.state:O', '{}:Q'.format(column))
    chart = alt.Chart(geo_data).mark_geoshape(
    ).encode(
        color=alt.Color('{}:Q'.format(column), scale=alt.Scale(type=scale, scheme='greenblue')),
        tooltip=[alt.Tooltip(col, title=col.split(':')[0]) for col in tooltip_cols]
    ).properties(
        width=1000,
        height=600
    ).transform_lookup(
        lookup='properties.fips',
        from_=alt.LookupData(df, "fips", [column])
    ).project(
        'albersUsa'
    )

    return chart


def feature_dropdown(s, key, default_val):
    remove_cols = ('fips', 'cz', 'state_id', 'stateabbrv', 'csa', 'cbsa', 'intersects_msa')
    keep_cols = [c for c in df.columns if 'name' not in c and c not in remove_cols]
    default_index = keep_cols.index(default_val)
    return st.selectbox(s, keep_cols, key=key, index=default_index)


def scale_dropdown(key):
    return st.selectbox('Log or linear scale?', ('log', 'linear'), key=key)


def pair_plot(df, x_str, y_str, scale_str, tooltip_cols=[]):
    scale_params = {'zero': False} if scale_str == 'linear' else {'type': 'log', 'domain': [1, 10000000]}

    return alt.Chart(df).mark_point().encode(
        x=alt.X(x_str, scale=alt.Scale(type='log')),
        y=alt.Y(y_str, scale=alt.Scale(**scale_params)),
        tooltip=[alt.Tooltip(col, title=col.split(':')[0]) for col in tooltip_cols],
        color=alt.Color('statename:N')
    ).properties(
        width=600,
        height=400
    )


def find_common(row):
    county = row.County
    if county in foreign_counties and county in selected_counties:
        color = "darkorange"
    else:
        color = "white"
    return ["background-color: %s" % color for _ in row]


st.title("Confronting Negative Stereotypes of Immigration")

df = load_data()

st.markdown("One does not have to look far or hard to find political commentary peddling the dangers of allowing "
            "widespread immigration into the United States. When many voices speak with authority, it can be difficult "
            "to know what to listen to and how to distinguish fact from fiction. While data may not be perfect, and we "
            "certainly do not claim to be, we think that by exploring some of the statistics behind the claims, we can "
            "offer a different perspective. For our analysis we considered [this summary]"
            "(https://www.cato.org/blog/14-most-common-arguments-against-immigration-why-theyre-wrong) "
            "of common arguments against liberal immigration policies in America. It is written by "
            "[Alex Nowrasteh](https://www.cato.org/people/alex-nowrasteh), the Directory OF Immigration Studies at the "
            "Center For Global Liberty And Prosperity within the [CATO Institute](https://www.cato.org). The CATO "
            "institute is a Washington DC based think tank that has been in operation since the late 1970s. While "
            "Mr. Nowrasteh offers some economic and theoretical counter arguments to common immigration concerns, we "
            "visualized data made available by Raj Chetty's (Harvard University) group, [Opportunity Insights]"
            "(https://opportunityinsights.org), that studies social mobility within America to augment his arguments.")

st.header("As we begin to explore this data, let's consider five of the arguments offered against liberal "
          "immigration policies.")

st.write("""
         1. Immigrants will take jobs and lower wages
         2. Immigrants will increase the poverty rate
         3. Immigrants increase income inequality
         4. Immigrants are a major source of crime
         5. Immigrants bring negative cultural influences
         """)

st.write("Fortunately for us, these five arguments against immigration are all referenced in the Opportunity Insights "
         "Dataset.")

# Dictionary storing the dataframe column name and the associated table title
# Value format: (df column title, initial table title, ascending sorting order)
first_columns = {
    "Change in the Labor Force between 1980 and 2000":
        ("lf_d_2000_1980", "Least Growth in Labor Force", True, "Growth in the Labor Force Between 1980 and 2000"),
    "Labor Force Participation":
        ("cs_labforce", "Lowest Labor Force Participation", True, "Total Participation in the Labor Force"),
    "Poverty Rate":
        ("poor_share", "Highest Poverty Rate", False, "Poverty Rate"),
    "Segregation of Poverty (Lowest 25% of Earners)":
        ("cs00_seg_inc_pov25", "Greatest Segregation in Poverty", False, "Segregation of Poverty (Lowest 25%)"),
    "Segregation of Affluence (Highest 25% of Earners)":
        ("cs00_seg_inc_aff75", "Greatest Segregation in Wealth", False, "Segregation of Affluence (Highest 25%"),
    "Crime Rate":
        ("crime_total", "Highest Crime Rate", False, "Crime Rate"),
    "Fraction of Children with Single Mother":
        ("cs_fam_wkidsinglemom", "Most Kids with a Single Mom", False, "Children with a Single Mother"),
    "High School Dropout Rate":
        ("dropout_r", "Highest High School Dropout Rates", False, "High School Dropout Rate"),
    "Percent College Graduates":
        ("graduate_r", "Lowest Rate of College Graduation", True, "Percent With a College Degree")
}
table_index = pd.Index([i for i in range(1, 11)])
column_names = {
    "county_name": "County",
    "statename": "State",
    "cs_labforce": "Labor Force Participation",
    "bmi_obese_q2": "BMI",
    "cs_born_foreign": "Percent Foreign Born"
}
compare_to = st.selectbox('Explore the data available and see if you can find any comparable counties',
                          list(first_columns.keys()))

# Get the two dataframes to compare (first is static, second is dynamic)
top_10_foreign_df = df[['county_name', 'statename', 'cs_born_foreign']] \
    .sort_values('cs_born_foreign', ascending=False) \
    .head(10)[['county_name', 'statename']].set_index(table_index)
foreign_counties = set(top_10_foreign_df['county_name'].tolist())
foreign_states = set(top_10_foreign_df['statename'].tolist())

top_10_selected_df = df[['county_name', 'statename', first_columns[compare_to][0]]] \
    .sort_values(first_columns[compare_to][0], ascending=first_columns[compare_to][2]) \
    .head(10)[['county_name', 'statename']].set_index(table_index)
selected_counties = set(top_10_selected_df['county_name'].tolist())
selected_states = set(top_10_selected_df['statename'].tolist())
all_states = foreign_states.union(selected_states)

# Lay out the tables side by side
col1, col2 = st.beta_columns(2)
col1.subheader("Counties With the Most Immigrants")
col1.table(top_10_foreign_df.rename(mapper=column_names, axis=1).style.apply(find_common, axis=1))
col2.subheader(first_columns[compare_to][1])
col2.table(top_10_selected_df.rename(mapper=column_names, axis=1).style.apply(find_common, axis=1))

chart = alt.Chart(
    df[df.statename.isin(all_states)].rename(mapper=column_names, axis=1),
    title=f"Comparing Percent Foreign Born to {compare_to}"
).mark_point().encode(
    tooltip=["State:N", "County:N", "Percent Foreign Born:Q"],
    x=alt.X("Percent Foreign Born", scale=alt.Scale(zero=False), title="Percent Foreign Born"),
    y=alt.Y(first_columns[compare_to][0], scale=alt.Scale(zero=False), title=first_columns[compare_to][3]),
    color=alt.Color("State:N")
).properties(
    width=800,
    height=600
)

st.write(chart)

st.write("As we can see from playing with this data, at least in the extremes the negative outcomes which some argue "
         "come from having more immigrants don't really seem to be correlated in our data.")

st.write("If having a higher proportion of immigrants in your county isn't an indicator of these negative factors, "
         "what is it related to?")

# create three charts showing things which are at least somewhat correlated to immigrant presence in the community

lab_force_part = alt.Chart(
    df.rename(mapper=column_names, axis=1)
).mark_point(color="lightblue").encode(
    tooltip=["Labor Force Participation:Q", "Percent Foreign Born:Q", 'County:N', 'State:N'],
    x=alt.X("Percent Foreign Born", scale=alt.Scale(zero=False), title="Percent Foreign Born"),
    y=alt.Y("Labor Force Participation", scale=alt.Scale(zero=False), title="Participate in the Labor Force")
)

lab_force_regression = \
    lab_force_part.transform_regression("Percent Foreign Born", "Labor Force Participation").mark_line(color="red")

percent_obese = alt.Chart(
    df.rename(mapper=column_names, axis=1)
).mark_point(color="lightblue").encode(
    x=alt.X("Percent Foreign Born", scale=alt.Scale(zero=False), title="Percent Foreign Born"),
    y=alt.Y("BMI", scale=alt.Scale(zero=False), title="Percent Obese")
)

percent_obese_regression = \
    percent_obese.transform_regression("Percent Foreign Born", "BMI").mark_line(color="red")

# Write the two charts as columns
col1, col2 = st.beta_columns(2)
col1.subheader("Participation in Labor Force")
col1.write(lab_force_part + lab_force_regression)
col2.subheader("Percent of the Population Obese")
col2.write(percent_obese + percent_obese_regression)

st.write("Our data suggests that in terms of health and economy, having a high number of immigrants in your county may "
         "actually be a good thing! While there is a lot of noise in the data, it does seem that there is a general "
         "correlation between a high percentage of immigrants and more people working and being *generally* healthy.")

st.write(df.median_house_value)

scale = scale_dropdown('pair_plot_scale')
x_str = feature_dropdown('Choose x-axis feature.', 'x_feature', 'cty_pop2000')
y_str = feature_dropdown('Choose y-axis feature.', 'y_feature', 'median_house_value')
st.write(pair_plot(df, x_str, y_str, scale, [x_str, y_str, 'county_name', 'statename']))

# avg all counties for each state, plot that avg as representative
agg_df = df.groupby('statename').mean()
agg_df['statename'] = [name for name, _ in df.groupby('statename')]

st.write(pair_plot(agg_df, x_str, y_str, scale, [x_str, y_str, 'statename']))

st.write('This is less crowded, though we lose some information.')

tsne_df = clustering_visual(df)

chart = alt.Chart(tsne_df).mark_point().encode(
    x=alt.X("tsne_x"),
    y=alt.Y("tsne_y"),
    color=alt.Color("cluster:N")
).properties(
    width=600, height=400
)

st.write(chart)

st.write(
    "What I've done above is running kmeans clustering on all numeric data. We can probably find a better clustering",
    "But, the point is to answer 'Which counties are similar? We might find some interesting relationships this way.")

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

st.write(counties_map)

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
  - Might be too much for this homework, but we could maybe run clustering algorithms using these features.

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

feature = feature_dropdown('Which feature would you like to look at?', 'choro_feature', 'cty_pop2000')

scale = scale_dropdown('choro_scale')

st.write(choro_map(counties_data, df, feature, scale))

state = st.selectbox('Would you like to zoom in on any particular state?',
                     ['None'] + list(df.statename.unique()))

if state != 'None':
    st.write(choro_map(counties_data, df[df.statename == state], feature, scale))
