import requests
import time
import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from biopygeon.config import get_s2_key, get_user_email
from biopygeon.engines.assistant import _call_groq_with_fallback

http_session = requests.Session()
http_session.headers.update({'User-Agent': 'BiopygeonCLI/0.5 (https://github.com/biopygeon/biopygeon)'})

def _reconstruct_openalex_abstract(inverted_index):
    if not inverted_index:
        return ""
    try:
        max_idx = 0
        for positions in inverted_index.values():
            for pos in positions:
                if pos > max_idx:
                    max_idx = pos
        words = [""] * (max_idx + 1)
        for word, positions in inverted_index.items():
            for pos in positions:
                words[pos] = word
        return " ".join(words).strip()
    except:
        return ""

def _scrape_abstract_fallback(doi_url):
    try:
        response = http_session.get(doi_url, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            abstract_div = soup.find(lambda tag: tag.name in ["div", "section", "p"] and 
                                     tag.has_attr('class') and 
                                     any('abstract' in c.lower() for c in tag['class']))
            if abstract_div:
                return abstract_div.get_text(separator=' ', strip=True)
            
            meta_abs = soup.find('meta', attrs={'name': 'citation_abstract'}) or \
                       soup.find('meta', attrs={'name': 'dc.description'}) or \
                       soup.find('meta', property='og:description')
            if meta_abs and meta_abs.get('content'):
                return meta_abs['content']
    except:
        pass
    return ""

def extract_intent(query: str):
    prompt = f"""Analyze this academic search query and extract key semantic components. ALWAYS translate input to English keywords.

Query: "{query}"

JSON FORMAT:
{{
    "intent": {{
        "main_topic": "short descriptive name of the topic",
        "main_entity": "biological name/species (e.g. 'Holothuria scabra') or primary object. If none, put ''",
        "topic_keywords": ["specific", "keywords"],
        "domain": "string (e.g. biology)",
        "causal_relation": "string (optional)"
    }}
}}"""
    try:
        res = _call_groq_with_fallback(
            system_prompt="You are an expert academic librarian. Output pure JSON only.", 
            user_prompt=prompt, 
            response_format={"type": "json_object"}, 
            temperature=0.1,
            max_tokens=300
        )
        return json.loads(res.get("content", "{}")).get("intent", {})
    except:
        return {"main_topic": query, "main_entity": "", "topic_keywords": query.split(), "domain": ""}

def optimize_boolean(query: str):
    prompt = f"""Generate ONE precise "Broad Context" boolean search query for the OpenAlex database.
USER INPUT: "{query}"

OUTPUT FORMAT JSON:
{{
    "reasoning": "brief explanation",
    "complexity": "Simple or Complex",
    "query": "the boolean query string"
}}"""
    try:
        res = _call_groq_with_fallback(
            system_prompt="You are an expert researcher. Output pure JSON only.", 
            user_prompt=prompt, 
            response_format={"type": "json_object"}, 
            temperature=0.1,
            max_tokens=300
        )
        data = json.loads(res.get("content", "{}"))
        return data.get("query", query), data.get("reasoning", "")
    except:
        return query, "Fallback to original query due to error."

def search_semanticscholar(keyword, max_results=50, year_filter=None, oa_filter=False, progress_callback=None):
    api_key = get_s2_key()
    headers = {"x-api-key": api_key} if api_key else {}
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": keyword, "limit": max_results,
        "fields": "title,year,citationCount,isOpenAccess,openAccessPdf,authors,tldr,venue,externalIds,abstract"
    }
    if year_filter: params["year"] = str(year_filter)
    if oa_filter: params["openAccessPdf"] = "true"

    try:
        response = http_session.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        jurnal_lists = []
        for paper in data.get('data', []):
            if not paper.get('title'): continue
            authors_data = paper.get('authors', [])
            authors_list = [a.get('name') for a in authors_data] if authors_data else []
            authors = ", ".join(authors_list) if authors_list else "Unknown"
            doi = (paper.get('externalIds') or {}).get('DOI', '')
            tldr = paper.get('tldr')
            abs_text = "[AI TLDR] " + tldr.get('text') if tldr and isinstance(tldr, dict) and tldr.get('text') else paper.get('abstract', '')
            
            jurnal_lists.append({
                "source": "S2", "title": paper.get('title'), "authors": authors, "journal": paper.get('venue') or "Unknown",
                "year": paper.get('year') or 0, "citations": paper.get('citationCount') or 0,
                "is_oa": "Ya" if paper.get('isOpenAccess') else "Tidak",
                "doi": doi, "doi_url": f"https://doi.org/{doi}" if doi else "", "abstract": abs_text or ""
            })
        return jurnal_lists
    except Exception as e:
        return []

def search_openalex(boolean_query, max_results=50, year_filter=None, oa_filter=False, progress_callback=None):
    url = "https://api.openalex.org/works"
    params = {"search": boolean_query, "per-page": max_results}
    filters = []
    if year_filter: filters.append(f"publication_year:{year_filter}")
    if oa_filter: filters.append("is_oa:true")
    if filters: params["filter"] = ",".join(filters)
    user_email = get_user_email()
    if user_email:
        params["mailto"] = user_email

    try:
        response = http_session.get(url, params=params, timeout=15)
        response.raise_for_status()
        jurnal_lists = []
        for work in response.json().get("results", []):
            authors = [a["author"]["display_name"] for a in work.get("authorships", [])]
            author_str = ", ".join(authors) if authors else "Unknown"
            venue = work.get("primary_location", {})
            venue_name = venue.get("source", {}).get("display_name") if venue and venue.get("source") else "Unknown"
            doi_url = work.get("doi", "")
            doi = doi_url.replace("https://doi.org/", "") if doi_url else ""
            abstract_text = _reconstruct_openalex_abstract(work.get("abstract_inverted_index"))
            
            jurnal_lists.append({
                "source": "OpenAlex", "title": work.get("title", ""), "authors": author_str, "journal": venue_name,
                "year": work.get("publication_year", 0), "citations": work.get("cited_by_count", 0),
                "is_oa": "Ya" if work.get("open_access", {}).get("is_oa") else "Tidak",
                "doi": doi, "doi_url": doi_url, "abstract": abstract_text
            })
        return jurnal_lists
    except Exception as e:
        return []

def search_pubmed(boolean_query, max_results=50, year_filter=None, oa_filter=False, progress_callback=None):
    from Bio import Entrez
    user_email = get_user_email()
    Entrez.email = user_email if user_email else "biopygeon@example.com"
    try:
        q = boolean_query
        if year_filter: q += f" AND {year_filter}[pdat]"
        handle = Entrez.esearch(db="pubmed", term=q, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()
        id_list = record.get("IdList", [])
        if not id_list: return []

        handle = Entrez.esummary(db="pubmed", id=",".join(id_list))
        summaries = Entrez.read(handle)
        handle.close()

        handle = Entrez.efetch(db="pubmed", id=",".join(id_list), retmode="xml")
        records = Entrez.read(handle)
        handle.close()

        abstracts_dict = {}
        for article in records.get('PubmedArticle', []):
            try:
                pmid = str(article['MedlineCitation']['PMID'])
                abs_text = article['MedlineCitation']['Article'].get('Abstract', {}).get('AbstractText', [''])
                abstracts_dict[pmid] = str(abs_text[0]) if abs_text else ""
            except: pass

        jurnal_lists = []
        for doc in summaries:
            authors = doc.get("AuthorList", [])
            author_str = ", ".join(authors) if authors else "Unknown"
            pubdate = doc.get("PubDate", "")
            year = int(pubdate.split()[0]) if pubdate else 0
            
            article_ids = doc.get("ArticleIds", {})
            doi = article_ids.get("doi", "")
            if isinstance(doi, dict):
                doi = ""
            doi_url = f"https://doi.org/{doi}" if doi else ""
            
            pmc_ref_count = doc.get("PmcRefCount", 0)
            try:
                citations = int(pmc_ref_count)
            except:
                citations = 0
                
            is_oa = "Ya" if "pmc" in article_ids or "pmcid" in article_ids else "Tidak"
            
            jurnal_lists.append({
                "source": "PubMed", "title": doc.get("Title", ""), "authors": author_str, "journal": doc.get("Source", "Unknown"),
                "year": year, "citations": citations, "is_oa": is_oa, "doi": doi, "doi_url": doi_url, "abstract": abstracts_dict.get(str(doc.get("Id", "")), "")
            })
        return jurnal_lists
    except Exception as e:
        return []

def deduplicate_results(results):
    merged = {}
    for r in results:
        key = r['doi'].lower().strip() if r.get('doi') else r['title'].lower().strip()
        if not key: continue
        if key in merged:
            if len(r['abstract']) > len(merged[key]['abstract']):
                merged[key]['abstract'] = r['abstract']
            if r['source'] not in merged[key]['source']:
                merged[key]['source'] += f", {r['source']}"
                
            # Safely get max citations
            c1 = merged[key].get('citations')
            c2 = r.get('citations')
            c1 = int(c1) if (c1 is not None and str(c1).isdigit()) else 0
            c2 = int(c2) if (c2 is not None and str(c2).isdigit()) else 0
            merged[key]['citations'] = max(c1, c2)
            
            # Prioritize 'Ya' or 'Tidak' over 'Unknown'
            if r.get('is_oa') == "Ya" or r.get('is_oa') == True:
                merged[key]['is_oa'] = "Ya"
            elif r.get('is_oa') == "Tidak" and merged[key].get('is_oa') == "Unknown":
                merged[key]['is_oa'] = "Tidak"
        else:
            merged[key] = r
    return list(merged.values())

def rank_results(results, intent, query, max_results=5, progress_callback=None):
    if not results: return []
    if progress_callback: progress_callback("[Phase 4] Menghitung Skor Heuristik (Tier 1)...")
    
    ranked_t1 = []
    entity = intent.get("main_entity", "").lower()
    for r in results:
        score = 0
        text = (r['title'] + " " + r['abstract']).lower()
        if entity:
            if entity in text:
                score += 40
            else:
                score -= 100
        score += math.log(r['citations'] + 1) * 2
        r['t1_score'] = score
        ranked_t1.append(r)
        
    ranked_t1 = sorted(ranked_t1, key=lambda x: x['t1_score'], reverse=True)[:25]
    if not ranked_t1: return []
    
    if progress_callback: progress_callback(f"[Phase 4] Semantic Ranking (Tier 2) untuk Top {len(ranked_t1)}...")
    
    prompt = f"Score academic relevance (0-100).\nQuery: \"{query}\"\nTopic Requirement: {intent.get('main_topic', '')}\nEntity Requirement: {intent.get('main_entity', '') or 'Any'}\n\nSCORING RULES:\n1. If entity differs significantly, score < 20.\n2. Unrelated topic < 20.\n3. High score (80+) ONLY if matches both well.\n\n"
    
    for i, r in enumerate(ranked_t1):
        prompt += f"[{i}] {r['title']} - {r['abstract'][:300]}\n"
        
    prompt += "\nJSON ONLY: {\"0\": 85, \"1\": 15}"
    
    try:
        res = _call_groq_with_fallback(
            system_prompt="You are a strict academic reviewer. Output JSON only.", 
            user_prompt=prompt, 
            response_format={"type": "json_object"}, 
            temperature=0.1,
            max_tokens=800
        )
        scores = json.loads(res.get("content", "{}"))
    except:
        scores = {}
        
    final_results = []
    for i, r in enumerate(ranked_t1):
        llm_score = scores.get(str(i), r['t1_score'])
        if isinstance(llm_score, str) and llm_score.isdigit(): llm_score = int(llm_score)
        try: llm_score = float(llm_score)
        except: llm_score = 50.0
        
        age = 2026 - r['year'] if r['year'] else 5
        recency = (1 / (age + 1)) * 100
        
        if llm_score < 40:
            final_score = (llm_score * 0.7) + (r['t1_score'] * 0.2) + (recency * 0.1)
        else:
            final_score = (llm_score * 0.6) + (r['t1_score'] * 0.3) + (recency * 0.1)
            
        r['final_score'] = final_score
        r['relevance_score'] = f"{final_score:.1f}"
        final_results.append(r)
        
    final_results = sorted(final_results, key=lambda x: x['final_score'], reverse=True)[:max_results]
    
    for i, r in enumerate(final_results):
        if not r['abstract'] and r['doi_url']:
            if progress_callback: progress_callback(f"[Phase 5] Scraping fallback abstrak untuk {i+1}/{len(final_results)}...")
            r['abstract'] = _scrape_abstract_fallback(r['doi_url'])
            
    return final_results

def search_literature_with_fallback(keyword, max_results=5, year_filter=None, oa_filter=False, sort_by='1', progress_callback=None, skip_ranking=False, return_metadata=False):
    if progress_callback: progress_callback("[Phase 1] Mengekstrak intent kueri menggunakan AI...")
    intent = extract_intent(keyword)
    
    if progress_callback: progress_callback("[Phase 2] Membangun Boolean Query Strategy...")
    bool_query, reason = optimize_boolean(keyword)
    
    english_query = " ".join(intent.get("topic_keywords", []))
    if intent.get("main_entity"):
        english_query += " " + intent.get("main_entity")
    if not english_query.strip():
        english_query = keyword
        
    if progress_callback: progress_callback(f"[Phase 3] Pencarian paralel S2, OpenAlex, dan PubMed (Query: {bool_query})...")
    
    # Untuk pencarian massal, kita tingkatkan fetch per API agar deduplikasi menghasilkan target akhir
    fetch_per_api = max_results if skip_ranking else max(30, max_results * 3)
    
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(search_semanticscholar, english_query, fetch_per_api, year_filter, oa_filter, progress_callback): "S2",
            executor.submit(search_openalex, bool_query, fetch_per_api, year_filter, oa_filter, progress_callback): "OpenAlex",
            executor.submit(search_pubmed, bool_query, fetch_per_api, year_filter, oa_filter, progress_callback): "PubMed"
        }
        for future in as_completed(futures):
            res = future.result()
            if res: results.extend(res)
            
    if progress_callback: progress_callback(f"[Phase 3] Deduplikasi hasil dari {len(results)} jurnal...")
    unique_results = deduplicate_results(results)
    
    if skip_ranking:
        # Jika bibliometrik, lewati AI ranking dan kembalikan langsung (urutkan berdasarkan sitasi)
        if progress_callback: progress_callback(f"[Phase 4] Melewati Semantic Ranking untuk mode Bibliometrik...")
        unique_results = sorted(unique_results, key=lambda x: x['citations'], reverse=True)
        final_results = unique_results[:max_results]
    else:
        final_results = rank_results(unique_results, intent, keyword, max_results, progress_callback)
    
    
    if progress_callback: progress_callback("[Done] Proses pipeline selesai.")
    if return_metadata:
        return final_results, {
            "english_query": english_query,
            "bool_query": bool_query,
            "intent": intent
        }
    return final_results
