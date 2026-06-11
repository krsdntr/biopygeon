def search_protein_structure(protein_name, max_results=5, progress_callback=None):
    """
    Mencari struktur protein dari basis data Structure (PDB) di NCBI via Biopython Entrez.
    """
    from Bio import Entrez
    Entrez.email = "biopygeon@example.com"
    
    if progress_callback: progress_callback(f"Menghubungi NCBI Structure untuk '{protein_name}'...")
    
    try:
        # Search for the protein name in the structure database (PDB)
        handle = Entrez.esearch(db="structure", term=protein_name, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()
        
        id_list = record.get("IdList", [])
        if not id_list:
            return []
            
        if progress_callback: progress_callback("Mengambil ringkasan struktur dari NCBI...")
        handle = Entrez.esummary(db="structure", id=",".join(id_list))
        summaries = Entrez.read(handle)
        handle.close()
        
        results = []
        for doc in summaries:
            pdb_acc = doc.get("PdbAcc", "")
            title = doc.get("PdbDescr", "No Title")
            resolution = doc.get("Resolution", "Unknown")
            tax_name = doc.get("TaxId", "Unknown") # Alternatively, some fields contain organism
            
            # extract organism from extra fields if available
            organism = doc.get("ExpMethod", "Unknown Method")
            
            results.append({
                "pdb_id": pdb_acc,
                "title": title,
                "resolution": resolution,
                "method": organism
            })
            
        if progress_callback: progress_callback("Pencarian struktur selesai.")
        return results
    except Exception as e:
        raise RuntimeError(f"Gagal menghubungi NCBI Structure: {e}")

def calculate_protparam(seq: str) -> str:
    from Bio.SeqUtils.ProtParam import ProteinAnalysis
    # Remove whitespace and invalid characters
    clean_seq = "".join(seq.split()).upper()
    valid_chars = set("ACDEFGHIKLMNPQRSTVWY")
    filtered_seq = "".join([c for c in clean_seq if c in valid_chars])
    
    if not filtered_seq:
        raise ValueError("Sekuens tidak mengandung asam amino valid.")
        
    analysis = ProteinAnalysis(filtered_seq)
    
    # Sequence formatting
    seq_lines = []
    seq_lines.append("        10         20         30         40         50         60 ")
    for i in range(0, len(filtered_seq), 60):
        chunk = filtered_seq[i:i+60]
        blocks = [chunk[j:j+10] for j in range(0, len(chunk), 10)]
        seq_lines.append(" ".join(blocks))
        if i + 60 < len(filtered_seq):
            next_start = i + 60
            header = ""
            for h in range(next_start + 10, min(next_start + 70, len(filtered_seq) + 10), 10):
                header += f"{h:>10} "
            seq_lines.append("")
            seq_lines.append(header.rstrip())
            
    mw = analysis.molecular_weight()
    pi = analysis.isoelectric_point()
    length = len(filtered_seq)
    
    aa_counts = analysis.count_amino_acids()
    if hasattr(analysis, "amino_acids_percent"):
        aa_percent = analysis.amino_acids_percent
    else:
        aa_percent = analysis.get_amino_acids_percent()
    
    aa_map = {
        'A': 'Ala', 'R': 'Arg', 'N': 'Asn', 'D': 'Asp', 'C': 'Cys',
        'Q': 'Gln', 'E': 'Glu', 'G': 'Gly', 'H': 'His', 'I': 'Ile',
        'L': 'Leu', 'K': 'Lys', 'M': 'Met', 'F': 'Phe', 'P': 'Pro',
        'S': 'Ser', 'T': 'Thr', 'W': 'Trp', 'Y': 'Tyr', 'V': 'Val'
    }
    
    aa_comp = []
    for code, name in aa_map.items():
        count = aa_counts.get(code, 0)
        pct = aa_percent.get(code, 0) * 100
        aa_comp.append(f"{name} ({code}) {count:>3}\t{pct:>5.1f}%")
        
    aa_comp_str = "\n".join(aa_comp)
    
    neg_charge = aa_counts.get('D', 0) + aa_counts.get('E', 0)
    pos_charge = aa_counts.get('R', 0) + aa_counts.get('K', 0)
    
    atom_map = {
        'A': {'C':3, 'H':5, 'N':1, 'O':1, 'S':0},
        'R': {'C':6, 'H':12, 'N':4, 'O':1, 'S':0},
        'N': {'C':4, 'H':6, 'N':2, 'O':2, 'S':0},
        'D': {'C':4, 'H':5, 'N':1, 'O':3, 'S':0},
        'C': {'C':3, 'H':5, 'N':1, 'O':1, 'S':1},
        'Q': {'C':5, 'H':8, 'N':2, 'O':2, 'S':0},
        'E': {'C':5, 'H':7, 'N':1, 'O':3, 'S':0},
        'G': {'C':2, 'H':3, 'N':1, 'O':1, 'S':0},
        'H': {'C':6, 'H':7, 'N':3, 'O':1, 'S':0},
        'I': {'C':6, 'H':11, 'N':1, 'O':1, 'S':0},
        'L': {'C':6, 'H':11, 'N':1, 'O':1, 'S':0},
        'K': {'C':6, 'H':12, 'N':2, 'O':1, 'S':0},
        'M': {'C':5, 'H':9, 'N':1, 'O':1, 'S':1},
        'F': {'C':9, 'H':9, 'N':1, 'O':1, 'S':0},
        'P': {'C':5, 'H':7, 'N':1, 'O':1, 'S':0},
        'S': {'C':3, 'H':5, 'N':1, 'O':2, 'S':0},
        'T': {'C':4, 'H':7, 'N':1, 'O':2, 'S':0},
        'W': {'C':11, 'H':10, 'N':2, 'O':1, 'S':0},
        'Y': {'C':9, 'H':9, 'N':1, 'O':2, 'S':0},
        'V': {'C':5, 'H':9, 'N':1, 'O':1, 'S':0}
    }
    
    total_atoms = {'C':0, 'H':0, 'N':0, 'O':0, 'S':0}
    for c in filtered_seq:
        for atom, count in atom_map[c].items():
            total_atoms[atom] += count
            
    total_atoms['H'] += 2
    total_atoms['O'] += 1
    total_atom_count = sum(total_atoms.values())
    
    atomic_str = f"Carbon      C\t{total_atoms['C']:>10}\n" \
                 f"Hydrogen    H\t{total_atoms['H']:>10}\n" \
                 f"Nitrogen    N\t{total_atoms['N']:>10}\n" \
                 f"Oxygen      O\t{total_atoms['O']:>10}\n" \
                 f"Sulfur      S\t{total_atoms['S']:>10}\n"
                 
    formula = "".join([f"{atom}{total_atoms[atom]}" for atom in ['C', 'H', 'N', 'O', 'S'] if total_atoms[atom] > 0])
            
    try:
        ext = analysis.molar_extinction_coefficient()
        abs_cys_form = ext[0] / mw if mw else 0
        abs_cys_reduced = ext[1] / mw if mw else 0
        ext_str = (
            "Extinction coefficients:\n"
            "Extinction coefficients are in units of  M-1 cm-1, at 280 nm measured in water.\n"
            f"Ext. coefficient    {ext[0]}\n"
            f"Abs 0.1% (=1 g/l)   {abs_cys_form:.3f}, assuming all pairs of Cys residues form cystines\n\n"
            f"Ext. coefficient    {ext[1]}\n"
            f"Abs 0.1% (=1 g/l)   {abs_cys_reduced:.3f}, assuming all Cys residues are reduced"
        )
    except:
        ext_str = "Extinction coefficients: N/A"
        
    term = filtered_seq[0]
    term_name = aa_map.get(term, term)
    hl_str = f"Estimated half-life:\n" \
             f"The N-terminal of the sequence considered is {term} ({term_name}).\n" \
             f"The estimated half-life is: "
    
    if term in ['M', 'G', 'A', 'S', 'T', 'V', 'P']:
        hl_str += ">20 hours (mammalian reticulocytes, in vitro).\n"
    elif term in ['I', 'E']:
        hl_str += "30 min (mammalian reticulocytes, in vitro).\n"
    elif term in ['Y', 'Q']:
        hl_str += "10 min (mammalian reticulocytes, in vitro).\n"
    elif term in ['L', 'F', 'D', 'K']:
        hl_str += "3 min (mammalian reticulocytes, in vitro).\n"
    elif term == 'R':
        hl_str += "2 min (mammalian reticulocytes, in vitro).\n"
    else:
        hl_str += "1.3 hours (mammalian reticulocytes, in vitro).\n"
        
    hl_str += "                            >20 hours (yeast, in vivo).\n"
    hl_str += "                            >10 hours (Escherichia coli, in vivo)."

    ii = analysis.instability_index()
    stable_str = "stable" if ii < 40 else "unstable"
    aliphatic = 100 * (aa_percent.get('A', 0) + 2.9 * aa_percent.get('V', 0) + 3.9 * (aa_percent.get('I', 0) + aa_percent.get('L', 0)))
    gravy = analysis.gravy()
    
    template = f"""User-provided sequence:
{seq_lines[0]}
{seq_lines[1]}

[Documentation / Reference]
Number of amino acids: {length}
Theoretical pI: {pi:.2f}
Molecular weight: {mw:.2f}

Amino acid composition: 
{aa_comp_str}
Pyl (O)   0	  0.0%
Sec (U)   0	  0.0%

 (B)   0	  0.0%
 (Z)   0	  0.0%
 (X)   0	  0.0%

Total number of negatively charged residues (Asp + Glu): {neg_charge}
Total number of positively charged residues (Arg + Lys): {pos_charge}

Atomic composition:
{atomic_str}
Formula: {formula}
Total number of atoms: {total_atom_count}

{ext_str}

{hl_str}

Instability index:
The instability index (II) is computed to be {ii:.2f}
This classifies the protein as {stable_str}.

Aliphatic index: {aliphatic:.2f}
Grand average of hydropathicity (GRAVY): {gravy:.3f}
"""
    data_dict = {
        "Number of amino acids": length,
        "Theoretical pI": round(pi, 2),
        "Molecular weight": round(mw, 2),
        "Total atoms": total_atom_count,
        "Instability index": round(ii, 2),
        "Classification": stable_str,
        "Aliphatic index": round(aliphatic, 2),
        "GRAVY": round(gravy, 3)
    }
    return template, data_dict

def design_pcr_primers(sequence: str, prod_size_min=150, prod_size_max=500, tm_opt=60.0, tm_min=57.0, tm_max=63.0,
                       fwd_enzyme="", fwd_enzyme_seq="", rev_enzyme="", rev_enzyme_seq="",
                       fwd_overhang="", rev_overhang="", drop_stop_codon=False):
    """Mendesain primer PCR menggunakan primer3. Jika parameter enzim/overhang diberikan, mode kloning diaktifkan."""
    import primer3
    from Bio.Seq import Seq
    clean_seq = "".join(sequence.split()).upper()
    valid_nucs = set("ACGT")
    if not all(c in valid_nucs for c in clean_seq):
        raise ValueError("Sekuens hanya boleh mengandung nukleotida A, C, G, T.")
        
    if drop_stop_codon and clean_seq[-3:] in ["TAA", "TAG", "TGA"]:
        clean_seq = clean_seq[:-3]

    cloning_mode = bool(fwd_enzyme_seq or rev_enzyme_seq or fwd_overhang or rev_overhang)
    
    if cloning_mode:
        # Dalam mode kloning gen utuh, primer harus di ujung sekuens.
        # Cari panjang optimal (18-25 bp) yang paling mendekati tm_opt
        best_fwd_len = 20
        best_rev_len = 20
        min_diff_fwd = 999
        min_diff_rev = 999
        
        for l in range(18, 26):
            if l <= len(clean_seq):
                tm_f = primer3.calc_tm(clean_seq[:l])
                if abs(tm_f - tm_opt) < min_diff_fwd:
                    min_diff_fwd = abs(tm_f - tm_opt)
                    best_fwd_len = l
                    
                tm_r = primer3.calc_tm(str(Seq(clean_seq[-l:]).reverse_complement()))
                if abs(tm_r - tm_opt) < min_diff_rev:
                    min_diff_rev = abs(tm_r - tm_opt)
                    best_rev_len = l
                    
        fwd_bind = clean_seq[:best_fwd_len]
        rev_bind = str(Seq(clean_seq[-best_rev_len:]).reverse_complement())
        
        fwd_full = fwd_overhang + fwd_enzyme_seq + fwd_bind
        rev_full = rev_overhang + rev_enzyme_seq + rev_bind
        
        tm_fwd_bind = primer3.calc_tm(fwd_bind)
        tm_rev_bind = primer3.calc_tm(rev_bind)
        
        return [{
            'rank': 1,
            'penalty': 0.0,
            'product_size': len(clean_seq),
            'forward': {
                'sequence': fwd_full,
                'tm_bind': round(tm_fwd_bind, 2),
                'tm_full': round(primer3.calc_tm(fwd_full), 2),
                'gc': round((fwd_full.count('G') + fwd_full.count('C')) / len(fwd_full) * 100, 2),
                'length': len(fwd_full),
                'enzyme': fwd_enzyme,
                'overhang': fwd_overhang
            },
            'reverse': {
                'sequence': rev_full,
                'tm_bind': round(tm_rev_bind, 2),
                'tm_full': round(primer3.calc_tm(rev_full), 2),
                'gc': round((rev_full.count('G') + rev_full.count('C')) / len(rev_full) * 100, 2),
                'length': len(rev_full),
                'enzyme': rev_enzyme,
                'overhang': rev_overhang
            },
            'cloning_mode': True
        }]
    
    # Mode standar primer internal
    seq_args = {
        'SEQUENCE_ID': 'target',
        'SEQUENCE_TEMPLATE': clean_seq,
    }
    
    global_args = {
        'PRIMER_OPT_SIZE': 20,
        'PRIMER_PICK_INTERNAL_OLIGO': 0,
        'PRIMER_INTERNAL_MAX_SELF_END': 8,
        'PRIMER_MIN_SIZE': 18,
        'PRIMER_MAX_SIZE': 25,
        'PRIMER_OPT_TM': tm_opt,
        'PRIMER_MIN_TM': tm_min,
        'PRIMER_MAX_TM': tm_max,
        'PRIMER_MIN_GC': 40.0,
        'PRIMER_MAX_GC': 60.0,
        'PRIMER_MAX_POLY_X': 5,
        'PRIMER_INTERNAL_MAX_POLY_X': 5,
        'PRIMER_SALT_MONOVALENT': 50.0,
        'PRIMER_DNA_CONC': 50.0,
        'PRIMER_MAX_NS_ACCEPTED': 0,
        'PRIMER_MAX_SELF_ANY': 8,
        'PRIMER_MAX_SELF_END': 3,
        'PRIMER_PAIR_MAX_COMPL_ANY': 8,
        'PRIMER_PAIR_MAX_COMPL_END': 3,
        'PRIMER_PRODUCT_SIZE_RANGE': [[prod_size_min, prod_size_max]]
    }
    
    res = primer3.bindings.design_primers(seq_args, global_args)
    
    if res.get('PRIMER_PAIR_NUM_RETURNED', 0) == 0:
        return None
        
    primer_results = []
    for i in range(res['PRIMER_PAIR_NUM_RETURNED']):
        fwd_seq = res[f'PRIMER_LEFT_{i}_SEQUENCE']
        rev_seq = res[f'PRIMER_RIGHT_{i}_SEQUENCE']
        
        primer_results.append({
            'rank': i + 1,
            'penalty': round(res[f'PRIMER_PAIR_{i}_PENALTY'], 3),
            'product_size': res[f'PRIMER_PAIR_{i}_PRODUCT_SIZE'],
            'forward': {
                'sequence': fwd_seq,
                'tm': round(res[f'PRIMER_LEFT_{i}_TM'], 2),
                'gc': round(res[f'PRIMER_LEFT_{i}_GC_PERCENT'], 2),
                'length': len(fwd_seq)
            },
            'reverse': {
                'sequence': rev_seq,
                'tm': round(res[f'PRIMER_RIGHT_{i}_TM'], 2),
                'gc': round(res[f'PRIMER_RIGHT_{i}_GC_PERCENT'], 2),
                'length': len(rev_seq)
            },
            'cloning_mode': False
        })
    return primer_results

def run_ncbi_blast(seq: str, program: str = "blastp", database: str = "nr_cluster_seq", max_results: int = 5, progress_callback=None):
    from Bio.Blast import NCBIXML
    import requests
    import time
    import re
    import io
    
    if progress_callback: progress_callback(f"Menghubungi server NCBI BLAST ({program})... (Bisa memakan waktu 1-5 menit)")
    
    clean_seq = "".join(seq.split()).upper()
    
    # 1. PUT request
    put_url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
    put_params = {
        "CMD": "Put",
        "PROGRAM": program,
        "DATABASE": database,
        "QUERY": clean_seq,
        "HITLIST_SIZE": max_results,
        "ALIGNMENTS": max_results,
        "DESCRIPTIONS": max_results,
        "FORMAT_TYPE": "XML"
    }
    if program == "blastn":
        put_params["MEGABLAST"] = "on"
        
    response = requests.post(put_url, data=put_params)
    if response.status_code != 200:
        raise RuntimeError(f"Koneksi ke NCBI gagal: {response.status_code}")
        
    # Extract RID
    match = re.search(r'RID = (.*?)\n', response.text)
    if not match:
        raise RuntimeError("Gagal mendapatkan RID dari NCBI.")
    rid = match.group(1).strip()
    
    # Extract RTOE (Estimated time)
    rtoe_match = re.search(r'RTOE = (.*?)\n', response.text)
    if rtoe_match:
        time.sleep(min(int(rtoe_match.group(1).strip()), 30))
    else:
        time.sleep(5)
        
    # 2. Polling
    poll_url = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
    start_time = time.time()
    
    while True:
        elapsed = int(time.time() - start_time)
        if progress_callback and elapsed > 0 and elapsed % 5 == 0:
            progress_callback(f"Menunggu respons NCBI (RID: {rid})... ({elapsed} detik berlalu)")
            
        r = requests.get(poll_url, params={"CMD": "Get", "FORMAT_OBJECT": "SearchInfo", "RID": rid})
        if "Status=WAITING" in r.text:
            time.sleep(5)
            continue
        if "Status=FAILED" in r.text:
            raise RuntimeError(f"BLAST gagal di server NCBI (RID: {rid}).")
        if "Status=UNKNOWN" in r.text:
            raise RuntimeError(f"Sesi BLAST kadaluarsa (RID: {rid}).")
        if "Status=READY" in r.text:
            if "ThereAreHits=yes" in r.text:
                break
            else:
                return [], rid
        time.sleep(5)
        
    # 3. GET XML
    if progress_callback: progress_callback("Mem-parsing hasil BLAST...")
    r = requests.get(poll_url, params={"CMD": "Get", "FORMAT_TYPE": "XML", "RID": rid})
    
    blast_record = NCBIXML.read(io.StringIO(r.text))
    
    results = []
    for alignment in blast_record.alignments[:max_results]:
        for hsp in alignment.hsps:
            q_len = blast_record.query_length
            q_cov = min(100, int((hsp.align_length / q_len) * 100)) if q_len else 0
            
            desc = alignment.hit_def if hasattr(alignment, 'hit_def') and alignment.hit_def else alignment.title.split("|", 2)[-1]
            
            results.append({
                "description": desc[:50] + ("..." if len(desc) > 50 else ""),
                "max_score": round(hsp.bits),
                "total_score": round(hsp.bits),
                "query_cover": f"{q_cov}%",
                "e_value": hsp.expect,
                "per_ident": f"{(hsp.identities/hsp.align_length)*100:.2f}%",
                "acc_len": alignment.length,
                "accession": alignment.accession,
                "alignment_text": f"Query:  {hsp.query}\nMatch:  {hsp.match}\nSbjct:  {hsp.sbjct}"
            })
            break # usually just the top HSP
            
    return results, rid

def clean_pdb_for_docking(input_path: str, output_path: str, progress_callback=None):
    if progress_callback: progress_callback(f"Membersihkan PDB: {input_path}")
    import os
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File tidak ditemukan: {input_path}")
        
    lines_kept = 0
    with open(input_path, 'r') as f_in, open(output_path, 'w') as f_out:
        for line in f_in:
            if line.startswith("ATOM"):
                f_out.write(line)
                lines_kept += 1
            elif line.startswith("TER") or line.startswith("END"):
                f_out.write(line)
                
    if progress_callback: progress_callback(f"Selesai! {lines_kept} atom tersisa. File siap: {output_path}")
    return output_path


def run_ebi_clustalo(input_fasta: str, output_fasta: str, email: str = "biopygeon@example.com", progress_callback=None):
    """
    Menjalankan Multiple Sequence Alignment via EBI Clustal Omega API.
    """
    import requests
    import time
    import os
    
    if not os.path.exists(input_fasta):
        raise FileNotFoundError(f"File input tidak ditemukan: {input_fasta}")
        
    with open(input_fasta, 'r') as f:
        seqs = f.read()
        
    if progress_callback: progress_callback("Mengirim sekuens ke server EBI Clustal Omega...")
    
    try:
        res = requests.post("https://www.ebi.ac.uk/Tools/services/rest/clustalo/run", data={"email": email, "sequence": seqs})
        res.raise_for_status()
        job_id = res.text
    except Exception as e:
        raise RuntimeError(f"Gagal terhubung ke EBI Clustal Omega: {e}")
    
    if progress_callback: progress_callback(f"Pekerjaan diterima (Job ID: {job_id}). Menunggu antrean...")
    
    while True:
        try:
            status_res = requests.get(f"https://www.ebi.ac.uk/Tools/services/rest/clustalo/status/{job_id}")
            status = status_res.text
            if status in ["FINISHED", "ERROR", "NOT_FOUND"]:
                break
        except:
            pass
        time.sleep(5)
        if progress_callback: progress_callback(f"Status pekerjaan: {status}...")
        
    if status == "FINISHED":
        if progress_callback: progress_callback("Penyelarasan selesai. Mengunduh hasil...")
        try:
            aln_res = requests.get(f"https://www.ebi.ac.uk/Tools/services/rest/clustalo/result/{job_id}/fa")
            aln_res.raise_for_status()
            
            with open(output_fasta, 'w') as f:
                f.write(aln_res.text)
                
            if progress_callback: progress_callback(f"Hasil MSA berhasil disimpan ke {output_fasta}")
            return output_fasta
        except Exception as e:
            raise RuntimeError(f"Gagal mengunduh hasil dari EBI: {e}")
    else:
        raise RuntimeError(f"Gagal melakukan MSA. Status terakhir EBI: {status}")

def extract_domain(sequence: str, motif: str = "WFQNHR", before_aa: int = 30, after_aa: int = 25) -> dict:
    """
    Ekstrak koordinat nukleotida dari sebuah motif asam amino.
    """
    import re
    from Bio.Seq import Seq
    clean_seq = "".join(sequence.split()).upper()
    seq_obj = Seq(clean_seq)
    
    # Translasi
    protein = str(seq_obj.translate(to_stop=False))
    
    # Cari motif
    match = re.search(motif, protein)
    if not match:
        raise ValueError(f"Motif {motif} tidak ditemukan dalam hasil translasi.")
    
    start_aa = max(0, match.start() - before_aa)
    end_aa = min(len(protein), match.end() + after_aa)
    
    domain_protein = protein[start_aa:end_aa]
    
    # Back-translate ke koordinat nukleotida
    start_nt = start_aa * 3
    end_nt = end_aa * 3
    domain_nt = clean_seq[start_nt:end_nt]
    
    return {
        "full_protein_length": len(protein),
        "domain_start_aa": start_aa,
        "domain_end_aa": end_aa,
        "domain_nt_length": len(domain_nt),
        "domain_nucleotide_sequence": domain_nt,
        "domain_protein_sequence": domain_protein
    }


def calculate_protein_params(sequence: str, fusion_tag: str = "LEHHHHHH") -> dict:
    """
    Menghitung sifat fisikokimia protein. Jika input nukleotida, diubah dulu ke asam amino.
    """
    from Bio.SeqUtils.ProtParam import ProteinAnalysis
    from Bio.Seq import Seq
    
    clean_seq = "".join(sequence.split()).upper()
    valid_nucs = set("ACGT")
    
    if all(c in valid_nucs for c in clean_seq):
        protein_seq = str(Seq(clean_seq).translate(to_stop=False))
    else:
        protein_seq = clean_seq
        
    # Tambahkan tag fusi
    protein_seq += fusion_tag

    valid_aa = set("ACDEFGHIKLMNPQRSTVWY")
    filtered_seq = "".join([c for c in protein_seq if c in valid_aa])
    
    if not filtered_seq:
        raise ValueError("Sekuens tidak mengandung asam amino valid.")

    analysis = ProteinAnalysis(filtered_seq)
    
    return {
        "amino_acid_sequence": filtered_seq,
        "length_aa": len(filtered_seq),
        "molecular_weight_kDa": round(analysis.molecular_weight() / 1000, 2),
        "isoelectric_point": round(analysis.isoelectric_point(), 2),
        "charge_at_ph7": "+" if analysis.isoelectric_point() > 7 else "-"
    }

def fetch_fasta_sequence(accession: str, progress_callback=None) -> str:
    """Mengunduh sekuens FASTA dari NCBI."""
    from Bio import Entrez
    Entrez.email = "biopygeon@example.com"
    if progress_callback: progress_callback(f"Mengunduh FASTA untuk {accession} dari NCBI...")
    try:
        handle = Entrez.efetch(db="protein", id=accession, rettype="fasta", retmode="text")
        seq_data = handle.read()
        handle.close()
        return seq_data
    except Exception as e:
        raise RuntimeError(f"Gagal mengunduh FASTA dari NCBI: {e}")

def download_protein_files(pdb_id: str, file_type: str = "both", output_dir: str = None, progress_callback=None) -> list:
    """Mengunduh file struktur PDB dan/atau FASTA dari server RCSB PDB."""
    import urllib.request
    import os
    from biopygeon.engines.cache_manager import get_cache_dir
    
    if output_dir is None:
        output_dir = get_cache_dir()
        
    pdb_id = pdb_id.strip().upper()
    downloaded_files = []
    
    if file_type.lower() in ["pdb", "both"]:
        if progress_callback: progress_callback(f"Mengunduh file struktur PDB untuk {pdb_id}...")
        pdb_url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
        pdb_path = os.path.join(output_dir, f"{pdb_id}.pdb")
        try:
            urllib.request.urlretrieve(pdb_url, pdb_path)
            downloaded_files.append(pdb_path)
        except Exception as e:
            raise RuntimeError(f"Gagal mengunduh file PDB ({pdb_id}) dari RCSB: {e}")
            
    if file_type.lower() in ["fasta", "both"]:
        if progress_callback: progress_callback(f"Mengunduh sekuens FASTA untuk {pdb_id}...")
        fasta_url = f"https://www.rcsb.org/fasta/entry/{pdb_id}"
        fasta_path = os.path.join(output_dir, f"{pdb_id}.fasta")
        try:
            urllib.request.urlretrieve(fasta_url, fasta_path)
            downloaded_files.append(fasta_path)
        except Exception as e:
            raise RuntimeError(f"Gagal mengunduh file FASTA ({pdb_id}) dari RCSB: {e}")
            
    return downloaded_files

def fetch_alphafold_structure(uniprot_id: str, output_dir: str = None, progress_callback=None) -> list:
    """Mengunduh model prediksi struktur 3D dari AlphaFold Protein Structure Database."""
    import urllib.request
    import json
    import os
    from biopygeon.engines.cache_manager import get_cache_dir
    
    if output_dir is None:
        output_dir = get_cache_dir()
    
    uniprot_id = uniprot_id.strip().upper()
    if progress_callback: progress_callback(f"Menghubungi AlphaFold DB untuk {uniprot_id}...")
    
    try:
        # Get metadata to find the correct version URL
        api_url = f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req)
        data = json.loads(res.read())
        
        if not data or len(data) == 0:
            raise RuntimeError(f"Model AlphaFold tidak ditemukan untuk UniProt ID: {uniprot_id}.")
            
        # Get the PDB URL from the first prediction result
        af_url = data[0].get("pdbUrl")
        if not af_url:
            raise RuntimeError(f"URL PDB tidak tersedia di metadata AlphaFold untuk: {uniprot_id}.")
            
        af_path = os.path.join(output_dir, f"AF-{uniprot_id}.pdb")
        
        # Download the actual PDB file
        urllib.request.urlretrieve(af_url, af_path)
        if progress_callback: progress_callback(f"Berhasil mengunduh model prediksi AlphaFold: {af_path}")
        return [af_path]
        
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError(f"Model AlphaFold tidak ditemukan untuk UniProt ID: {uniprot_id}.")
            
        raise RuntimeError(f"Gagal mengunduh metadata AlphaFold: HTTP Error {e.code}")
    except Exception as e:
        raise RuntimeError(f"Gagal mengunduh model AlphaFold: {e}")
