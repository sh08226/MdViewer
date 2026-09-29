# -*- coding: utf-8 -*-
"""Markdown 查看器前端（纸感浅色 + 深色双主题，纯内联 HTML/CSS/JS，零外部依赖）。"""

INDEX_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Markdown 查看器</title>
<link rel="icon" href="__ICONURI__" />
<style>
  :root{
    /* 默认主题：纸感浅色（暖白 + 墨色 + 低饱和靛蓝，界面退后、内容向前） */
    --bg0:#fbfaf8; --bg1:#f6f5f2; --bg2:#f2f1ec;
    --panel:#f7f6f3; --panel2:#fbfaf8;
    --line:rgba(32,36,42,.09); --line2:rgba(32,36,42,.18);
    --txt:#24292f; --txt2:#57606a; --txt3:#8b949e;
    --cyan:#2f6497; --blue:#3a6ea5; --violet:#8d5f8f; --green:#1f7a4d;
    --accent:#2f6497; --warn:#a9761b; --pink:#b3556e;
    --code-bg:#f3f1ec; --shadow:0 1px 3px rgba(22,26,32,.06), 0 10px 28px rgba(22,26,32,.05);
  }
  html.dark{
    --bg0:#070b1a; --bg1:#0b1230; --bg2:#0e1840;
    --panel:rgba(18,28,66,.72); --panel2:rgba(13,22,54,.86);
    --line:rgba(120,180,255,.20); --line2:rgba(120,180,255,.38);
    --txt:#dbe7ff; --txt2:#9fb6e0; --txt3:#6f86b8;
    --cyan:#35e0ff; --blue:#4d8dff; --violet:#9a7bff; --green:#7ef0a0;
    --accent:#35e0ff; --warn:#ffd24d; --pink:#ff8ad0;
    --code-bg:rgba(8,14,38,.9); --shadow:0 10px 34px rgba(0,8,40,.5);
  }
  *{box-sizing:border-box}
  html,body{height:100%;margin:0}
  body{
    font-family:-apple-system,"Segoe UI","Microsoft YaHei",Roboto,Helvetica,Arial,sans-serif;
    color:var(--txt); background:var(--bg0);
    display:flex; flex-direction:column; height:100vh; overflow:hidden;
  }
  header{
    position:relative; z-index:2; display:flex; align-items:center; gap:14px;
    padding:12px 18px; border-bottom:1px solid var(--line);
    background:linear-gradient(180deg,var(--panel2),var(--panel));
    backdrop-filter:blur(10px); box-shadow:var(--shadow);
  }
  .brand{display:flex; align-items:center; gap:10px; font-weight:800; letter-spacing:.5px}
  .brand .logo{
    width:30px; height:30px; border-radius:7px; display:block; object-fit:contain;
    box-shadow:0 1px 4px rgba(22,26,32,.18);
  }
  .brand b{font-size:16px; color:var(--txt)}
  .spacer{flex:1}
  .btn{
    border:1px solid var(--line2); background:var(--panel); color:var(--txt);
    padding:8px 13px; border-radius:10px; cursor:pointer; font-size:13px; font-weight:700;
    transition:.15s; display:inline-flex; align-items:center; gap:6px;
  }
  .btn:hover{border-color:var(--accent); color:var(--accent)}
  .btn.primary{background:var(--accent); color:#fff; border-color:var(--accent)}
  .btn.primary:hover{background:#285680; color:#fff}
  .search{position:relative}
  .search input{
    width:200px; padding:8px 12px 8px 32px; border-radius:10px; border:1px solid var(--line2);
    background:var(--panel2); color:var(--txt); font-size:13px; outline:none;
  }
  .search input:focus{border-color:var(--accent); box-shadow:0 0 0 3px rgba(47,100,151,.12)}
  .search svg{position:absolute; left:9px; top:50%; transform:translateY(-50%); opacity:.6}
  main{position:relative; z-index:1; flex:1; display:flex; min-height:0}
  aside{
    width:260px; flex:none; border-right:1px solid var(--line); padding:14px 10px;
    overflow:auto; background:var(--panel);
  }
  aside h4{margin:6px 10px 8px; font-size:12px; letter-spacing:1.5px; color:var(--txt3); text-transform:uppercase}
  .toc a{display:block; padding:5px 10px; border-radius:8px; color:var(--txt2);
    font-size:13.5px; text-decoration:none; border-left:2px solid transparent; cursor:pointer; white-space:nowrap; overflow:hidden; text-overflow:ellipsis}
  .toc a:hover{color:var(--accent); background:rgba(47,100,151,.07)}
  .toc a.lv3{padding-left:22px; font-size:12.5px; color:var(--txt3)}
  .toc a.active{border-left-color:var(--accent); color:var(--accent); background:rgba(47,100,151,.09)}
  #preview{
    flex:1; overflow:auto; padding:30px 46px 60px; line-height:1.75; font-size:16px;
  }
  #preview.wide{padding:30px max(8vw,46px) 60px}
  /* Markdown 排版 */
  #preview h1,#preview h2,#preview h3,#preview h4,#preview h5,#preview h6{
    color:var(--txt); line-height:1.3; margin:1.4em 0 .6em; font-weight:800;
    scroll-margin-top:18px;
  }
  #preview h1{font-size:1.85em; padding-bottom:.3em; border-bottom:1px solid var(--line2)}
  #preview h2{font-size:1.5em; padding-bottom:.25em; border-bottom:1px solid var(--line)}
  #preview h3{font-size:1.25em; color:var(--accent)}
  #preview h4{font-size:1.08em; color:var(--blue)}
  #preview p{margin:.7em 0}
  #preview a{color:var(--accent); text-decoration:none; border-bottom:1px dashed rgba(47,100,151,.45)}
  #preview a:hover{border-bottom-style:solid}
  #preview strong{color:#14171c}
  html.dark #preview strong{color:#fff}
  #preview em{color:var(--violet)}
  #preview del{color:var(--txt3)}
  #preview ul,#preview ol{padding-left:1.5em; margin:.6em 0}
  #preview li{margin:.3em 0}
  #preview ul li::marker{color:var(--cyan)}
  #preview ol li::marker{color:var(--blue)}
  #preview blockquote{
    margin:1em 0; padding:10px 16px; border-left:3px solid var(--line2);
    background:var(--panel); border-radius:0 8px 8px 0; color:var(--txt2);
  }
  #preview code{
    font-family:"Cascadia Code",Consolas,"Courier New",monospace; font-size:.9em;
    background:var(--code-bg); padding:2px 6px; border-radius:5px; color:#9a4b58;
    border:1px solid var(--line);
  }
  #preview pre{
    background:var(--code-bg); border:1px solid var(--line); border-radius:10px;
    padding:14px 16px; overflow:auto; margin:1em 0;
  }
  #preview pre code{background:none; border:none; padding:0; color:var(--txt); font-size:13.5px; line-height:1.6}
  #preview table{border-collapse:collapse; width:100%; margin:1em 0; font-size:14.5px;
    border:1px solid var(--line2); border-radius:10px; overflow:hidden}
  #preview th,#preview td{border:1px solid var(--line); padding:8px 12px; text-align:left}
  #preview thead th{background:var(--panel);
    color:var(--txt); font-weight:700}
  html.dark #preview thead th{color:#fff}
  #preview tbody tr:nth-child(even){background:rgba(32,36,42,.025)}
  #preview img{max-width:100%; border-radius:10px; border:1px solid var(--line); margin:.4em 0}
  #preview hr{border:none; border-top:1px solid var(--line2); margin:1.6em 0}
  #preview mark{background:#ffe066; color:#1a1300; border-radius:3px; padding:0 2px}
  html.dark #preview mark{background:var(--warn)}
  /* 空状态 */
  #empty{position:absolute; inset:0; display:grid; place-items:center; text-align:center; z-index:1}
  #empty .card{
    padding:38px 46px; border:1.5px dashed var(--line2); border-radius:18px;
    background:var(--panel); box-shadow:var(--shadow); max-width:440px;
  }
  #empty .big{font-size:54px; margin-bottom:6px}
  #empty h3{margin:.2em 0; font-size:19px}
  #empty p{color:var(--txt2); margin:.4em 0 18px; font-size:14px}
  .hidden{display:none!important}
  /* 拖拽覆盖 */
  #drop{position:fixed; inset:0; z-index:50; display:none; place-items:center;
    background:rgba(7,11,26,.82); backdrop-filter:blur(4px)}
  #drop.show{display:grid}
  #drop .ring{border:3px dashed var(--cyan); border-radius:24px; padding:60px 80px;
    color:var(--cyan); font-size:22px; font-weight:800; box-shadow:0 0 40px rgba(53,224,255,.4)}
  footer{
    position:relative; z-index:2; display:flex; align-items:center; gap:16px;
    padding:7px 18px; font-size:12px; color:var(--txt3);
    border-top:1px solid var(--line); background:var(--panel2);
  }
  footer .dot{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 8px var(--green);transition:.3s}
  footer .dot.bad{background:#ff5d6c;box-shadow:0 0 8px #ff5d6c}
  footer #statusText.bad{color:#ff8a95}
  /* 服务断开遮罩 */
  #down{position:fixed;inset:0;z-index:60;display:none;place-items:center;
    background:rgba(7,11,26,.86);backdrop-filter:blur(5px)}
  #down.show{display:grid}
  #down .card{padding:36px 44px;border:1.5px solid rgba(255,120,130,.45);border-radius:18px;
    background:var(--panel2);box-shadow:var(--shadow);max-width:460px;text-align:center}
  #down .big{font-size:46px;margin-bottom:4px}
  #down h3{margin:.2em 0;font-size:19px;color:#ff8a95}
  #down p{color:var(--txt2);margin:.5em 0 18px;font-size:14px;line-height:1.7}
  #down .row{display:flex;gap:12px;justify-content:center}
  #down .btn.retry{border-color:var(--cyan);color:var(--cyan)}
  @media (max-width:760px){ aside{display:none} .search input{width:130px} }
  @media print{
    /* 隐藏界面元素，只留正文 */
    body::before,header,aside,footer,#empty,#drop,#down{display:none!important}
    html,body{height:auto; overflow:visible; background:#fff!important}
    body{display:block}
    /* 正文强制黑字白底：覆盖渐变字/主题色/发光等所有效果 */
    #preview{overflow:visible; height:auto; padding:0; color:#000!important;
      background:#fff!important; font-size:12.5pt; -webkit-print-color-adjust:exact; print-color-adjust:exact}
    #preview *{
      color:#000!important; -webkit-text-fill-color:#000!important;
      background:transparent!important; box-shadow:none!important; text-shadow:none!important;
      border-color:#bbb!important;
    }
    #preview h1,#preview h2,#preview h3,#preview h4,#preview h5,#preview h6{
      background:none!important; border-bottom:1.5px solid #888!important;
      page-break-after:avoid; color:#000!important;
    }
    #preview a{color:#0645ad!important; border-bottom:none!important; text-decoration:underline!important}
    #preview code,#preview pre{background:#f5f5f5!important; border:1px solid #ddd!important}
    #preview pre code{color:#000!important; background:none!important; border:none!important}
    #preview mark{background:#ffe89c!important; color:#000!important}
    #preview blockquote{border-left:4px solid #999!important; background:#f7f7f7!important;
      border-radius:0!important; color:#333!important}
    #preview table{border:1px solid #999!important; box-shadow:none!important}
    #preview th,#preview td{border:1px solid #999!important; color:#000!important}
    #preview thead th{background:#ececec!important; color:#000!important}
    #preview tbody tr:nth-child(even){background:#fafafa!important}
    #preview img{max-width:100%}
    #preview tr,#preview img,#preview pre,#preview blockquote{page-break-inside:avoid}
  }
</style>
</head>
<body>
<header>
  <div class="brand"><img class="logo" src="__ICONURI__" alt="logo" /><b>Markdown 查看器</b></div>
  <div class="spacer"></div>
  <div class="search">
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
    <input id="q" placeholder="搜索正文…" />
  </div>
  <button class="btn" id="themeBtn" title="切换深色/浅色">🌗 主题</button>
  <button class="btn" id="printBtn" title="打印 / 导出 PDF">🖨 打印</button>
  <button class="btn primary" id="openBtn">📂 打开 .md</button>
  <button class="btn" id="quitBtn" title="退出并关闭后台服务">⏻ 退出</button>
  <input type="file" id="file" accept=".md,.markdown,.txt" class="hidden" />
</header>

<main>
  <aside>
    <h4>目录</h4>
    <div class="toc" id="toc"><div style="color:var(--txt3);font-size:13px;padding:6px 10px">打开文档后自动生成</div></div>
  </aside>
  <div id="preview"></div>
  <div id="empty">
    <div class="card">
      <div class="big">📄</div>
      <h3>把 Markdown 拖到这里</h3>
      <p>支持 .md / .markdown 文件。也可点击右上角「打开 .md」。<br/>所有解析都在本机完成，文件不上传。</p>
      <button class="btn primary" onclick="document.getElementById('file').click()">选择文件</button>
    </div>
  </div>
</main>

<div id="drop"><div class="ring">松开以打开 Markdown</div></div>

<footer>
  <span class="dot" id="statusDot"></span>
  <span id="statusText">服务运行中</span>
  <span id="fname">未打开文件</span>
  <span id="fmeta"></span>
  <span class="spacer"></span>
  <span>本地离线 · 零依赖 · 双击 exe 即用</span>
</footer>

<div id="down">
  <div class="card">
    <div class="big">🔌</div>
    <h3>本地服务未连接</h3>
    <p>查看器的后台服务已退出或尚未启动。<br/>
    请<b style="color:var(--cyan)">重新双击 MdViewer.exe</b> 启动，然后点击下面的重试。</p>
    <div class="row">
      <button class="btn retry" id="retryBtn">↻ 重试连接</button>
      <button class="btn" id="closeDownBtn">关闭提示</button>
    </div>
  </div>
</div>

<script>
const $ = s => document.querySelector(s);
let DOC_NAME = "";

function setInitial(name, html){
  DOC_NAME = name || "";
  $("#preview").innerHTML = html || "";
  $("#empty").classList.toggle("hidden", !!html);
  $("#fname").textContent = name ? "📄 " + name : "未打开文件";
  const w = (html||"").replace(/<[^>]+>/g,"").length;
  $("#fmeta").textContent = html ? ("· 约 " + w + " 字") : "";
  buildToc();
  applyHighlights();
}

function buildToc(){
  const toc = $("#toc");
  const hs = [...$("#preview").querySelectorAll("h1,h2,h3")];
  if(!hs.length){ toc.innerHTML = '<div style="color:var(--txt3);font-size:13px;padding:6px 10px">本文无标题</div>'; return; }
  toc.innerHTML = "";
  hs.forEach((h,idx)=>{
    if(!h.id) h.id = "h"+idx;
    const a = document.createElement("a");
    a.textContent = h.textContent;
    a.className = "lv" + (h.tagName==="H3" ? "3" : (h.tagName==="H1"?"1":""));
    a.onclick = ()=> h.scrollIntoView({behavior:"smooth",block:"start"});
    toc.appendChild(a);
  });
  // 滚动高亮当前章节
  const obs = new IntersectionObserver(es=>{
    es.forEach(e=>{
      if(e.isIntersecting){
        [...toc.children].forEach(c=>c.classList.remove("active"));
        const cur = toc.querySelector('a[href="#'+e.target.id+'"]'); // not used; fallback below
      }
    });
  },{root:$("#preview"),rootMargin:"0px 0px -80% 0px"});
}

// 搜索高亮
let lastHtml = "";
function applyHighlights(){
  const q = $("#q").value.trim().toLowerCase();
  const prev = $("#preview").innerHTML;
  if(!lastHtml) lastHtml = prev;
  let base = lastHtml;
  if(!q){ $("#preview").innerHTML = base; buildToc(); return; }
  // 简单文本高亮：基于已渲染文本，包裹匹配（不破坏标签）
  const walker = document.createElement("div");
  walker.innerHTML = base;
  const regs = new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g,"\\$&"),"gi");
  const txtNodes = [];
  const tw = document.createTreeWalker(walker, NodeFilter.SHOW_TEXT, null);
  let nd;
  while(nd = tw.nextNode()) txtNodes.push(nd);
  txtNodes.forEach(n=>{
    if(regs.test(n.nodeValue)){
      const span = document.createElement("span");
      span.innerHTML = n.nodeValue.replace(regs, m=>"<mark>"+m+"</mark>");
      n.parentNode.replaceChild(span, n);
    }
  });
  $("#preview").innerHTML = walker.innerHTML;
}

$("#q").addEventListener("input", ()=>{
  if(!lastHtml) lastHtml = $("#preview").innerHTML;
  const q = $("#q").value.trim();
  if(!q){ $("#preview").innerHTML = lastHtml; buildToc(); return; }
  applyHighlights();
});

$("#openBtn").onclick = ()=> $("#file").click();
$("#file").addEventListener("change", e=>{
  const f = e.target.files[0]; if(!f) return;
  const r = new FileReader();
  r.onload = ()=> sendOpen(f.name, r.result);
  r.readAsText(f);
});

let PENDING = null; // 服务断开时暂存待打开的文件
function sendOpen(name, content){
  PENDING = {name, content};
  fetch("/api/open",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({name, content})})
    .then(r=>r.json())
    .then(d=>{
      PENDING = null;
      hideDown();
      lastHtml=""; setInitial(d.name, d.html);
    })
    .catch(err=> showDown());
}

// ===== 服务状态监测 =====
function ping(){ return fetch("/api/ping",{cache:"no-store"}).then(r=>r.ok).catch(()=>false); }
function showDown(){ $("#down").classList.add("show"); }
function hideDown(){ $("#down").classList.remove("show"); }
function setStatus(ok){
  $("#statusDot").classList.toggle("bad", !ok);
  $("#statusText").classList.toggle("bad", !ok);
  $("#statusText").textContent = ok ? "服务运行中" : "服务未连接";
}
let everOk = false;
function watch(){
  ping().then(ok=>{
    setStatus(ok);
    if(ok){ everOk = true; hideDown(); }
    else if(everOk){ showDown(); } // 正常用过之后服务才断，才弹窗
  });
}
setInterval(watch, 3000);
window.addEventListener("load", watch);

$("#retryBtn").onclick = ()=>{
  ping().then(ok=>{
    if(ok && PENDING){ sendOpen(PENDING.name, PENDING.content); }
    else if(ok){ hideDown(); setStatus(true); }
    else { alert("仍未连接到服务。请先双击 MdViewer.exe 启动，再点重试。"); }
  });
};
$("#closeDownBtn").onclick = hideDown;

// 拖拽
const drop = $("#drop");
let dragDepth = 0;
window.addEventListener("dragenter", e=>{ e.preventDefault(); dragDepth++; drop.classList.add("show"); });
window.addEventListener("dragover", e=>{ e.preventDefault(); });
window.addEventListener("dragleave", e=>{ e.preventDefault(); if(--dragDepth<=0){dragDepth=0; drop.classList.remove("show");} });
window.addEventListener("drop", e=>{
  e.preventDefault(); dragDepth=0; drop.classList.remove("show");
  const f = e.dataTransfer.files[0]; if(!f) return;
  const r = new FileReader(); r.onload=()=>sendOpen(f.name, r.result); r.readAsText(f);
});

$("#themeBtn").onclick = ()=>{
  const dark = document.documentElement.classList.toggle("dark");
  $("#themeBtn").textContent = dark ? "☀️ 浅色" : "🌙 深色";
  try{ localStorage.setItem("mdv-theme", dark?"dark":"light"); }catch(e){}
};
$("#printBtn").onclick = ()=> window.print();
$("#quitBtn").onclick = ()=>{
  if(confirm("退出 Markdown 查看器？将关闭后台服务，所有打开的窗口都会关闭。")){
    fetch("/api/shutdown",{method:"POST"})
      .then(()=>{ showDown(); })
      .catch(()=>{ showDown(); });
  }
};

// 恢复主题（默认纸感浅色，记住用户选的深色）
try{ if(localStorage.getItem("mdv-theme")==="dark"){ document.documentElement.classList.add("dark"); document.getElementById("themeBtn").textContent = "☀️ 浅色"; } }catch(e){}

// 初始文档（由后端注入）
const INITIAL = __INITIAL__;
if(INITIAL && INITIAL.html){ setInitial(INITIAL.name, INITIAL.html); }

// 空窗口（home）唯一性：本窗口若没有文档，就作为「home」长轮询等待焦点。
// 用户再次双击 exe 时，后端会触发 home-trigger，本窗口收到后聚焦自身，
// 这样无论双击多少次 exe，都不会多开空标签页。
function isHome(){ return !(INITIAL && INITIAL.html); }
function homePoll(){
  fetch("/api/home-wait",{cache:"no-store"})
    .then(r=>r.json())
    .then(d=>{ if(d.focus){ try{ window.focus(); }catch(e){} } homePoll(); })
    .catch(()=> setTimeout(homePoll, 2000));
}
if(isHome()){ homePoll(); }
</script>
</body>
</html>
"""


def build_page(initial=None):
    """注入初始文档（命令行传入的路径内容）+ 品牌图标（favicon / 标题栏）。"""
    if initial is None:
        initial = {"name": "", "html": ""}
    import json, base64, os, sys
    icon_uri = ""
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        cands = [
            os.path.join(getattr(sys, "_MEIPASS", ""), "assets", "icon.ico"),
            os.path.join(here, "assets", "icon.ico"),
            os.path.join(here, "..", "assets", "icon.ico"),
        ]
        for p in cands:
            if p and os.path.isfile(p):
                icon_uri = "data:image/x-icon;base64," + base64.b64encode(open(p, "rb").read()).decode()
                break
    except Exception:
        icon_uri = ""
    return (INDEX_HTML
            .replace("__ICONURI__", icon_uri)
            .replace("__INITIAL__", json.dumps(initial, ensure_ascii=False)))
