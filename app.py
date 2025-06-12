import streamlit as st
import pandas as pd
import plotly.express as px

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(
    page_title="Anime Explorer & Personal Watchlist (Non-Persistent)",
    page_icon="🌸",
    layout="wide"
)

# --- Judul Aplikasi ---
st.title("🌸 Anime Explorer & Personal Watchlist (Non-Persistent Local Edition) 🌸")
st.markdown("---")

# --- Nama File Data Anime Master ---
ANIME_DATA_FILE = "anime.csv"

# --- Fungsi Memuat Data ---
@st.cache_data(ttl=3600)
def load_anime_data():
    try:
        df = pd.read_csv(ANIME_DATA_FILE)

        # Tambah kolom Mal ID (karena tidak ada di CSV)
        df.reset_index(inplace=True)
        df.rename(columns={"index": "Mal ID"}, inplace=True)
        df["Mal ID"] += 1

        # Bersihkan kolom numerik
        for col in ['Score', 'Popularity', 'Episodes', 'Vote', 'Ranked']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Pastikan kolom list diparsing dengan baik
        for col in ['Producers', 'Studios']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: [i.strip() for i in str(x).split(',') if i.strip()] if pd.notna(x) else [])

        df.drop_duplicates(subset=['Mal ID'], inplace=True)
        return df

    except FileNotFoundError:
        st.error(f"File '{ANIME_DATA_FILE}' tidak ditemukan.")
        st.stop()
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        st.stop()

# --- Inisialisasi Watchlist ---
if 'watchlist_data' not in st.session_state:
    st.session_state.watchlist_data = pd.DataFrame(columns=['Mal ID', 'Title', 'Status', 'Personal Rating', 'Notes', 'Progress'])

# --- Load Data ---
df_anime = load_anime_data()
if df_anime.empty:
    st.error("Data anime kosong.")
    st.stop()

# --- Sidebar Navigasi ---
st.sidebar.header("Navigasi")
page = st.sidebar.radio("Pilih Halaman:", ["Explorer Dashboard", "Personal Watchlist"])

# --- Explorer Dashboard ---
if page == "Explorer Dashboard":
    st.header("🔍 Explorer Dashboard")
    col1, col2 = st.columns(2)

    all_types = df_anime['Type'].dropna().unique().tolist()
    selected_types = col1.multiselect("Pilih Tipe:", all_types, default=all_types)

    all_sources = df_anime['Source'].dropna().unique().tolist()
    selected_sources = col2.multiselect("Pilih Source:", all_sources, default=all_sources[:3])

    min_score, max_score = col1.slider("Rentang Skor:",
        min_value=float(df_anime['Score'].min()),
        max_value=float(df_anime['Score'].max()),
        value=(float(df_anime['Score'].min()), float(df_anime['Score'].max()))
    )

    max_episodes = col2.slider("Maksimal Episode:",
        min_value=1,
        max_value=int(df_anime['Episodes'].max()),
        value=int(df_anime['Episodes'].max())
    )

    filtered_df = df_anime[
        (df_anime['Score'] >= min_score) &
        (df_anime['Score'] <= max_score) &
        (df_anime['Episodes'] <= max_episodes) &
        (df_anime['Type'].isin(selected_types)) &
        (df_anime['Source'].isin(selected_sources))
    ]

    st.subheader(f"Ditemukan {len(filtered_df)} Anime")

    if not filtered_df.empty:
        st.markdown("### Distribusi Skor Anime")
        fig_score = px.histogram(filtered_df, x='Score', nbins=20, title='Distribusi Skor')
        st.plotly_chart(fig_score, use_container_width=True)

        st.markdown("### Scatterplot Skor vs. Popularity")
        fig_scatter = px.scatter(filtered_df, x='Score', y='Popularity', hover_name='Title')
        st.plotly_chart(fig_scatter, use_container_width=True)

        st.subheader("Daftar Anime")
        st.dataframe(filtered_df[['Title', 'Type', 'Episodes', 'Score', 'Source', 'Studios']].sort_values(by='Score', ascending=False), height=400)

# --- Watchlist ---
elif page == "Personal Watchlist":
    st.header("📝 Personal Watchlist")
    if st.session_state.watchlist_data.empty:
        st.info("Watchlist kosong. Tambahkan anime dari Explorer.")
    else:
        st.subheader("Daftar Anda")
        edited = st.data_editor(
            st.session_state.watchlist_data,
            column_config={
                "Status": st.column_config.SelectboxColumn("Status", options=["Belum Ditonton", "Sedang Menonton", "Selesai", "Dropped"]),
                "Personal Rating": st.column_config.NumberColumn("Rating", min_value=1, max_value=10),
                "Notes": st.column_config.TextColumn("Catatan"),
                "Progress": st.column_config.TextColumn("Progress")
            },
            num_rows="dynamic",
            use_container_width=True
        )
        st.session_state.watchlist_data = edited
        st.success("Perubahan disimpan sementara.")
