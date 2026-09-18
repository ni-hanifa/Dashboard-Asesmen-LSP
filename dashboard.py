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
    # Menggunakan nama file soal yang baru
    file_path = "New Monitoring Asesmen Pemanen LSP 2026 (1).xlsx"
    
    # Membaca struktur sheet yang baru
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

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Total Asesi (Selesai)", value=f"{len(df_filtered[df_filtered['ASESMEN'] == 'DONE']):,}")
with col2:
    st.metric(label="Total Target Asesi", value=f"{len(df_filtered):,}")
with col3:
    st.metric(label="Total PT Terlibat", value=f"{df_filtered['PT'].nunique():,}")
with col4:
    st.metric(label="Total Asesor Aktif", value=f"{df_filtered['ASESOR'].nunique():,}")

st.write("    ")
st.markdown("---")

# ---------------------------------------------------------
# GRAFIK 1 & 2: TAHAPAN BLANKO & TUNGGAKAN
# ---------------------------------------------------------
col_funnel, col_tunggakan = st.columns(2)

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

with col_tunggakan:
    st.subheader("Monitoring Target Belum Selesai (NOT DONE)")
    df_not_done = df_filtered[df_filtered['ASESMEN'] == 'NOT DONE']
    tunggakan_asesor = df_not_done['ASESOR'].value_counts().reset_index()
    tunggakan_asesor.columns = ['Nama Asesor', 'Jumlah Target Tertunda']
    
    if not tunggakan_asesor.empty:
        fig_tunggakan = px.bar(
            tunggakan_asesor.head(top_n), x='Jumlah Target Tertunda', y='Nama Asesor', 
            orientation='h', text='Jumlah Target Tertunda', color_discrete_sequence=['#e74c3c'] 
        )
        fig_tunggakan.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_tunggakan, use_container_width=True)
        st.write("    ")
    else:
        st.success("Semua target selesai! (Tidak ada status NOT DONE)")
        st.write("    ")

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
# GRAFIK 8: CAPAIAN REGION
# ---------------------------------------------------------
st.subheader("Capaian per Region")
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
st.dataframe(df_asesor, use_container_width=True, hide_index=True)
st.write("    ")