*Read this in other languages: [English](README_en.md) | [Bahasa Indonesia](README.md)*

# 🕊️ Biopygeon
**The Last Mile Publication Aggregator & Intelligent Bioinformatics Assistant**

Biopygeon is an innovative command-line interface (CLI) and web interface that integrates bioinformatics instruments (NCBI BLAST, ExPASy ProtParam, Enrichr, PDB) directly with an artificial intelligence agent (LLM - Groq). This tool is designed to act as a bridge between raw biological data output and the generation of visualizations and reports standardized for Q1 journals (*Nature*, *Science*, *Elsevier*).

Unlike conventional static scripts, Biopygeon is equipped with an **AI Router** that dynamically and autonomously calls up to **18 smart tools** based on natural language conversations with the user.

---

## 🚀 Key Features

- 🤖 **Autonomous Intelligent Agent (`biopygeon chat` & Web UI)**: AI dynamically routes your chat to bioinformatics functions intelligently, accessible via Terminal (CLI) and interactive Web UI.
- 🧠 **ReAct Autonomous Pipeline**: A smart agent chaining feature capable of performing multiple complex tasks autonomously through dynamic code execution.
- 🎨 **Graphical Web Interface (Web UI)**: Provides a seamless visual chat experience supporting drag & drop file uploads, interactive downloads, floating settings, and session management.
- 🔬 **Comprehensive Biology Analysis Catalog**: From *ProtParam* calculations, 3D structure searches, *Multiple Sequence Alignment*, to cloning primer design!
- 🧬 **AlphaFold & 3D Interactive Viewer**: Asynchronous extraction of AlphaFold v4 (Google DeepMind) predicted models with real-time WebGL visualization embedded in the Streamlit UI without requiring external desktop applications.
- 📊 **Q1 Visualizations (Omics & Networks)**: Generates *Bubble Plots*, renders interactive networks (SSN), and algorithmically harmonizes CSV data.
- 📚 **Tri-Engine Literature Search**: Simultaneous access to Semantic Scholar, OpenAlex, and PubMed with *Polite Pool* API management (ban-free).
- 📑 **Automated Methodology & PDF Compilation**: Instantly drafts research narratives and executive PDF reports from computational results.
- 🛡️ **Smart Caching & Enterprise Security**: An intelligent standalone cache memory management system (`~/.biopygeon/cache`) with auto-cleanup (memory bloat-free) and an *Auto-Fallback Directory* architecture that is immune to *PermissionError* when executed in restricted OS environments (such as `System32`).

---

## 🛠️ Installation Guide (Onboarding)

Ensure you are using Python 3.9 or newer.
```bash
pip install biopygeon
```

*For Developers to run Unit Tests:*
```bash
pip install pytest pytest-mock responses
```

---

## 🔐 Authentication & API Configuration

The system requires minimal authentication to operate optimally. Keys and Email will be securely stored locally in `~/.bio_pipeline/config.json`.

**1. Setting API Keys and Email**
To comply with the *Polite Pool* policy (NCBI E-utilities & OpenAlex) and prevent rate limiting:
```bash
biopygeon auth set-key --groq-key "gsk_xxxx..." --s2-key "xxxx..." --email "your@email.com"
```

**2. Verifying Status**
```bash
biopygeon auth status
```

---

## 🧠 Comprehensive AI Tools Catalog (18 Smart Tools Blueprint)

Through the `biopygeon chat` command, the AI agent has direct access to the following tool blueprint. You simply ask in human language, and the AI will assemble its function parameters!

### A. Literature & Search Module (Literature Engine)
1. **`lit_search`**: Extraction of articles and metadata from PubMed and Semantic Scholar for Q&A.
2. **`lit_search_bibliometrics`**: Massive scale journal extraction via OpenAlex for publication network mapping (SSN).
3. **`export_results`**: Saves and converts literature search results to PDF, CSV, XML, JSON, TSV, or FASTA formats.

### B. Biological Computation Module (Bio Engine)
4. **`find_protein`**: Directly queries RCSB PDB to find 3D / NMR crystal structures.
5. **`download_protein_data`**: Downloads and extracts `.pdb` (structure) or `.fasta` (sequence) files from RCSB PDB.
6. **`analyze_protparam`**: Calculates physicochemical properties like isoelectric point (pI), molecular weight, and instability index (relies on BioPython).
7. **`calculate_protein_params`**: Mass calculation extension for recombinant proteins (e.g., added with purification tags like His-tag).
8. **`run_blast`**: Remote execution of NCBI BLAST (blastp/blastn) with real-time HSP data parsing.
9. **`run_msa`**: Triggers asynchronous *Multiple Sequence Alignment* using the EBI Clustal Omega server.
10. **`extract_domain`**: Extracts specific domains/nucleotides from complete genomes based on motif matching (RegEx).
11. **`design_primer`**: Designs and validates oligonucleotide pairs (primers) for PCR reactions and cloning assembly (*Primer3* wrapper).
12. **`prepare_docking`**: Pre-processes PDB models by cleaning solvent molecules (H2O) and removing heteroatom chains.
13. **`fetch_alphafold_structure`**: Downloads cutting-edge 3D structure prediction models from the AlphaFold Protein Structure Database via UniProt Accession ID.

### C. Omics Data & Visualization Module (Pipeline Engine)
14. **`harmonize_data`**: CSV Data Pre-processing (*Baseline correction ALS*, *mean/median* missing value imputation).
15. **`plot_enrichment` & `plot_heatmap`**: Generates *Bubble Plots* for biological pathways and expression *Heatmaps* interactively using the Plotly engine.
16. **`render_network`**: Computes target & source columns (edges) into interactive HTML format SSN diagrams with D3.js.
17. **`plot_q1_figure` & `plot_volcano` (Auto-GraphPad & Smart Stats)**: Creation of Q1 quality plots. The *Smart Stats* engine will automatically perform assumption testing before executing *Parametric* or *Non-Parametric Tests*. P-value significance (*, **, ***) is added visually.
18. **`render_3d_structure`**: Interactive 3D molecular structure visualization directly (WebGL) inside the web chat interface using py3Dmol/stmol with *cartoon spectrum* coloring.
19. **`generate_methodology`**: The assistant formulates and rewrites data parameters into a draft "Research Methods" paragraph.
20. **`format_manuscript`**: Adapts the docx manuscript draft file with docx journal templates using MS Word Native COM Automation.

### D. Autonomous Execution Module (ReAct Agent & Primitives)
Through the **Autonomous Pipeline** feature, the agent can chain these primitive tools without user intervention:
21. **`tool_run_python`**: Executes Python dynamically in the background (Local Code Interpreter).
22. **`tool_web_scrape` & `tool_http_request`**: Browses the web network or extracts external APIs autonomously.
23. **`tool_read_file`, `tool_write_file`, `tool_merge_documents`, `tool_extract_text`**: Extensive manipulation for document systems and PDF extraction.

### E. Unified Architecture & Audit Trail (*Enterprise-Grade Traceability*)
24. **Single Source of Truth Tool Registry**: All tool definitions are elegantly unified in a single *registry*. This eliminates blind spots and minimizes redundancy.
25. **Audit Trail Logging**: Every executed tool is perfectly and structurally recorded into a log document (`biopygeon_audit.jsonl`). Providing absolute visibility over the agent's computational activities.

---

## 💬 AI Assistant Interaction Modes

Biopygeon offers two highly user-friendly ways to interact with the AI without memorizing command lines:

### 1. Interactive Web Interface (Recommended)
Invoke the elegant and highly functional Web UI (Streamlit-based) directly from your terminal:
```bash
biopygeon ui
```
This will open a graphical chat interface in your browser (usually at `http://localhost:8501`), where you can upload `.csv`, `.pdb`, or `.docx` files via drag & drop, view the AI's autonomous thinking progress in real-time, and download export results (PDF/HTML Dashboard) with just one click!

### 2. Interactive Terminal Mode (CLI Chat)
If you are working on a server or prefer a standard terminal:
```bash
biopygeon chat
```

**You can type natural commands on both platforms:**
- *"Find 10 latest journals on stem cell therapy."* (Triggers `lit_search`)
- *"What is the molecular weight and pI of the MLRYAIL protein sequence?"* (Triggers `analyze_protparam`)
- *"Run BLAST for 1SLT_A and please download the structure data."* (Triggers `run_blast` and `download_protein_data`)
- *"Create an interactive SSN network plot from the interaksi.csv file"* (Triggers `render_network`)
- *"Clean the water molecules in my_protein.pdb to be ready for docking"* (Triggers `prepare_docking`)

The AI will intelligently handle parameters (routing), ask if any input data is missing, and present the results along with options to generate an executive report in PDF format.

---

## 🧪 Software Validation (QA & Testing)

As Research-Grade Software, Biopygeon utilizes strict Unit Testing with API Mocking so the test suite can be run without consuming network quotas.

To validate the integrity of the 18 functions prior to updates (`pytest` is required):
```bash
$env:PYTHONPATH="."  # For Windows users
# or export PYTHONPATH="." for Mac/Linux

python -m pytest tests/
```
Automated tests execute *Dummy Responses* (XML from PubMed, JSON from OpenAlex, RCSB, etc.) to ensure the entire data pipeline is 100% stable.

---

## 📜 Legal License (GPLv3)

Biopygeon is distributed openly under the **GNU General Public License v3.0 (GPLv3)**. 
This means you are free to use, modify, and redistribute this software for free for educational and research purposes. 

However, if you redistribute this application or embed it into your product (either wholly or modified), you are **legally required** to release the source code of that product under the same free GPLv3 license.

*For commercial use in Closed-Source / Proprietary software systems, please contact the development team to discuss separate Commercial License Purchasing (Enterprise Dual-Licensing).*

---

*Developed to transform complex bioinformatics analysis into simple dialogues — from raw data to Q1 publications instantly.*
