# -*- coding: utf-8 -*-
"""轻量 Markdown -> HTML 渲染器（纯标准库，零依赖）。

覆盖日常写作最常用的语法：
  标题 #~###### / 无序-有序列表(支持嵌套) / 引用(支持嵌套) /
  围栏代码块 ``` / 缩进代码块 / 表格(GFM) / 水平线 / 行内代码·粗体·斜体·删除线·链接·图片·自动链接。
所有文本均做 HTML 转义，避免原始 HTML 注入。
"""
import re


def escape_html(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


def _inline(text):
    """处理行内标记。输入为已转义文本（除代码外）。"""
    codes = []

    def stash_code(m):
        codes.append(m.group(1))
        return "\x00CODE%d\x00" % (len(codes) - 1)

    # 行内代码 `code`
    text = re.sub(r"`([^`]+)`", stash_code, text)
    # 图片 ![alt](url)
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)",
                  lambda m: '<img src="%s" alt="%s"%s />' % (
                      escape_html(m.group(2)), escape_html(m.group(1)),
                      ' title="%s"' % escape_html(m.group(3)) if m.group(3) else ""),
                  text)
    # 链接 [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)",
                  lambda m: '<a href="%s" target="_blank" rel="noopener">%s</a>' % (
                      escape_html(m.group(2)), escape_html(m.group(1))),
                  text)
    # 自动链接 <http...>
    text = re.sub(r"&lt;(https?://[^&]+)&gt;",
                  lambda m: '<a href="%s" target="_blank" rel="noopener">%s</a>' % (
                      m.group(1), m.group(1)), text)
    # 粗体 **x** / __x__
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
    # 斜体 *x* / _x_
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"(?<!_)_(?!_)(.+?)_(?!_)", r"<em>\1</em>", text)
    # 删除线 ~~x~~
    text = re.sub(r"~~(.+?)~~", r"<del>\1</del>", text)
    # 还原行内代码
    for i, c in enumerate(codes):
        text = text.replace("\x00CODE%d\x00" % i, "<code>%s</code>" % escape_html(c))
    # 行尾两空格 -> 换行
    text = re.sub(r"  \n", "<br />\n", text)
    return text


def _is_block_start(line):
    s = line.lstrip()
    if s.startswith("```") or s.startswith(">") or s.startswith("#"):
        return True
    if re.match(r"^(\s*)([-*+]|\d+[.)])\s+", line):
        return True
    if re.match(r"^(\s*[-*_]){3,}\s*$", line) and set(line.strip()) <= set("-*_ "):
        return True
    return False


def _split_table_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _parse_list(lines, start):
    """解析一个列表（支持嵌套）。返回 (html, next_index)。"""
    n = len(lines)
    first_indent = len(lines[start]) - len(lines[start].lstrip())
    ordered = bool(re.match(r"^\s*\d+[.)]\s+", lines[start]))
    items_html = []
    i = start

    def item_text(idx):
        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", lines[idx])
        return m.group(3) if m else lines[idx].strip()

    while i < n:
        line = lines[i]
        if line.strip() == "":
            # 允许列表项之间空行（下一项仍是同层或更深列表）
            j = i + 1
            while j < n and lines[j].strip() == "":
                j += 1
            if (j < n and re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[j])
                    and (len(lines[j]) - len(lines[j].lstrip())) >= first_indent):
                i = j
                continue
            break
        m = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
        if not m:
            break
        indent = len(m.group(1))
        if indent < first_indent:
            break
        if indent > first_indent:
            # 嵌套应由递归处理；若出现在这里说明结构异常，停止
            break
        # 同层列表项
        content_parts = [m.group(3)]
        i += 1
        while i < n:
            if lines[i].strip() == "":
                j = i + 1
                while j < n and lines[j].strip() == "":
                    j += 1
                if j < n and re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[j]) \
                        and (len(lines[j]) - len(lines[j].lstrip())) > first_indent:
                    i = j
                    continue
                break
            mm = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", lines[i])
            if mm and len(mm.group(1)) > first_indent:
                sub, i = _parse_list(lines, i)
                content_parts.append(sub)
                continue
            if mm and len(mm.group(1)) <= first_indent:
                break
            content_parts.append(lines[i].strip())
            i += 1
        inner = _inline(escape_html(" ".join(content_parts)))
        items_html.append("<li>%s</li>" % inner)

    tag = "ol" if ordered else "ul"
    return "<%s>%s</%s>" % (tag, "".join(items_html), tag), i


def render(md_text, annotate=False):
    """将 Markdown 文本渲染为 HTML 片段（不含 <html> 外壳）。

    annotate=True 时为顶层区块元素附加 data-ln="起始行-结束行"（1-based，
    对应规范化换行后的源文件行号），供前端「双击就地编辑」定位源码。
    """
    lines = md_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    def A(s, e):
        return ' data-ln="%d-%d"' % (s, e) if annotate else ""

    out = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        # 围栏代码块
        if line.lstrip().startswith("```"):
            lang = line.lstrip()[3:].strip()
            s0 = i
            buf = []
            i += 1
            while i < n and not lines[i].lstrip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # 跳过结束 ```
            cls = (' class="lang-%s"' % escape_html(lang)) if lang else ""
            out.append("<pre%s><code%s>%s</code></pre>" % (A(s0 + 1, i), cls, escape_html("\n".join(buf))))
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            out.append("<h%d%s>%s</h%d>" % (level, A(i + 1, i + 1), _inline(escape_html(m.group(2).strip())), level))
            i += 1
            continue

        # 水平线
        if re.match(r"^(\s*[-*_]){3,}\s*$", line) and set(line.strip()) <= set("-*_ "):
            out.append("<hr />")
            i += 1
            continue

        # 引用块
        if line.lstrip().startswith(">"):
            s0 = i
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(lines[i].lstrip()[1:].lstrip())
                i += 1
            out.append("<blockquote%s>%s</blockquote>" % (A(s0 + 1, i), render("\n".join(buf))))
            continue

        # 表格
        if "|" in line and i + 1 < n and "-" in lines[i + 1] \
                and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1]):
            s0 = i
            header = _split_table_row(line)
            sep = _split_table_row(lines[i + 1])
            aligns = []
            for s in sep:
                left, right = s.startswith(":"), s.endswith(":")
                aligns.append("center" if left and right else "right" if right else "left" if left else "")
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip() != "":
                rows.append(_split_table_row(lines[i]))
                i += 1
            thead = "<tr>" + "".join(
                '<th%s>%s</th>' % (' style="text-align:%s"' % a if a else "", _inline(escape_html(c)))
                for c, a in zip(header, aligns)) + "</tr>"
            tbody = "".join(
                "<tr>" + "".join(
                    '<td%s>%s</td>' % (' style="text-align:%s"' % a if a else "", _inline(escape_html(c)))
                    for c, a in zip(r, aligns)) + "</tr>"
                for r in rows)
            out.append("<table%s><thead>%s</thead><tbody>%s</tbody></table>" % (A(s0 + 1, i), thead, tbody))
            continue

        # 列表
        if re.match(r"^(\s*)([-*+]|\d+[.)])\s+", line):
            s0 = i
            items, i = _parse_list(lines, i)
            items = re.sub(r"^<(ul|ol)", lambda m: "<%s%s" % (m.group(1), A(s0 + 1, i)), items, count=1)
            out.append(items)
            continue

        # 缩进代码块
        if line.startswith("    ") or line.startswith("\t"):
            s0 = i
            buf = []
            while i < n and (lines[i].startswith("    ") or lines[i].startswith("\t") or lines[i].strip() == ""):
                buf.append(lines[i].replace("\t", "    ")[4:] if lines[i].strip() != "" else "")
                i += 1
            while buf and buf[-1] == "":
                buf.pop()
            out.append("<pre%s><code>%s</code></pre>" % (A(s0 + 1, i), escape_html("\n".join(buf))))
            continue

        # 空行
        if line.strip() == "":
            i += 1
            continue

        # 段落
        s0 = i
        para = [line]
        i += 1
        while i < n and lines[i].strip() != "" and not _is_block_start(lines[i]):
            para.append(lines[i])
            i += 1
        out.append("<p%s>%s</p>" % (A(s0 + 1, i), _inline(escape_html(" ".join(para)))))

    return "\n".join(out)


if __name__ == "__main__":
    sample = """# 标题一
## 标题二
这是**粗体**和*斜体*以及`行内代码`，还有[链接](https://example.com)与~~删除~~。

> 引用一行
> 第二行

- 项目一
- 项目二
  - 子项 A
  - 子项 B
    - 孙项
1. 第一
2. 第二

| 名称 | 数量 |
| --- | ---: |
| 苹果 | 3 |
| 香蕉 | 5 |

```python
print("hello")
```

---
结束段落，含 *强调*。
"""
    print(render(sample))
