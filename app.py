import pandas as pd
import streamlit as st
import plotly.express as px

# ---------------- PAGE CONFIG ----------------
st.set_page_config(layout='wide', page_title='Startup Analysis')

# ---------------- LOAD DATA (CACHED) ----------------
@st.cache_data
def load_data():
    df = pd.read_csv("startup_cleaned.csv")
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df.dropna(subset=['startup', 'amount'], inplace=True)

    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year
    return df

df = load_data()

# ---------------- SIDEBAR ----------------
st.sidebar.title("Startup Funding Analysis")

option = st.sidebar.selectbox(
    "Select Analysis",
    ['Overall Analysis', 'Investor']
)

# Global Filters
st.sidebar.markdown("### Filters")
selected_year = st.sidebar.multiselect(
    "Select Year",
    sorted(df['year'].dropna().unique())
)

if selected_year:
    df = df[df['year'].isin(selected_year)]

# ---------------- OVERALL ANALYSIS ----------------
def load_overall_analysis():
    st.title('📊 Overall Analysis')

    total = round(df['amount'].sum())
    max_funding = df.groupby('startup')['amount'].sum().max()
    avg_funding = round(df.groupby('startup')['amount'].sum().mean())
    num_startups = df['startup'].nunique()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric('Total Funding', f"{total} Cr")
    col2.metric('Highest Funding', f"{max_funding} Cr")
    col3.metric('Avg Funding', f"{avg_funding} Cr")
    col4.metric('Funded Startups', num_startups)

    st.markdown("---")

    # MoM Trend
    st.subheader('📈 Monthly Trend')

    trend_type = st.selectbox('Select Type', ['Total', 'Count'])

    if trend_type == 'Total':
        temp_df = df.groupby(['year', 'month'])['amount'].sum().reset_index()
    else:
        temp_df = df.groupby(['year', 'month'])['amount'].count().reset_index()

    temp_df['date'] = temp_df['year'].astype(str) + '-' + temp_df['month'].astype(str)

    fig = px.line(temp_df, x='date', y='amount', title='Monthly Trend')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Insights
    st.subheader("🔍 Key Insights")
    top_startup = df.groupby('startup')['amount'].sum().idxmax()
    st.write(f"• Top funded startup: **{top_startup}**")

    st.markdown('---')
    st.subheader('📊 Sector Analysis')
    col1,col2 = st.columns(2)

    with col1:
        st.markdown("### Deal Count by Sector")
        sector_count = df['vertical'].value_counts().head(10)
        fig_count = px.pie(
            values=sector_count.values,
            names=sector_count.index,
            title='Top Sectors by Deal Count'
        )
        st.plotly_chart(fig_count,use_container_width=True)

    with col2:
        st.markdown('### Total Funding  by Sector')    
        sector_sum = df.groupby('vertical')['amount'].sum().sort_values(ascending=False).head(10)
        fig_sum = px.pie(
            values=sector_sum.values,
            names=sector_sum.index,
            title='Top Sectors by Funding'
        )
        st.plotly_chart(fig_sum,use_container_width=True)
    
    st.markdown("---")
    st.subheader("🌍 City-wise Funding")

    col3, col4 = st.columns(2)

    # -------- TOP CITIES (BAR CHART) --------
    with col3:
        st.markdown("### Top Cities by Funding")
        
        city_sum = df.groupby('city')['amount'].sum().sort_values(ascending=False).head(10)

        fig_city_bar = px.bar(
            x=city_sum.index,
            y=city_sum.values,
            title="Top Cities by Total Funding"
        )
        st.plotly_chart(fig_city_bar, use_container_width=True)

    with col4:
        st.markdown("### Funding Distribution by City")
    
        fig_city_pie = px.pie(
        values=city_sum.values,
        names=city_sum.index,
        title="City-wise Distribution"
        )
        st.plotly_chart(fig_city_pie, use_container_width=True)  

    st.markdown("---")
    st.subheader("🏆 Top Investors Ranking")

    # -------- PREPROCESS INVESTORS --------
    investor_df = df.copy()

    investor_df = investor_df.dropna(subset=['investors'])
    investor_df['investors'] = investor_df['investors'].str.split(',')

    # explode (VERY IMPORTANT)[convert to list]
    investor_df = investor_df.explode('investors')

    # clean names
    investor_df['investors'] = investor_df['investors'].str.strip()        
            
    top_investors = (
        investor_df.groupby('investors')['amount'].sum().sort_values(ascending=False).head(10)
    )

    fig_inv = px.bar(
        x=top_investors.values,
        y=top_investors.index,
        orientation='h',
        title="Top Investors by Total Funding"
    )

    st.plotly_chart(fig_inv, use_container_width=True)  

    st.markdown("### 📊 Most Active Investors (Deal Count)")

    top_count = (
        investor_df['investors'].value_counts().head(10)
    )

    fig_count = px.bar(
        x=top_count.values,
        y=top_count.index,
        orientation='h',
        title="Top Investors by Deal Count"
    )

    st.plotly_chart(fig_count, use_container_width=True)              
          


# ---------------- INVESTOR ANALYSIS ----------------
def investor_info(investor):
    st.title(f'💼 {investor}')

    temp = df[df['investors'].str.contains(investor, na=False)]

    st.subheader('Recent Investments')
    st.dataframe(temp.head()[['date', 'startup', 'vertical', 'city', 'round', 'amount']])

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader('Top Startups')
        highest =  df[df['investors'].str.contains(investor)].groupby('startup')['amount'].sum().sort_values(ascending=False).head()
        fig = px.bar(x=highest.index, y=highest.values, title="Top Investments")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader('Sector Distribution')
        sector = temp.groupby('vertical')['amount'].sum()
        fig = px.pie(values=sector.values, names=sector.index)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    col3, col4 = st.columns(2)

    with col3:
        st.subheader('Stage Distribution')
        stage = temp.groupby('round')['amount'].sum()
        fig = px.pie(values=stage.values, names=stage.index)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.subheader('City Distribution')
        city = temp.groupby('city')['amount'].sum()
        fig = px.pie(values=city.values, names=city.index)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader('Yearly Trend')
    yearly = temp.groupby('year')['amount'].sum().reset_index()
    fig = px.line(yearly, x='year', y='amount')
    st.plotly_chart(fig, use_container_width=True)

# ---------------- MAIN ROUTING ----------------
if option == 'Overall Analysis':
    load_overall_analysis()

else:
    investors_list = sorted(set(df['investors'].dropna().str.split(',').sum()))

    investor_name = st.sidebar.selectbox('Select Investor', investors_list)

    if st.sidebar.button('Analyze Investor'):
        investor_info(investor_name)