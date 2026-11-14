import os
import json
import urllib.request
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

sns.set_theme(style="whitegrid")

WARNA = "#4CC9F0"     
SOROT = "#FF6B35"     
GARIS = "#222222"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GEOJSON_URL = ("https://raw.githubusercontent.com/codeforamerica/click_that_hood/"
               "master/public/data/brazil-states.geojson")

# Pengelompokan negara bagian Brasil ke 5 wilayah
REGION_MAP = {
    "AC": "Utara", "AM": "Utara", "AP": "Utara", "PA": "Utara", "RO": "Utara", "RR": "Utara", "TO": "Utara",
    "AL": "Timur Laut", "BA": "Timur Laut", "CE": "Timur Laut", "MA": "Timur Laut", "PB": "Timur Laut",
    "PE": "Timur Laut", "PI": "Timur Laut", "RN": "Timur Laut", "SE": "Timur Laut",
    "DF": "Tengah-Barat", "GO": "Tengah-Barat", "MT": "Tengah-Barat", "MS": "Tengah-Barat",
    "ES": "Tenggara", "MG": "Tenggara", "RJ": "Tenggara", "SP": "Tenggara",
    "PR": "Selatan", "RS": "Selatan", "SC": "Selatan",
}


def get_review_by_status(df):
    result = (df.dropna(subset=["review_score"])
                .groupby("status_kirim", as_index=False)
                .review_score.mean()
                .round(2))
    return result.sort_values("review_score")


def get_review_distribution(df):
    dist = pd.crosstab(df.status_kirim, df.review_score, normalize="index") * 100
    dist = dist.round(1).reset_index().melt(id_vars="status_kirim", var_name="review_score",
                                            value_name="persen")
    dist["review_score"] = dist.review_score.astype(int)
    return dist


def get_late_by_state(df, min_orders):
    result = df.groupby("customer_state").agg(
        total_pesanan=("order_id", "nunique"),
        pesanan_terlambat=("is_late", "sum")
    )
    result = result[result.total_pesanan >= min_orders]
    result["persen_terlambat"] = (result.pesanan_terlambat / result.total_pesanan * 100).round(2)
    return result.sort_values("persen_terlambat", ascending=False).reset_index()


def get_late_by_region(df):
    temp = df.assign(wilayah=df.customer_state.map(REGION_MAP))
    result = temp.groupby("wilayah").agg(
        total_pesanan=("order_id", "nunique"),
        persen_terlambat=("is_late", lambda x: round(x.mean() * 100, 2))
    )
    return result.sort_values("persen_terlambat", ascending=False).reset_index()


def get_monthly_orders(df):
    bulan = df.order_purchase_timestamp.dt.to_period("M").astype(str)
    result = df.groupby(bulan).order_id.nunique().reset_index()
    result.columns = ["bulan", "jumlah_pesanan"]
    result["perubahan"] = result.jumlah_pesanan.diff()
    result["pertumbuhan_persen"] = (result.jumlah_pesanan.pct_change() * 100).round(1)
    return result


@st.cache_data
def load_data():
    data = pd.read_csv(os.path.join(BASE_DIR, "main_data.csv"),
                       parse_dates=["order_purchase_timestamp"])
    return data.sort_values("order_purchase_timestamp").reset_index(drop=True)


@st.cache_data
def load_geojson():
    try:
        with urllib.request.urlopen(GEOJSON_URL, timeout=20) as response:
            return json.load(response)
    except Exception:
        return None


def draw_choropleth(geojson, values_by_state, title):
    patches, values, labels = [], [], []
    for feature in geojson["features"]:
        sigla = feature["properties"]["sigla"]
        geom = feature["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        biggest = max(polys, key=lambda p: len(p[0]))
        for poly in polys:
            patches.append(Polygon(np.array(poly[0]), closed=True))
            values.append(values_by_state.get(sigla, np.nan))
        ring = np.array(biggest[0])
        labels.append((sigla, ring[:, 0].mean(), ring[:, 1].mean()))

    cmap = plt.get_cmap("YlOrRd").copy()
    cmap.set_bad("#EEEEEE")
    fig, ax = plt.subplots(figsize=(8, 8))
    collection = PatchCollection(patches, cmap=cmap, edgecolor="white", linewidth=0.6)
    collection.set_array(np.ma.masked_invalid(values))
    ax.add_collection(collection)
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.axis("off")
    for sigla, x, y in labels:
        nilai = values_by_state.get(sigla, np.nan)
        warna_teks = "white" if (not np.isnan(nilai) and nilai > 15) else "black"
        ax.annotate(sigla, (x, y), ha="center", va="center", fontsize=8, color=warna_teks)
    fig.colorbar(collection, ax=ax, shrink=0.6, label="% pesanan terlambat")
    ax.set_title(title, fontsize=14)
    return fig


all_df = load_data()

tanggal_awal = all_df.order_purchase_timestamp.min().date()
tanggal_akhir = all_df.order_purchase_timestamp.max().date()
daftar_state = sorted(all_df.customer_state.unique())

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] { background-color: #E3F2FD; }
    [data-testid="stSidebar"] { background-color: #BBDEFB; }
    [data-testid="stHeader"] { background: rgba(0, 0, 0, 0); }

    h1, h2, h3, h4, p, li, label,
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"],
    [data-testid="stCaptionContainer"] { color: #1A2B3C !important; }
    </style>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.title("Filter Data")
    rentang = st.date_input("Rentang waktu pesanan", value=(tanggal_awal, tanggal_akhir),
                            min_value=tanggal_awal, max_value=tanggal_akhir)
    pilihan_state = st.multiselect("Negara bagian", daftar_state, default=daftar_state)
    st.caption("Data: pesanan berstatus delivered, Januari 2017 - Agustus 2018.")

if not isinstance(rentang, tuple) or len(rentang) != 2:
    st.info("Pilih tanggal awal dan tanggal akhir di sidebar.")
    st.stop()

main_df = all_df[(all_df.order_purchase_timestamp.dt.date >= rentang[0]) &
                 (all_df.order_purchase_timestamp.dt.date <= rentang[1]) &
                 (all_df.customer_state.isin(pilihan_state))]

if main_df.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

st.header("Dashboard Pengiriman & Kepuasan Pelanggan")
st.caption("Brazilian E-Commerce (Olist)")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Pesanan", f"{main_df.order_id.nunique():,}")
m2.metric("Pesanan Terlambat", f"{main_df.is_late.mean() * 100:.2f}%")
m3.metric("Rata-rata Review", f"{main_df.review_score.mean():.2f}")
m4.metric("Jumlah Negara Bagian", main_df.customer_state.nunique())

# Pertanyaan 1 
st.subheader("Keterlambatan pengiriman dan review score")
review_df = get_review_by_status(main_df)

fig, ax = plt.subplots(figsize=(8, 5))
sns.barplot(x="status_kirim", y="review_score", data=review_df, color=WARNA, ax=ax)
for bar in ax.containers:
    ax.bar_label(bar, fmt="%.2f", fontsize=12)
ax.set_title("Rata-rata Review Score", fontsize=16)
ax.set_xlabel(None)
ax.set_ylabel(None)
ax.set_ylim(0, 5)
st.pyplot(fig)

if len(review_df) == 2:
    nilai = review_df.set_index("status_kirim").review_score
    st.write(f"Pesanan terlambat memiliki rata-rata review **{nilai['Tepat waktu'] - nilai['Terlambat']:.2f} poin** "
             f"lebih rendah dibanding pesanan yang tepat waktu. Ini menunjukkan adanya hubungan antara "
             f"keterlambatan dan rendahnya penilaian, bukan bukti sebab-akibat.")

dist_df = get_review_distribution(main_df.dropna(subset=["review_score"]))
fig, ax = plt.subplots(figsize=(9, 5))
sns.barplot(x="review_score", y="persen", hue="status_kirim", data=dist_df,
            palette={"Tepat waktu": "#B0BEC5", "Terlambat": WARNA}, ax=ax)
ax.set_title("Distribusi Review Score berdasarkan Status Pengiriman", fontsize=16)
ax.set_xlabel("Review score")
ax.set_ylabel("% pesanan dalam kelompok")
ax.legend(title=None)
st.pyplot(fig)

# Pertanyaan 2 
st.subheader("Negara bagian dengan pesanan terlambat tertinggi")
batas_minimal = st.slider("Minimal jumlah pesanan per negara bagian", 0, 1000, 100, step=50,
                          help="Negara bagian dengan pesanan sedikit membuat persentase kurang stabil.")
state_df = get_late_by_state(main_df, batas_minimal)

if state_df.empty:
    st.warning("Tidak ada negara bagian yang memenuhi batas minimal pesanan.")
else:
    fig, ax = plt.subplots(figsize=(10, max(4, len(state_df) * 0.35)))
    sns.barplot(x="persen_terlambat", y="customer_state", data=state_df, color=WARNA, ax=ax)
    ax.axvline(main_df.is_late.mean() * 100, color=GARIS, linestyle="--", label="Rata-rata keseluruhan")
    ax.set_title("Persentase Pesanan Terlambat per Negara Bagian", fontsize=16)
    ax.set_xlabel("% pesanan terlambat")
    ax.set_ylabel(None)
    ax.legend()
    st.pyplot(fig)

    teratas = state_df.iloc[0]
    st.write(f"Tertinggi: **{teratas.customer_state}** dengan {teratas.persen_terlambat:.2f}% "
             f"dari {int(teratas.total_pesanan):,} pesanan.")
    with st.expander("Lihat tabel data"):
        st.dataframe(state_df, hide_index=True)

# Peta choropleth
peta_df = get_late_by_state(main_df, 0)
geojson = load_geojson()
if geojson is None:
    st.info("Peta tidak dapat dimuat (butuh koneksi internet untuk mengunduh batas wilayah).")
else:
    fig = draw_choropleth(geojson, dict(zip(peta_df.customer_state, peta_df.persen_terlambat)),
                          "Peta Persentase Pesanan Terlambat per Negara Bagian")
    st.pyplot(fig)

st.subheader("Perbandingan keterlambatan antar wilayah")
region_df = get_late_by_region(main_df)

fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(x="wilayah", y="persen_terlambat", data=region_df, color=WARNA, ax=ax)
for bar in ax.containers:
    ax.bar_label(bar, fmt="%.2f%%", fontsize=11)
ax.set_title("Persentase Pesanan Terlambat per Wilayah", fontsize=16)
ax.set_xlabel(None)
ax.set_ylabel(None)
st.pyplot(fig)

# Pertanyaan 3 
st.subheader("Tren jumlah pesanan per bulan (2017)")
st.caption("Bagian ini selalu memakai periode Januari - Desember 2017 sesuai pertanyaan bisnis, "
           "dan hanya mengikuti filter negara bagian.")
data_2017 = all_df[(all_df.order_purchase_timestamp.dt.year == 2017) &
                   (all_df.customer_state.isin(pilihan_state))]
bulanan_df = get_monthly_orders(data_2017)

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(bulanan_df.bulan, bulanan_df.jumlah_pesanan, marker="o", linewidth=2.5, color=WARNA)
for _, row in bulanan_df.iterrows():
    ax.annotate(f"{int(row.jumlah_pesanan):,}", (row.bulan, row.jumlah_pesanan),
                textcoords="offset points", xytext=(0, 9), ha="center", fontsize=9)
puncak = bulanan_df.loc[bulanan_df.jumlah_pesanan.idxmax()]
ax.scatter(puncak.bulan, puncak.jumlah_pesanan, color=SOROT, s=120, zorder=3)
ax.set_title("Jumlah Pesanan per Bulan, 2017", fontsize=16)
ax.set_xlabel(None)
ax.set_ylabel(None)
plt.xticks(rotation=45)
st.pyplot(fig)

if len(bulanan_df) > 1:
    tumbuh = bulanan_df.loc[bulanan_df.pertumbuhan_persen.idxmax()]
    turun = bulanan_df.loc[bulanan_df.pertumbuhan_persen.idxmin()]
    st.write(f"- Bulan paling ramai: **{puncak.bulan}** dengan **{int(puncak.jumlah_pesanan):,}** pesanan.")
    st.write(f"- Pertumbuhan terbesar: **{tumbuh.bulan}** ({tumbuh.pertumbuhan_persen:+.1f}% dari bulan sebelumnya).")
    st.write(f"- Penurunan terbesar: **{turun.bulan}** ({turun.pertumbuhan_persen:+.1f}% dari bulan sebelumnya).")

with st.expander("Lihat tabel perubahan bulanan"):
    st.dataframe(bulanan_df, hide_index=True)