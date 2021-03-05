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
