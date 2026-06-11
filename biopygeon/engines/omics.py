import pandas as pd
import numpy as np

def calculate_volcano_stats(df: pd.DataFrame, pvalue_col: str, fc_col: str, pval_threshold: float, log2fc_threshold: float):
    """
    Mengkalkulasi dan memfilter data untuk Volcano Plot.
    Menambahkan kolom 'Regulation' untuk menandai Upregulated/Downregulated.
    """
    if pvalue_col not in df.columns or fc_col not in df.columns:
        raise ValueError(f"Kolom {pvalue_col} atau {fc_col} tidak ditemukan dalam data.")

    # Tambahkan log10(p-value)
    df['-log10(pvalue)'] = -np.log10(df[pvalue_col])
    
    # Kategori Regulasi
    conditions = [
        (df[pvalue_col] < pval_threshold) & (df[fc_col] > log2fc_threshold),
        (df[pvalue_col] < pval_threshold) & (df[fc_col] < -log2fc_threshold)
    ]
    choices = ['Upregulated', 'Downregulated']
    df['Regulation'] = np.select(conditions, choices, default='Not Significant')
    
    up_count = (df['Regulation'] == 'Upregulated').sum()
    down_count = (df['Regulation'] == 'Downregulated').sum()
    total_filtered = up_count + down_count
    
    return df, total_filtered, up_count, down_count

def fetch_enrichr_pathways(gene_list: list, library_name: str = "GO_Biological_Process_2021", progress_callback=None):
    import requests
    import json
    
    if progress_callback: progress_callback("Menambahkan daftar gen ke Enrichr...")
    
    ENRICHR_URL = 'https://maayanlab.cloud/Enrichr/addList'
    payload = {
        'list': (None, '\n'.join(gene_list)),
        'description': (None, 'Biopygeon Analysis')
    }
    
    response = requests.post(ENRICHR_URL, files=payload)
    if not response.ok:
        raise RuntimeError("Gagal menambahkan daftar gen ke Enrichr")
        
    data = response.json()
    user_list_id = data['userListId']
    
    if progress_callback: progress_callback(f"Mengambil hasil pengayaan dari {library_name}...")
    ENRICHR_URL_RESULTS = 'https://maayanlab.cloud/Enrichr/enrich'
    query_string = f'?userListId={user_list_id}&backgroundType={library_name}'
    
    res = requests.get(ENRICHR_URL_RESULTS + query_string)
    if not res.ok:
        raise RuntimeError("Gagal mengambil hasil dari Enrichr")
        
    res_json = res.json()
    pathways = res_json.get(library_name, [])
    
    # Format Enrichr: [Rank, Term, P-value, Z-score, Combined Score, Overlapping Genes, Adjusted P-value, ...]
    results = []
    for p in pathways[:15]: # Ambil top 15
        results.append({
            "Term": p[1],
            "P-value": p[2],
            "Adjusted P-value": p[6],
            "Combined Score": p[4],
            "Genes": p[5]
        })
        
    return results

def plot_enrichment(input_csv: str, output_html: str):
    import os
    import pandas as pd
    import plotly.express as px
    
    if not os.path.exists(input_csv):
        return f"[Error] File {input_csv} tidak ditemukan."
    df = pd.read_csv(input_csv)
    
    # Sort by P-value or Adjusted P-value
    sort_col = "Adjusted P-value" if "Adjusted P-value" in df.columns else "P-value"
    if sort_col in df.columns:
        df = df.sort_values(sort_col).head(20)
        # Tambahkan -log10(p-value)
        df['-log10(P-value)'] = -np.log10(df[sort_col])
        
        # Plot bubble
        fig = px.scatter(
            df,
            x='Combined Score',
            y='Term',
            size='-log10(P-value)',
            color='-log10(P-value)',
            hover_name='Term',
            hover_data=['Genes', sort_col],
            color_continuous_scale='Viridis',
            title='Pathway Enrichment Analysis'
        )
        fig.update_layout(
            template='plotly_white',
            yaxis={'categoryorder':'total ascending'}
        )
        os.makedirs(os.path.dirname(output_html) if os.path.dirname(output_html) else '.', exist_ok=True)
        config = {
            'toImageButtonOptions': {
                'format': 'svg',
                'filename': 'enrichment_plot',
                'height': 800,
                'width': 1000,
                'scale': 4
            }
        }
        fig.write_html(output_html, config=config)
        return f"Berhasil membuat Interactive Enrichment Plot di {output_html}"
    return "[Error] Kolom P-value tidak ditemukan dalam CSV."

def plot_heatmap(input_csv: str, output_html: str):
    import os
    import pandas as pd
    import plotly.express as px
    
    if not os.path.exists(input_csv):
        return f"[Error] File {input_csv} tidak ditemukan."
    df = pd.read_csv(input_csv, index_col=0) # Asumsikan kolom pertama adalah nama gen/sampel
    
    # Hanya ambil kolom numerik
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.empty:
        return "[Error] Tidak ada kolom numerik untuk dibuat Heatmap."
        
    fig = px.imshow(
        numeric_df,
        aspect="auto",
        color_continuous_scale="RdBu_r",
        title="Interactive Expression Heatmap"
    )
    fig.update_layout(template='plotly_white')
    
    os.makedirs(os.path.dirname(output_html) if os.path.dirname(output_html) else '.', exist_ok=True)
    config = {
        'toImageButtonOptions': {
            'format': 'svg',
            'filename': 'heatmap',
            'height': 800,
            'width': 1000,
            'scale': 4
        }
    }
    fig.write_html(output_html, config=config)
    return f"Berhasil membuat Interactive Heatmap di {output_html}"

def plot_volcano(input_csv: str, output_html: str, pvalue_col: str, fc_col: str, pval_threshold: float = 0.05, log2fc_threshold: float = 1.0, gene_col: str = None):
    import os
    import pandas as pd
    import plotly.express as px
    
    if not os.path.exists(input_csv):
        return f"[Error] File {input_csv} tidak ditemukan."
    df = pd.read_csv(input_csv)
    
    df, _, _, _ = calculate_volcano_stats(df, pvalue_col, fc_col, pval_threshold, log2fc_threshold)
    
    color_map = {
        'Upregulated': '#ef4444',
        'Downregulated': '#3b82f6',
        'Not Significant': '#94a3b8'
    }
    
    hover_data = [pvalue_col, fc_col]
    if gene_col and gene_col in df.columns:
        hover_name = gene_col
    else:
        hover_name = df.columns[0] # Fallback kolom pertama
        
    fig = px.scatter(
        df,
        x=fc_col,
        y='-log10(pvalue)',
        color='Regulation',
        color_discrete_map=color_map,
        hover_name=hover_name,
        hover_data=hover_data,
        title="Interactive Volcano Plot"
    )
    
    # Garis threshold
    fig.add_hline(y=-np.log10(pval_threshold), line_dash="dash", line_color="gray")
    fig.add_vline(x=log2fc_threshold, line_dash="dash", line_color="gray")
    fig.add_vline(x=-log2fc_threshold, line_dash="dash", line_color="gray")
    
    fig.update_layout(template='plotly_white')
    
    os.makedirs(os.path.dirname(output_html) if os.path.dirname(output_html) else '.', exist_ok=True)
    config = {
        'toImageButtonOptions': {
            'format': 'svg',
            'filename': 'volcano_plot',
            'height': 800,
            'width': 1000,
            'scale': 4
        }
    }
    fig.write_html(output_html, config=config)
    return f"Berhasil membuat Interactive Volcano Plot di {output_html}"
