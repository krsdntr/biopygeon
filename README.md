# 🕊️ Biopygeon
**The Last Mile Publication Aggregator & Intelligent Bioinformatics Assistant**

Biopygeon adalah antarmuka baris perintah (CLI) inovatif yang mengintegrasikan instrumen bioinformatika (NCBI BLAST, ExPASy ProtParam, Enrichr, PDB) langsung dengan agen kecerdasan buatan (LLM - Groq). Alat ini dirancang untuk menjadi jembatan antara output mentah data biologis dan pembuatan visualisasi serta laporan berstandar jurnal Q1 (*Nature*, *Science*, *Elsevier*).

Berbeda dengan skrip statis konvensional, Biopygeon dibekali dengan **AI Router** yang secara dinamis dan otonom dapat memanggil hingga **18 alat cerdas (Tools)** berdasarkan percakapan (bahasa natural) dengan pengguna.

---

## 🚀 Fitur Utama

- 🤖 **Agen Asisten Cerdas Otonom (`biopygeon chat` & Web UI)**: AI secara dinamis merutekan obrolan Anda ke fungsi bioinformatika secara cerdas, dapat diakses via Terminal (CLI) maupun Antarmuka Web interaktif (UI).
- 🧠 **ReAct Autonomous Pipeline**: Fitur agen pintar (*Chaining*) yang mampu melakukan tugas ganda dan rumit tanpa henti secara mandiri melalui eksekusi kode dinamis.
- 🎨 **Antarmuka Grafis (Web UI)**: Memberikan pengalaman percakapan *chat* visual yang mulus dengan dukungan fitur *upload* berkas langsung (*drag & drop*), unduhan interaktif, *floating settings*, dan manajemen sesi.
- 🔬 **Katalog Lengkap Analisis Biologi**: Dari kalkulasi *ProtParam*, pencarian struktur 3D, *Multiple Sequence Alignment*, hingga desain primer kloning!
- 🧬 **AlphaFold & 3D Interactive Viewer**: Ekstraksi model prediksi AlphaFold v4 (Google DeepMind) secara asinkron dengan visualisasi WebGL Real-time tertanam di Streamlit UI tanpa perlu instalasi aplikasi desktop eksternal.
- 📊 **Visualisasi Q1 (Omics & Jaringan)**: Membuat *Bubble Plot*, merender jaringan interaktif (SSN), dan mengharmonisasi data CSV secara algoritmik.
- 📚 **Pencarian Literatur Tiga Mesin**: Akses simultan ke Semantic Scholar, OpenAlex, dan PubMed dengan manajemen API *Polite Pool* (bebas banned).
- 📑 **Penyusunan Metodologi & PDF Otomatis**: Menyusun narasi draf penelitian dan laporan eksekutif PDF secara instan dari hasil komputasi.
- 🛡️ **Smart Caching & Enterprise Security**: Sistem manajemen memori *cache* mandiri (`~/.biopygeon/cache`) yang cerdas dengan *auto-cleanup* (bebas pembengkakan memori) serta arsitektur *Auto-Fallback Directory* yang kebal terhadap *PermissionError* saat dieksekusi di *environment* sistem operasi terestriksi (seperti `System32`).

---

## 🛠️ Panduan Instalasi (Onboarding)

Pastikan Anda menggunakan Python 3.9 atau yang lebih baru.
```bash
pip install biopygeon
```

*Untuk kebutuhan pengembang (Developer) agar dapat menjalankan Unit Tests:*
```bash
pip install pytest pytest-mock responses
```

---

## 🔐 Autentikasi & Konfigurasi API

Sistem memerlukan autentikasi minimum untuk beroperasi optimal. Data kunci (Keys) dan Email akan disimpan aman secara lokal di `~/.bio_pipeline/config.json`.

**1. Mengatur API Keys dan Email**
Untuk mematuhi kebijakan *Polite Pool* (NCBI E-utilities & OpenAlex) dan mencegah pembatasan kecepatan (*rate limit*):
```bash
biopygeon auth set-key --groq-key "gsk_xxxx..." --s2-key "xxxx..." --email "anda@email.com"
```

**2. Verifikasi Status**
```bash
biopygeon auth status
```

---

## 🧠 Katalog Lengkap Alat AI (18 Smart Tools Blueprint)

Melalui perintah `biopygeon chat`, agen AI memiliki akses langsung ke *blueprint* alat berikut. Anda cukup meminta dalam bahasa manusia, dan AI akan merangkai parameter fungsinya!

### A. Modul Literatur & Pencarian (Literature Engine)
1. **`lit_search`**: Ekstraksi artikel dan metadata dari PubMed dan Semantic Scholar untuk menjawab pertanyaan (Q&A).
2. **`lit_search_bibliometrics`**: Ekstraksi jurnal berskala masif melalui OpenAlex untuk pemetaan jaringan publikasi (SSN).
3. **`export_results`**: Menyimpan dan mengonversi data hasil pencarian literatur ke format PDF, CSV, XML, JSON, TSV, atau FASTA.

### B. Modul Komputasi Biologi (Bio Engine)
4. **`find_protein`**: Melakukan kueri langsung ke RCSB PDB untuk menemukan struktur kristal 3D / NMR.
5. **`download_protein_data`**: Mengunduh dan mengekstrak berkas `.pdb` (struktur) atau `.fasta` (sekuens) dari RCSB PDB.
6. **`analyze_protparam`**: Mengkalkulasi sifat fisikokimia seperti titik isoelektrik (pI), berat molekul, dan indeks kestabilan (mengandalkan BioPython).
7. **`calculate_protein_params`**: Ekstensi kalkulasi massa untuk protein rekombinan (misalnya ditambahkan dengan tag purifikasi seperti His-tag).
8. **`run_blast`**: Eksekusi *remote* NCBI BLAST (blastp/blastn) dengan *parsing* data HSP secara real-time.
9. **`run_msa`**: Memicu *Multiple Sequence Alignment* secara asinkron menggunakan server EBI Clustal Omega.
10. **`extract_domain`**: Mengekstrak domain/nukleotida spesifik dari genom lengkap berdasarkan pencocokan motif (RegEx).
11. **`design_primer`**: Mendesain dan memvalidasi pasangan oligonukleotida (primer) untuk reaksi PCR dan perakitan kloning (*Primer3* wrapper).
12. **`prepare_docking`**: Melakukan pra-pemrosesan model PDB dengan membersihkan molekul pelarut (H2O) dan membuang rantai heteroatom.
13. **`fetch_alphafold_structure`**: Mengunduh model prediksi struktur 3D mutakhir dari AlphaFold Protein Structure Database via UniProt Accession ID.

### C. Modul Data Omics & Visualisasi (Pipeline Engine)
14. **`harmonize_data`**: Pra-pemrosesan Data CSV (*Baseline correction ALS*, imputasi *missing value* dengan *mean/median*).
15. **`plot_enrichment` & `plot_heatmap`**: Menggenerasi *Bubble Plot* jalur biologis dan *Heatmap* ekspresi secara interaktif menggunakan mesin Plotly.
16. **`render_network`**: Mengomputasi kolom target & sumber (*edges*) menjadi diagram SSN format HTML interaktif dengan D3.js.
17. **`plot_q1_figure` & `plot_volcano` (Auto-GraphPad & Smart Stats)**: Pembuatan plot kualitas Q1. Mesin *Smart Stats* akan melakukan uji asumsi otomatis sebelum mengeksekusi *Parametric* atau *Non-Parametric Test*. Signifikansi P-value (*, **, ***) dibubuhkan secara visual.
18. **`render_3d_structure`**: Visualisasi interaktif struktur 3D molekuler secara langsung (WebGL) di dalam antarmuka obrolan web menggunakan py3Dmol/stmol dengan pewarnaan *cartoon spectrum*.
19. **`generate_methodology`**: Asisten merumuskan dan menulis ulang parameter data ke dalam draf paragraf "Metode Penelitian".
20. **`format_manuscript`**: Menyesuaikan file draft naskah docx dengan template jurnal docx menggunakan MS Word Native COM Automation.

### D. Modul Eksekusi Otonom (ReAct Agent & Primitives)
Melalui fitur **Autonomous Pipeline**, agen dapat menggabungkan alat-alat primitif ini tanpa intervensi pengguna:
21. **`tool_run_python`**: Mengeksekusi Python secara dinamis di latar belakang (Code Interpreter lokal).
22. **`tool_web_scrape` & `tool_http_request`**: Menjelajah jaringan web atau mengekstraksi API eksternal secara mandiri.
23. **`tool_read_file`, `tool_write_file`, `tool_merge_documents`, `tool_extract_text`**: Manipulasi ekstensif untuk sistem dokumen dan ekstraksi PDF.

### E. Arsitektur Terpadu & Jejak Audit (*Enterprise-Grade Traceability*)
24. **Single Source of Truth Tool Registry**: Seluruh definisi alat disatukan secara elegan dalam satu *registry*. Hal ini menghapus *blind spot* (ketidaktahuan alat) dan meminimalisasi redundansi.
25. **Audit Trail Logging**: Setiap alat yang dieksekusi direkam sempurna secara terstruktur ke dalam dokumen log (`biopygeon_audit.jsonl`). Memberikan visibilitas absolut atas aktivitas komputasi agen.

---

## 💬 Mode Interaksi Asisten AI

Biopygeon menawarkan dua cara yang sangat ramah pengguna untuk berinteraksi dengan AI tanpa perlu menghafal baris perintah:

### 1. Antarmuka Web Interaktif (Rekomendasi)
Panggil Web UI (berbasis Streamlit) yang elegan dan sangat fungsional langsung dari terminal Anda:
```bash
biopygeon ui
```
Ini akan membuka antarmuka obrolan grafis di *browser* Anda (biasanya di `http://localhost:8501`), di mana Anda bisa mengunggah *file* `.csv`, `.pdb`, atau `.docx` dengan cara *drag & drop*, melihat progres pemikiran otonom AI secara *realtime*, dan mengunduh hasil ekspor (PDF/Dashboard HTML) cukup dengan sekali klik!

### 2. Mode Terminal Interaktif (CLI Chat)
Jika Anda bekerja di *server* atau preferensi terminal biasa:
```bash
biopygeon chat
```

**Anda dapat mengetikkan perintah natural pada kedua *platform* tersebut:**
- *"Cari 10 jurnal terbaru tentang terapi sel punca."* (Memicu `lit_search`)
- *"Berapa bobot molekul dan pI dari sekuens protein MLRYAIL?"* (Memicu `analyze_protparam`)
- *"Jalankan BLAST untuk 1SLT_A dan tolong unduhkan data strukturnya."* (Memicu `run_blast` dan `download_protein_data`)
- *"Buat plot jaringan SSN interaktif dari file interaksi.csv"* (Memicu `render_network`)
- *"Bersihkan molekul air pada protein_saya.pdb agar siap didocking"* (Memicu `prepare_docking`)

AI akan secara pintar menangani parameter (*routing*), menanyakan jika ada data masukan yang kurang, dan menyajikan hasil beserta opsi pembuatan laporan eksekutif berformat PDF.

---

## 🧪 Validasi Perangkat Lunak (QA & Testing)

Sebagai perangkat lunak kelas penelitian (*Research-Grade Software*), Biopygeon menggunakan *Unit Testing* ketat dengan isolasi API (*API Mocking*) agar *test suite* dapat dijalankan tanpa menghabiskan kuota jaringan.

Untuk memvalidasi integritas 18 fungsi sebelum pembaruan (diperlukan `pytest`):
```bash
$env:PYTHONPATH="."  # Untuk pengguna Windows
# atau export PYTHONPATH="." untuk Mac/Linux

python -m pytest tests/
```
Uji coba otomatis mengeksekusi *Dummy Responses* (XML dari PubMed, JSON dari OpenAlex, RCSB, dsb) untuk memastikan seluruh pipa data (*pipeline*) stabil 100%.

---

## 📜 Lisensi Hukum (GPLv3)

Biopygeon didistribusikan secara terbuka di bawah naungan **GNU General Public License v3.0 (GPLv3)**. 
Artinya, Anda bebas untuk menggunakan, memodifikasi, dan mendistribusikan ulang perangkat lunak ini secara gratis untuk keperluan edukasi dan riset. 

Namun, jika Anda mendistribusikan ulang aplikasi ini atau menyematkannya ke dalam produk Anda (baik secara utuh maupun dimodifikasi), Anda **diwajibkan secara hukum** untuk merilis *source code* produk tersebut di bawah lisensi GPLv3 yang sama secara gratis.

*Untuk penggunaan komersial dalam sistem perangkat lunak tertutup (Closed-Source / Proprietary), silakan hubungi tim pengembang untuk mendiskusikan Pembelian Lisensi Komersial Terpisah (Enterprise Dual-Licensing).*

---

*Dikembangkan untuk mentransformasi analisis bioinformatika yang kompleks menjadi dialog sederhana — dari data mentah menuju publikasi Q1 secara instan.*
