import os
import json
import pandas as pd
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.signal import savgol_filter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx

try:
    from pyvis.network import Network
    PYVIS_AVAILABLE = True
except ImportError:
    PYVIS_AVAILABLE = False

try:
    from jinja2 import Template
    JINJA_AVAILABLE = True
except ImportError:
    JINJA_AVAILABLE = False

# ==========================================
# Modul A: Data Harmonization
# ==========================================

def baseline_als(y, lam, p, niter=10):
    L = len(y)
    D = sparse.diags([1, -2, 1], [0, 1, 2], shape=(L - 2, L))
    w = np.ones(L)
    for i in range(niter):
        W = sparse.spdiags(w, 0, L, L)
        Z = W + lam * D.dot(D.T)
        z = spsolve(Z, w * y)
        w = p * (y > z) + (1 - p) * (y < z)
    return z

def harmonize_data(input_csv: str, output_csv: str, delimiter: str = ',', strategy: str = 'mean', do_baseline: bool = True, baseline_method: str = 'als', lam: int = 100000, p: float = 0.01) -> str:
    if not os.path.exists(input_csv):
        return f"[Error] File input tidak ditemukan: {input_csv}"
    
    df = pd.read_csv(input_csv, delimiter=delimiter)
    
    # Missing Value Handling
    for col in df.columns:
        if df[col].isnull().any():
            if strategy == "drop":
                df = df.dropna(subset=[col])
            elif strategy == "mean" and pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].mean())
            elif strategy == "median" and pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].median())
                
    # Baseline correction for numeric columns
    if do_baseline:
        for col in df.select_dtypes(include=[np.number]).columns:
            y = df[col].values
            if baseline_method == 'als':
                baseline = baseline_als(y, lam, p)
                df[col] = y - baseline
            elif baseline_method == 'polynomial':
                x = np.arange(len(y))
                poly_coefs = np.polyfit(x, y, 2)
                baseline = np.polyval(poly_coefs, x)
                df[col] = y - baseline
                
    os.makedirs(os.path.dirname(output_csv) if os.path.dirname(output_csv) else '.', exist_ok=True)
    df.to_csv(output_csv, index=False)
    return f"Data berhasil diharmonisasikan dan disimpan ke {output_csv}."

# ==========================================
# Modul B: Network Rendering
# ==========================================

def render_network(input_csv: str, output_tiff: str, output_html: str, source_col: str, target_col: str, weight_col: str = None, min_weight: float = 0.0, layout: str = 'spring', nodes_csv: str = None) -> str:
    if not os.path.exists(input_csv):
        return f"[Error] File input tidak ditemukan: {input_csv}"
        
    df = pd.read_csv(input_csv)
    if source_col not in df.columns or target_col not in df.columns:
        if len(df.columns) >= 2:
            source_col = df.columns[0]
            target_col = df.columns[1]
        else:
            return f"[Error] Kolom '{source_col}' atau '{target_col}' tidak ada."
        
    if weight_col and weight_col in df.columns:
        df = df[pd.to_numeric(df[weight_col], errors='coerce') >= min_weight]
        
    G = nx.Graph()
    for _, row in df.iterrows():
        w = float(row[weight_col]) if weight_col and weight_col in df.columns else 1.0
        e_attr = row.to_dict()
        for c in [weight_col, source_col, target_col]:
            if c in e_attr: del e_attr[c]
        G.add_edge(str(row[source_col]), str(row[target_col]), weight=w, **e_attr)
        
    if G.number_of_nodes() == 0:
        return "[Error] Jaringan kosong. Turunkan min_weight atau periksa data."
        
    if layout == "spring":
        pos = nx.spring_layout(G, k=0.15, seed=42)
    elif layout == "circular":
        pos = nx.circular_layout(G)
    elif layout == "kamada_kawai":
        pos = nx.kamada_kawai_layout(G)
    else:
        pos = nx.spring_layout(G)
        
    # ---- TIFF Static Export ----
    fig, ax = plt.subplots(figsize=(10, 10))
    degrees = dict(G.degree())
    node_sizes = [degrees[n] * 30 for n in G.nodes()]
    
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color='#1f77b4', alpha=0.85, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color='#cbd5e1', alpha=0.5, ax=ax)
    high_degree = {n: n for n, d in degrees.items() if d > np.percentile(list(degrees.values()), 80) if len(degrees) > 5}
    if not high_degree and len(degrees) <= 5:
        high_degree = {n: n for n in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=high_degree, font_size=8, ax=ax)
    
    ax.axis('off')
    plt.tight_layout()
    if output_tiff:
        os.makedirs(os.path.dirname(output_tiff) if os.path.dirname(output_tiff) else '.', exist_ok=True)
        plt.savefig(output_tiff, format='tiff', dpi=300, bbox_inches='tight')
    plt.close()
    
    msg = f"Network statis diekspor ke {output_tiff}." if output_tiff else ""
    
    # ---- Custom D3.js HTML Interactive Export ----
    if output_html:
        betweenness = nx.betweenness_centrality(G)
        clustering = nx.clustering(G)
        
        node_attrs = {}
        if nodes_csv and os.path.exists(nodes_csv):
            df_nodes = pd.read_csv(nodes_csv)
            if len(df_nodes.columns) > 0:
                node_id_col = df_nodes.columns[0]
                df_nodes = df_nodes.fillna("")
                df_nodes[node_id_col] = df_nodes[node_id_col].astype(str)
                node_attrs = df_nodes.set_index(node_id_col).to_dict('index')

        nodes_data = []
        for node in G.nodes():
            n_data = {
                "id": node,
                "degree": degrees[node],
                "betweenness": round(betweenness.get(node, 0), 4),
                "clustering": round(clustering.get(node, 0), 4),
            }
            if node in node_attrs:
                n_data["details"] = node_attrs[node]
            nodes_data.append(n_data)
        
        edges_data = []
        all_weights = []
        for u, v, data in G.edges(data=True):
            w = data.get('weight', 1.0)
            all_weights.append(w)
            e_data = {"source": u, "target": v, "weight": round(w, 4)}
            e_details = {k: v for k, v in data.items() if k != 'weight' and k != 'title'}
            if e_details:
                e_data["details"] = e_details
            edges_data.append(e_data)
        
        max_weight = max(all_weights) if all_weights else 1.0
        min_weight_val = min(all_weights) if all_weights else 0.0
        density = round(nx.density(G), 4)
        n_nodes = G.number_of_nodes()
        n_edges = G.number_of_edges()
        
        step = round((max_weight - min_weight_val) / 100, 4) if max_weight != min_weight_val else 0.01

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Network Visualization | Biopygeon</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Inter',sans-serif;background:#0f172a;color:#e2e8f0;display:flex;height:100vh;overflow:hidden;}}
#sidebar{{width:290px;min-width:290px;background:#1e293b;border-right:1px solid #334155;display:flex;flex-direction:column;overflow-y:auto;z-index:10;}}
.sb-header{{padding:18px;background:linear-gradient(135deg,#0f2744,#0f172a);border-bottom:1px solid #334155;}}
.sb-header h2{{font-size:13px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#38bdf8;margin-bottom:3px;}}
.sb-header p{{font-size:11px;color:#475569;}}
.section{{padding:14px 16px;border-bottom:1px solid #0f172a;}}
.sec-title{{font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#475569;margin-bottom:10px;}}
.ctrl-row{{margin-bottom:10px;}}
.ctrl-lbl{{display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;margin-bottom:4px;}}
.ctrl-lbl .v{{color:#38bdf8;font-weight:600;font-size:12px;}}
input[type=range]{{width:100%;-webkit-appearance:none;height:3px;border-radius:2px;background:#334155;outline:none;cursor:pointer;}}
input[type=range]::-webkit-slider-thumb{{-webkit-appearance:none;width:13px;height:13px;border-radius:50%;background:#38bdf8;cursor:pointer;transition:transform .1s;}}
input[type=range]::-webkit-slider-thumb:hover{{transform:scale(1.25);}}
select,input[type=text]{{width:100%;background:#0f172a;border:1px solid #334155;color:#e2e8f0;padding:6px 10px;border-radius:6px;font-size:11px;font-family:'Inter',sans-serif;cursor:pointer;outline:none;}}
select:focus,input[type=text]:focus{{border-color:#38bdf8;}}
input[type=text]::placeholder{{color:#334155;}}
.clr-grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:5px;margin-bottom:10px;}}
.clr-dot{{width:22px;height:22px;border-radius:50%;cursor:pointer;border:2px solid transparent;transition:transform .15s,border-color .15s;}}
.clr-dot:hover{{transform:scale(1.2);}}
.clr-dot.active{{border-color:#fff;}}
#node-info{{background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;padding:11px;min-height:70px;font-size:11px;color:#334155;}}
#node-info.live{{color:#e2e8f0;}}
.sr{{display:flex;justify-content:space-between;margin-bottom:4px;font-size:11px;}}
.sl{{color:#64748b;}}.sv{{color:#38bdf8;font-weight:600;}}
.btn-grid{{display:grid;grid-template-columns:1fr 1fr;gap:7px;}}
.btn{{padding:7px 10px;border-radius:6px;border:1px solid #334155;background:#0f172a;color:#64748b;font-size:11px;font-weight:500;cursor:pointer;font-family:'Inter',sans-serif;transition:all .15s;text-align:center;}}
.btn:hover{{background:#1e293b;color:#e2e8f0;border-color:#475569;}}
.btn.pri{{background:linear-gradient(135deg,#0ea5e9,#38bdf8);border:none;color:#fff;font-weight:700;}}
.btn.pri:hover{{opacity:.88;transform:translateY(-1px);}}
.btn.full{{grid-column:1/-1;}}
.chk{{display:flex;align-items:center;gap:7px;margin-bottom:7px;font-size:11px;color:#94a3b8;cursor:pointer;}}
.chk input{{accent-color:#38bdf8;cursor:pointer;}}
#main{{flex:1;position:relative;overflow:hidden;}}
#nsvg{{width:100%;height:100%;}}
#stat-bar{{position:absolute;bottom:14px;left:50%;transform:translateX(-50%);display:flex;gap:16px;background:rgba(15,23,42,.88);backdrop-filter:blur(10px);border:1px solid #334155;border-radius:12px;padding:9px 18px;font-size:12px;white-space:nowrap;}}
.schip{{display:flex;align-items:center;gap:5px;}}
.schip .dot{{width:7px;height:7px;border-radius:50%;}}
.schip .n{{font-weight:700;color:#f8fafc;}}.schip .l{{color:#475569;}}
#tt{{position:absolute;background:rgba(15,23,42,.96);border:1px solid #334155;border-radius:8px;padding:10px 14px;font-size:11px;pointer-events:none;opacity:0;transition:opacity .15s;max-width:200px;z-index:200;}}
#tt .ttt{{font-weight:700;color:#38bdf8;margin-bottom:5px;font-size:13px;}}
#legend{{position:absolute;top:14px;right:14px;background:rgba(30,41,59,.92);border:1px solid #334155;border-radius:8px;padding:11px 13px;font-size:11px;backdrop-filter:blur(8px);}}
#legend .lt{{font-weight:600;color:#475569;margin-bottom:7px;letter-spacing:.05em;text-transform:uppercase;font-size:10px;}}
.lr{{display:flex;align-items:center;gap:7px;margin-bottom:3px;color:#94a3b8;}}
</style>
</head>
<body>
<div id="sidebar">
  <div class="sb-header">
    <h2>🧬 Network Explorer</h2>
    <p>Biopygeon SSN Visualizer</p>
  </div>

  <div class="section">
    <div class="sec-title">Warna Node</div>
    <div class="clr-grid" id="cp">
      <div class="clr-dot active" style="background:#38bdf8" data-c="#38bdf8"></div>
      <div class="clr-dot" style="background:#818cf8" data-c="#818cf8"></div>
      <div class="clr-dot" style="background:#34d399" data-c="#34d399"></div>
      <div class="clr-dot" style="background:#fb923c" data-c="#fb923c"></div>
      <div class="clr-dot" style="background:#f472b6" data-c="#f472b6"></div>
      <div class="clr-dot" style="background:#facc15" data-c="#facc15"></div>
    </div>
    <div class="ctrl-row">
      <div class="ctrl-lbl">Ukuran Node <span class="v" id="vns">1.0x</span></div>
      <input type="range" id="sNS" min="0.3" max="3" step="0.1" value="1">
    </div>
    <div class="ctrl-row">
      <div class="ctrl-lbl">Opacity Node <span class="v" id="vno">85%</span></div>
      <input type="range" id="sNO" min="0.1" max="1" step="0.05" value="0.85">
    </div>
    <div class="ctrl-row">
      <div class="ctrl-lbl">Ukuran Label <span class="v" id="vfs">11px</span></div>
      <input type="range" id="sFS" min="6" max="22" step="1" value="11">
    </div>
  </div>

  <div class="section">
    <div class="sec-title">Edge</div>
    <div class="ctrl-row">
      <div class="ctrl-lbl">Min. Bobot <span class="v" id="vmw">{round(min_weight_val,2)}</span></div>
      <input type="range" id="sMW" min="{round(min_weight_val,4)}" max="{round(max_weight,4)}" step="{step}" value="{round(min_weight_val,4)}">
    </div>
    <div class="ctrl-row">
      <div class="ctrl-lbl">Ketebalan Edge <span class="v" id="vet">1.0x</span></div>
      <input type="range" id="sET" min="0.2" max="5" step="0.1" value="1">
    </div>
    <div class="ctrl-row">
      <div class="ctrl-lbl">Opacity Edge <span class="v" id="veo">50%</span></div>
      <input type="range" id="sEO" min="0.05" max="1" step="0.05" value="0.5">
    </div>
    <label class="chk"><input type="checkbox" id="cbL" checked> Tampilkan Label</label>
    <label class="chk"><input type="checkbox" id="cbW"> Bobot pada Edge</label>
  </div>

  <div class="section">
    <div class="sec-title">Filter & Layout</div>
    <input type="text" id="srch" placeholder="Cari node..." style="margin-bottom:8px">
    <div class="ctrl-row">
      <div class="ctrl-lbl">Min. Degree <span class="v" id="vmd">1</span></div>
      <input type="range" id="sMD" min="1" max="10" step="1" value="1">
    </div>
    <div class="ctrl-row">
      <div class="ctrl-lbl">Gaya Simulasi <span class="v" id="vst">-200</span></div>
      <input type="range" id="sST" min="-700" max="-30" step="10" value="-200">
    </div>
    <div class="ctrl-row">
      <div class="ctrl-lbl" style="margin-bottom:6px">Tema Latar</div>
      <select id="selBg">
        <option value="#0f172a">Gelap (default)</option>
        <option value="#1a1a2e">Midnight Blue</option>
        <option value="#ffffff">Terang</option>
        <option value="#f8fafc">Abu-abu terang</option>
        <option value="#0d1117">GitHub Dark</option>
      </select>
    </div>
  </div>

  <div class="section">
    <div class="sec-title">Detail Node</div>
    <div id="node-info">Klik node untuk detail…</div>
  </div>

  <div class="section">
    <div class="sec-title">Ekspor</div>
    <div class="btn-grid">
      <button class="btn" onclick="xSVG()">📄 SVG</button>
      <button class="btn" onclick="xPNG()">🖼️ PNG</button>
      <button class="btn" onclick="xCSV()">📊 CSV</button>
      <button class="btn" onclick="xJSON()">📦 JSON</button>
      <button class="btn full pri" onclick="resetView()">↺ Reset Tampilan</button>
    </div>
  </div>
</div>

<div id="main">
  <svg id="nsvg"></svg>
  <div id="tt"><div class="ttt" id="ttT"></div><div id="ttB"></div></div>
  <div id="legend">
    <div class="lt">Legenda</div>
    <div class="lr"><svg width="14" height="14"><circle cx="7" cy="7" r="6" fill="#38bdf8" opacity=".9"/></svg> Node (ukuran=degree)</div>
    <div class="lr"><svg width="14" height="3"><line x1="0" y1="1.5" x2="14" y2="1.5" stroke="#94a3b8" stroke-width="1.5"/></svg> Edge (tebal=bobot)</div>
  </div>
  <div id="stat-bar">
    <div class="schip"><div class="dot" style="background:#38bdf8"></div><span class="n">{n_nodes}</span><span class="l">Nodes</span></div>
    <div class="schip"><div class="dot" style="background:#818cf8"></div><span class="n" id="sb-e">{n_edges}</span><span class="l">Edges</span></div>
    <div class="schip"><div class="dot" style="background:#34d399"></div><span class="n" id="sb-v">{n_nodes}</span><span class="l">Visible</span></div>
    <div class="schip"><div class="dot" style="background:#fb923c"></div><span class="n">{density}</span><span class="l">Density</span></div>
  </div>
</div>

<script>
const RN = {json.dumps(nodes_data)};
const RE = {json.dumps(edges_data)};
const WMAX = {round(max_weight,4)};
const WMIN = {round(min_weight_val,4)};

let NC="#38bdf8", sim, svg2, g2, LS, NS, LBS, ELS;
let CN=[], CE=[];

const W=()=>document.getElementById('main').clientWidth;
const H=()=>document.getElementById('main').clientHeight;

svg2=d3.select("#nsvg").call(d3.zoom().scaleExtent([0.08,10]).on("zoom",e=>g2.attr("transform",e.transform)));
g2=svg2.append("g");

const dfs=svg2.append("defs");
const gf=dfs.append("filter").attr("id","glow").attr("x","-40%").attr("y","-40%").attr("width","180%").attr("height","180%");
gf.append("feGaussianBlur").attr("stdDeviation","5").attr("result","cb");
const fm=gf.append("feMerge");
fm.append("feMergeNode").attr("in","cb");
fm.append("feMergeNode").attr("in","SourceGraphic");

function buildGraph(){{
  const md=+document.getElementById('sMD').value;
  const mw=+document.getElementById('sMW').value;
  const q=document.getElementById('srch').value.toLowerCase();
  let fe=RE.filter(e=>e.weight>=mw);
  const dc={{}};
  fe.forEach(e=>{{dc[e.source]=(dc[e.source]||0)+1;dc[e.target]=(dc[e.target]||0)+1;}});
  let fn=RN.filter(n=>(dc[n.id]||0)>=md);
  if(q) fn=fn.filter(n=>n.id.toLowerCase().includes(q));
  const ns=new Set(fn.map(n=>n.id));
  fe=fe.filter(e=>ns.has(e.source)&&ns.has(e.target));
  CN=fn; CE=fe;
  document.getElementById('sb-v').textContent=fn.length;
  document.getElementById('sb-e').textContent=fe.length;
  render();
}}

function render(){{
  const ns=+document.getElementById('sNS').value;
  const no=+document.getElementById('sNO').value;
  const et=+document.getElementById('sET').value;
  const eo=+document.getElementById('sEO').value;
  const fs=+document.getElementById('sFS').value;
  const sl=document.getElementById('cbL').checked;
  const sw=document.getElementById('cbW').checked;
  const st=+document.getElementById('sST').value;
  
  const mx=d3.max(CN,n=>n.degree)||1;
  const rs=d3.scaleSqrt().domain([1,mx]).range([6*ns,24*ns]);
  const wm=d3.min(CE,e=>e.weight)||0;
  const wx=d3.max(CE,e=>e.weight)||1;
  const ws=d3.scaleLinear().domain([wm,wx]).range([0.8*et,4.5*et]);
  
  const bg = document.getElementById('selBg').value;
  const isLight = bg === '#ffffff' || bg === '#f8fafc';
  const txtColor = isLight ? '#0f172a' : '#e2e8f0';
  const edgeColor = isLight ? '#64748b' : '#94a3b8';
  const strokeColor = isLight ? "rgba(0,0,0,0.2)" : "rgba(255,255,255,0.3)";

  g2.selectAll("*").remove();
  if(sim) sim.stop();
  
  const nodes=CN.map(d=>Object.assign({{}},d));
  const edges=CE.map(d=>Object.assign({{}},d));
  
  sim=d3.forceSimulation(nodes)
    .force("link",d3.forceLink(edges).id(d=>d.id).distance(90))
    .force("charge",d3.forceManyBody().strength(st))
    .force("center",d3.forceCenter(W()/2,H()/2))
    .force("collide",d3.forceCollide().radius(d=>rs(d.degree||1)+6));
  
  LS=g2.append("g").selectAll("line").data(edges).join("line")
    .attr("stroke",edgeColor).attr("stroke-width",d=>ws(d.weight)).attr("stroke-opacity",eo);
  LS.append("title").text(d => {{
      let txt = `Weight: ${{d.weight.toFixed(4)}}`;
      if (d.details) {{
          for (const k in d.details) {{ txt += `\n${{k}}: ${{d.details[k]}}`; }}
      }}
      return txt;
  }});
  
  ELS=g2.append("g").selectAll("text.el").data(sw?edges:[]).join("text").attr("class","el")
    .text(d=>d.weight.toFixed(2)).attr("font-size","9px").attr("fill",txtColor).attr("text-anchor","middle");
  
  NS=g2.append("g").selectAll("circle").data(nodes).join("circle")
    .attr("r",d=>rs(d.degree||1)).attr("fill",NC).attr("opacity",no)
    .attr("stroke",strokeColor).attr("stroke-width",1.2)
    .style("cursor","pointer")
    .on("mouseover",onHov).on("mouseout",onOut).on("click",onClick)
    .call(d3.drag()
      .on("start",(e,d)=>{{if(!e.active)sim.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y;}})
      .on("drag",(e,d)=>{{d.fx=e.x;d.fy=e.y;}})
      .on("end",(e,d)=>{{if(!e.active)sim.alphaTarget(0);d.fx=null;d.fy=null;}}));
  
  LBS=g2.append("g").selectAll("text.nl").data(sl?nodes:[]).join("text").attr("class","nl")
    .text(d=>d.id).attr("font-size",`${{fs}}px`).attr("fill",txtColor)
    .attr("font-family","Inter,sans-serif").attr("font-weight","600")
    .attr("text-anchor","middle").style("pointer-events","none");
  
  sim.on("tick",()=>{{
    LS.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y).attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);
    ELS.attr("x",d=>((d.source.x||0)+(d.target.x||0))/2).attr("y",d=>((d.source.y||0)+(d.target.y||0))/2);
    NS.attr("cx",d=>d.x).attr("cy",d=>d.y);
    LBS.attr("x",d=>d.x).attr("y",d=>d.y-(rs(d.degree||1)+4));
  }});
}}

function onHov(e,d){{
  d3.select(this).attr("filter","url(#glow)").attr("stroke","#fff").attr("stroke-width",2);
  const tt=document.getElementById('tt');
  document.getElementById('ttT').textContent=d.id;
  let extra = "";
  if(d.details) {{
      for(const k in d.details) {{
          extra += `<div class="sr"><span class="sl">${{k}}</span><span class="sv">${{d.details[k]}}</span></div>`;
      }}
  }}
  document.getElementById('ttB').innerHTML=`<div class="sr"><span class="sl">Degree</span><span class="sv">${{d.degree}}</span></div><div class="sr"><span class="sl">Betweenness</span><span class="sv">${{d.betweenness}}</span></div><div class="sr"><span class="sl">Clustering</span><span class="sv">${{d.clustering}}</span></div>` + extra;
  tt.style.opacity=1;
  tt.style.left=(e.clientX-310)+'px';
  tt.style.top=(e.clientY-20)+'px';
}}
function onOut(e,d){{
  const bg = document.getElementById('selBg').value;
  const isLight = bg === '#ffffff' || bg === '#f8fafc';
  const strokeColor = isLight ? "rgba(0,0,0,0.2)" : "rgba(255,255,255,0.3)";
  d3.select(this).attr("filter",null).attr("stroke",strokeColor).attr("stroke-width",1.2);
  document.getElementById('tt').style.opacity=0;
}}

function onClick(e,d){{
  const bg = document.getElementById('selBg').value;
  const isLight = bg === '#ffffff' || bg === '#f8fafc';
  const edgeColor = isLight ? '#64748b' : '#94a3b8';

  NS.attr("opacity",0.12);
  d3.select(this).attr("opacity",1).attr("filter","url(#glow)");
  LS.each(function(l){{
    const ok=l.source.id===d.id||l.target.id===d.id;
    d3.select(this).attr("stroke-opacity",ok?1:0.04).attr("stroke",ok?NC:edgeColor);
  }});
  NS.each(function(n){{
    const isN=CE.some(ex=>(ex.source===d.id&&ex.target===n.id)||(ex.target===d.id&&ex.source===n.id));
    d3.select(this).attr("opacity",n.id===d.id?1:isN?0.9:0.1);
  }});
  const nbrs=CE.filter(ex=>ex.source===d.id||ex.target===d.id).map(ex=>ex.source===d.id?ex.target:ex.source);
  const inf=document.getElementById('node-info');
  inf.className='live';
  let extra2 = "";
  if(d.details) {{
      for(const k in d.details) {{
          extra2 += `<div class="sr"><span class="sl">${{k}}</span><span class="sv">${{d.details[k]}}</span></div>`;
      }}
  }}
  inf.innerHTML=`<div class="sr"><span class="sl">Node</span><span class="sv" style="color:#38bdf8;font-weight:700">${{d.id}}</span></div><div class="sr"><span class="sl">Degree</span><span class="sv">${{d.degree}}</span></div><div class="sr"><span class="sl">Betweenness</span><span class="sv">${{d.betweenness}}</span></div><div class="sr"><span class="sl">Clustering</span><span class="sv">${{d.clustering}}</span></div>` + extra2 + `<div style="margin-top:7px;font-size:10px;color:#475569">Neighbors:<br><span style="color:#cbd5e1">${{nbrs.join(', ')||'-'}}</span></div>`;
}}

function resetView(){{
  const bg = document.getElementById('selBg').value;
  const isLight = bg === '#ffffff' || bg === '#f8fafc';
  const edgeColor = isLight ? '#64748b' : '#94a3b8';
  const strokeColor = isLight ? "rgba(0,0,0,0.2)" : "rgba(255,255,255,0.3)";

  svg2.transition().duration(500).call(d3.zoom().transform,d3.zoomIdentity);
  NS&&NS.attr("opacity",+document.getElementById('sNO').value).attr("filter",null).attr("stroke",strokeColor).attr("stroke-width",1.2);
  LS&&LS.attr("stroke-opacity",+document.getElementById('sEO').value).attr("stroke",edgeColor);
  document.getElementById('node-info').innerHTML="Klik node untuk detail…";
  document.getElementById('node-info').className='';
}}

// Export
function xSVG(){{const el=document.getElementById('nsvg');const d2=new XMLSerializer().serializeToString(el);const b=new Blob([d2],{{type:'image/svg+xml'}});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='network.svg';a.click();}}
function xPNG(){{const el=document.getElementById('nsvg');const d2=new XMLSerializer().serializeToString(el);const c=document.createElement('canvas');c.width=W()*2;c.height=H()*2;const ctx=c.getContext('2d');ctx.scale(2,2);ctx.fillStyle=document.body.style.background||'#0f172a';ctx.fillRect(0,0,W(),H());const img=new Image();img.onload=()=>{{ctx.drawImage(img,0,0);const a=document.createElement('a');a.href=c.toDataURL('image/png');a.download='network.png';a.click();}};img.src='data:image/svg+xml;base64,'+btoa(unescape(encodeURIComponent(d2)));}}
function xCSV(){{let c='source,target,weight\\n';CE.forEach(e=>c+=`${{e.source.id||e.source}},${{e.target.id||e.target}},${{e.weight}}\\n`);const b=new Blob([c],{{type:'text/csv'}});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='network_edges.csv';a.click();}}
function xJSON(){{const d2={{nodes:CN,edges:CE.map(e=>({{"source":e.source.id||e.source,"target":e.target.id||e.target,"weight":e.weight}}))}};const b=new Blob([JSON.stringify(d2,null,2)],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='network.json';a.click();}}

// Wire controls
document.getElementById('cp').querySelectorAll('.clr-dot').forEach(dot=>{{
  dot.addEventListener('click',()=>{{
    document.querySelectorAll('.clr-dot').forEach(x=>x.classList.remove('active'));
    dot.classList.add('active');NC=dot.dataset.c;render();
  }});
}});

const sliders=[
  ['sNS','vns',v=>v+'x'],['sNO','vno',v=>Math.round(v*100)+'%'],
  ['sFS','vfs',v=>v+'px'],['sMW','vmw',v=>(+v).toFixed(2)],
  ['sET','vet',v=>v+'x'],['sEO','veo',v=>Math.round(v*100)+'%'],
  ['sMD','vmd',v=>v],['sST','vst',v=>v],
];
sliders.forEach(([id,vid,fmt])=>{{
  const el=document.getElementById(id);
  const vel=document.getElementById(vid);
  el.addEventListener('input',()=>{{
    if(vel) vel.textContent=fmt(el.value);
    if(['sMD','sST','sMW'].includes(id)) buildGraph(); else render();
  }});
}});
document.getElementById('cbL').addEventListener('change',render);
document.getElementById('cbW').addEventListener('change',render);
document.getElementById('srch').addEventListener('input',buildGraph);
document.getElementById('selBg').addEventListener('change',e=>{{
  document.body.style.background=e.target.value;
  document.getElementById('nsvg').style.background=e.target.value;
  render();
}});

buildGraph();
</script>
</body>
</html>"""
        os.makedirs(os.path.dirname(output_html) if os.path.dirname(output_html) else '.', exist_ok=True)
        with open(output_html, 'w', encoding='utf-8') as f:
            f.write(html)
        msg += f" Visualisasi interaktif D3.js premium diekspor ke {output_html}."
        
    return msg

# ==========================================
# Modul C: Q1 Figure Formatting
# ==========================================

def plot_q1_figure(input_csv: str, output_html: str, plot_type: str, x_col: str, y_col: str, hue_col: str = None) -> str:
    import plotly.express as px
    import plotly.graph_objects as go
    from scipy import stats
    import itertools

    if not os.path.exists(input_csv):
        return f"[Error] File input tidak ditemukan: {input_csv}"
        
    df = pd.read_csv(input_csv)
    
    # Bersihkan NaN pada kolom x dan y
    df = df.dropna(subset=[x_col, y_col])
    
    groups = df[x_col].unique()
    group_data = [df[df[x_col] == g][y_col].values for g in groups]
    
    # --- UJI STATISTIK CERDAS (SMART-STATS ENGINE) ---
    stat_msg = ""
    p_values = {}
    
    # 1. Uji Asumsi (Normalitas & Homogenitas Varians)
    # Shapiro-Wilk (cek normalitas tiap grup, jika ada satu yang < 0.05, maka distribusinya dianggap tidak normal)
    is_normal = True
    for d in group_data:
        if len(d) >= 3:
            _, p_shapiro = stats.shapiro(d)
            if p_shapiro < 0.05:
                is_normal = False
                break
        else:
            # Jika n < 3, kita asumsikan tidak normal agar aman
            is_normal = False
            break
            
    # Levene's test (cek kesamaan varians antar grup)
    is_equal_var = True
    if len(group_data) >= 2 and all(len(d) >= 3 for d in group_data):
        _, p_levene = stats.levene(*group_data)
        if p_levene < 0.05:
            is_equal_var = False
            
    if len(groups) == 2:
        if is_normal and is_equal_var:
            test_name = "Student's t-test"
            _, p_val = stats.ttest_ind(group_data[0], group_data[1], equal_var=True)
        elif is_normal and not is_equal_var:
            test_name = "Welch's t-test"
            _, p_val = stats.ttest_ind(group_data[0], group_data[1], equal_var=False)
        else:
            test_name = "Mann-Whitney U"
            _, p_val = stats.mannwhitneyu(group_data[0], group_data[1])
            
        p_values[(groups[0], groups[1])] = p_val
        stat_msg = f"{test_name} p-value: {p_val:.4e}"
        
    elif len(groups) > 2:
        if is_normal and is_equal_var:
            test_name = "One-Way ANOVA"
            _, p_val = stats.f_oneway(*group_data)
        else:
            test_name = "Kruskal-Wallis"
            _, p_val = stats.kruskal(*group_data)
            
        stat_msg = f"{test_name} p-value: {p_val:.4e}"
        
        # Post-hoc analisis (jika p < 0.05) vs Kontrol
        if p_val < 0.05:
            control = groups[0]
            for i in range(1, len(groups)):
                if is_normal and is_equal_var:
                    _, pw_pval = stats.ttest_ind(df[df[x_col] == control][y_col], group_data[i], equal_var=True)
                elif is_normal and not is_equal_var:
                    _, pw_pval = stats.ttest_ind(df[df[x_col] == control][y_col], group_data[i], equal_var=False)
                else:
                    _, pw_pval = stats.mannwhitneyu(df[df[x_col] == control][y_col], group_data[i])
                p_values[(control, groups[i])] = pw_pval

    # --- PLOTLY RENDERING ---
    if plot_type == 'boxplot':
        fig = px.box(df, x=x_col, y=y_col, color=hue_col, title=f"Auto-GraphPad: {plot_type.capitalize()}")
    elif plot_type == 'violin':
        fig = px.violin(df, x=x_col, y=y_col, color=hue_col, box=True, title=f"Auto-GraphPad: {plot_type.capitalize()}")
    elif plot_type == 'scatter':
        fig = px.strip(df, x=x_col, y=y_col, color=hue_col, title=f"Auto-GraphPad: {plot_type.capitalize()}")
    else: # bar
        # Bar chart with error bars
        grouped = df.groupby(x_col)[y_col].agg(['mean', 'sem']).reset_index()
        fig = px.bar(grouped, x=x_col, y='mean', error_y='sem', title=f"Auto-GraphPad: {plot_type.capitalize()}")
        
    fig.update_layout(
        template='plotly_white',
        annotations=[
            dict(
                x=0.5,
                y=1.05,
                xref="paper",
                yref="paper",
                text=f"<i>{stat_msg}</i>",
                showarrow=False,
                font=dict(size=12, color="gray")
            )
        ]
    )
    
    # --- ANOTASI P-VALUE (BRACKETS) ---
    if p_values:
        y_max = df[y_col].max()
        y_range = df[y_col].max() - df[y_col].min()
        step = y_range * 0.1
        
        current_y = y_max + step
        for (g1, g2), p in p_values.items():
            if p < 0.001: star = "***"
            elif p < 0.01: star = "**"
            elif p < 0.05: star = "*"
            else: star = "ns"
            
            fig.add_shape(type="line", x0=g1, x1=g1, y0=current_y, y1=current_y + step*0.2, line=dict(color="black", width=1))
            fig.add_shape(type="line", x0=g2, x1=g2, y0=current_y, y1=current_y + step*0.2, line=dict(color="black", width=1))
            fig.add_shape(type="line", x0=g1, x1=g2, y0=current_y + step*0.2, y1=current_y + step*0.2, line=dict(color="black", width=1))
            
            fig.add_annotation(x=(list(groups).index(g1) + list(groups).index(g2))/2, y=current_y + step*0.4, text=star, showarrow=False, font=dict(size=14))
            current_y += step * 0.8

    os.makedirs(os.path.dirname(output_html) if os.path.dirname(output_html) else '.', exist_ok=True)
    config = {
        'toImageButtonOptions': {
            'format': 'svg',
            'filename': f'q1_{plot_type}_figure',
            'height': 800,
            'width': 1000,
            'scale': 4
        }
    }
    fig.write_html(output_html, config=config)
    
    return f"Figure Q1 ({plot_type}) dengan uji statistik berhasil diekspor ke {output_html}. Analisis: {stat_msg}"

# ==========================================
# Modul D: Methodology Draft
# ==========================================

def generate_methodology(output_txt: str, baseline_method: str = 'als', plot_type: str = 'boxplot', journal: str = 'nature') -> str:
    text = (
        f"Data harmonization was performed using {baseline_method.upper()} baseline correction. "
        f"Visualizations and network topology were rendered programmatically. "
        f"High-resolution figures ({plot_type}) were generated adhering to {journal.capitalize()} publication guidelines."
    )
    
    if JINJA_AVAILABLE:
        template = Template(text)
        rendered = template.render()
    else:
        rendered = text
        
    os.makedirs(os.path.dirname(output_txt) if os.path.dirname(output_txt) else '.', exist_ok=True)
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(rendered)
        
    return f"Metodologi tersimpan di {output_txt}."
