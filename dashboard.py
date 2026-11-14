import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

sns.set_theme(style="whitegrid")

SOROT = "#FF6B35"  
LAIN = "#4CC9F0"  
GARIS = "#222222"   
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#Pengelompokan negara bagian Brasil ke 5 wilayah
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
    return result

@st.cache_data
def load_data():
    data = pd.read_csv(os.path.join(BASE_DIR, "main_data.csv"),
                       parse_dates=["order_purchase_timestamp"])
    return data.sort_values("order_purchase_timestamp").reset_index(drop=True)


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

#Pertanyaan 1
st.subheader("Seberapa besar keterlambatan menurunkan review score?")
review_df = get_review_by_status(main_df)

fig, ax = plt.subplots(figsize=(8, 5))
sns.barplot(x="status_kirim", y="review_score", data=review_df, hue="status_kirim",
            palette={"Terlambat": SOROT, "Tepat waktu": LAIN}, legend=False, ax=ax)
for bar in ax.containers:
    ax.bar_label(bar, fmt="%.2f", fontsize=12)
ax.set_title("Rata-rata Review Score", fontsize=16)
ax.set_xlabel(None)
ax.set_ylabel(None)
ax.set_ylim(0, 5)
st.pyplot(fig)

if len(review_df) == 2:
    nilai = review_df.set_index("status_kirim").review_score
    st.write(f"Pesanan terlambat mendapat review rata-rata **{nilai['Tepat waktu'] - nilai['Terlambat']:.2f} poin** "
             f"lebih rendah dibanding pesanan yang tepat waktu.")


#Pertanyaan 2
st.subheader("Negara bagian dengan pesanan terlambat tertinggi")
batas_minimal = st.slider("Minimal jumlah pesanan per negara bagian", 0, 1000, 100, step=50,
                          help="Negara bagian dengan pesanan sedikit membuat persentase kurang stabil.")
state_df = get_late_by_state(main_df, batas_minimal)

if state_df.empty:
    st.warning("Tidak ada negara bagian yang memenuhi batas minimal pesanan.")
else:
    n_top = min(5, len(state_df))
    warna = {s: (SOROT if i < n_top else LAIN) for i, s in enumerate(state_df.customer_state)}

    fig, ax = plt.subplots(figsize=(10, max(4, len(state_df) * 0.35)))
    sns.barplot(x="persen_terlambat", y="customer_state", data=state_df, hue="customer_state",
                palette=warna, legend=False, ax=ax)
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

#Perbandingan wilayah
st.subheader("Perbandingan keterlambatan antar wilayah")
region_df = get_late_by_region(main_df)

fig, ax = plt.subplots(figsize=(10, 5))
warna_region = {w: (SOROT if i == 0 else LAIN) for i, w in enumerate(region_df.wilayah)}
sns.barplot(x="wilayah", y="persen_terlambat", data=region_df, hue="wilayah",
            palette=warna_region, legend=False, ax=ax)
for bar in ax.containers:
    ax.bar_label(bar, fmt="%.2f%%", fontsize=11)
ax.set_title("Persentase Pesanan Terlambat per Wilayah", fontsize=16)
ax.set_xlabel(None)
ax.set_ylabel(None)
st.pyplot(fig)

#Pertanyaan 3
st.subheader("Tren jumlah pesanan per bulan")
bulanan_df = get_monthly_orders(main_df)

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(bulanan_df.bulan, bulanan_df.jumlah_pesanan, marker="o", linewidth=2.5, color=LAIN)
puncak = bulanan_df.loc[bulanan_df.jumlah_pesanan.idxmax()]
ax.scatter(puncak.bulan, puncak.jumlah_pesanan, color=SOROT, s=120, zorder=3)
ax.annotate(f"Puncak: {int(puncak.jumlah_pesanan):,}", (puncak.bulan, puncak.jumlah_pesanan),
            textcoords="offset points", xytext=(-70, -5), color=SOROT, fontweight="bold")
ax.set_title("Jumlah Pesanan per Bulan", fontsize=16)
ax.set_xlabel(None)
ax.set_ylabel(None)
plt.xticks(rotation=45)
st.pyplot(fig)

st.write(f"Bulan paling ramai: **{puncak.bulan}** dengan **{int(puncak.jumlah_pesanan):,}** pesanan.")
