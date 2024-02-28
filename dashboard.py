import pandas as pd
import psycopg2
import streamlit as st
import altair as alt

# set up page
st.set_page_config(
    page_title="1st for EPA fails",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

# get data
conn = psycopg2.connect(database="db_name", user="user_name", password="password", host="host_name")

df_KSBs = pd.read_sql_query("SELECT * FROM table_name", conn)
df_comments = pd.read_sql_query("SELECT * FROM table_name", conn)
Ks = ['K'+ str(n) for n in range(1,16)]
Ss = ['S'+ str(n) for n in range(1,16)]
Bs = ['B'+ str(n) for n in range(1,8)]
KSBs = Ks + Ss + Bs
df_KSB_categories = pd.DataFrame({
    'ksb':KSBs,
    'assessment_method':[2,2,1,1,2,2,2,1,1,2,1,1,2,2,2,1,1,1,1,2,1,1,1,2,2,2,1,2,2,1,2,2,1,1,2,2,2]
})
df_KSBs = pd.merge(df_KSBs,df_KSB_categories,how='left',on='ksb')


with st.sidebar:
    st.title('1st for EPA fails')
    
    assessment_method = list(df_KSB_categories.assessment_method.unique())[::-1]
    
    selected_assessment_method = st.selectbox('Select an assessment method', assessment_method)
    df_selected_KSBs = df_KSBs.loc[df_KSBs.assessment_method == selected_assessment_method]
    df_selected_KSBs_sorted = df_selected_KSBs.groupby(by='ksb').size().reset_index(name='count').sort_values(by="count")

    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds']
    selected_color_theme = st.selectbox('Select a color theme', color_theme_list)
