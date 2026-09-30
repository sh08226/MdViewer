# -*- coding: utf-8 -*-
"""Markdown 查看器 · 本地 HTTP 服务（纯标准库，零 pip 依赖）。

设计要点：
- 单后台服务实例：端口锁文件保证同一时刻只有一个 HTTP 服务在跑。
- 双击 .md 文件 → 在同服务下以独立浏览器标签打开（URL 带 ?doc=路径），支持双开 / 多开。
- 双击 exe（无参数）→ 只打开「一个」空窗口；再次双击会**聚焦**已开的空窗口，
  不再新开空标签页（通过后端长轮询 home-wait 实现）。
- 后台服务在所有浏览器标签关闭且无活动 30 分钟后自动退出，释放端口。
- 界面提供「退出」按钮，可立即关闭后台服务。
以上所有解析在本机完成，文件不上传任何服务器。
"""
import os
import sys
import json
import webbrowser
import threading
import time
import tempfile
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import mdrender
from frontend import build_page

IDLE_TIMEOUT = 30 * 60  # 秒：无任何浏览器活动则自动退出

# ---- 空窗口（home）唯一性：长轮询焦点机制 ----
# home 窗口加载后会长轮询 /api/home-wait；当另一个无参 exe 启动时，
# 后端触发 /api/home-trigger，正在轮询的 home 窗口收到信号后调用 window.focus()。
_home_cv = threading.Condition()
_home_gen = 0
_home_waiters = 0


def _home_active():
    with _home_cv:
        return _home_waiters > 0


def _home_trigger():
    global _home_gen
    with _home_cv:
        _home_gen += 1
        _home_cv.notify_all()


def _home_release():
    """服务退出时唤醒所有等待中的 home 轮询，让它们正常返回。"""
    with _home_cv:
        _home_gen += 1
        _home_cv.notify_all()


def resolve_base():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _read_md(path):
    """读取 .md 文件并返回 {name, html, path, src}；失败返回 None。"""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return {"name": os.path.basename(path), "html": mdrender.render(text, annotate=True),
                "path": path, "src": text}
    except OSError:
        return None


_MD_EXTS = (".md", ".markdown", ".txt")


def _load_lines(path):
    """读取文件为行列表（保留原始换行风格信息）。返回 (lines, crlf) 或 None。"""
    if not path or not os.path.isfile(path) or not path.lower().endswith(_MD_EXTS):
        return None
    try:
        with open(path, "r", encoding="utf-8", errors="ignore", newline="") as f:
            raw = f.read()
    except OSError:
        return None
    crlf = "\r\n" in raw
    return raw.replace("\r\n", "\n").replace("\r", "\n").split("\n"), crlf


# ---- 端口锁 / 活动心跳 ----
_last_active = time.time()
_active_lock = threading.Lock()
httpd_global = None


def _mark_active():
    global _last_active
    with _active_lock:
        _last_active = time.time()


def _idle_seconds():
    with _active_lock:
        return time.time() - _last_active


def _port_file():
    return os.path.join(tempfile.gettempdir(), "mdviewer.port")


def _write_port_file(port):
    try:
        with open(_port_file(), "w", encoding="utf-8") as f:
            f.write(str(port))
    except Exception:
        pass


def _remove_port_file():
    try:
        os.remove(_port_file())
    except Exception:
        pass


def _find_running():
    """返回运行中服务的端口；无则 None。"""
    candidates = []
    pf = _port_file()
    if os.path.exists(pf):
        try:
            candidates.append(int(open(pf, encoding="utf-8").read().strip()))
        except Exception:
            pass
    candidates += list(range(8620, 8631))
    seen = set()
    for p in candidates:
        if p in seen:
            continue
        seen.add(p)
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/api/ping" % p, timeout=0.4)
            return p
        except Exception:
            continue
    return None


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            try:
                self.wfile.write(data)
            except Exception:
                pass

    def do_GET(self):
        _mark_active()
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            qs = urllib.parse.parse_qs(parsed.query)
            doc_path = urllib.parse.unquote(qs.get("doc", [""])[0])
            initial = None
            if doc_path and os.path.isfile(doc_path):
                initial = _read_md(doc_path)
            elif doc_path:
                safe = doc_path.replace("<", "&lt;").replace(">", "&gt;")
                initial = {"name": os.path.basename(doc_path),
                           "html": "<p style='color:#b00'>无法读取文件：<br/>%s</p>" % safe}
            self._send(200, build_page(initial), "text/html; charset=utf-8")
        elif parsed.path == "/api/source":
            # 读取某文件指定行区间的原始源码（供就地编辑弹框显示）
            qs = urllib.parse.parse_qs(parsed.query)
            p = urllib.parse.unquote(qs.get("path", [""])[0])
            try:
                s = max(1, int(qs.get("start", ["1"])[0]))
                e = int(qs.get("end", ["1"])[0])
            except ValueError:
                self._send(400, json.dumps({"error": "bad line range"})); return
            data = _load_lines(p)
            if data is None:
                self._send(404, json.dumps({"error": "file not found"})); return
            lines, _crlf = data
            e = min(e, len(lines))
            if s > e:
                self._send(400, json.dumps({"error": "bad line range"})); return
            self._send(200, json.dumps({"text": "\n".join(lines[s - 1:e])},
                                       ensure_ascii=False))
        elif parsed.path == "/api/ping":
            self._send(200, json.dumps({"ok": True}))
        elif parsed.path == "/api/home-active":
            # 是否已有 home（空窗口）在长轮询等待焦点
            self._send(200, json.dumps({"active": _home_active()}))
        elif parsed.path == "/api/home-trigger":
            # 由「再次双击 exe」调用：唤醒正在等待的 home 窗口去聚焦
            _home_trigger()
            self._send(200, json.dumps({"ok": True}))
        elif parsed.path == "/api/home-wait":
            # home 窗口长轮询：有触发则返回 focus=true，否则超时后由前端重连
            global _home_gen, _home_waiters
            with _home_cv:
                _home_waiters += 1
                my_gen = _home_gen
                try:
                    fired = _home_cv.wait_for(lambda: _home_gen > my_gen, timeout=30)
                finally:
                    _home_waiters -= 1
            self._send(200, json.dumps({"focus": bool(fired)}))
        elif parsed.path == "/api/shutdown":
            self._send(200, json.dumps({"ok": True}))
            threading.Thread(target=_delayed_shutdown, daemon=True).start()
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        _mark_active()
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/open":
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b""
                payload = json.loads(raw.decode("utf-8"))
                name = payload.get("name", "未命名.md")
                content = payload.get("content", "")
                html = mdrender.render(content)
                self._send(200, json.dumps({"name": name, "html": html},
                                           ensure_ascii=False))
            except Exception as e:  # noqa
                self._send(500, json.dumps({"error": str(e)}, ensure_ascii=False))
        elif parsed.path == "/api/save-block":
            # 就地编辑保存：把文件 [start,end] 行替换为 text，返回整篇重新渲染的 HTML
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b""
                payload = json.loads(raw.decode("utf-8"))
                p = payload.get("path", "")
                s = int(payload.get("start", 0))
                e = int(payload.get("end", 0))
                text = payload.get("text", "")
                if not p.lower().endswith(_MD_EXTS):
                    self._send(400, json.dumps({"error": "仅支持 .md/.markdown/.txt"})); return
                data = _load_lines(p)
                if data is None:
                    self._send(404, json.dumps({"error": "文件不存在"})); return
                lines, crlf = data
                s, e = max(1, s), max(s, e)
                e = min(e, len(lines))
                new_lines = text.replace("\r\n", "\n").split("\n")
                lines[s - 1:e] = new_lines
                new_text = "\n".join(lines)
                with open(p, "w", encoding="utf-8", newline="") as f:
                    f.write(new_text.replace("\n", "\r\n") if crlf else new_text)
                self._send(200, json.dumps({"ok": True, "html": mdrender.render(new_text, annotate=True)},
                                           ensure_ascii=False))
            except Exception as ex:  # noqa
                self._send(500, json.dumps({"error": str(ex)}, ensure_ascii=False))
        elif parsed.path == "/api/shutdown":
            self._send(200, json.dumps({"ok": True}))
            threading.Thread(target=_delayed_shutdown, daemon=True).start()
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def log_message(self, *args):
        pass  # 静默日志


def _delayed_shutdown():
    global httpd_global
    _home_release()
    time.sleep(0.2)
    if httpd_global is not None:
        try:
            httpd_global.shutdown()
        except Exception:
            pass


def _idle_watchdog(httpd):
    while True:
        time.sleep(60)
        if _idle_seconds() > IDLE_TIMEOUT:
            try:
                httpd.shutdown()
            except Exception:
                pass
            break


def _open_url(port, file_arg):
    url = "http://127.0.0.1:%d/" % port
    if file_arg:
        url += "?doc=" + urllib.parse.quote(file_arg, safe="")
    try:
        webbrowser.open(url)
    except Exception:
        pass


def _home_active_remote(port):
    try:
        d = json.loads(urllib.request.urlopen(
            "http://127.0.0.1:%d/api/home-active" % port, timeout=1).read())
        return bool(d.get("active"))
    except Exception:
        return False


def _home_trigger_remote(port):
    try:
        urllib.request.urlopen(
            "http://127.0.0.1:%d/api/home-trigger" % port, timeout=2).read()
    except Exception:
        pass


def serve():
    # 解析命令行：端口 + 可选的 .md 路径
    file_arg = None
    port = 8620
    for a in sys.argv[1:]:
        if a.startswith("--port="):
            try:
                port = int(a.split("=", 1)[1])
            except ValueError:
                pass
        elif os.path.isfile(a) and a.lower().endswith((".md", ".markdown", ".txt")):
            file_arg = a

    # 已有实例在跑：把打开请求交给它。
    running = _find_running()
    if running is not None:
        if file_arg:
            # 带文件 → 独立浏览器标签（支持双开 / 多开）
            _open_url(running, file_arg)
        else:
            # 无参数（空窗口）：若已有 home 在等待焦点 → 只聚焦、不新开标签；
            # 否则新开一个 home 标签。
            if _home_active_remote(running):
                _home_trigger_remote(running)
            else:
                _open_url(running, None)
        return

    # 没有运行实例：本进程作为唯一后台服务
    httpd = None
    tried = port
    for p in range(tried, tried + 20):
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            port = p
            break
        except OSError:
            continue
    if httpd is None:
        print("[错误] 无法绑定本地端口，请检查端口占用。")
        return

    global httpd_global
    httpd_global = httpd
    try:
        _write_port_file(port)
    except Exception:
        pass
    threading.Thread(target=_idle_watchdog, args=(httpd,), daemon=True).start()

    url = "http://127.0.0.1:%d/" % port
    if file_arg:
        url += "?doc=" + urllib.parse.quote(file_arg, safe="")
    print("Markdown 查看器已启动：%s" % url)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        _remove_port_file()


if __name__ == "__main__":
    serve()
