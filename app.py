import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os # Untuk memeriksa keberadaan file

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(
    page_title="Anime Explorer & Personal Watchlist (Local)",
    page_icon="🌸",
    layout="wide"
)

# --- Judul Aplikasi ---
st.title("🌸 Anime Explorer & Personal Watchlist (Local Edition) 🌸")
st.markdown("---")

# --- Nama File Data Lokal ---
ANIME_DATA_FILE = "anime.csv"
WATCHLIST_DATA_FILE = "user_watchlist.csv"

# --- Fungsi untuk Memuat Data Anime Master (Read-Only) ---
@st.cache_data(ttl=3600) # Cache data anime selama 1 jam
def load_anime_data():
    """Memuat data anime dari file CSV lokal."""
    try:
        df = pd.read_csv(ANIME_DATA_FILE)

        # Konversi tipe data dan bersihkan
        df['Score'] = pd.to_numeric(df['Score'], errors='coerce')
        df['Popularity'] = pd.to_numeric(df['Popularity'], errors='coerce')
        df['Members'] = pd.to_numeric(df['Members'], errors='coerce')
        df['Episodes'] = pd.to_numeric(df['Episodes'], errors='coerce')

        df['Genres'] = df['Genres'].apply(lambda x: [g.strip() for g in str(x).split(',') if g.strip()] if pd.notna(x) else [])
        df['Producers'] = df['Producers'].apply(lambda x: [p.strip() for p in str(x).split(',') if p.strip()] if pd.notna(x) else [])
        df['Studios'] = df['Studios'].apply(lambda x: [s.strip() for s in str(x).split(',') if s.strip()] if pd.notna(x) else [])

        df.dropna(subset=['Mal ID'], inplace=True)
        df.drop_duplicates(subset=['Mal ID'], inplace=True)

        return df
    except FileNotFoundError:
        st.error(f"Error: File '{ANIME_DATA_FILE}' tidak ditemukan. Pastikan file ini ada di folder yang sama dengan app.py.")
        st.stop()
    except Exception as e:
        st.error(f"Error memuat data anime dari '{ANIME_DATA_FILE}': {e}")
        st.stop()

# --- Fungsi untuk Memuat Data Watchlist Pribadi ---
@st.cache_data(ttl=60) # Cache data watchlist sebentar karena bisa sering diupdate
def load_watchlist_data():
    """Memuat data watchlist dari file CSV lokal, atau membuat DataFrame kosong jika tidak ada."""
    if os.path.exists(WATCHLIST_DATA_FILE):
        try:
            df = pd.read_csv(WATCHLIST_DATA_FILE)
            # Pastikan kolom Mal ID adalah int/float untuk merge
            df['Mal ID'] = pd.to_numeric(df['Mal ID'], errors='coerce').astype('Int64') # Int64 untuk handle NaN
            df['Personal Rating'] = pd.to_numeric(df['Personal Rating'], errors='coerce')
            return df
        except Exception as e:
            st.warning(f"Error memuat watchlist dari '{WATCHLIST_DATA_FILE}': {e}. Membuat watchlist baru.")
            return pd.DataFrame(columns=['Mal ID', 'Title', 'Status', 'Personal Rating', 'Notes', 'Progress'])
    else:
        st.info("File watchlist tidak ditemukan. Membuat watchlist baru.")
        return pd.DataFrame(columns=['Mal ID', 'Title', 'Status', 'Personal Rating', 'Notes', 'Progress'])

# --- Fungsi untuk Menyimpan Data Watchlist Pribadi ---
def save_watchlist_data(df_watchlist):
    """Menyimpan DataFrame watchlist ke file CSV lokal."""
    try:
        df_watchlist.to_csv(WATCHLIST_DATA_FILE, index=False)
        st.success("Watchlist berhasil diperbarui dan disimpan!")
        load_watchlist_data.clear() # Hapus cache agar data terbaru dimuat
    except Exception as e:
        st.error(f"Gagal menyimpan watchlist: {e}")

# --- Inisialisasi Data ---
df_anime = load_anime_data()
df_watchlist = load_watchlist_data()

# Pastikan df_anime tidak kosong
if df_anime.empty:
    st.error("Tidak ada data anime yang dimuat dari 'anime.csv'. Pastikan file tidak kosong.")
    st.stop()

# --- Sidebar Navigasi ---
st.sidebar.header("Navigasi")
page = st.sidebar.radio("Pilih Halaman:", ["Explorer Dashboard", "Personal Watchlist"])
st.sidebar.markdown("---")

# --- Bagian Explorer Dashboard ---
if page == "Explorer Dashboard":
    st.header("🔍 Explorer Dashboard")

    col1, col2 = st.columns(2)

    # Filter Genre
    all_genres = sorted(list(set(g for sublist in df_anime['Genres'] for g in sublist)))
    selected_genres = col1.multiselect("Pilih Genre(s):", all_genres, default=all_genres[:5])

    # Filter Type
    all_types = df_anime['Type'].unique().tolist()
    selected_types = col2.multiselect("Pilih Tipe:", all_types, default=all_types)

    # Filter Score
    min_score, max_score = col1.slider(
        "Rentang Skor (Overall):",
        min_value=float(df_anime['Score'].min()),
        max_value=float(df_anime['Score'].max()),
        value=(float(df_anime['Score'].min()), float(df_anime['Score'].max()))
    )

    # Filter Episodes
    max_episodes = col2.slider(
        "Maksimal Episode:",
        min_value=1,
        max_value=int(df_anime['Episodes'].max()),
        value=int(df_anime['Episodes'].max())
    )

    # Filter data berdasarkan pilihan
    filtered_df = df_anime[
        (df_anime['Score'] >= min_score) &
        (df_anime['Score'] <= max_score) &
        (df_anime['Episodes'] <= max_episodes) &
        (df_anime['Type'].isin(selected_types))
    ]

    # Filter genre (lebih kompleks karena list)
    if selected_genres:
        filtered_df = filtered_df[filtered_df['Genres'].apply(lambda x: any(genre in x for genre in selected_genres))]

    st.subheader(f"Ditemukan {len(filtered_df)} Anime")

    # --- Visualisasi ---
    st.subheader("Visualisasi Tren Anime")

    if not filtered_df.empty:
        # Visualisasi 1: Top 10 Genres by Count
        st.markdown("### Top 10 Genre Terpopuler (Berdasarkan Jumlah Anime)")
        genre_counts = pd.Series([g for sublist in filtered_df['Genres'] for g in sublist]).value_counts().head(10)
        fig_genre = px.bar(genre_counts, x=genre_counts.index, y=genre_counts.values,
                           labels={'x': 'Genre', 'y': 'Jumlah Anime'},
                           title='Distribusi Genre Anime')
        fig_genre.update_xaxes(tickangle=45)
        st.plotly_chart(fig_genre, use_container_width=True)

        # Visualisasi 2: Score Distribution
        st.markdown("### Distribusi Skor Anime")
        fig_score_dist = px.histogram(filtered_df, x='Score', nbins=20,
                                      title='Distribusi Skor Anime',
                                      labels={'Score': 'Skor Rata-rata'})
        st.plotly_chart(fig_score_dist, use_container_width=True)

        # Visualisasi 3: Top 10 Studios by Count (jika ada data studio)
        if 'Studios' in filtered_df.columns and not filtered_df['Studios'].apply(lambda x: len(x) == 0).all():
            st.markdown("### Top 10 Studio Anime")
            studio_counts = pd.Series([s for sublist in filtered_df['Studios'] for s in sublist]).value_counts().head(10)
            if not studio_counts.empty:
                fig_studio = px.bar(studio_counts, x=studio_counts.index, y=studio_counts.values,
                                    labels={'x': 'Studio', 'y': 'Jumlah Anime'},
                                    title='Top 10 Studio Anime')
                fig_studio.update_xaxes(tickangle=45)
                st.plotly_chart(fig_studio, use_container_width=True)
            else:
                st.info("Tidak ada data studio yang tersedia untuk visualisasi ini.")
        else:
            st.info("Kolom 'Studios' tidak ditemukan atau kosong untuk visualisasi ini.")

        # Visualisasi 4: Score vs Members (scatterplot)
        st.markdown("### Korelasi Skor vs. Jumlah Anggota (Pengguna)")
        fig_score_members = px.scatter(filtered_df, x='Score', y='Members',
                                       hover_name='Title', log_y=True,
                                       title='Skor Anime vs. Jumlah Anggota')
        st.plotly_chart(fig_score_members, use_container_width=True)

        # --- Tabel Anime Interaktif ---
        st.subheader("Daftar Anime")
        st.write("Klik baris untuk melihat detail atau menambah ke watchlist.")

        st.session_state.current_selected_anime = None
        selected_row = st.dataframe(
            filtered_df[['Title', 'Type', 'Episodes', 'Score', 'Genres', 'Studios', 'Producers']],
            hide_index=True,
            use_container_width=True,
            height=300,
            selection_mode="single-row",
            on_select="rerun"
        )

        if selected_row.selection.rows:
            selected_index = selected_row.selection.rows[0]
            st.session_state.current_selected_anime = filtered_df.iloc[selected_index]

        # --- Detail dan Aksi pada Anime ---
        if st.session_state.current_selected_anime is not None:
            anime_detail = st.session_state.current_selected_anime
            st.markdown(f"### Detail Anime: {anime_detail['Title']}")
            st.write(f"**MAL ID:** {anime_detail['Mal ID']}")
            st.write(f"**Tipe:** {anime_detail['Type']}")
            st.write(f"**Episode:** {int(anime_detail['Episodes']) if pd.notna(anime_detail['Episodes']) else 'N/A'}")
            st.write(f"**Skor (Overall):** {anime_detail['Score']:.2f}")
            st.write(f"**Genre:** {', '.join(anime_detail['Genres'])}")
            st.write(f"**Studio:** {', '.join(anime_detail['Studios'])}")
            st.write(f"**Producer:** {', '.join(anime_detail['Producers'])}")
            st.write(f"**Status Rilis:** {anime_detail['Status']}")
            st.write(f"**Tanggal Tayang:** {anime_detail['Aired']}")
            st.write(f"**Sinopsis:** {anime_detail['Description'] if pd.notna(anime_detail['Description']) else 'Tidak tersedia.'}")

            st.markdown("---")
            # --- Tambahkan ke Watchlist ---
            if st.button("➕ Tambahkan ke Watchlist"):
                # Pastikan Mal ID adalah integer untuk perbandingan yang konsisten
                anime_mal_id = int(anime_detail['Mal ID'])

                if not df_watchlist.empty and anime_mal_id in df_watchlist['Mal ID'].values:
                    st.warning("Anime ini sudah ada di watchlist Anda!")
                else:
                    new_entry = {
                        'Mal ID': anime_mal_id,
                        'Title': anime_detail['Title'],
                        'Status': 'Belum Ditonton',
                        'Personal Rating': None,
                        'Notes': '',
                        'Progress': ''
                    }
                    df_watchlist_temp = pd.concat([df_watchlist, pd.DataFrame([new_entry])], ignore_index=True)
                    save_watchlist_data(df_watchlist_temp)
                    st.success(f"'{anime_detail['Title']}' berhasil ditambahkan ke watchlist Anda!")
                    st.rerun()
    else:
        st.warning("Tidak ada anime yang cocok dengan filter yang dipilih.")

# --- Bagian Personal Watchlist ---
elif page == "Personal Watchlist":
    st.header("📝 Personal Watchlist")

    if df_watchlist.empty:
        st.info("Watchlist Anda kosong. Tambahkan anime dari 'Explorer Dashboard'.")
    else:
        st.subheader("Daftar Watchlist Anda")

        # Merge dengan df_anime untuk mendapatkan detail lengkap
        # Hanya merge kolom yang relevan dari df_anime
        df_watchlist_display = pd.merge(df_watchlist, df_anime[['Mal ID', 'Type', 'Episodes', 'Score', 'Genres']],
                                        on='Mal ID', how='left') # Tidak perlu join 'Title' karena sudah ada di watchlist

        # Pastikan kolom yang dibutuhkan ada setelah merge
        display_cols = ['Title', 'Status', 'Personal Rating', 'Notes', 'Progress', 'Type', 'Episodes', 'Score']
        # Handle kasus jika kolom dari df_anime tidak ditemukan setelah merge
        for col in ['Type', 'Episodes', 'Score', 'Genres']:
            if col not in df_watchlist_display.columns:
                df_watchlist_display[col] = None # Atau nilai default lainnya

        # Ensure 'Title' is from watchlist for editing consistency
        df_watchlist_display['Title'] = df_watchlist['Title']

        edited_watchlist = st.data_editor(
            df_watchlist_display,
            column_config={
                "Title": st.column_config.Column("Judul Anime", disabled=True),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Belum Ditonton", "Sedang Menonton", "Ditonton", "Dropped"],
                    required=True,
                ),
                "Personal Rating": st.column_config.NumberColumn(
                    "Rating Pribadi",
                    min_value=1,
                    max_value=10,
                    step=1,
                    format="%d ⭐",
                ),
                "Notes": st.column_config.TextColumn("Catatan", width="large"),
                "Progress": st.column_config.TextColumn("Progres Tontonan"),
                "Type": st.column_config.Column("Tipe", disabled=True),
                "Episodes": st.column_config.Column("Episode", disabled=True),
                "Score": st.column_config.Column("Skor", disabled=True)
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
            key="watchlist_editor"
        )

        if st.button("💾 Simpan Perubahan Watchlist"):
            # Karena st.data_editor mengembalikan DataFrame yang sudah diubah,
            # kita hanya perlu memastikan kolom-kolom yang asli tetap ada
            # dan Mal ID tidak berubah.
            # Mal ID tidak terlihat di data_editor, jadi kita perlu menggabungkannya kembali.
            final_watchlist_df = df_watchlist_display[['Mal ID']].merge(
                edited_watchlist[['Title', 'Status', 'Personal Rating', 'Notes', 'Progress']],
                left_index=True, right_index=True
            )
            # Pastikan Mal ID dan Title diambil dari df_watchlist asli atau df_anime jika diperlukan
            # Menggunakan Mal ID dari df_watchlist asli agar tidak berubah saat editing
            final_watchlist_df['Mal ID'] = df_watchlist['Mal ID']
            final_watchlist_df['Title'] = df_watchlist['Title'] # Pastikan Title tidak berubah

            save_watchlist_data(final_watchlist_df)
            st.rerun() # Refresh halaman setelah simpan

        st.markdown("---")
        st.subheader("Ringkasan Watchlist")

        # Visualisasi Ringkasan Watchlist
        if not edited_watchlist.empty:
            # Status Distribusi
            status_counts = edited_watchlist['Status'].value_counts()
            fig_status = px.pie(status_counts, values=status_counts.values, names=status_counts.index,
                                title='Distribusi Status Tontonan', hole=0.3)
            st.plotly_chart(fig_status, use_container_width=True)

            # Rata-rata Rating Pribadi
            avg_rating = edited_watchlist['Personal Rating'].mean()
            if pd.notna(avg_rating):
                st.metric(label="Rata-rata Rating Pribadi", value=f"{avg_rating:.2f} ⭐")
            else:
                st.info("Belum ada rating pribadi yang diberikan.")

            # Top 5 Anime dengan Rating Pribadi Tertinggi
            if 'Personal Rating' in edited_watchlist.columns and edited_watchlist['Personal Rating'].notna().any():
                top_rated = edited_watchlist.sort_values(by='Personal Rating', ascending=False).head(5)
                st.markdown("### Top 5 Anime dengan Rating Pribadi Tertinggi")
                st.dataframe(top_rated[['Title', 'Personal Rating', 'Status']], hide_index=True)