import pickle
import streamlit as st
import requests
import pandas as pd
import random

API_KEY = "ENTER YOUR API KEY"

# Fetch movie details including IMDb link
def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    response = requests.get(url)
    data = response.json()

    imdb_id = data.get("imdb_id", None)
    imdb_url = f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else None

    details = {
        "title": data.get("title", "Unknown"),
        "poster": "https://image.tmdb.org/t/p/w500/" + data['poster_path'] if data.get('poster_path') else "https://via.placeholder.com/500x750?text=No+Poster",
        "release_date": data.get("release_date", "N/A"),
        "rating": data.get("vote_average", "N/A"),
        "genres": ", ".join([g['name'] for g in data.get("genres", [])]),
        "overview": data.get("overview", "No description available"),
        "imdb_url": imdb_url
    }
    return details

# Recommendation function
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        details = fetch_movie_details(movie_id)
        recommended_movies.append(details)

    return recommended_movies

# Trending movies from TMDB
def fetch_trending_movies():
    url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={API_KEY}"
    response = requests.get(url)
    data = response.json()
    trending = []
    for movie in data.get("results", [])[:5]:
        imdb_id = movie.get("id")
        imdb_url = None
        if imdb_id:
            # fetch imdb_id from TMDB details
            imdb_data = requests.get(f"https://api.themoviedb.org/3/movie/{imdb_id}?api_key={API_KEY}&language=en-US").json()
            imdb_url = f"https://www.imdb.com/title/{imdb_data.get('imdb_id')}/" if imdb_data.get("imdb_id") else None

        details = {
            "title": movie.get("title", "Unknown"),
            "poster": "https://image.tmdb.org/t/p/w500/" + movie['poster_path'] if movie.get('poster_path') else "https://via.placeholder.com/500x750?text=No+Poster",
            "release_date": movie.get("release_date", "N/A"),
            "rating": movie.get("vote_average", "N/A"),
            "overview": movie.get("overview", "No description available"),
            "imdb_url": imdb_url
        }
        trending.append(details)
    return trending

# Surprise Me function
def surprise_me():
    random_movie = random.choice(movies['title'].values)
    return recommend(random_movie)

# Streamlit UI
st.title('🎬 Movie Recommender System')

movies_dict = pickle.load(open('movies_dict.pkl','rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl','rb'))

movie_list = movies['title'].values
selected_movie = st.selectbox("Type or select a movie", movie_list)

# Cinematic Background CSS + Hexagon Hover + Glassmorphism
st.markdown(
    """
    <style>
    /* Animated gradient background */
    .stApp {
        background: linear-gradient(-45deg, #1c1c3c, #3c1c1c, #0d0d0d, #1c3c1c);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        color: white;
    }
    @keyframes gradient {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }

    /* Hexagon hover effect */
    .hexagon {
        width: 200px;
        height: 230px;
        background: rgba(255,255,255,0.1);
        clip-path: polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%);
        margin: 20px auto;
        transition: 0.3s;
        border: 3px solid #ff4b4b;
        overflow: hidden;
        backdrop-filter: blur(10px);
    }
    .hexagon img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        clip-path: inherit;
    }
    .hexagon:hover {
        border-color: #00ffcc;
        transform: scale(1.05);
        box-shadow: 0 0 20px #00ffcc;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Show Recommendations
if st.button('Show Recommendation'):
    recommendations = recommend(selected_movie)
    cols = st.columns(5)

    for idx, col in enumerate(cols):
        if idx < len(recommendations):
            details = recommendations[idx]
            imdb_url = details["imdb_url"]
            with col:
                st.markdown(
                    f"""
                    <a href="{imdb_url}" target="_blank">
                        <div class="hexagon">
                            <img src="{details['poster']}">
                        </div>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
                st.markdown(f"**{details['title']}**")
                st.caption(f"Release: {details['release_date']} | ⭐ {details['rating']} | {details['genres']}")
                st.write(details["overview"][:120] + "...")
                if imdb_url:
                    st.markdown(f"[More Info on IMDb]({imdb_url})")

# Surprise Me Button
if st.button("🎲 Surprise Me"):
    recommendations = surprise_me()
    st.subheader("Your Surprise Recommendations")
    cols = st.columns(5)
    for idx, col in enumerate(cols):
        if idx < len(recommendations):
            details = recommendations[idx]
            imdb_url = details["imdb_url"]
            with col:
                st.markdown(
                    f"""
                    <a href="{imdb_url}" target="_blank">
                        <div class="hexagon">
                            <img src="{details['poster']}">
                        </div>
                    </a>
                    """,
                    unsafe_allow_html=True
                )
                st.markdown(f"**{details['title']}**")
                st.caption(f"Release: {details['release_date']} | ⭐ {details['rating']} | {details['genres']}")
                st.write(details["overview"][:120] + "...")
                if imdb_url:
                    st.markdown(f"[More Info on IMDb]({imdb_url})")

# Trending Movies Section
st.subheader("🔥 Trending Movies")
trending = fetch_trending_movies()
cols = st.columns(5)
for idx, col in enumerate(cols):
    if idx < len(trending):
        details = trending[idx]
        imdb_url = details["imdb_url"]
        with col:
            st.markdown(
                f"""
                <a href="{imdb_url}" target="_blank">
                    <div class="hexagon">
                        <img src="{details['poster']}">
                    </div>
                </a>
                """,
                unsafe_allow_html=True
            )
            st.markdown(f"**{details['title']}**")
            st.caption(f"Release: {details['release_date']} | ⭐ {details['rating']}")
            st.write(details["overview"][:120] + "...")
            if imdb_url:
                st.markdown(f"[More Info on IMDb]({imdb_url})")
