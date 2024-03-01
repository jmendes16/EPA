import pandas as pd
import streamlit as st
import altair as alt
import matplotlib.pyplot as plt

from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from sqlalchemy import create_engine

# set up page
st.set_page_config(
    page_title="ADFL4 EPA fails",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

# get data
engine = create_engine('postgresql://user:password@localhost:port/mydatabase')

df_KSBs = pd.read_sql_query("SELECT * FROM table_name", engine)
df_comments = pd.read_sql_query("SELECT * FROM table_name", engine)
Ks = ['K'+ str(n) for n in range(1,16)]
Ss = ['S'+ str(n) for n in range(1,16)]
Bs = ['B'+ str(n) for n in range(1,8)]
KSBs = Ks + Ss + Bs
df_KSB_categories = pd.DataFrame({
    'ksb':KSBs,
    'assessment_method':[2,2,1,1,2,2,2,1,1,2,1,1,2,2,2,1,1,1,1,2,1,1,1,2,2,2,1,2,2,1,2,2,1,1,2,2,2]
})
df_KSBs = pd.merge(df_KSBs,df_KSB_categories,how='left',on='ksb')

# the filters
with st.sidebar:
    st.title('ADFL4 fails')
    
    assessment_method = list(df_KSB_categories.assessment_method.unique())[::-1]
    
    selected_assessment_method = st.selectbox('Select an assessment method', assessment_method)
    df_selected_KSBs = df_KSBs.loc[df_KSBs.assessment_method == selected_assessment_method]
    df_selected_KSBs_sorted = df_selected_KSBs.groupby(by='ksb').size().reset_index(name='count').sort_values(by="count")
    if assessment_method == 1:
        comments = df_comments.project_comment
    else:
        comments = df_comments.portfolio_comment
    comment_string = ''
    for i in range(len(comments)):
        comment_string += ' ' + comments[i]

    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds']
    selected_color_theme = st.selectbox('Select a color theme', color_theme_list)

# the graphs
def make_barchart(input_df, input_y, input_x, input_color_theme):
    barchart = alt.Chart(input_df).mark_bar().encode(
            y=alt.Y(f'{input_y}', axis=alt.Axis(title="Occurence", titleFontSize=18, titlePadding=15, titleFontWeight=900, labelAngle=0)),
            x=alt.X(f'{input_x}', 
                    axis=alt.Axis(title="KSBs", titleFontSize=18, titlePadding=15, titleFontWeight=900),
                    sort=alt.EncodingSortField(field=f'{input_x}', op=f'{input_y}', order='ascending')),
            stroke=alt.value('black'),
            strokeWidth=alt.value(0.25),
            color=input_color_theme
        ).properties(width=900, height=800
        ).configure_axis(
        labelFontSize=12,
        titleFontSize=12
        ) 
    return barchart

def make_wordcloud(input_string):
    fig, ax =plt.subplots(figsize=(9,6))

    wordcloud = WordCloud().generate(input_string)

    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    fig = plt.figure(1, figsize=(900, 600))
    plt.axis('off')
    plt.imshow(wordcloud)
    return fig

# dashboard layout
col = st.columns((1,1), gap='medium')

with col[0]:
    st.markdown('### KSB Occurences in Fail reports')

    barchart = make_barchart(df_selected_KSBs_sorted, 'count', 'ksb', 'ksb')
    st.altair_chart(barchart, use_container_width=True)

with col[1]:
    st.markdown('### Comment analysis')

    wordCloud = make_wordcloud(comment_string)
    st.pyplot(wordCloud, use_container_width=True)