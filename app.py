import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ------------------- CONFIG -------------------
st.set_page_config(
    page_title="Anime Explorer & Watchlist",
    layout="wide",
    page_icon="🎌"
)

# ------------------- LOAD DATA -------------------
@st.cache_data
def load_dataset():
    try:
        df = pd.read_csv("anime.csv")
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        st.error("File 'anime_dataset.csv' tidak ditemukan.")
        return pd.DataFrame()

@st.cache_data
def load_watchlist():
    if os.path.exists("watchlist.csv"):
        return pd.read_csv("watchlist.csv")
    return pd.DataFrame()

def save_watchlist(df):
    df.to_csv("watchlist.csv", index=False)

df_anime = load_dataset()
df_watchlist = load_watchlist()

if df_anime.empty:
    st.stop()

# ------------------- TAB SETUP -------------------
tab1, tab2 = st.tabs(["🔍 Explorer", "📝 Watchlist"])

# ------------------- EXPLORER -------------------
with tab1:
    st.header("🔍 Anime Explorer")

    col1, col2 = st.columns(2)
    selected_types = col1.multiselect("Pilih Tipe:", df_anime['Type'].dropna().unique(), default=None)
    selected_sources = col2.multiselect("Pilih Source:", df_anime['Source'].dropna().unique(), default=None)

    filtered = df_anime.copy()
    if selected_types:
        filtered = filtered[filtered['Type'].isin(selected_types)]
    if selected_sources:
        filtered = filtered[filtered['Source'].isin(selected_sources)]

    st.subheader("📊 Visualisasi")
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("### Jumlah Anime per Tahun Rilis")
        if 'Aired' in df_anime.columns:
            df_anime['Year'] = pd.to_datetime(df_anime['Aired'], errors='coerce').dt.year
            year_counts = df_anime['Year'].value_counts().sort_index()
            fig, ax = plt.subplots()
            sns.barplot(x=year_counts.index, y=year_counts.values, ax=ax)
            plt.xticks(rotation=45)
            ax.set_xlabel("Tahun")
            ax.set_ylabel("Jumlah Anime")
            st.pyplot(fig)
        else:
            st.warning("Kolom 'Aired' tidak ditemukan untuk membuat grafik tahun.")

    with col4:
        st.markdown("### Jumlah Anime per Rating Umur")
        if 'Rating' in df_anime.columns:
            rating_counts = df_anime['Rating'].value_counts()
            fig2, ax2 = plt.subplots()
            sns.barplot(y=rating_counts.index, x=rating_counts.values, ax=ax2)
            ax2.set_xlabel("Jumlah")
            ax2.set_ylabel("Rating Umur")
            st.pyplot(fig2)
        else:
            st.warning("Kolom 'Rating' tidak ditemukan untuk membuat grafik rating.")

    st.subheader("📄 Daftar Anime")
    selected_anime = st.selectbox("Pilih anime untuk ditambahkan ke Watchlist:", filtered['Title'].dropna().unique())
    if st.button("➕ Tambah ke Watchlist"):
        selected_row = filtered[filtered['Title'] == selected_anime]
        if not selected_row.empty:
            if df_watchlist.empty or selected_anime not in df_watchlist['Title'].values:
                df_watchlist = pd.concat([df_watchlist, selected_row], ignore_index=True)
                save_watchlist(df_watchlist)
                st.success(f"{selected_anime} berhasil ditambahkan ke watchlist!")
            else:
                st.info(f"{selected_anime} sudah ada di watchlist.")

    st.dataframe(filtered.reset_index(drop=True), use_container_width=True)

# ------------------- WATCHLIST -------------------
with tab2:
    st.header("📝 Watchlist Saya")
    if df_watchlist.empty:
        st.info("Watchlist masih kosong. Tambahkan anime dari tab Explorer.")
    else:
        st.dataframe(df_watchlist.reset_index(drop=True), use_container_width=True)
        if st.button("🗑️ Hapus Semua Watchlist"):
            save_watchlist(pd.DataFrame())
            st.success("Watchlist berhasil dikosongkan.")
