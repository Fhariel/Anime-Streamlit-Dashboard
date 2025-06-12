import streamlit as st
import pandas as pd

# ------------------- CONFIG -------------------
st.set_page_config(
    page_title="Anime Explorer & Watchlist",
    layout="wide",
    page_icon="🎌"
)

# ------------------- LOAD DATA -------------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("anime.csv")
        df.columns = df.columns.str.strip()  # bersihkan spasi
        return df
    except FileNotFoundError:
        st.error("File 'anime_dataset.csv' tidak ditemukan. Pastikan file ada di folder yang sama dengan app.py.")
        return pd.DataFrame()

df_anime = load_data()

if df_anime.empty:
    st.stop()  # Hentikan app jika dataset kosong

# ------------------- TABS -------------------
tab1, tab2 = st.tabs(["🔍 Explorer", "📝 Watchlist"])

# ------------------- EXPLORER TAB -------------------
with tab1:
    st.header("🔍 Anime Explorer Dashboard")

    col1, col2 = st.columns(2)

    all_types = df_anime['Type'].dropna().unique().tolist() if 'Type' in df_anime else []
    selected_types = col1.multiselect("Pilih Tipe:", all_types, default=all_types)

    all_sources = df_anime['Source'].dropna().unique().tolist() if 'Source' in df_anime else []
    selected_sources = col2.multiselect("Pilih Source:", all_sources, default=all_sources)

    filtered_df = df_anime.copy()
    if selected_types:
        filtered_df = filtered_df[filtered_df['Type'].isin(selected_types)]
    if selected_sources:
        filtered_df = filtered_df[filtered_df['Source'].isin(selected_sources)]

    st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)

# ------------------- WATCHLIST TAB -------------------
with tab2:
    st.header("📝 Personal Watchlist")
    st.info("✨ Fitur ini masih pengembangan. Silakan tentukan bagaimana kamu ingin menyimpan data watchlist (misalnya file lokal, SQLite, dsb).")

    st.markdown("""
    - 🎯 Kamu bisa tambahkan fitur input untuk memilih anime dari data dan disimpan ke `watchlist.csv`
    - 💾 Watchlist bisa dibaca menggunakan `pd.read_csv("watchlist.csv")` dan ditampilkan di sini
    - 🧠 Bisa dikembangkan pakai fitur simpan lokal (pickle, CSV) atau database
    """)

