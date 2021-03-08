import streamlit as st
import pandas as pd
import altair as alt

st.title("Let's analyze some Social Mobility Data 📊.")


@st.cache  # add caching so we load the data only once
def load_data():
    # Load the social mobility data from Opportunity Insights
    return pd.read_csv("health_ineq_online_table_12.csv")


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

st.write(
    "Yikes, that isn't super helpful, everyone is bunched in the corner and the states are too numerous to be clearly "
    "visible! Maybe we could do some filtering?")

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

Our design in greater detail:
- A single map showing the entire US with charts showing aggregate statistics on the right
  or maybe under the main plot (configurable displays, but maybe only show set combinations)
- The ability to compare two states with a choropleth display of the state's outline and a
  selected feature to compare more broadly.
    - sub-plots below compare the states more directly in different areas.
- Can guide a viewer through a story to expose differences between the Northeast and Southeast,
  mid-west and south-west, and/or the pacific north-west

"""
