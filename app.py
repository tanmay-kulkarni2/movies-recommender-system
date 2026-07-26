import pickle
import streamlit as st
import requests
import pandas as pd
import random

# ------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------
API_KEY = "c3cb4316e3ff7ad445124a0287af1d89"   # <-- put your real TMDB API key here

st.set_page_config(page_title="Movie Recommender System", page_icon="🎬", layout="centered")


# ------------------------------------------------------------------
# DATA HELPERS
# ------------------------------------------------------------------
@st.cache_data
def fetch_movie_details(movie_id):
    """Fetch full movie details (poster, rating, genres, IMDb link) from TMDB."""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException:
        return {
            "title": "Unavailable",
            "poster": "https://via.placeholder.com/500x750?text=No+Poster",
            "release_date": "N/A",
            "rating": "N/A",
            "genres": "",
            "overview": "Could not fetch details for this movie.",
            "imdb_url": None,
        }

    imdb_id = data.get("imdb_id")
    imdb_url = f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else None

    return {
        "title": data.get("title", "Unknown"),
        "poster": "https://image.tmdb.org/t/p/w500/" + data["poster_path"]
        if data.get("poster_path")
        else "https://via.placeholder.com/500x750?text=No+Poster",
        "release_date": data.get("release_date", "N/A"),
        "rating": data.get("vote_average", "N/A"),
        "genres": ", ".join([g["name"] for g in data.get("genres", [])]),
        "overview": data.get("overview", "No description available"),
        "imdb_url": imdb_url,
    }


def recommend(movie):
    """Return top-5 recommended movies similar to the given movie title."""
    movie_index = movies[movies["title"] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(fetch_movie_details(movie_id))

    return recommended_movies


@st.cache_data(ttl=3600)  # refresh trending list once an hour
def fetch_trending_movies():
    """Fetch today's trending movies from TMDB (reuses fetch_movie_details, no duplicate calls)."""
    url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException:
        return []

    trending = []
    for movie in data.get("results", [])[:5]:
        details = fetch_movie_details(movie["id"])
        trending.append(details)
    return trending


def surprise_me():
    random_movie = random.choice(movies["title"].values)
    return recommend(random_movie)


def render_movie_row(movie_details_list):
    """Render a row of hexagon poster cards for a list of movie detail dicts."""
    cols = st.columns(5)
    for idx, col in enumerate(cols):
        if idx < len(movie_details_list):
            details = movie_details_list[idx]
            imdb_url = details["imdb_url"] or "#"
            with col:
                st.markdown(
                    f"""
                    <a href="{imdb_url}" target="_blank">
                        <div class="hexagon">
                            <img src="{details['poster']}">
                        </div>
                    </a>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(f"**{details['title']}**")
                rating_line = f"Release: {details['release_date']} | ⭐ {details['rating']}"
                if details.get("genres"):
                    rating_line += f" | {details['genres']}"
                st.caption(rating_line)
                st.write(details["overview"][:120] + "...")
                if details["imdb_url"]:
                    st.markdown(f"[More Info on IMDb]({details['imdb_url']})")


# ------------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------------
st.title("🎬 Movie Recommender System")

if API_KEY == "ENTER YOUR API KEY":
    st.warning("⚠️ Add your TMDB API key in `app.py` before running — posters and details won't load without it.")

movies_dict = pickle.load(open("movies_dict.pkl", "rb"))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open("similarity.pkl", "rb"))

movie_list = movies["title"].values
selected_movie = st.selectbox("Type or select a movie", movie_list)

# ------------------------------------------------------------------
# STYLING — animated gradient background + hexagon hover effect
# ------------------------------------------------------------------
st.markdown(
    """
    <style>
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
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# SHOW RECOMMENDATIONS
# ------------------------------------------------------------------
if st.button("Show Recommendation"):
    with st.spinner("Finding movies you'll love..."):
        recommendations = recommend(selected_movie)
    render_movie_row(recommendations)

# ------------------------------------------------------------------
# SURPRISE ME
# ------------------------------------------------------------------
if st.button("🎲 Surprise Me"):
    with st.spinner("Picking something fun..."):
        recommendations = surprise_me()
    st.subheader("Your Surprise Recommendations")
    render_movie_row(recommendations)

# ------------------------------------------------------------------
# TRENDING MOVIES
# ------------------------------------------------------------------
st.subheader("🔥 Trending Movies")
trending = fetch_trending_movies()
if trending:
    render_movie_row(trending)
else:
    st.info("Couldn't load trending movies right now — check your API key or internet connection.")