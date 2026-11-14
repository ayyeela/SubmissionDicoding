# Proyek Analisis Data: Brazilian E-Commerce (Olist)

Proyek ini menganalisis data pesanan e-commerce Brasil (Olist) periode **Januari 2017 - Agustus 2018** untuk menjawab tiga pertanyaan bisnis tentang pengiriman dan kepuasan pelanggan:

1. Seberapa besar keterlambatan pengiriman menurunkan review score pelanggan?
2. Negara bagian mana yang persentase pesanan terlambatnya paling tinggi?
3. Bagaimana tren jumlah pesanan per bulan sepanjang tahun 2017 dan bulan apa yang paling ramai?

Analisis lanjutan yang digunakan: **geospatial analysis** dan **manual grouping** (pengelompokan negara bagian ke 5 wilayah Brasil)

## Struktur Direktori

```
submission
├── dashboard
│   ├── main_data.csv
│   └── dashboard.py
├── data
│   ├── orders_dataset.csv
│   ├── customers_dataset.csv
│   ├── order_reviews_dataset.csv
│   └── geolocation_dataset.csv
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

- `dashboard/` berisi `dashboard.py` dan `main_data.csv` (data hasil olahan dari notebook).
- `data/` berisi dataset asli yang dipakai di notebook.
- `notebook.ipynb` berisi seluruh proses analisis data.
- `url.txt` berisi tautan dashboard yang sudah di deploy.

## Setup Environment - Anaconda

```
conda create --name main-ds python=3.12
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal

```
git clone https://github.com/ayyeela/SubmissionDicoding.git
cd SubmissionDicoding
pipenv install
pipenv shell
pip install -r requirements.txt
```

## Run Streamlit App

```
cd dashboard
streamlit run dashboard.py
```

Dashboard akan terbuka otomatis di `http://localhost:8501`.

## Dashboard Online

Dashboard dapat dilihat di: **ISI_ALAMAT_DASHBOARD_ANDA**
