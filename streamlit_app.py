import streamlit as st
import pandas as pd
import altair as alt

from sklearn.cluster import DBSCAN, KMeans
from sklearn.manifold import TSNE

from vega_datasets import data

# mapping the features in our df that interest us to nice strings for vis
feature_titles = [
  ('puninsured2010', '% uninsured'),
  ('poor_share', 'poverty rate'),
  ('cs_frac_black', '% black'),
  ('cs_frac_hisp', '% hispanic'),
  ('unemp_rate', 'unemployment rate'),
  ('cs_born_foreign', '% foreign-born'),
  ('hhinc00', 'avg. household income'),
  ('cs_educ_ba', '% with Bachelors degree'),
  ('crime_total', 'crime rate')
]

title_to_feature = {b: a for a, b in feature_titles}
feature_to_title = {a: b for a, b in feature_titles}

@st.cache
def load_geodata():
  ''' load topographical data for US county data '''
  return alt.topo_feature(
    "https://raw.githubusercontent.com/deldersveld/topojson/master/countries/united-states/us-albers-counties.json",
    "collection"
  )


@st.cache
def clustering_visual(df):
  ''' perform KMeans clustering on features '''
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
  ''' render choropleth map using topo layout from @geo_data,
      colored by feature @column in data @df, using linear or log @scale '''
  def get_title(s): # get display title for tooltips
    s = s.split(':')[0]
    if s.startswith('properties'):
      s = s.split('.')[1]
    return feature_to_title.get(s, s)

  col_feature = title_to_feature.get(column, column)
  tooltip_cols = ('properties.name:O', 'properties.state:O', '{}:Q'.format(col_feature))

  return alt.Chart(geo_data).mark_geoshape(
  ).encode(
    color=alt.Color('{}:Q'.format(col_feature), title=column, scale=alt.Scale(type=scale, scheme='greenblue')),
    tooltip=[alt.Tooltip(col, title=get_title(col)) for col in tooltip_cols]
  ).properties(
    width=800,
    height=600
  ).transform_lookup(
    lookup='properties.fips',
    from_=alt.LookupData(df, "fips", [col_feature])
  ).project(
    'albersUsa'
  )


def feature_dropdown(s, key, default_val, features):
  get_title = lambda x: feature_to_title[x] if x in feature_to_title else x
  default_index = features.index(default_val)
  return st.selectbox(s, [get_title(f) for f in features], key=key, index=default_index)


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


st.title("Confronting Stereotypes in the Immigration Debate.")
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

st.write('How do these factors look like individually, across the US?')

choro_features= ['puninsured2010', 'poor_share', 'cs_frac_black', 'cs_frac_hispanic', 'unemp_rate',
  'cs_born_foreign', 'hhinc00', 'cs_educ_ba', 'crime_total']
#choro_features = list(df.columns)
feature = feature_dropdown('Which feature would you like to look at?', 'choro_feature', 'crime_total', choro_features)
scale = scale_dropdown('choro_scale')

counties_data = load_geodata()
st.write(choro_map(counties_data, df, feature, scale))

state = st.selectbox('Would you like to zoom in on any particular state?',
  ['None'] + list(df.statename.unique()))

if state != 'None':
  st.write(choro_map(counties_data, df[df.statename == state], feature, scale))
