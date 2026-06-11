import os
import pandas as pd
import numpy as np
from collections import defaultdict
import json
import re

def get_top_authors(df, top_n=10):
    author_counts = defaultdict(int)
    for _, row in df.iterrows():
        authors = str(row.get('authors', ''))
        authorships = str(row.get('authorships', ''))
        
        if 'display_name' in authorships:
            matches = re.findall(r"'display_name':\s*'([^']+)'", authorships)
            for a in matches:
                if len(a) > 2: author_counts[a] += 1
        else:
            if not authors or pd.isna(authors) or authors.lower() == 'unknown':
                continue
            author_list = [a.strip() for a in authors.replace(' and ', ',').split(',')]
            for author in author_list:
                if len(author) > 2:
                    author_counts[author] += 1
                
    sorted_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    labels = [x[0][:25]+"..." if len(x[0])>25 else x[0] for x in sorted_authors]
    return {"labels": labels, "counts": [x[1] for x in sorted_authors]}

STOP_WORDS = set([
    'i','me','my','myself','we','our','ours','ourselves','you','your','yours','yourself','yourselves',
    'he','him','his','himself','she','her','hers','herself','it','its','itself','they','them','their',
    'theirs','themselves','what','which','who','whom','this','that','these','those','am','is','are',
    'was','were','be','been','being','have','has','had','having','do','does','did','doing','a','an',
    'the','and','but','if','or','because','as','until','while','of','at','by','for','with','about',
    'against','between','into','through','during','before','after','above','below','to','from','up',
    'down','in','out','on','off','over','under','again','further','then','once','here','there','when',
    'where','why','how','all','any','both','each','few','more','most','other','some','such','no','nor',
    'not','only','own','same','so','than','too','very','s','t','can','will','just','don','should','now',
    'ai','tldr','using','used','based','study','results','analysis','method','data','approach','new','model'
])

def get_top_keywords(df, top_n=20):
    from collections import Counter
    counter = Counter()
    for _, row in df.iterrows():
        t = str(row.get('title', ''))
        a = str(row.get('abstract', ''))
        if a.startswith("[AI TLDR]"): a = a[9:]
        text = (t + " " + a).lower()
        
        text = re.sub(r'[^a-z0-9\s]', '', text)
        words = [w for w in text.split() if w not in STOP_WORDS and len(w) > 2]
        
        counter.update(words)
        
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        counter.update(bigrams)
        
    if not counter:
        return {"words": [], "counts": []}
        
    common = counter.most_common(top_n)
    return {"words": [x[0] for x in common], "counts": [x[1] for x in common]}

def get_publication_years(df):
    year_col = None
    for col in ['publication_year', 'year', 'date', 'published']:
        if col in df.columns:
            year_col = col
            break
            
    if not year_col:
        return {"years": [], "pubs": [], "cits": []}
        
    try:
        df['year_clean'] = df[year_col].astype(str).str.extract(r'(\d{4})')[0].dropna().astype(int)
        df['citations_clean'] = pd.to_numeric(df.get('citations', df.get('cited_by_count', 0)), errors='coerce').fillna(0)
        
        grouped = df.groupby('year_clean').agg({'title':'count', 'citations_clean':'sum'})
        if len(grouped) == 0:
            return {"years": [], "pubs": [], "cits": []}
            
        min_y = int(grouped.index.min())
        max_y = int(grouped.index.max())
        full_range = range(min_y, max_y + 1)
        grouped = grouped.reindex(full_range, fill_value=0)
        
        return {
            "years": [int(x) for x in grouped.index], 
            "pubs": [int(x) for x in grouped['title']],
            "cits": [int(x) for x in grouped['citations_clean']]
        }
            
    except Exception:
        return {"years": [], "pubs": [], "cits": []}

def get_top_sources(df, top_n=10):
    source_counts = defaultdict(int)
    source_cits = defaultdict(int)
    for _, row in df.iterrows():
        source_name = None
        for col in ['journal', 'venue', 'publisher']:
            val = str(row.get(col, ''))
            if val and val.lower() not in ['nan', 'none', 'unknown']:
                source_name = val
                break
                
        if not source_name:
            loc = str(row.get('primary_location', ''))
            if 'display_name' in loc:
                match = re.search(r"'display_name':\s*'([^']+)'", loc)
                if match: source_name = match.group(1)
                    
        if source_name and len(source_name) > 2:
            source_counts[source_name] += 1
            cit = pd.to_numeric(row.get('citations', row.get('cited_by_count', 0)), errors='coerce')
            if not pd.isna(cit):
                source_cits[source_name] += int(cit)
            
    sorted_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    labels = [x[0][:30]+"..." if len(x[0])>30 else x[0] for x in sorted_sources]
    return {
        "labels": labels, 
        "pubs": [x[1] for x in sorted_sources],
        "cits": [source_cits[x[0]] for x in sorted_sources]
    }

def get_top_cited_papers(df, top_n=10):
    citation_col = 'citations' if 'citations' in df.columns else 'cited_by_count'
    if citation_col in df.columns and 'title' in df.columns:
        df['temp_citations'] = pd.to_numeric(df[citation_col], errors='coerce').fillna(0)
        df_sorted = df.sort_values(by='temp_citations', ascending=False).head(top_n)
        
        papers = []
        rank = 1
        for _, row in df_sorted.iterrows():
            if int(row['temp_citations']) == 0: continue
            
            title = str(row['title'])
            if len(title) > 80: title = title[:77] + '...'
            authors = str(row.get('authors', 'Unknown'))
            if len(authors) > 35: authors = authors[:32] + '...'
            journal = str(row.get('journal', row.get('venue', 'Unknown')))
            if len(journal) > 30: journal = journal[:27] + '...'
            doi = str(row.get('doi_url', f"https://doi.org/{row.get('doi','')}"))
            if doi == "https://doi.org/": doi = "#"
                
            papers.append({
                'rank': rank,
                'title': title,
                'authors': authors,
                'journal': journal,
                'citations': int(row['temp_citations']),
                'year': str(row.get('year', row.get('publication_year', '-'))),
                'doi': doi
            })
            rank += 1
        return papers
    return []

def get_oa_stats(df):
    yes_count = 0
    no_count = 0
    for _, row in df.iterrows():
        oa = str(row.get('is_oa', '')).lower()
        if oa in ['ya', 'yes', 'true']:
            yes_count += 1
        else:
            no_count += 1
    return {"yes": yes_count, "no": no_count}

def get_citation_distribution(df):
    citation_col = 'citations' if 'citations' in df.columns else 'cited_by_count'
    dist = {"0-10": 0, "11-50": 0, "51-100": 0, "101-500": 0, "500+": 0}
    if citation_col in df.columns:
        cits = pd.to_numeric(df[citation_col], errors='coerce').fillna(0)
        for c in cits:
            if c <= 10: dist["0-10"] += 1
            elif c <= 50: dist["11-50"] += 1
            elif c <= 100: dist["51-100"] += 1
            elif c <= 500: dist["101-500"] += 1
            else: dist["500+"] += 1
    return {"labels": list(dist.keys()), "values": list(dist.values())}

def render_bibliometric_dashboard(df, output_path="Bibliometric_Dashboard.html", progress_callback=None, query="", limit=100, year=None, metadata=None):
    if progress_callback: progress_callback("Mengekstrak statistik penulis...")
    authors_data = get_top_authors(df)
    
    if progress_callback: progress_callback("Mengekstrak frekuensi kata kunci...")
    keywords_data = get_top_keywords(df)
    
    if progress_callback: progress_callback("Menganalisis tren publikasi...")
    trend_data = get_publication_years(df)
    
    if progress_callback: progress_callback("Menganalisis sumber jurnal...")
    journals_data = get_top_sources(df)
    
    if progress_callback: progress_callback("Mencari makalah paling banyak disitasi...")
    top_papers = get_top_cited_papers(df)
    
    oa_data = get_oa_stats(df)
    cit_dist = get_citation_distribution(df)
    
    data_obj = {
        "authors": authors_data,
        "journals": journals_data,
        "trend": trend_data,
        "keywords": keywords_data,
        "oa": oa_data,
        "citDist": cit_dist,
        "topCited": top_papers
    }
    
    # Calculate stats for injection
    total_literature = len(df)
    
    unique_authors_set = set()
    for _, row in df.iterrows():
        a = str(row.get('authors', ''))
        if a and a.lower() != 'unknown':
            for ax in a.replace(' and ', ',').split(','):
                if len(ax.strip()) > 2: unique_authors_set.add(ax.strip())
    unique_authors = len(unique_authors_set)
    
    citation_col = 'citations' if 'citations' in df.columns else 'cited_by_count'
    cits_arr = pd.to_numeric(df[citation_col], errors='coerce').fillna(0) if citation_col in df.columns else pd.Series([0])
    total_citations = int(cits_arr.sum())
    
    if total_citations >= 1000:
        total_citations_fmt = f"{total_citations/1000:.1f}K"
    else:
        total_citations_fmt = str(total_citations)
        
    mean_citations = int(cits_arr.mean()) if total_literature > 0 else 0
    
    oa_percent = round((oa_data['yes'] / total_literature) * 100, 1) if total_literature > 0 else 0
    
    peak_year = trend_data['years'][np.argmax(trend_data['pubs'])] if trend_data['pubs'] else "N/A"
    peak_year_pubs = max(trend_data['pubs']) if trend_data['pubs'] else 0
    
    english_query = metadata.get("english_query", "N/A") if metadata else "N/A"
    bool_query = metadata.get("bool_query", "N/A") if metadata else "N/A"
    
    # Load template
    template_path = os.path.join(os.path.dirname(__file__), "dashboard_pro_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
        
    # Inject values
    replacements = {
        "{query}": str(query),
        "{total_literature}": str(total_literature),
        "{unique_authors}": str(unique_authors),
        "{total_citations_fmt}": str(total_citations_fmt),
        "{total_citations}": f"{total_citations:,}",
        "{mean_citations}": str(mean_citations),
        "{oa_percent}": str(oa_percent),
        "{oa_count}": str(oa_data['yes']),
        "{peak_year}": str(peak_year),
        "{peak_year_pubs}": str(peak_year_pubs),
        "{english_query}": str(english_query),
        "{bool_query}": str(bool_query)
    }
    
    for k, v in replacements.items():
        html = html.replace(k, v)
    
    # Inject DATA json
    html = html.replace("/*PYTHON_DATA_INJECT_HERE*/ {}", json.dumps(data_obj))
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    return output_path
