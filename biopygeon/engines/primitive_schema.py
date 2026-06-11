PRIMITIVE_TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "store_variable",
            "description": "Simpan variabel ke memori agen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "string"}
                },
                "required": ["key", "value"]
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
                    "key": {"type": "string"}
                },
                "required": ["key"]
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
                    "filepath": {"type": "string"}
                },
                "required": ["filepath"]
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
                    "filepath": {"type": "string"},
                    "content": {"type": "string"},
                    "append": {"type": "boolean"}
                },
                "required": ["filepath", "content"]
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
                    "url": {"type": "string"},
                    "method": {"type": "string", "enum": ["GET", "POST"]},
                    "payload": {"type": "string", "description": "JSON string for POST body"}
                },
                "required": ["url"]
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
                    "url": {"type": "string"}
                },
                "required": ["url"]
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
                    "code": {"type": "string"}
                },
                "required": ["code"]
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
                    "gene_id": {"type": "string"},
                    "db": {"type": "string", "enum": ["uniprot", "ncbi"]}
                },
                "required": ["gene_id"]
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
                    "input_data": {"type": "string", "description": "Raw sequence data"},
                    "from_fmt": {"type": "string"},
                    "to_fmt": {"type": "string"}
                },
                "required": ["input_data", "from_fmt", "to_fmt"]
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
                    "filepath": {"type": "string"}
                },
                "required": ["filepath"]
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
                    "file_list_json": {"type": "string", "description": "JSON array of filepaths"},
                    "output_path": {"type": "string"}
                },
                "required": ["file_list_json", "output_path"]
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
                    "sequence": {"type": "string", "description": "Sekuens asam amino mentah"}
                },
                "required": ["sequence"]
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
                    "sequence": {"type": "string", "description": "Sekuens asam amino mentah"},
                    "fusion_tag": {"type": "string", "description": "Fusion tag, misal LEHHHHHH"}
                },
                "required": ["sequence"]
            }
        }
    }
]
