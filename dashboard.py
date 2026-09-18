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
# [BARU] NORMALISASI NAMA PT
# Kolom "PT" di DATA ASESMEN berisi kode internal (PT. GBSM, PT. BBB-K, dst),
# sementara kolom "ASAL PT" di sheet yang sama sudah berisi nama panjang resmi
# dan terisi lengkap (0 baris kosong, dicek langsung dari data). Mapping di
# bawah diambil dari pasangan kode<->ASAL PT itu, bukan tebakan.
#
# Dipakai untuk menyeragamkan 3 sumber yang formatnya berbeda:
#   - DATA ASESMEN                -> kode ber-prefix ("PT. GBSM")
#   - Monitoring asesmen asesor   -> kode tanpa prefix ("GBSM", "DLJ2")
#   - DATA ASESOR                 -> nama panjang title case ("PT. Gawi Bahandep Sawit Mekar")
# Setelah dinormalkan, filter sidebar dan semua grafik memakai label yang sama.
# ==========================================
NAMA_PT_LENGKAP = {
    'AAPA':   'PT. ANUGERAH AGUNG PRIMA ABADI',
    'BBB-K':  'PT. SAWIT BRAHMA',
    'BBB-S':  'PT. BRAHMA BINABAKTI SEKERNAN',
    'BBB':    'PT. BRAHMA BINABAKTI SEKERNAN',
    'DLJ 1':  'PT. DWIWIRA LESTARI JAYA 1',
    'DLJ1':   'PT. DWIWIRA LESTARI JAYA 1',
    'DLJ 2':  'PT. DWIWIRA LESTARI JAYA 2',
    'DLJ2':   'PT. DWIWIRA LESTARI JAYA 2',
    'EBL':    'PT. ETAM BERSAMA LESTARI',
    'FLTI':   'PT. FIRST LAMANDAU TIMBER INTERNATIONAL',
    'GBSM':   'PT. GAWI BAHANDEP SAWIT MEKAR',
    'HPM':    'PT. HAMPARAN PERKASA MANDIRI',
    'MIK':    'PT. MEGA IKA KHANSA',
    'NPN':    'PT. NATURA PASIFIC NUSANTARA',
    'SAWA':   'PT. SUBUR ABADI WANA AGUNG',
    'SKM':    'PT. SUKSES KARYA MANDIRI',
    'SLE':    'PT. MUARATOYU SUBUR LESTARI',
    'TAN':    'PT. TRIEKA AGRO NUSANTARA',
    'YWA':    'PT. YUDHA WAHANA ABADI',
    'HO':     'HEAD OFFICE (HO)',
}

# Perbaikan salah tulis nama panjang yang ada di kolom ASAL PT / DATA ASESOR,
# supaya satu PT tidak terpecah jadi dua entri berbeda di filter.
KOREKSI_NAMA_PANJANG = {
    'PT. FIRST TIMBER LAMANDAU INTERNASIONAL': 'PT. FIRST LAMANDAU TIMBER INTERNATIONAL',
    'PT. HAMPARAN MANDIRI PERKASA':            'PT. HAMPARAN PERKASA MANDIRI',
    'PT. BRAHMA BINABAKTI':                    'PT. BRAHMA BINABAKTI SEKERNAN',
    'PT. DWIWIRA LESTARI JAYA':                'PT. DWIWIRA LESTARI JAYA 1',
}

def normalisasi_nama_pt(nilai):
    """Ubah kode PT / nama panjang apa pun menjadi satu nama panjang baku (huruf kapital)."""
    if pd.isna(nilai):
        return nilai
    teks = ' '.join(str(nilai).split()).strip().upper()   # rapikan spasi ganda ("DLJ  2")
    kunci = teks[3:].strip() if teks.startswith('PT.') else (teks[2:].strip() if teks.startswith('PT ') else teks)
    if kunci in NAMA_PT_LENGKAP:
        return NAMA_PT_LENGKAP[kunci]
    if teks in NAMA_PT_LENGKAP:
        return NAMA_PT_LENGKAP[teks]
    return KOREKSI_NAMA_PANJANG.get(teks, teks)

# ==========================================
# [BARU] NORMALISASI NAMA ASESOR
# Nama yang sama ditulis beda-beda di 3 sheet: kadang disingkat pakai inisial
# ("HERWAN THEO L."), kadang lengkap ("HERWAN THEO LOLOPAYUNG"), kadang beda
# tanda titik/spasi ("Wedly AP Sitanggang" vs "WEDLY AP. SITANGGANG" vs
# "Wedly A. P. Sitanggang"). Kalau tidak diseragamkan, satu orang bisa
# terhitung sebagai 2 asesor berbeda di grafik/filter.
#
# Bentuk lengkap yang dipakai sebagai acuan = ejaan di sheet DATA ASESOR
# (data master biodata asesor), karena itu satu-satunya sheet yang punya
# nama lengkap resmi untuk orang-orang ini. Variasi tersingkat diambil
# langsung dari isi DATA ASESMEN & Monitoring asesmen asesor (dicek manual,
# bukan tebakan) lalu dipetakan ke bentuk lengkap tsb.
# ==========================================
NAMA_ASESOR_LENGKAP = {
    'ERIKSON H. SARAGIH':        'Erikson Hasiholan Saragih',
    'ERIKSON H SARAGIH':         'Erikson Hasiholan Saragih',
    'ERIKSON HASIHOLAN SARAGIH': 'Erikson Hasiholan Saragih',
    'HERWAN THEO L.':            'Herwan Theo Lolopayung',
    'HERWAN THEO L':             'Herwan Theo Lolopayung',
    'HERWAN THEO LOLOPAYUNG':    'Herwan Theo Lolopayung',
    'RIKARDUS S. MARINO':        'Rikardus Severinus Marino',
    'RIKARDUS S MARINO':         'Rikardus Severinus Marino',
    'RIKARDUS SEVERINUS MARINO': 'Rikardus Severinus Marino',
    'SAIPUL R. SARAGIH':         'Saipul Ramadhan Saragih',
    'SAIPUL R SARAGIH':          'Saipul Ramadhan Saragih',
    'SAIPUL RAMADHAN SARAGIH':   'Saipul Ramadhan Saragih',
    'WEDLY AP. SITANGGANG':      'Wedly A. P. Sitanggang',
    'WEDLY AP SITANGGANG':       'Wedly A. P. Sitanggang',
    'WEDLY A. P. SITANGGANG':    'Wedly A. P. Sitanggang',
    'WEDLY A P SITANGGANG':      'Wedly A. P. Sitanggang',
}

def normalisasi_nama_asesor(nilai):
    """Seragamkan variasi penulisan nama asesor (singkatan/tanda baca) ke satu nama lengkap baku."""
    if pd.isna(nilai):
        return nilai
    teks = ' '.join(str(nilai).split()).strip()
    kunci = teks.upper()
    if kunci in NAMA_ASESOR_LENGKAP:
        return NAMA_ASESOR_LENGKAP[kunci]
    return teks.title()  # nama lain yang sudah konsisten -> disamakan formatnya (Title Case)

# ==========================================
# 2. LOAD & CLEAN DATA EXCEL BARU
# ==========================================
@st.cache_data
def load_data():
    file_path = "New Monitoring Asesmen Pemanen LSP 2026 (1).xlsx"

    df_asesmen = pd.read_excel(file_path, sheet_name='DATA ASESMEN')
    df_asesor = pd.read_excel(file_path, sheet_name='DATA ASESOR')

    # [DIPERBARUI] Normalisasi nama asesor: dulu hanya 4 pasang di-hardcode
    # untuk DATA ASESMEN saja (via dict koreksi_nama), sekarang dipakai satu
    # fungsi yang sama untuk DATA ASESMEN, DATA ASESOR, dan sheet target,
    # supaya nama yang sama tidak lagi tampil ganda antar sheet.
    df_asesmen['ASESOR'] = df_asesmen['ASESOR'].apply(normalisasi_nama_asesor)
    df_asesor['Nama Lengkap'] = df_asesor['Nama Lengkap'].apply(normalisasi_nama_asesor)

    # [BARU] Kolom PT tidak lagi berisi singkatan, tapi nama panjang resmi.
    df_asesmen['PT'] = df_asesmen['PT'].apply(normalisasi_nama_pt)
    df_asesmen['ASAL PT'] = df_asesmen['ASAL PT'].apply(normalisasi_nama_pt)
    df_asesor['Instansi Tempat Bekerja'] = df_asesor['Instansi Tempat Bekerja'].apply(normalisasi_nama_pt)

    # ------------------------------------------------------------------
    # [POIN B] Parser untuk sheet "Monitoring asesmen asesor" (target resmi).
    # Sheet ini punya header bertingkat (baris NAMA/PT/BULAN, lalu TGT/ACT
    # per bulan), jadi dibaca tanpa header (header=None) lalu di-reshape:
    #   - kolom 1  = NAMA, kolom 2 = PT
    #   - kolom 3..26  = 12 bulan (JAN..DES), tiap bulan 2 kolom (TGT, ACT)
    #   - kolom 27..30 = TOTAL TGT, TOTAL ACT, GAP, % ACH
    #   - baris data dimulai dari baris ke-6 (index 5), dan ada baris
    #     ringkasan "TOTAL" di akhir yang harus dibuang supaya tidak ikut
    #     dihitung sebagai satu asesor.
    # ------------------------------------------------------------------
    df_target_raw = pd.read_excel(file_path, sheet_name='Monitoring asesmen asesor', header=None)
    data_rows = df_target_raw.iloc[5:].reset_index(drop=True)
    data_rows = data_rows[data_rows[1].notna()]
    data_rows = data_rows[data_rows[1].astype(str).str.strip().str.upper() != 'TOTAL']

    # [BARU] Nama & PT di sheet target ikut dinormalkan supaya bisa disatukan
    # dengan DATA ASESMEN pada chart & filter.
    nama_target = data_rows[1].apply(normalisasi_nama_asesor)
    pt_target = data_rows[2].apply(normalisasi_nama_pt)

    # Rekap TOTAL TGT/ACT/GAP/%ACH per asesor (sumber untuk chart "Capaian Target per Asesor")
    df_target_asesor = pd.DataFrame({
        'ASESOR': nama_target,
        'PT': pt_target,
        'TOTAL_TGT': pd.to_numeric(data_rows[27], errors='coerce').fillna(0),
        'TOTAL_ACT': pd.to_numeric(data_rows[28], errors='coerce').fillna(0),
        'GAP': pd.to_numeric(data_rows[29], errors='coerce').fillna(0),
        'PCT_ACH': pd.to_numeric(data_rows[30], errors='coerce').fillna(0),
    }).reset_index(drop=True)

    # Rekap TGT/ACT per bulan (semua asesor) - sumber untuk chart "Target vs Aktualisasi"
    bulan_order = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']
    bulanan_records = []
    for i, bulan in enumerate(bulan_order):
        col_tgt = 3 + i * 2
        col_act = 4 + i * 2
        bulanan_records.append(pd.DataFrame({
            'ASESOR': nama_target,
            'PT': pt_target,
            'BULAN': bulan,
            'TGT': pd.to_numeric(data_rows[col_tgt], errors='coerce').fillna(0),
            'ACT': pd.to_numeric(data_rows[col_act], errors='coerce').fillna(0),
        }))
    df_target_bulanan = pd.concat(bulanan_records, ignore_index=True)

    return df_asesmen, df_asesor, df_target_asesor, df_target_bulanan

df_asesmen, df_asesor, df_target_asesor, df_target_bulanan = load_data()

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

# [BARU] Karena nama PT & Asesor sudah seragam lintas sheet, dua sumber target
# resmi ikut difilter oleh pilihan PT dan Asesor (Tahun/Region tetap tidak bisa,
# sheet target tidak punya kolom tersebut).
df_target_asesor_f = df_target_asesor.copy()
df_target_bulanan_f = df_target_bulanan.copy()
if pilihan_pt:
    df_target_asesor_f = df_target_asesor_f[df_target_asesor_f['PT'].isin(pilihan_pt)]
    df_target_bulanan_f = df_target_bulanan_f[df_target_bulanan_f['PT'].isin(pilihan_pt)]
if pilihan_asesor:
    df_target_asesor_f = df_target_asesor_f[df_target_asesor_f['ASESOR'].isin(pilihan_asesor)]
    df_target_bulanan_f = df_target_bulanan_f[df_target_bulanan_f['ASESOR'].isin(pilihan_asesor)]

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
    # Total asesor terdaftar (dari master data, bukan hanya yg muncul di data asesmen terfilter)
    st.metric(label="Total Asesor Terdaftar", value=f"{df_asesor['Nama Lengkap'].nunique():,}")

st.write("    ")
st.markdown("---")

# ---------------------------------------------------------
# SEBARAN ASESOR PER PT & PER REGION
# Requirement no. 2: "sebaran asesor per PT, sebaran asesor per Region"
# [DIPERBARUI]
#  - "per PT" tetap dari DATA ASESOR (satu-satunya sheet berisi biodata &
#    instansi asesor), sekarang pakai nama PT panjang yang sudah seragam.
#  - "per Region" SEBELUMNYA salah pakai kolom Provinsi (alamat domisili
#    asesor) sebagai pengganti Region, padahal Region (KALTENG 1, KALTENG 2,
#    KALTIM 1, KALTIM 2, SUMATERA) itu wilayah kerja/penugasan dan kolom itu
#    HANYA ada di DATA ASESMEN, bukan di DATA ASESOR. Sekarang diambil dari
#    pasangan (ASESOR, Region) pada DATA ASESMEN: dihitung asesor unik per
#    Region. Beberapa asesor bertugas di lebih dari satu Region, sehingga
#    mereka dihitung di setiap Region tempat mereka tercatat mengases
#    (bukan dipaksa satu Region saja, supaya tidak kehilangan data
#    penugasan yang sebenarnya).
# ---------------------------------------------------------
st.subheader("Sebaran Asesor")
col_sebaran_pt, col_sebaran_region = st.columns(2)

with col_sebaran_pt:
    st.markdown("**Jumlah Asesor per PT / Instansi** _(sumber: DATA ASESOR)_")
    sebaran_pt = df_asesor['Instansi Tempat Bekerja'].value_counts().reset_index()
    sebaran_pt.columns = ['Instansi Tempat Bekerja', 'Jumlah Asesor']

    if not sebaran_pt.empty:
        fig_sebaran_pt = px.bar(
            sebaran_pt.sort_values('Jumlah Asesor', ascending=True),
            x='Jumlah Asesor', y='Instansi Tempat Bekerja', orientation='h',
            text='Jumlah Asesor', color='Jumlah Asesor',
            color_continuous_scale=['#C9B8F5', '#5B21B6']  # ungu muda -> ungu tua (tidak mulai dari putih)
        )
        fig_sebaran_pt.update_layout(showlegend=False, yaxis_title=None)
        st.plotly_chart(fig_sebaran_pt, use_container_width=True)
    else:
        st.info("Data instansi asesor tidak tersedia.")

with col_sebaran_region:
    st.markdown("**Jumlah Asesor per Region** _(sumber: DATA ASESMEN)_")
    sebaran_region = df_asesmen[['ASESOR', 'Region']].dropna().drop_duplicates()
    sebaran_region = sebaran_region['Region'].value_counts().reset_index()
    sebaran_region.columns = ['Region', 'Jumlah Asesor']

    if not sebaran_region.empty:
        fig_sebaran_region = px.bar(
            sebaran_region.sort_values('Jumlah Asesor', ascending=True),
            x='Jumlah Asesor', y='Region', orientation='h',
            text='Jumlah Asesor', color='Jumlah Asesor', color_continuous_scale='Oranges'
        )
        fig_sebaran_region.update_layout(showlegend=False, yaxis_title=None)
        st.plotly_chart(fig_sebaran_region, use_container_width=True)
    else:
        st.info("Data Region asesor tidak tersedia.")

st.caption("Catatan: sebaran per Region dihitung dari pasangan Asesor-Region pada DATA ASESMEN (DATA ASESOR tidak memiliki kolom Region). Sejumlah asesor tercatat mengases di lebih dari satu Region, sehingga mereka dihitung di setiap Region tempat bertugas dan total lintas-Region bisa melebihi jumlah asesor unik.")

st.markdown("---")

# ---------------------------------------------------------
# GRAFIK 1 & 2: TAHAPAN BLANKO & CAPAIAN TARGET PER ASESOR
# [POIN B + C] Grafik "Capaian Target per Asesor" memakai TGT & ACT resmi
# dari sheet "Monitoring asesmen asesor".
# [BARU] Nama asesor & PT di sheet target sudah diseragamkan, sehingga chart
# ini kini MENGIKUTI filter PT & Asesor di sidebar (Tahun/Region tetap tidak
# berlaku karena sheet target tidak punya kolom tersebut).
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
    st.subheader("Capaian Target per Asesor (TGT vs ACT resmi)")

    capaian_asesor_top = df_target_asesor_f.sort_values('TOTAL_TGT', ascending=False).head(top_n)
    capaian_asesor_long = capaian_asesor_top.melt(
        id_vars=['ASESOR'], value_vars=['TOTAL_TGT', 'TOTAL_ACT'],
        var_name='Status', value_name='Jumlah'
    )
    capaian_asesor_long['Status'] = capaian_asesor_long['Status'].map({'TOTAL_TGT': 'TARGET', 'TOTAL_ACT': 'AKTUAL'})

    if not capaian_asesor_long.empty:
        fig_capaian_asesor = px.bar(
            capaian_asesor_long, x='Jumlah', y='ASESOR', color='Status',
            orientation='h', text='Jumlah', barmode='group',
            color_discrete_map={'TARGET': '#f39c12', 'AKTUAL': '#2ecc71'}
        )
        fig_capaian_asesor.update_layout(
            yaxis={'categoryorder': 'total ascending'}, yaxis_title=None,
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
    # [POIN A - FIX BUG] ['No'].count() -> .size(): .count() mengabaikan baris
    # dengan kolom "No" kosong (NaN), sehingga asesor dengan baris NOT DONE
    # tanpa nomor urut jadi tidak terhitung. .size() menghitung semua baris.
    rekap_drilldown = df_drilldown.groupby(['ASESOR', 'TAHUN SERTIFIKASI', 'BULAN SERTIFIKASI']).size().reset_index()
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
# [POIN B + C] TGT & ACT diambil dari sheet "Monitoring asesmen asesor"
# (target resmi, dijumlah semua asesor per bulan).
# ---------------------------------------------------------
st.subheader("Target vs Aktualisasi (Target Resmi per Bulan)")

bulan_order = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']
target_bulanan_agg = df_target_bulanan_f.groupby('BULAN')[['TGT', 'ACT']].sum().reindex(bulan_order, fill_value=0).fillna(0)
bulan_label = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Ags', 'Sep', 'Okt', 'Nov', 'Des']

fig_target_aktual = go.Figure()
fig_target_aktual.add_trace(go.Bar(x=bulan_label, y=target_bulanan_agg['ACT'].values, name='Aktualisasi (ACT)', marker_color='#2ecc71'))
fig_target_aktual.add_trace(go.Scatter(x=bulan_label, y=target_bulanan_agg['TGT'].values, name='Target Resmi (TGT)', mode='lines+markers', line=dict(color='orange', width=3, dash='solid')))

fig_target_aktual.update_layout(xaxis_title="Bulan", yaxis_title="Jumlah Asesi", barmode='group', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig_target_aktual, use_container_width=True)
st.caption("Sumber: sheet \"Monitoring asesmen asesor\" (kolom TGT/ACT resmi per asesor per bulan), dijumlahkan lintas asesor. Chart ini mengikuti filter PT & Asesor, tetapi belum bisa mengikuti filter Tahun/Region karena sheet target tidak memiliki kolom tersebut.")
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
    # [POIN A - FIX BUG] ['No'].count() -> .size()
    tren_tahunan = df_done.groupby('TAHUN SERTIFIKASI').size().reset_index()
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
# GRAFIK: TOP ASESOR
# [DIHAPUS] "Top PT Penyumbang Asesi" dihapus sesuai permintaan - Sheet1
# (Instruksi Kerja) hanya meminta sebaran asesor per PT/Region, capaian per
# PT/Region, dan tahapan blanko; tidak ada permintaan ranking PT berdasarkan
# jumlah asesi, jadi chart ini di luar cakupan dan dibuang (bukan diganti
# data lain).
# ---------------------------------------------------------
df_done = df_filtered[df_filtered['ASESMEN'] == 'DONE']

st.subheader(f"Top {top_n} Asesor (Berdasarkan Tahun)")
if not df_done.empty:
    top_asesor_rank = df_done['ASESOR'].value_counts().head(top_n).index.tolist()
    df_top_asesor = df_done[df_done['ASESOR'].isin(top_asesor_rank)]

    # [POIN A - FIX BUG] ['No'].count() -> .size()
    asesor_yearly = df_top_asesor.groupby(['ASESOR', 'TAHUN SERTIFIKASI']).size().reset_index()
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
# GRAFIK: CAPAIAN REGION (asesi)
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