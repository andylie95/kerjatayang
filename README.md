# kerjatayang
Kerja Tayang merupakan platform simulasi situasi di dunia kerja untuk melatih softskill pengguna agar siap kerja melengkapi dengan hardskill yang telah dipelajari. 

## Konfigurasi Azure Language Service

Aplikasi membaca `AZURE_KEY` (wajib), `AZURE_ENDPOINT`, dan `AZURE_REGION` (opsional) dari Streamlit secrets, dengan fallback ke environment variable.

**Lokal**

1. Salin `.streamlit/secrets.toml.example` menjadi `.streamlit/secrets.toml` (file ini sudah ada di `.gitignore`).
2. Isi nilainya dengan key, endpoint, dan region dari resource Azure Language Service milikmu.
3. Jalankan `streamlit run app.py`.

Alternatif: set environment variable `AZURE_KEY`, `AZURE_ENDPOINT`, dan `AZURE_REGION` sebelum menjalankan aplikasi.

**Streamlit Cloud**

Buka **App settings → Secrets**, lalu tempel isi yang sama seperti `secrets.toml` (format TOML) dengan nilai aslimu.
