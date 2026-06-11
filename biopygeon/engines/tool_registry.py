
import json
from biopygeon.engines.primitives import (
    tool_store_variable, tool_retrieve_variable, tool_read_file, tool_write_file,
    tool_http_request, tool_web_scrape, tool_run_python, tool_fetch_sequence,
    tool_convert_format, tool_extract_text, tool_merge_documents
)
from biopygeon.engines.biology import (
    search_protein_structure, calculate_protparam, design_pcr_primers,
    run_ncbi_blast, clean_pdb_for_docking, run_ebi_clustalo, extract_domain,
    calculate_protein_params, download_protein_files
)
from biopygeon.engines.q1_pipeline import (
    harmonize_data, render_network, plot_q1_figure, generate_methodology
)
from biopygeon.engines.omics import (
    plot_enrichment, plot_heatmap, plot_volcano
)
from biopygeon.engines.literature import search_literature_with_fallback
from biopygeon.engines.formatter import format_manuscript_engine

# ================= SCHEMA ================= #
DOMAIN_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "run_autonomous_pipeline",
            "description": "Gunakan INI SEBAGAI PRIORITAS UTAMA JIKA pengguna memberikan instruksi berantai, multi-langkah, ATAU menggunakan kata hubung seperti 'lalu', 'kemudian', 'dan'. (contoh: 'unduh protein X LALU lakukan blast', 'cari sekuens lalu analisis protparam'). WAJIB DIPILIH untuk task majemuk!",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Tuliskan ulang instruksi lengkap pengguna yang memiliki banyak langkah."
                    }
                },
                "required": [
                    "task_description"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lit_search",
            "description": "Gunakan ini HANYA untuk menjawab pertanyaan spesifik (Q&A) berbasis jurnal, atau mencari referensi sangat singkat (< 20 jurnal). JANGAN gunakan jika pengguna HANYA meminta dicarikan sekumpulan jurnal tanpa pertanyaan analisis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Kata kunci pencarian dalam bahasa Inggris"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Jumlah paper"
                    }
                },
                "required": [
                    "query"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_protein",
            "description": "Mencari struktur protein di database PDB.",
            "parameters": {
                "type": "object",
                "properties": {
                    "protein_name": {
                        "type": "string",
                        "description": "Nama protein dalam bahasa Inggris"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Jumlah struktur"
                    }
                },
                "required": [
                    "protein_name"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lit_search_bibliometrics",
            "description": "Gunakan ini jika pengguna HANYA meminta dicarikan sekumpulan jurnal (>= 20 jurnal) tanpa ada pertanyaan spesifik, ATAU pengguna menyebutkan 'bibliometrik', 'pemetaan', 'VOSviewer', dll. Ini akan mengunduh metadata secara massal tanpa sintesis AI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Kata kunci pencarian pemetaan dalam bahasa Inggris"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Jumlah jurnal (disarankan 100-500)"
                    }
                },
                "required": [
                    "query"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "export_results",
            "description": "Mengekspor atau membuat laporan dari hasil pencarian sebelumnya.",
            "parameters": {
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "enum": [
                            "pdf",
                            "csv",
                            "xml",
                            "json",
                            "asn1",
                            "tsv",
                            "text",
                            "fasta"
                        ]
                    }
                },
                "required": [
                    "format"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_protparam",
            "description": "Menghitung sifat fisikokimia dari sekuens asam amino.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sequence": {
                        "type": "string",
                        "description": "Sekuens asam amino mentah"
                    }
                },
                "required": [
                    "sequence"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_blast",
            "description": "Mengeksekusi pencarian BLAST di server NCBI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sequence": {
                        "type": "string",
                        "description": "Sekuens query"
                    },
                    "program": {
                        "type": "string",
                        "enum": [
                            "blastp",
                            "blastn"
                        ]
                    },
                    "database": {
                        "type": "string",
                        "description": "Database (misal: swissprot, nr, nr_cluster_seq, nt). Default: nr_cluster_seq utk blastp, nt utk blastn"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Jumlah maksimum hit yang ingin dikembalikan"
                    }
                },
                "required": [
                    "sequence"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "prepare_docking",
            "description": "Membersihkan file PDB dari air dan heteroatom.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path file PDB input"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path tujuan penyimpanan output"
                    }
                },
                "required": [
                    "input_path",
                    "output_path"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "plot_enrichment",
            "description": "Membuat plot pengayaan (Enrichment Bubble Plot) interaktif dari file CSV menggunakan Plotly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_csv": {
                        "type": "string",
                        "description": "Path file CSV"
                    },
                    "output_html": {
                        "type": "string",
                        "description": "Path file HTML tujuan"
                    }
                },
                "required": [
                    "input_csv"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "plot_heatmap",
            "description": "Membuat Heatmap ekspresi genetik interaktif dari file CSV menggunakan Plotly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_csv": {
                        "type": "string",
                        "description": "Path file CSV"
                    },
                    "output_html": {
                        "type": "string",
                        "description": "Path file HTML tujuan"
                    }
                },
                "required": [
                    "input_csv"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "plot_volcano",
            "description": "Membuat Volcano Plot interaktif dari file CSV menggunakan Plotly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_csv": {
                        "type": "string",
                        "description": "Path file CSV"
                    },
                    "output_html": {
                        "type": "string",
                        "description": "Path file HTML tujuan"
                    },
                    "pvalue_col": {
                        "type": "string",
                        "description": "Nama kolom untuk P-value"
                    },
                    "fc_col": {
                        "type": "string",
                        "description": "Nama kolom untuk Fold Change (Log2FC)"
                    },
                    "pval_threshold": {
                        "type": "number",
                        "description": "Batas signifikansi P-value (default: 0.05)"
                    },
                    "log2fc_threshold": {
                        "type": "number",
                        "description": "Batas signifikansi Log2FC (default: 1.0)"
                    },
                    "gene_col": {
                        "type": "string",
                        "description": "Nama kolom untuk nama gen (opsional)"
                    }
                },
                "required": [
                    "input_csv",
                    "pvalue_col",
                    "fc_col"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "design_primer",
            "description": "Mendesain primer PCR (termasuk untuk kloning) untuk sekuens DNA target.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sequence": {
                        "type": "string",
                        "description": "Sekuens DNA murni (CDS)"
                    },
                    "fwd_enzyme": {
                        "type": "string",
                        "description": "Nama enzim restriksi forward (default: NheI)"
                    },
                    "fwd_enzyme_seq": {
                        "type": "string",
                        "description": "Sekuens pengenal enzim forward (default: GCTAGC)"
                    },
                    "rev_enzyme": {
                        "type": "string",
                        "description": "Nama enzim restriksi reverse (default: XhoI)"
                    },
                    "rev_enzyme_seq": {
                        "type": "string",
                        "description": "Sekuens pengenal enzim reverse (default: CTCGAG)"
                    },
                    "fwd_overhang": {
                        "type": "string",
                        "description": "Overhang 5' untuk forward primer (default: CGCG)"
                    },
                    "rev_overhang": {
                        "type": "string",
                        "description": "Overhang 5' untuk reverse primer (default: CGCG)"
                    },
                    "drop_stop_codon": {
                        "type": "boolean",
                        "description": "Hapus stop codon di akhir gen agar in-frame dengan tag plasmid (default: true)"
                    }
                },
                "required": [
                    "sequence"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "download_protein_data",
            "description": "Mengunduh file struktur PDB (.pdb) atau sekuens FASTA (.fasta) dari RCSB PDB berdasarkan PDB ID. PENTING: PDB ID harus 4-karakter (contoh: 1SLT). JANGAN PERNAH gunakan alat ini untuk mengunduh prediksi AlphaFold atau memproses UniProt ID (6 karakter)! Untuk AlphaFold, WAJIB gunakan alat fetch_alphafold_structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pdb_id": {
                        "type": "string",
                        "description": "4-karakter PDB ID, contoh: 1SLT"
                    },
                    "file_type": {
                        "type": "string",
                        "enum": [
                            "pdb",
                            "fasta",
                            "both"
                        ],
                        "description": "Jenis file yang ingin diunduh: pdb, fasta, atau both"
                    }
                },
                "required": [
                    "pdb_id",
                    "file_type"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_msa",
            "description": "Mengeksekusi Multiple Sequence Alignment via EBI Clustal Omega.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_fasta": {
                        "type": "string",
                        "description": "Path lengkap file FASTA input"
                    },
                    "output_fasta": {
                        "type": "string",
                        "description": "Path lengkap file FASTA tujuan"
                    }
                },
                "required": [
                    "input_fasta",
                    "output_fasta"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_domain",
            "description": "Ekstrak sekuens nukleotida spesifik domain dari sekuens gen penuh menggunakan pencarian motif asam amino.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sequence": {
                        "type": "string",
                        "description": "Sekuens DNA lengkap mentah"
                    },
                    "motif": {
                        "type": "string",
                        "description": "Motif asam amino yang dicari (default: WFQNHR)"
                    },
                    "before_aa": {
                        "type": "integer",
                        "description": "Jumlah asam amino hulu yang diambil (default: 30)"
                    },
                    "after_aa": {
                        "type": "integer",
                        "description": "Jumlah asam amino hilir yang diambil (default: 25)"
                    }
                },
                "required": [
                    "sequence"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_protein_params",
            "description": "Menghitung sifat fisikokimia protein rekombinan (MW, pI, charge).",
            "parameters": {
                "type": "object",
                "properties": {
                    "sequence": {
                        "type": "string",
                        "description": "Sekuens DNA CDS yang akan diekspresikan"
                    },
                    "fusion_tag": {
                        "type": "string",
                        "description": "Tag asam amino tambahan di ujung, contoh: LEHHHHHH (default)"
                    }
                },
                "required": [
                    "sequence"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "harmonize_data",
            "description": "Modul A: Membersihkan dan mengharmonisasi data CSV mentah (Missing value, Baseline Correction ALS).",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_csv": {
                        "type": "string",
                        "description": "Path ke data CSV mentah"
                    },
                    "output_csv": {
                        "type": "string",
                        "description": "Path untuk menyimpan CSV bersih"
                    },
                    "strategy": {
                        "type": "string",
                        "enum": [
                            "drop",
                            "mean",
                            "median"
                        ]
                    },
                    "baseline_method": {
                        "type": "string",
                        "enum": [
                            "als",
                            "polynomial"
                        ]
                    }
                },
                "required": [
                    "input_csv",
                    "output_csv"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "render_network",
            "description": "Modul B: Membuat jaringan (SSN) dari data relasi edge menjadi file HTML interaktif dan TIFF statis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_csv": {
                        "type": "string",
                        "description": "Nama file CSV edges (EKSTRAK MENTAH SESUAI INPUT PENGGUNA, JANGAN TAMBAHKAN path/to/)"
                    },
                    "output_tiff": {
                        "type": "string",
                        "description": "Nama file TIFF. Jika pengguna tidak menyebutkan, ISI OTOMATIS dengan 'hasil.tiff'."
                    },
                    "output_html": {
                        "type": "string",
                        "description": "Nama file HTML. Jika pengguna tidak menyebutkan, ISI OTOMATIS dengan 'hasil.html'."
                    },
                    "source_col": {
                        "type": "string",
                        "description": "Nama kolom sumber (opsional, kosongkan jika tidak tahu)"
                    },
                    "target_col": {
                        "type": "string",
                        "description": "Nama kolom target (opsional, kosongkan jika tidak tahu)"
                    },
                    "nodes_csv": {
                        "type": "string",
                        "description": "Nama file CSV nodes (EKSTRAK MENTAH JIKA ADA, JANGAN TAMBAHKAN path/to/)"
                    }
                },
                "required": [
                    "input_csv"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "plot_q1_figure",
            "description": "Modul C (Auto-GraphPad): Membuat plot statistik interaktif (T-Test/ANOVA) dengan style journal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_csv": {
                        "type": "string",
                        "description": "Path data CSV bersih"
                    },
                    "output_html": {
                        "type": "string",
                        "description": "Path penyimpanan dokumen HTML interaktif"
                    },
                    "plot_type": {
                        "type": "string",
                        "enum": [
                            "boxplot",
                            "violin",
                            "scatter",
                            "bar"
                        ]
                    },
                    "x_col": {
                        "type": "string",
                        "description": "Kolom X (kelompok/kategori)"
                    },
                    "y_col": {
                        "type": "string",
                        "description": "Kolom Y (nilai numerik)"
                    }
                },
                "required": [
                    "input_csv",
                    "output_html",
                    "plot_type",
                    "x_col",
                    "y_col"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_methodology",
            "description": "Modul D: Menulis draf teks metodologi penelitian secara otomatis berdasarkan parameter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "output_txt": {
                        "type": "string",
                        "description": "Path penyimpanan dokumen metodologi"
                    },
                    "baseline_method": {
                        "type": "string",
                        "enum": [
                            "als",
                            "polynomial"
                        ]
                    },
                    "plot_type": {
                        "type": "string",
                        "enum": [
                            "boxplot",
                            "violin",
                            "scatter",
                            "bar"
                        ]
                    },
                    "journal": {
                        "type": "string",
                        "enum": [
                            "nature",
                            "elsevier"
                        ]
                    }
                },
                "required": [
                    "output_txt"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "format_manuscript",
            "description": "Menyesuaikan file draft naskah docx dengan template jurnal docx.",
            "parameters": {
                "type": "object",
                "properties": {
                    "draft_docx": {
                        "type": "string",
                        "description": "Path ke file draft naskah docx"
                    },
                    "template_docx": {
                        "type": "string",
                        "description": "Path ke file template jurnal docx"
                    },
                    "output_docx": {
                        "type": "string",
                        "description": "Path untuk menyimpan file docx hasil format"
                    }
                },
                "required": [
                    "draft_docx",
                    "template_docx",
                    "output_docx"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_alphafold_structure",
            "description": "Gunakan ini KHUSUS untuk mengunduh model prediksi struktur 3D dari AlphaFold Protein Structure Database menggunakan UniProt ID (contoh: P04637).",
            "parameters": {
                "type": "object",
                "properties": {
                    "uniprot_id": {
                        "type": "string",
                        "description": "UniProt Accession ID (misal: P04637)"
                    }
                },
                "required": [
                    "uniprot_id"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "render_3d_structure",
            "description": "Menampilkan molekul protein 3D interaktif di layar pengguna. Gunakan ini setelah Anda berhasil mengunduh file PDB.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pdb_path": {
                        "type": "string",
                        "description": "Path lokal ke file PDB yang akan dirender"
                    }
                },
                "required": [
                    "pdb_path"
                ]
            }
        }
    }
]

PRIMITIVE_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "store_variable",
            "description": "Simpan variabel ke memori agen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string"
                    },
                    "value": {
                        "type": "string"
                    }
                },
                "required": [
                    "key",
                    "value"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_variable",
            "description": "Ambil variabel dari memori agen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string"
                    }
                },
                "required": [
                    "key"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Membaca isi file teks lokal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string"
                    }
                },
                "required": [
                    "filepath"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Menyimpan atau menambahkan string ke dalam file lokal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string"
                    },
                    "content": {
                        "type": "string"
                    },
                    "append": {
                        "type": "boolean"
                    }
                },
                "required": [
                    "filepath",
                    "content"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "http_request",
            "description": "Melakukan request HTTP API generic (GET/POST).",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string"
                    },
                    "method": {
                        "type": "string",
                        "enum": [
                            "GET",
                            "POST"
                        ]
                    },
                    "payload": {
                        "type": "string",
                        "description": "JSON string for POST body"
                    }
                },
                "required": [
                    "url"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_scrape",
            "description": "Mengunduh konten teks mentah dari halaman web URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string"
                    }
                },
                "required": [
                    "url"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Mengeksekusi skrip python dinamis dan mengembalikan stdout.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string"
                    }
                },
                "required": [
                    "code"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_sequence",
            "description": "Menarik sekuens FASTA dari ID spesifik.",
            "parameters": {
                "type": "object",
                "properties": {
                    "gene_id": {
                        "type": "string"
                    },
                    "db": {
                        "type": "string",
                        "enum": [
                            "uniprot",
                            "ncbi"
                        ]
                    }
                },
                "required": [
                    "gene_id"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "convert_format",
            "description": "Mengonversi format bioinformatika menggunakan SeqIO.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_data": {
                        "type": "string",
                        "description": "Raw sequence data"
                    },
                    "from_fmt": {
                        "type": "string"
                    },
                    "to_fmt": {
                        "type": "string"
                    }
                },
                "required": [
                    "input_data",
                    "from_fmt",
                    "to_fmt"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_text",
            "description": "Mengekstrak teks dari PDF atau DOCX.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string"
                    }
                },
                "required": [
                    "filepath"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "merge_documents",
            "description": "Menggabungkan dokumen PDF/DOCX.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_list_json": {
                        "type": "string",
                        "description": "JSON array of filepaths"
                    },
                    "output_path": {
                        "type": "string"
                    }
                },
                "required": [
                    "file_list_json",
                    "output_path"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_protparam",
            "description": "Menghitung sifat fisikokimia dari sekuens asam amino (MW, pI, dsb).",
            "parameters": {
                "type": "object",
                "properties": {
                    "sequence": {
                        "type": "string",
                        "description": "Sekuens asam amino mentah"
                    }
                },
                "required": [
                    "sequence"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_protein_params",
            "description": "Menghitung sifat fisikokimia protein rekombinan dengan fusion tag.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sequence": {
                        "type": "string",
                        "description": "Sekuens asam amino mentah"
                    },
                    "fusion_tag": {
                        "type": "string",
                        "description": "Fusion tag, misal LEHHHHHH"
                    }
                },
                "required": [
                    "sequence"
                ]
            }
        }
    }
]


# The router uses all tools
ROUTER_TOOLS_SCHEMA = PRIMITIVE_TOOLS_SCHEMA + DOMAIN_TOOLS_SCHEMA

# The autonomous loop uses all tools except 'run_autonomous_pipeline' to prevent recursion
FULL_TOOLS_SCHEMA = PRIMITIVE_TOOLS_SCHEMA + [t for t in DOMAIN_TOOLS_SCHEMA if t['function']['name'] != 'run_autonomous_pipeline']

# ================= EXECUTION REGISTRY ================= #

def _wrap_protparam(sequence):
    try:
        res, _ = calculate_protparam(sequence)
        return str(res)
    except Exception as e:
        return f"Error: {e}"

def _wrap_protein_params(sequence, fusion_tag="LEHHHHHH"):
    try:
        return str(calculate_protein_params(sequence, fusion_tag))
    except Exception as e:
        return f"Error: {e}"

def _wrap_download(pdb_id, file_type="both"):
    from biopygeon.engines.cache_manager import get_cache_dir
    downloads_path = get_cache_dir()
    try:
        return str(download_protein_files(pdb_id, file_type, downloads_path))
    except Exception as e:
        return f"Error: {e}"

def _wrap_blast(**kwargs):
    try:
        return str(run_ncbi_blast(**kwargs))
    except Exception as e:
        return f"Error: {e}"

def _wrap_msa(**kwargs):
    try:
        return str(run_ebi_clustalo(**kwargs))
    except Exception as e:
        return f"Error: {e}"

def _wrap_lit_search(query, limit=5):
    try:
        res = search_literature_with_fallback(query, max_results=limit, skip_ranking=True)
        return str(res)
    except Exception as e:
        return f"Error: {e}"

def _wrap_find_protein(protein_name, limit=5):
    try:
        return str(search_protein_structure(protein_name, limit))
    except Exception as e:
        return f"Error: {e}"

def _wrap_design_primer(**kwargs):
    try:
        return str(design_pcr_primers(**kwargs))
    except Exception as e:
        return f"Error: {e}"

def _wrap_harmonize_data(**kwargs):
    try:
        return str(harmonize_data(**kwargs))
    except Exception as e:
        return f"Error: {e}"

def _wrap_render_network(**kwargs):
    try:
        return str(render_network(**kwargs))
    except Exception as e:
        return f"Error: {e}"

def _wrap_plot_q1(**kwargs):
    try:
        return str(plot_q1_figure(**kwargs))
    except Exception as e:
        return f"Error: {e}"

def _wrap_methodology(**kwargs):
    try:
        return str(generate_methodology(**kwargs))
    except Exception as e:
        return f"Error: {e}"

def _wrap_export(**kwargs):
    return "Export UI action triggered."

def _wrap_plot_enrichment(**kwargs):
    try:
        plot_enrichment(**kwargs)
        return "Plot enrichment generated at " + kwargs.get('output_html', 'output')
    except Exception as e:
        return f"Error: {e}"

def _wrap_plot_heatmap(**kwargs):
    try:
        plot_heatmap(**kwargs)
        return "Plot heatmap generated at " + kwargs.get('output_html', 'output')
    except Exception as e:
        return f"Error: {e}"

def _wrap_plot_volcano(**kwargs):
    try:
        plot_volcano(**kwargs)
        return "Plot volcano generated at " + kwargs.get('output_html', 'output')
    except Exception as e:
        return f"Error: {e}"

def _wrap_extract_domain(**kwargs):
    try:
        return str(extract_domain(**kwargs))
    except Exception as e:
        return f"Error: {e}"

def _wrap_prepare_docking(**kwargs):
    try:
        return str(clean_pdb_for_docking(**kwargs))
    except Exception as e:
        return f"Error: {e}"

def _wrap_format_manuscript(**kwargs):
    try:
        return str(format_manuscript_engine(**kwargs))
    except Exception as e:
        return f"Error: {e}"

def _wrap_fetch_alphafold(**kwargs):
    from biopygeon.engines.biology import fetch_alphafold_structure
    from biopygeon.engines.cache_manager import get_cache_dir
    downloads_path = get_cache_dir()
    try:
        kwargs['output_dir'] = downloads_path
        res = fetch_alphafold_structure(**kwargs)
        return f"AlphaFold model downloaded to: {res}"
    except Exception as e:
        return f"Error: {e}"

def _wrap_render_3d(**kwargs):
    pdb_path = kwargs.get("pdb_path")
    return {"pdb_content": pdb_path}
FULL_FUNCTIONS = {
    "store_variable": tool_store_variable,
    "retrieve_variable": tool_retrieve_variable,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "http_request": tool_http_request,
    "web_scrape": tool_web_scrape,
    "run_python": tool_run_python,
    "fetch_sequence": tool_fetch_sequence,
    "convert_format": tool_convert_format,
    "extract_text": tool_extract_text,
    "merge_documents": tool_merge_documents,
    "analyze_protparam": _wrap_protparam,
    "calculate_protein_params": _wrap_protein_params,
    "download_protein_data": _wrap_download,
    "run_blast": _wrap_blast,
    "run_msa": _wrap_msa,
    "lit_search": _wrap_lit_search,
    "find_protein": _wrap_find_protein,
    "design_primer": _wrap_design_primer,
    "harmonize_data": _wrap_harmonize_data,
    "render_network": _wrap_render_network,
    "plot_q1_figure": _wrap_plot_q1,
    "generate_methodology": _wrap_methodology,
    "export_results": _wrap_export,
    "plot_enrichment": _wrap_plot_enrichment,
    "plot_heatmap": _wrap_plot_heatmap,
    "plot_volcano": _wrap_plot_volcano,
    "extract_domain": _wrap_extract_domain,
    "prepare_docking": _wrap_prepare_docking,
    "format_manuscript": _wrap_format_manuscript,
    "fetch_alphafold_structure": _wrap_fetch_alphafold,
    "render_3d_structure": _wrap_render_3d
}
