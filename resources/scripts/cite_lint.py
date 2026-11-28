#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cite_lint.py — 引用与论断绑定核验器（intro-related-work-writer Skill 的执行内核）

解决的问题：引言与相关工作最致命的错误是"引用了不存在的文献""转述与原文不符"
"断言没有出处"。这三类问题肉眼难以逐条核对，但机械可查。

子命令：
  scan   解析材料里的参考文献库（.bib / markdown / txt / json）→ refs.json
  check  解析草稿的引用标记，与文献库比对 → cite_report.json + cite_report.md
  contrib 检查贡献条目是否与正文的图/表/数字一一对应 → contrib_report.json

比对输出的五类结果：
  hallucinated  草稿引用了文献库里查不到的条目（幻觉引用，必须改）
  unused        文献库有、草稿未引（覆盖不足，建议补）
  metadata      编号/年份/作者与文献库不一致（引用元数据错误）
  uncited       含强断言但无引用标记的句子（断言缺证据）
  matched       引用可回查且元数据一致

用法：
  python3 cite_lint.py scan    --materials /app/work/materials --out /app/work/refs.json
  python3 cite_lint.py check   --refs-json /app/work/refs.json --draft /app/output/intro_related_work.md --out /app/work
  python3 cite_lint.py contrib --draft /app/output/intro_related_work.md --out /app/work

设计原则：
  * 只读材料；结论都带 行号/编号 锚点。
  * 不做语义判断：uncited 只提示"强断言无引用"，由作者决定是否补引或标为作者判断。
  * 零第三方依赖。
"""

import argparse
import json
import re
import sys
from pathlib import Path

TEXT_EXT = {".bib", ".md", ".txt", ".json", ".yaml", ".yml", ".csv"}
BIB_ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", re.I)
BIB_FIELD = re.compile(r"(\w+)\s*=\s*[{\"](.+?)[}\"]\s*,?\s*$", re.S | re.M)

# 编号式：[1] [1,2] [1-3] [1–3]
CITE_NUM = re.compile(r"\[(\d{1,3}(?:\s*[,\-–—]\s*\d{1,3})*)\]")
# LaTeX 式：\cite{a,b} \citep{a}
CITE_TEX = re.compile(r"\\cite[a-z]*\{([^}]+)\}")
# 作者-年份式：(Smith et al., 2023) / (Smith & Lee 2021) / Smith et al. (2023)
CITE_AY = re.compile(
    r"\(([A-Z][A-Za-z\-']+)"
    r"(?:\s+(?:et\s+al\.?|and\s+[A-Z][A-Za-z\-']+|&\s*[A-Z][A-Za-z\-']+))?"
    r"[,\s]+((?:19|20)\d{2})[a-z]?[;)]"
)
# 不带外层括号：Liu et al. (2021) / Chen (2019)
CITE_AY2 = re.compile(
    r"\b([A-Z][A-Za-z\-']+)(?:\s+(?:et\s+al\.?|and\s+[A-Z][A-Za-z\-']+|&\s*[A-Z][A-Za-z\-']+))?"
    r"\s*\(((?:19|20)\d{2})[a-z]?\)"
)

ASSERT_WORDS = [
    "表明", "说明", "证明", "显示", "优于", "显著", "因此", "由此可见", "证实",
    "demonstrate", "show that", "shows that", "prove", "outperform", "significantly",
    "suggest that", "indicate that", "reveal", "confirm",
]
CONTRIB_WORDS = ["贡献", "本文提出", "我们提出", "we propose", "we present", "our contribution",
                 "in this work, we", "本文工作"]


def norm(s):
    return re.sub(r"[\s\-_]+", " ", str(s or "")).strip().lower()


def read_text(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


# ---------------------------------------------------------------- 文献库解析

def parse_bib(text):
    out = {}
    for m in BIB_ENTRY.finditer(text):
        key = m.group(2).strip()
        start = m.end()
        # 找到配对的右括号（粗粒度：下一个 @ 之前）
        nxt = text.find("\n@", start)
        body = text[start: nxt if nxt > 0 else len(text)]
        fields = {}
        for fm in BIB_FIELD.finditer(body):
            fields[fm.group(1).lower()] = re.sub(r"\s+", " ", fm.group(2)).strip()
        authors = fields.get("author", "")
        surnames = [a.strip().split(",")[0].strip() for a in authors.split(" and ") if a.strip()]
        out[key] = {
            "key": key, "type": m.group(1).lower(),
            "authors": surnames[:6], "year": fields.get("year", ""),
            "title": fields.get("title", ""), "venue": fields.get("journal") or fields.get("booktitle", ""),
            "raw_author": authors,
        }
    return out


def parse_ref_list(text):
    """编号式参考文献表：[1] Author, A. (2023). Title. / 1. Author (2023)"""
    out = {}
    for line in text.splitlines():
        s = line.strip()
        if not s or len(s) > 800:
            continue
        m = re.match(r"^\[?(\d{1,3})\]?[\.\)]?\s+(.+)$", s)
        if not m:
            continue
        num, rest = m.group(1), m.group(2)
        ym = re.search(r"\(?((?:19|20)\d{2})[a-z]?\)?", rest)
        am = re.match(r"^([A-Z][A-Za-z\-']+)", rest)
        out[num] = {"key": num, "type": "numbered", "year": ym.group(1) if ym else "",
                    "authors": [am.group(1)] if am else [], "title": rest[:200], "venue": "",
                    "raw_author": rest[:120]}
    return out


def parse_refs_json(text):
    try:
        data = json.loads(text)
    except Exception:
        return {}
    items = data.get("references") if isinstance(data, dict) else data
    out = {}
    if isinstance(items, list):
        for i, it in enumerate(items, 1):
            if not isinstance(it, dict):
                continue
            key = str(it.get("key") or it.get("id") or it.get("citation-key") or i)
            authors = it.get("authors") or it.get("author") or []
            if isinstance(authors, str):
                authors = [authors]
            out[key] = {"key": key, "type": "json", "authors": [str(a) for a in authors][:6],
                        "year": str(it.get("year") or ""), "title": str(it.get("title") or ""),
                        "venue": str(it.get("venue") or it.get("journal") or ""),
                        "raw_author": ", ".join(str(a) for a in authors[:3])}
    return out


def cmd_scan(args):
    root = Path(args.materials)
    if not root.exists():
        print(json.dumps({"ok": False, "error": f"材料目录不存在: {root}"}, ensure_ascii=False))
        return 1
    files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    refs, scanned, skipped = {}, [], []
    for p in files:
        ext = p.suffix.lower()
        if ext not in TEXT_EXT:
            skipped.append({"file": str(p), "reason": "非文本"})
            continue
        text = read_text(p)
        got = {}
        if ext == ".bib":
            got = parse_bib(text)
        elif ext == ".json":
            got = parse_refs_json(text)
        else:
            got = parse_ref_list(text)
        if not got:
            skipped.append({"file": str(p), "reason": "未检出参考文献条目"})
            continue
        scanned.append({"file": str(p), "count": len(got)})
        for k, v in got.items():
            v["source_file"] = str(p)
            refs.setdefault(k, v)
    out = {"ok": bool(refs), "materials_root": str(root), "scanned": scanned,
           "skipped": skipped, "ref_count": len(refs), "refs": refs}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": out["ok"], "out": args.out, "ref_count": len(refs),
                      "scanned": len(scanned)}, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------- 草稿核验

def expand_nums(spec):
    nums = []
    for part in re.split(r"[,\s]+", spec.strip()):
        if not part:
            continue
        m = re.match(r"^(\d{1,3})\s*[\-–—]\s*(\d{1,3})$", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if 0 <= b - a <= 60:
                nums.extend(str(i) for i in range(a, b + 1))
            continue
        if part.isdigit():
            nums.append(part)
    return nums


def extract_citations(draft_text):
    """返回 [{kind, key, line, snippet}]"""
    found = []
    lines = draft_text.splitlines()
    for i, line in enumerate(lines, 1):
        for m in CITE_NUM.finditer(line):
            for n in expand_nums(m.group(1)):
                found.append({"kind": "number", "key": n, "line": i,
                              "snippet": line.strip()[:160]})
        for m in CITE_TEX.finditer(line):
            for k in m.group(1).split(","):
                k = k.strip()
                if k:
                    found.append({"kind": "key", "key": k, "line": i,
                                  "snippet": line.strip()[:160]})
        for m in CITE_AY.finditer(line):
            found.append({"kind": "author_year", "key": f"{m.group(1)} {m.group(2)}".strip(),
                          "surname": m.group(1).split()[0], "year": m.group(2),
                          "line": i, "snippet": line.strip()[:160]})
        for m in CITE_AY2.finditer(line):
            found.append({"kind": "author_year", "key": f"{m.group(1)} {m.group(2)}".strip(),
                          "surname": m.group(1).split()[0], "year": m.group(2),
                          "line": i, "snippet": line.strip()[:160]})
    seen, uniq = set(), []
    for f in found:
        sig = (f["kind"], f["key"], f["line"])
        if sig in seen:
            continue
        seen.add(sig)
        uniq.append(f)
    return uniq


def cmd_check(args):
    lib = json.loads(Path(args.refs_json).read_text(encoding="utf-8"))
    refs = lib.get("refs", {})
    draft = read_text(Path(args.draft))
    if not draft:
        print(json.dumps({"ok": False, "error": "草稿为空或不存在"}, ensure_ascii=False))
        return 1
    cites = extract_citations(draft)

    # 编号式文献库的键集合
    num_keys = {k for k, v in refs.items() if str(v.get("type")) == "numbered"}
    key_keys = set(refs.keys())
    surname_year = {}
    for k, v in refs.items():
        for s in (v.get("authors") or []):
            if s:
                surname_year.setdefault((norm(s.split()[0]), str(v.get("year") or "")), k)

    hallucinated, matched, metadata = [], [], []
    used_keys = set()
    for c in cites:
        if c["kind"] == "number":
            if c["key"] in num_keys:
                matched.append(c)
                used_keys.add(c["key"])
            else:
                hallucinated.append({**c, "reason": "文献库无此编号",
                                     "action": "核对参考文献表编号，或删除/替换该引用"})
        elif c["kind"] == "key":
            if c["key"] in key_keys:
                matched.append(c)
                used_keys.add(c["key"])
            else:
                cand = [k for k in key_keys if norm(k) == norm(c["key"])]
                if cand:
                    metadata.append({**c, "reason": "键名大小写/格式不一致", "guess": cand[0],
                                     "action": f"改为 {cand[0]}"})
                    used_keys.add(cand[0])
                else:
                    hallucinated.append({**c, "reason": "文献库无此 bib key",
                                         "action": "确认该文献是否真实存在；不存在则删除该引用"})
        else:  # author_year
            hit = surname_year.get((norm(c["surname"]), str(c["year"])))
            if hit:
                matched.append({**c, "resolved": hit})
                used_keys.add(hit)
            else:
                near = [k for (s, y), k in surname_year.items() if s == norm(c["surname"])]
                if near:
                    real_year = refs[near[0]].get("year")
                    metadata.append({**c, "reason": f"年份不符，文献库为 {real_year}",
                                     "guess": near[0],
                                     "action": f"改为 ({c['surname']} et al., {real_year})"})
                    used_keys.add(near[0])
                else:
                    hallucinated.append({**c, "reason": "作者-年份在文献库中查不到",
                                         "action": "确认文献是否真实存在；不存在则删除该引用"})

    unused = [{"key": k, "year": v.get("year"), "title": (v.get("title") or "")[:120],
               "source": v.get("source_file", "")}
              for k, v in refs.items() if k not in used_keys]

    # 强断言无引用
    uncited = []
    for i, line in enumerate(draft.splitlines(), 1):
        s = line.strip()
        if len(s) < 25 or s.startswith(("#", "|", ">", "-", "*")):
            continue
        if not any(w.lower() in s.lower() for w in ASSERT_WORDS):
            continue
        if CITE_NUM.search(s) or CITE_TEX.search(s) or CITE_AY.search(s):
            continue
        uncited.append({"line": i, "snippet": s[:200],
                        "action": "补引用，或改写为作者判断并显式标注（如“我们认为”）"})

    total = len(cites)
    report = {
        "ok": True, "draft": str(args.draft), "refs_json": str(args.refs_json),
        "library_size": len(refs), "citation_marks": total,
        "matched_count": len(matched), "hallucinated_count": len(hallucinated),
        "metadata_count": len(metadata), "unused_count": len(unused),
        "uncited_assertion_count": len(uncited),
        "citation_precision": round(len(matched) / total, 4) if total else 0.0,
        "coverage": round(len(used_keys) / max(1, len(refs)), 4),
        "hallucinated": hallucinated, "metadata_mismatches": metadata,
        "unused": unused[:60], "uncited_assertions": uncited[:60],
        "verification_hint": {
            "citation_traceability": f"可回查引用 {len(matched)} / 引用标记 {total}",
            "citation_validity": f"幻觉/查不到 {len(hallucinated)} 条（必须为 0）",
            "reference_coverage": f"已引 {len(used_keys)} / 文献库 {len(refs)}",
            "assertion_grounding": f"无引用的强断言 {len(uncited)} 条",
        },
    }
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "cite_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md = ["# 引用与论断核验报告", "",
          f"- 文献库条目：{len(refs)}",
          f"- 草稿引用标记：{total}（可回查 {len(matched)}｜幻觉 {len(hallucinated)}｜元数据问题 {len(metadata)}）",
          f"- 文献库未引：{len(unused)}",
          f"- 强断言无引用：{len(uncited)}", ""]
    if hallucinated:
        md += ["## 幻觉引用（必须处理）", ""]
        for h in hallucinated:
            md.append(f"- `{h['key']}`（草稿 L{h['line']}）{h['reason']} — {h['snippet'][:100]}")
        md.append("")
    if metadata:
        md += ["## 元数据不一致（应改）", ""]
        for m in metadata:
            md.append(f"- `{m['key']}`（L{m['line']}）{m['reason']} → {m['action']}")
        md.append("")
    if uncited[:25]:
        md += ["## 强断言无引用（补引或标为作者判断）", ""]
        for u in uncited[:25]:
            md.append(f"- L{u['line']}：{u['snippet'][:140]}")
        md.append("")
    if unused[:25]:
        md += ["## 文献库未引用（评估是否应覆盖）", ""]
        for u in unused[:25]:
            md.append(f"- `{u['key']}` {u['year']} {u['title'][:80]}")
        md.append("")
    md += ["## 自检口径建议", ""]
    for k, v in report["verification_hint"].items():
        md.append(f"- `{k}`：{v}")
    (outdir / "cite_report.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["library_size", "citation_marks", "matched_count",
                                            "hallucinated_count", "metadata_count",
                                            "unused_count", "uncited_assertion_count",
                                            "citation_precision", "coverage"]}, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------- 贡献对齐

FIG_TAB = re.compile(r"(?:Fig(?:ure)?\.?|图|Table|表)\s*([\dIVX]+[a-z]?)", re.I)


def cmd_contrib(args):
    draft = read_text(Path(args.draft))
    if not draft:
        print(json.dumps({"ok": False, "error": "草稿为空"}, ensure_ascii=False))
        return 1
    lines = draft.splitlines()
    # 找贡献段：含贡献关键词的段落
    contrib_blocks = []
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if len(s) < 10:
            continue
        if any(w.lower() in s.lower() for w in CONTRIB_WORDS):
            contrib_blocks.append((i, s))
    # 抽取全文所有 图/表 引用
    body_figs = {}
    for i, line in enumerate(lines, 1):
        for m in FIG_TAB.finditer(line):
            body_figs.setdefault(m.group(1).upper(), []).append(i)
    items = []
    for ln, s in contrib_blocks:
        figs = [m.group(1).upper() for m in FIG_TAB.finditer(s)]
        nums = re.findall(r"\d+\.?\d*\s*%?", s)
        items.append({
            "line": ln, "text": s[:220],
            "fig_refs": figs,
            "fig_refs_resolvable": all(f in body_figs for f in figs),
            "has_numbers": bool(nums),
            "verdict": ("pass" if (not figs or all(f in body_figs for f in figs)) else "fail"),
        })
    report = {"ok": True, "draft": str(args.draft),
              "contrib_mentions": len(items), "body_figures": sorted(body_figs.keys()),
              "items": items,
              "verification_hint": {
                  "contribution_alignment": f"贡献条目 {len(items)} 条，图表引用可解析 {sum(1 for x in items if x['fig_refs_resolvable'])} 条",
              }}
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "contrib_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"contrib_mentions": len(items),
                      "unresolved_fig_refs": [x["line"] for x in items if not x["fig_refs_resolvable"]],
                      "body_figures": sorted(body_figs.keys())[:20]}, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser(description="引用与论断绑定核验器")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s1 = sub.add_parser("scan"); s1.add_argument("--materials", required=True); s1.add_argument("--out", required=True)
    s2 = sub.add_parser("check"); s2.add_argument("--refs-json", required=True)
    s2.add_argument("--draft", required=True); s2.add_argument("--out", required=True)
    s3 = sub.add_parser("contrib"); s3.add_argument("--draft", required=True); s3.add_argument("--out", required=True)
    a = ap.parse_args()
    return {"scan": cmd_scan, "check": cmd_check, "contrib": cmd_contrib}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
