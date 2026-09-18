import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="Dashboard Evaluasi LSP", layout="wide")

def hapus_semua_filter():
    st.session_state.filter_top_n = 5
    st.session_state.filter_tahun = []
    st.session_state.filter_pt = []
    st.session_state.filter_asesor = []
    st.session_state.filter_region = []

# ==========================================
# 2. LOAD & CLEAN DATA EXCEL BARU
# ==========================================
@st.cache_data
def load_data():
    file_path = "New Monitoring Asesmen Pemanen LSP 2026 (1).xlsx"

    df_asesmen = pd.read_excel(file_path, sheet_name='DATA ASESMEN')
    df_asesor = pd.read_excel(file_path, sheet_name='DATA ASESOR')

    # Cleaning Nama Asesor agar konsisten
    koreksi_nama = {
        'HERWAN THEO L.': 'HERWAN THEO LOLOPAYUNG',
        'RIKARDUS S. MARINO': 'RIKARDUS SEVERINUS MARINO',
        'SAIPUL R. SARAGIH': 'SAIPUL RAMADHAN SARAGIH',
        'ERIKSON H. SARAGIH': 'Erikson Hasiholan Saragih'
    }
    df_asesmen['ASESOR'] = df_asesmen['ASESOR'].replace(koreksi_nama)

    return df_asesmen, df_asesor

df_asesmen, df_asesor = load_data()

# ==========================================
# 3. SIDEBAR (FILTER)
# ==========================================
st.sidebar.header("Filter Data")
st.sidebar.markdown("**TAMPILAN TOP DATA**")
top_n = st.sidebar.slider("Jumlah Top PT & Asesor", min_value=3, max_value=25, value=5, key="filter_top_n")

st.sidebar.markdown("**TAHUN**")
list_tahun = sorted([int(x) for x in df_asesmen['TAHUN SERTIFIKASI'].dropna().unique()])
pilihan_tahun = st.sidebar.multiselect("Pilih Tahun", options=list_tahun, key="filter_tahun", label_visibility="collapsed", placeholder="Semua Tahun")

st.sidebar.markdown("**PT**")
list_pt = sorted([str(x) for x in df_asesmen['PT'].dropna().unique()])
pilihan_pt = st.sidebar.multiselect("Pilih PT", options=list_pt, key="filter_pt", label_visibility="collapsed", placeholder="Semua PT")

st.sidebar.markdown("**ASESOR**")
list_asesor = sorted([str(x) for x in df_asesmen['ASESOR'].dropna().unique()])
pilihan_asesor = st.sidebar.multiselect("Pilih Asesor", options=list_asesor, key="filter_asesor", label_visibility="collapsed", placeholder="Semua Asesor")

st.sidebar.markdown("**REGION / DAERAH**")
list_region = sorted([str(x) for x in df_asesmen['Region'].dropna().unique()])
pilihan_region = st.sidebar.multiselect("Pilih Region", options=list_region, key="filter_region", label_visibility="collapsed", placeholder="Semua Region")

st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.button("clear all", on_click=hapus_semua_filter, type="tertiary", use_container_width=True)

# ==========================================
# 4. LOGIKA FILTERING
# ==========================================
df_filtered = df_asesmen.copy()

if pilihan_tahun:
    df_filtered = df_filtered[df_filtered['TAHUN SERTIFIKASI'].isin(pilihan_tahun)]
if pilihan_pt:
    df_filtered = df_filtered[df_filtered['PT'].isin(pilihan_pt)]
if pilihan_asesor:
    df_filtered = df_filtered[df_filtered['ASESOR'].isin(pilihan_asesor)]
if pilihan_region:
    df_filtered = df_filtered[df_filtered['Region'].isin(pilihan_region)]

# ==========================================
# 5. KONTEN UTAMA & SUMMARY METRICS
# ==========================================
st.title("Dashboard Monitoring Asesmen Pemanen LSP")
st.markdown("---")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric(label="Total Asesi (Selesai)", value=f"{len(df_filtered[df_filtered['ASESMEN'] == 'DONE']):,}")
with col2:
    st.metric(label="Total Target Asesi", value=f"{len(df_filtered):,}")
with col3:
    st.metric(label="Total PT Terlibat", value=f"{df_filtered['PT'].nunique():,}")
with col4:
    st.metric(label="Total Asesor Aktif", value=f"{df_filtered['ASESOR'].nunique():,}")
with col5:
    # NEW: total asesor terdaftar (dari master data, bukan hanya yg muncul di data asesmen terfilter)
    st.metric(label="Total Asesor Terdaftar", value=f"{df_asesor['Nama Lengkap'].nunique():,}")

st.write("    ")
st.markdown("---")

# ---------------------------------------------------------
# NEW SECTION: SEBARAN ASESOR PER PT & PER REGION (dari DATA ASESOR)
# Requirement no. 2: "sebaran asesor per PT, sebaran asesor per Region"
# ---------------------------------------------------------
st.subheader("Sebaran Asesor (Berdasarkan Data Master Asesor)")
col_sebaran_pt, col_sebaran_region = st.columns(2)

with col_sebaran_pt:
    st.markdown("**Jumlah Asesor per PT / Instansi**")
    sebaran_pt = df_asesor['Instansi Tempat Bekerja'].value_counts().reset_index()
    sebaran_pt.columns = ['Instansi Tempat Bekerja', 'Jumlah Asesor']

    if not sebaran_pt.empty:
        fig_sebaran_pt = px.bar(
            sebaran_pt.sort_values('Jumlah Asesor', ascending=True),
            x='Jumlah Asesor', y='Instansi Tempat Bekerja', orientation='h',
            text='Jumlah Asesor', color='Jumlah Asesor', color_continuous_scale='Purples'
        )
        fig_sebaran_pt.update_layout(showlegend=False, yaxis_title=None)
        st.plotly_chart(fig_sebaran_pt, use_container_width=True)
    else:
        st.info("Data instansi asesor tidak tersedia.")

with col_sebaran_region:
    st.markdown("**Jumlah Asesor per Provinsi**")
    # df_asesor tidak punya kolom "Region" (KALTENG 1, dst) seperti df_asesmen,
    # jadi dipakai kolom Provinsi sebagai proksi sebaran wilayah asesor.
    sebaran_prov = df_asesor['Provinsi'].value_counts().reset_index()
    sebaran_prov.columns = ['Provinsi', 'Jumlah Asesor']

    if not sebaran_prov.empty:
        fig_sebaran_prov = px.bar(
            sebaran_prov.sort_values('Jumlah Asesor', ascending=True),
            x='Jumlah Asesor', y='Provinsi', orientation='h',
            text='Jumlah Asesor', color='Jumlah Asesor', color_continuous_scale='Oranges'
        )
        fig_sebaran_prov.update_layout(showlegend=False, yaxis_title=None)
        st.plotly_chart(fig_sebaran_prov, use_container_width=True)
    else:
        st.info("Data provinsi asesor tidak tersedia.")

st.caption("Catatan: sheet DATA ASESOR tidak memiliki kolom Region (KALTENG 1, KALTIM 2, dst) seperti di DATA ASESMEN, sehingga sebaran wilayah asesor ditampilkan berdasarkan Provinsi tempat tinggal.")

st.markdown("---")

# ---------------------------------------------------------
# GRAFIK 1 & 2: TAHAPAN BLANKO & CAPAIAN TARGET PER ASESOR (DONE vs NOT DONE)
# ---------------------------------------------------------
col_funnel, col_capaian_asesor = st.columns(2)

with col_funnel:
    st.subheader("Progress Tahapan Sertifikasi (Status 'DONE')")
    tahapan = ['ASESMEN', 'PENGAJUAN BLANKO', 'TERBIT BLANKO', 'DELIVERY BLANKO']
    jumlah_done = [df_filtered[kolom].value_counts().get('DONE', 0) if kolom in df_filtered.columns else 0 for kolom in tahapan]

    fig_funnel = go.Figure(go.Funnel(
        y=tahapan, x=jumlah_done, textinfo="value+percent initial",
        marker=dict(color=['#3498db', '#2980b9', '#1f618d', '#154360'])
    ))
    fig_funnel.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig_funnel, use_container_width=True)
    st.write("    ")

with col_capaian_asesor:
    # CHANGED: sebelumnya hanya menampilkan NOT DONE. Sekarang DONE vs NOT DONE
    # per asesor supaya terlihat rasio capaian terhadap target, bukan cuma tunggakan.
    st.subheader("Capaian Target per Asesor (DONE vs NOT DONE)")

    capaian_asesor = df_filtered.groupby(['ASESOR', 'ASESMEN'])['No'].count().reset_index()
    capaian_asesor.columns = ['Nama Asesor', 'Status', 'Jumlah']

    # urutkan asesor berdasarkan total target (DONE + NOT DONE), ambil top_n
    total_per_asesor = capaian_asesor.groupby('Nama Asesor')['Jumlah'].sum().sort_values(ascending=False)
    top_asesor_list = total_per_asesor.head(top_n).index.tolist()
    capaian_asesor_top = capaian_asesor[capaian_asesor['Nama Asesor'].isin(top_asesor_list)]

    if not capaian_asesor_top.empty:
        fig_capaian_asesor = px.bar(
            capaian_asesor_top, x='Jumlah', y='Nama Asesor', color='Status',
            orientation='h', text='Jumlah',
            color_discrete_map={'DONE': '#2ecc71', 'NOT DONE': '#e74c3c'}
        )
        fig_capaian_asesor.update_layout(
            barmode='stack', yaxis={'categoryorder': 'total ascending'},
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_capaian_asesor, use_container_width=True)
    else:
        st.info("Data capaian asesor tidak tersedia.")

st.markdown("---")

# ---------------------------------------------------------
# NEW SECTION: DRILL-DOWN TAHAPAN PER ASESOR / BULAN / TAHUN
# Requirement no. 3: "berapa jumlahnya, siapa saja asesornya, bulan berapa saja
# dan tahun berapa saja" untuk tiap tahap (ASESMEN, PENGAJUAN BLANKO,
# TERBIT BLANKO, DELIVERY BLANKO)
# ---------------------------------------------------------
st.subheader("Detail Tahapan: Siapa, Kapan, dan Statusnya")

col_pilih_tahap, col_pilih_status = st.columns(2)
with col_pilih_tahap:
    tahap_pilihan = st.selectbox(
        "Pilih Tahapan",
        options=['ASESMEN', 'PENGAJUAN BLANKO', 'TERBIT BLANKO', 'DELIVERY BLANKO']
    )
with col_pilih_status:
    status_pilihan = st.selectbox("Pilih Status", options=['DONE', 'NOT DONE', 'Semua'])

df_drilldown = df_filtered.copy()
if status_pilihan != 'Semua' and tahap_pilihan in df_drilldown.columns:
    df_drilldown = df_drilldown[df_drilldown[tahap_pilihan] == status_pilihan]

bulan_map = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'Mei', 6: 'Jun',
             7: 'Jul', 8: 'Ags', 9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Des'}

if not df_drilldown.empty:
    rekap_drilldown = df_drilldown.groupby(['ASESOR', 'TAHUN SERTIFIKASI', 'BULAN SERTIFIKASI'])['No'].count().reset_index()
    rekap_drilldown.columns = ['Asesor', 'Tahun', 'Bulan', 'Jumlah']
    rekap_drilldown['Bulan'] = rekap_drilldown['Bulan'].map(bulan_map).fillna(rekap_drilldown['Bulan'])
    rekap_drilldown = rekap_drilldown.sort_values(['Tahun', 'Jumlah'], ascending=[True, False])

    st.dataframe(rekap_drilldown, use_container_width=True, hide_index=True)
    st.caption(f"Total baris pada tahap **{tahap_pilihan}** dengan status **{status_pilihan}**: {len(df_drilldown):,}")
else:
    st.info("Tidak ada data untuk kombinasi tahap dan status ini.")

st.markdown("---")

# ---------------------------------------------------------
# GRAFIK 3: TARGET VS AKTUALISASI 2026
# ---------------------------------------------------------
st.subheader("Target vs Aktualisasi (Khusus Data 2026)")

df_2026 = df_filtered[df_filtered['TAHUN SERTIFIKASI'] == 2026]
target_per_bulan = df_2026.groupby('BULAN SERTIFIKASI')['No'].count().reindex(range(1, 13), fill_value=0)
aktual_per_bulan = df_2026[df_2026['ASESMEN'] == 'DONE'].groupby('BULAN SERTIFIKASI')['No'].count().reindex(range(1, 13), fill_value=0)
bulan_label = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Ags', 'Sep', 'Okt', 'Nov', 'Des']

fig_target_aktual = go.Figure()
fig_target_aktual.add_trace(go.Bar(x=bulan_label, y=aktual_per_bulan.values, name='Aktualisasi (DONE)', marker_color='#2ecc71'))
fig_target_aktual.add_trace(go.Scatter(x=bulan_label, y=target_per_bulan.values, name='Target Keseluruhan', mode='lines+markers', line=dict(color='orange', width=3, dash='solid')))

fig_target_aktual.update_layout(xaxis_title="Bulan", yaxis_title="Jumlah Asesi", barmode='group', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig_target_aktual, use_container_width=True)
st.write("    ")

st.markdown("---")

# ---------------------------------------------------------
# GRAFIK 4 & 5: STATUS TARGET & TREN TAHUNAN
# ---------------------------------------------------------
col_pie, col_line = st.columns(2)

with col_pie:
    st.subheader("Status Asesmen Keseluruhan")
    status_counts = df_filtered['ASESMEN'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Jumlah']

    if not status_counts.empty:
        warna_status = {'DONE': '#2ecc71', 'NOT DONE': '#e74c3c'}
        fig_status = px.pie(status_counts, names='Status', values='Jumlah', hole=0.4, color='Status', color_discrete_map=warna_status)
        st.plotly_chart(fig_status, use_container_width=True)
        st.write("    ")
    else:
        st.info("Data status tidak tersedia.")
        st.write("    ")

with col_line:
    st.subheader("Tren Sertifikasi Tahunan")
    df_done = df_filtered[df_filtered['ASESMEN'] == 'DONE']
    tren_tahunan = df_done.groupby('TAHUN SERTIFIKASI')['No'].count().reset_index()
    tren_tahunan.columns = ['Tahun', 'Jumlah Asesi (Selesai)']

    if not tren_tahunan.empty:
        fig_tren = px.line(tren_tahunan, x='Tahun', y='Jumlah Asesi (Selesai)', markers=True, line_shape='spline')
        fig_tren.update_layout(xaxis=dict(tickmode='linear', dtick=1))
        st.plotly_chart(fig_tren, use_container_width=True)
        st.write("    ")
    else:
        st.info("Data tren tidak tersedia.")
        st.write("    ")

st.markdown("---")

# ---------------------------------------------------------
# GRAFIK 6 & 7: TOP PT & TOP ASESOR
# ---------------------------------------------------------
col_pt, col_asesor = st.columns(2)
df_done = df_filtered[df_filtered['ASESMEN'] == 'DONE']

with col_pt:
    st.subheader(f"Top {top_n} PT Penyumbang Asesi")
    pt_counts = df_done['PT'].value_counts().reset_index()
    pt_counts.columns = ['Nama PT', 'Jumlah Asesi']

    if not pt_counts.empty:
        if len(pt_counts) > top_n:
            top_pt_df = pt_counts.iloc[:top_n]
            others_pt = pd.DataFrame({'Nama PT': ['Lainnya'], 'Jumlah Asesi': [pt_counts['Jumlah Asesi'].iloc[top_n:].sum()]})
            final_pt = pd.concat([top_pt_df, others_pt])
        else:
            final_pt = pt_counts

        fig_pt = px.bar(final_pt, x='Nama PT', y='Jumlah Asesi', text='Jumlah Asesi', color='Jumlah Asesi', color_continuous_scale='Teal')
        fig_pt.update_layout(showlegend=False)
        st.plotly_chart(fig_pt, use_container_width=True)
        st.write("    ")
    else:
        st.info("Data PT tidak tersedia.")
        st.write("    ")

with col_asesor:
    st.subheader(f"Top {top_n} Asesor (Berdasarkan Tahun)")
    if not df_done.empty:
        top_asesor_rank = df_done['ASESOR'].value_counts().head(top_n).index.tolist()
        df_top_asesor = df_done[df_done['ASESOR'].isin(top_asesor_rank)]

        asesor_yearly = df_top_asesor.groupby(['ASESOR', 'TAHUN SERTIFIKASI'])['No'].count().reset_index()
        asesor_yearly.columns = ['Nama Asesor', 'Tahun', 'Jumlah Asesi']
        asesor_yearly['Tahun'] = asesor_yearly['Tahun'].astype(str)

        fig_asesor = px.bar(
            asesor_yearly, x='Nama Asesor', y='Jumlah Asesi', color='Tahun', text='Jumlah Asesi',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_asesor.update_layout(barmode='stack', xaxis_title=None, legend_title_text='Tahun', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_asesor, use_container_width=True)
        st.write("    ")
    else:
        st.info("Data Asesor tidak tersedia.")
        st.write("    ")

st.markdown("---")

# ---------------------------------------------------------
# GRAFIK 8: CAPAIAN REGION (asesi)
# ---------------------------------------------------------
st.subheader("Capaian Asesi per Region")
region_count = df_done['Region'].value_counts().reset_index()
region_count.columns = ['Region', 'Jumlah Asesi']

if not region_count.empty:
    fig_region = px.bar(
        region_count.sort_values('Jumlah Asesi', ascending=True),
        x='Jumlah Asesi', y='Region', orientation='h', text='Jumlah Asesi',
        color='Jumlah Asesi', color_continuous_scale='Blues'
    )
    fig_region.update_layout(showlegend=False)
    st.plotly_chart(fig_region, use_container_width=True)
    st.write("    ")
else:
    st.info("Data Region tidak tersedia.")
    st.write("    ")

st.markdown("---")

# ---------------------------------------------------------
# TABEL MASTER: BIODATA ASESOR
# ---------------------------------------------------------
st.subheader("Data Master & Biodata Asesor")
# NIK tidak ditampilkan di dashboard (data sensitif), meski tetap ada di file Excel sumber.
kolom_sensitif = [kolom for kolom in df_asesor.columns if 'NIK' in kolom.upper()]
df_asesor_tampil = df_asesor.drop(columns=kolom_sensitif, errors='ignore')
st.dataframe(df_asesor_tampil, use_container_width=True, hide_index=True)
st.write("    ")