from st_aggrid import *
from yaml.loader import SafeLoader
import yaml
import pandas as pd
import os
import geopandas as gpd
import matplotlib.pyplot as plt
import streamlit as st
from wordcloud import WordCloud

# import altair_saver
from collections import Counter
import pyarrow as pa
import pyarrow.feather as feather
import pathlib
import openpyxl
import altair as alt
from gensim import corpora
import streamlit as st
from wordcloud import WordCloud, STOPWORDS
import streamlit_authenticator as stauth
import pandas as pd
from nltkmodules import *
import altair as alt
import folium

# import wordcloud
from wordcloud import WordCloud, STOPWORDS
import nltk, os
from nltk.corpus import stopwords

# https://towardsdatascience.com/how-to-add-a-user-authentication-service-in-streamlit-a8b93bf02031
# for "forgot password" and other authorization features
# https://docs.streamlit.io/library/get-started/multipage-apps
# for multipage setup


# st.write('Streamlit day 1 dsba5122')
# st.title('this is the app title')
# st.markdown('this is the header')
# st.subheader('this is the subheader')
# st.caption('this is the caption')
# st.code('x=2020')
# st.latex(r''' a+a r^1+A r^2 r^3 ''')

# st.image("norm.jpg")
# st.audio("fight_song.mp3")

################################################################################################
# Authentication and initial page setup
################################################################################################

st.set_page_config(layout="wide")

authorization_demo = False
authentication_status = False
username = ""

with st.sidebar:
    authorization_demo = st.checkbox(
        label="Authentication demo",
        help="If unchecked full access is granted.",
    )

user_groups = {"admin": ["tdzhafari"], "group1": ["jdoe"]}

if authorization_demo is True:
    config_path: pathlib.Path = pathlib.Path(os.getcwd(), "config.yaml")
    with open(config_path, "r") as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )

    # Check if 'key' already exists in session_state
    # If not, then initialize it
    if "key" not in st.session_state:
        st.session_state["key"] = "value"

    name, authentication_status, username = authenticator.login("login", "main")

    if authentication_status:
        authenticator.logout("Logout", "sidebar")
        st.write(f"Welcome *{name}* :wave:")

    elif authentication_status is False:
        st.error("Username/password is incorrect")
    elif authentication_status is None:
        st.warning("Please enter your username and password")
        # st.write(
        #     "Here will be a button to register. Feel free to use below credentials for now:"
        # )
        promise = st.checkbox(label="I promise, I can keep a secret!")
        if promise:
            expander = st.expander("For guest access credentials please click here.")
            expander.write("login: 'jdoe', password: 'abc1' - just don't tell anyone")
    # st.write(f'Your authentication status is {authentication_status}')

    if authentication_status:
        with st.sidebar:
            if st.button("Reset Password"):
                try:
                    if authenticator.reset_password(username, "Reset password"):
                        st.success("Password modified successfully")
                except Exception as e:
                    st.error(e)

# else:
#     authorization_demo = st.checkbox(label="Authentication demo")
st.sidebar.empty()

if authentication_status == True or authorization_demo is False:
    demo_type_name = st.sidebar.selectbox(
        label="Choose a demo",
        options=["Disasters", "NLP"],
        # horizontal=True,
        help="Please choose between the available demos",
    )

    ################################################################################################
    # A separate function to retrieve data from github
    ################################################################################################

    if demo_type_name == "Disasters":
        st.title("Disasters 2000-2023")
        st.subheader(
            "The data has been collected from EM-DAT The International Disaster Database Centre for Research on THe Epidemiology of Disasters (CRED)"
        )

        @st.cache_data
        def fetch_and_clean_data():
            # URL of the raw CSV file on GitHub
            disaster_data_path = pathlib.Path(
                os.getcwd(), "/data/2000-2023 disaster around the world.xlsx"
            )
            df = pd.read_excel(disaster_data_path, header=6, engine="openpyxl")
            df["Total Damages $$$"] = df["Total Damages, Adjusted ('000 US$)"]

            # Download GeoJSON file of world map
            world_map_url = "https://raw.githubusercontent.com/deldersveld/topojson/master/world-countries.json"
            world_map = alt.topo_feature(world_map_url, "countries")

            # Aggregate the data by country and region
            df_m = df.groupby(["Country", "Region"]).sum().reset_index()

            # Join the data with the GeoJSON file based on the "Country" field
            world_data = gpd.read_file(world_map_url)
            # df_map = world_data.merge(df_m, left_on='name', right_on='Country')

            merged_data = world_data.merge(df_m, left_on="name", right_on="Country")

            # Convert geopandas dataframe to pandas dataframe
            merged_data = pd.DataFrame(merged_data)

            return df, merged_data, world_map

        ################################################################################################
        # Interactive dashboards and additional functionality
        ################################################################################################

        if authentication_status or authorization_demo is False:
            # disease = st.selectbox('select a disease', set(my_df['Dim2']))
            # if not disease:
            #    AgGrid(my_df)
            # else:
            #    AgGrid(my_df[my_df['Dim2'] == disease])
            if username in user_groups.get("admin") or authorization_demo is False:
                source, line_plot, box_plot, map, tab5 = st.tabs(
                    ["Source", "Line Plot", "Box Plot", "Map", "Placeholder"]
                )
            else:
                source, line_plot, box_plot = st.tabs(
                    ["Source", "Line Plot", "Box Plot"]
                )
            with source:
                # expander = st.expander("How this works?")
                # expander.write(
                #     "Please choose a disaster type and a country you would like learn more about. The line plot will show you the number of people affected by chosen type of disaster in a country from 2000 to 2023."
                # )
                df, merged_data, world_map = fetch_and_clean_data()
                gb = GridOptionsBuilder.from_dataframe(df)
                # gb.configure_pagination(paginationAutoPageSize = True)
                gb.configure_side_bar()
                gb.configure_selection(
                    "multiple",
                    use_checkbox=True,
                    groupSelectsChildren="Group checkbox select children",
                )
                gridOptions = gb.build()

                grid_response = AgGrid(
                    df,
                    gridOptions=gridOptions,
                    data_return_mode="AS_INPUT",
                    update_mode="MODEL_CHANGED",
                    fit_columns_on_grid_load=False,
                    # theme="blue",
                    enable_enterprise_modules=True,
                    height=700,
                    width="100%",
                    reload_data=True,
                )

            ################################################################################################
            # Line plot tab
            ################################################################################################

            with line_plot:
                # expander = st.expander("How this works?")
                # expander.write(
                #     "Please choose a disaster type and a country you would like learn more about. The line plot will show you the number of people affected by chosen type of disaster in a country from 2000 to 2023."
                # )
                col1, col2 = st.columns(2)
                with col1:

                    # d_type = ''
                    # country = ''

                    # # default filters
                    # if d_type == "":
                    #     d_type = "Earthquake"
                    # if country == "":
                    #     country = "Turkey"

                    d_type = st.multiselect(
                        "select a disaster type",
                        list(set(df["Disaster Type"])),
                        default="Earthquake",
                    )
                    st.write(f"You have chosen {d_type}")
                with col2:
                    country = st.selectbox(
                        "select a country",
                        list(set(df["Country"])),
                        index=list(set(df["Country"])).index("Turkey"),
                    )
                    st.write(f"You have chosen {country}")
                if st.button("Remove filters"):
                    d_type = None
                    country = None
                if d_type and country:
                    df1 = df[
                        (df["Country"] == country) & df["Disaster Type"].isin(d_type)
                    ]
                    st.line_chart(
                        df1,
                        x="Year",
                        y="Total Affected",
                    )

            ################################################################################################
            # Box plot
            ################################################################################################

            with box_plot:
                expander = st.expander("How this works?")
                expander.write(
                    "Please choose a year to see which countries had the highest disaster related mortality for the year. Please note that if you hower over bars in the barplot you will see some useful information in the tooltip that will appear."
                )
                col1, col2 = st.columns(2)
                year = st.slider("Please choose a year", 2000, 2023, 2023)
                df2 = df[df["Year"] == year]
                # c = alt.Chart(df2.sort_values(by=['Total Deaths'], ascending = False)).mark_bar().encode(y = alt.Y("Region:N", sort = alt.EncodingSortField(field='Region', op = 'sum', order = 'ascending')), x = alt.X("Total Deaths", sort = '-x'))
                c = (
                    alt.Chart(df2.sort_values(by=["Total Deaths"], ascending=False))
                    .mark_bar()
                    .encode(
                        y=alt.Y(
                            "Region:N",
                            sort=alt.EncodingSortField(
                                field="Total Deaths", order="descending"
                            ),
                            axis=alt.Axis(title="Region"),
                        ),
                        x=alt.X(
                            "Total Deaths",
                            sort="-x",
                            axis=alt.Axis(title="Total Deaths"),
                        ),
                        tooltip=[
                            alt.Tooltip("Country:N", title="Country"),
                            alt.Tooltip("Total Deaths:Q", title="Total Deaths"),
                            alt.Tooltip("Total Affected:Q", title="Total Affected"),
                        ],
                    )
                )
                st.altair_chart(c, use_container_width=True)
            if username in user_groups.get("admin") or authorization_demo is False:

                ################################################################################################
                # Map
                ################################################################################################

                with map:
                    year_map = st.slider("Please choose a year:", 2000, 2023, 2023)

                    ## Convert pandas dataframe to Arrow table
                    # table = pa.Table.from_pandas(merged_data)

                    ## Write Arrow table to Feather format
                    # feather.write_feather(table, 'merged_data.feather')

                    ## Read Feather file into Arrow table
                    # table = feather.read_feather('merged_data.feather')

                    ## Convert Arrow table to pandas dataframe
                    # merged_data = table.to_pandas()

                    ## Create a heatmap with a tooltip
                    # heatmap = alt.Chart(merged_data).mark_geoshape().encode(
                    #    color=alt.Color('Total Deaths:Q', scale=alt.Scale(scheme='reds')),
                    #    #tooltip=[
                    #    #    alt.Tooltip('name:N', title='Country'),
                    #    #    alt.Tooltip('Total Deaths:Q', title='Total Deaths', format=',')
                    #    #]
                    # ).properties(
                    #    width=600,
                    #    height=400,
                    #    title='Total Deaths by Country'
                    # )

                    ## Add world map outlines
                    # world_outline = alt.Chart(world_map).mark_geoshape(stroke='white', strokeWidth=0.5).encode(
                    #    color=alt.value('transparent')
                    # ).properties(
                    #    width=600,
                    #    height=400,
                    # )

                    ## Combine the heatmap and world map outlines
                    # map_chart = world_outline + heatmap

                    ## Display the chart in Streamlit

                    # countries = alt.topo_feature(df2, "Country")
                    # source = df2[(df2['Year'] == year)]

                    # base = alt.Chart(source).mark_geoshape(
                    #    fill='#666666',
                    #    stroke='white'
                    # ).properties(
                    #    width=300,
                    #    height=180
                    # )

                    # projections = 'orthographic'
                    # st.altair_chart(base.projections.properties(title = projections))

                with tab5:
                    st.write(
                        "There will be something cool and creative below. Meanwhile enjoy some art by Edward Hopper."
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        st.image(
                            "https://media.tate.org.uk/aztate-prd-ew-dg-wgtail-st1-ctr-data/images/edward_hopper_automat.width-600.jpg"
                        )
                    with col2:
                        st.image(
                            "https://collectionapi.metmuseum.org/api/collection/v1/iiif/488730/1004971/restricted"
                        )
                    st.image(
                        "https://www.speakeasy-news.com/wp-content/uploads/2020/04/SN_hopper_home02.jpg"
                    )
        # if authentication_status and username in user_groups.get('group1'):

        #     uploaded_file = st.file_uploader(
        #         label='Reconciled Datadump',
        #         type='xlsx',
        #         help='Please upload Datadump here. The file will be checked for filename, extension, column formats etc. max weight = 200mb'
        #     )

        # st.dataframe(my_df[my_df['Dim2'] == disease])
        # print((my_df.head().to_string()))

    elif demo_type_name == "NLP":
        st.title("Shakespeare Demo")

        st.markdown(
            """
    # Analyzing Shakespeare Texts
    """
        )

        # Create a dictionary (not a list)
        books = {
            " ": " ",
            "A Mid Summer Night's Dream": "data/summer.txt",
            "The Merchant of Venice": "data/merchant.txt",
            "Romeo and Juliet": "data/romeo.txt",
        }

        # Sidebar
        st.sidebar.header("Word Cloud Settings")

        max_word = st.sidebar.slider(
            "Max Words", min_value=10, max_value=200, value=100, step=10
        )

        word_size = st.sidebar.slider(
            "Size of largest word", min_value=50, max_value=350, value=150, step=10
        )

        img_width = st.sidebar.slider(
            "Image width", min_value=100, max_value=800, value=600, step=10
        )

        rand_st = st.sidebar.slider(
            "Random State", min_value=20, max_value=100, value=50, step=1
        )

        remove_stop_words = st.sidebar.checkbox("Remove Stop Words?", value=True)

        st.sidebar.header("Word Count Settings")

        min_word_cnt = st.sidebar.slider(
            "Minimum count of words", min_value=5, max_value=100, value=30, step=1
        )
        ## Select text files
        image = st.selectbox("Choose a text file", books.keys())

        ## Get the value
        if image != " ":
            image = books.get(image)

        if image != " ":
            stop_words = []
            raw_text = open(image, "r").read().lower()
            nltk_stop_words = stopwords.words("english")

            if remove_stop_words:
                stop_words = set(nltk_stop_words)
                stop_words.update(
                    [
                        "us",
                        "one",
                        "though",
                        "will",
                        "said",
                        "now",
                        "well",
                        "man",
                        "may",
                        "little",
                        "say",
                        "must",
                        "way",
                        "long",
                        "yet",
                        "mean",
                        "put",
                        "seem",
                        "asked",
                        "made",
                        "half",
                        "much",
                        "certainly",
                        "might",
                        "came",
                        "thou",
                    ]
                )
                # These are all lowercase

            tokens = nltk.word_tokenize(raw_text)

            # simple for loop to remove stop words
            if remove_stop_words:
                for item in tokens:
                    if item in stop_words:
                        tokens.remove(item)
        else:
            tokens = " "

        tab1, tab2, tab3 = st.tabs(["Word Cloud", "Bar Chart", "View Text"])

        with tab1:

            # Define some text for the word cloud
            if image != " " and tokens:
                text = " ".join(tokens)

                # Generate the word cloud image
                wordcloud = WordCloud(
                    width=img_width,
                    height=400,
                    max_words=max_word,
                    background_color="white",
                ).generate(text)

                # Display the word cloud image using Matplotlib
                fig, ax = plt.subplots()
                ax.imshow(wordcloud, interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig)

        with tab2:

            # simple for loop to remove stop words
            if remove_stop_words and tokens != " ":
                for item in tokens:
                    if item in stop_words:
                        tokens.remove(item)
            # create a dictionary using gensim library
            if tokens != " ":

                word_counts = Counter(tokens)

                # Convert the Counter object to a dictionary
                word_counts_dict = dict(word_counts)

                # Create a DataFrame from the dictionary
                df = pd.DataFrame.from_dict(
                    {
                        "word": list(word_counts_dict.keys()),
                        "count": list(word_counts_dict.values()),
                    }
                )

                df = df[(df["count"] > min_word_cnt)]

                chart = (
                    alt.Chart(df)
                    .mark_bar()
                    .encode(x="count", y=alt.Y("word", sort="-x"))
                )

                # Display the chart in Streamlit using Altair
                st.altair_chart(chart, use_container_width=True)

        with tab3:
            if image != " ":
                raw_text = open(image, "r").read().lower()
                st.write(raw_text)
