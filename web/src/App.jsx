import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  ArrowSquareOut,
  Broadcast,
  CaretDown,
  Check,
  Copy,
  GithubLogo,
  LockKey,
  Plus,
  Rss,
  SlidersHorizontal,
  Sparkle,
  X,
} from "@phosphor-icons/react";
import ClickSpark from "./components/ClickSpark";
import DecryptedText from "./components/DecryptedText";
import Magnet from "./components/Magnet";

const FEED_URL = "./feed.json";
const RSS_URL = "https://jj1292.github.io/AI-Intelligence-Radar/feed.xml";
const JSON_URL = "https://jj1292.github.io/AI-Intelligence-Radar/feed.json";
const CONFIG_EDIT_URL =
  "https://github.com/jj1292/AI-Intelligence-Radar/edit/main/config/subscriptions.json";

const FILTERS = [
  { id: "all", label: "全部" },
  { id: "claude", label: "Claude" },
  { id: "openai", label: "OpenAI" },
  { id: "gemini", label: "Gemini" },
  { id: "agents", label: "Agents" },
];

const SOURCE_TYPES = [
  { value: "firecrawl", label: "博客 / 新闻网站（Firecrawl）" },
  { value: "rss", label: "RSS / Atom" },
  { value: "github", label: "GitHub Releases" },
  { value: "reddit", label: "Reddit 社区" },
];

function parseContent(content = "") {
  const [summaryPart, rest = ""] = content.split("\n\nWhy it matters:");
  const [whyPart = "", sourcePart = ""] = rest.split("\n\nSource:");
  return {
    summary: summaryPart.trim(),
    why: whyPart.trim() || "这条信号进入持续观察列表，仍需结合官方原文判断实际影响。",
    source: sourcePart.trim(),
  };
}

function normalizeItem(item) {
  const parsed = parseContent(item.content_text);
  const radar = item._radar || {};
  const tier = Number(radar.source_tier || 3);
  const tags = Array.isArray(item.tags) ? item.tags : [];
  const publishedAt = new Date(item.date_published);
  const impact = Number(radar.impact_score || (tier === 1 ? 3 : tier === 2 ? 3 : 2));
  const confidence = Number(
    radar.confidence || (tier === 1 ? 0.98 : tier === 2 ? 0.85 : 0.65),
  );

  return {
    ...item,
    company: radar.company || item.authors?.[0]?.name || "Unknown",
    sourceName: radar.source_name || parsed.source || "Unknown source",
    platform: radar.platform || "other",
    tier,
    impact,
    confidence,
    tags,
    publishedAt,
    summary: parsed.summary,
    why: parsed.why,
    evidence: Array.isArray(radar.evidence) ? radar.evidence : [],
  };
}

function matchesFilter(item, filter) {
  if (filter === "all") return true;
  const haystack = [item.title, item.company, item.sourceName, ...item.tags]
    .join(" ")
    .toLowerCase();
  if (filter === "claude") return /claude|anthropic/.test(haystack);
  if (filter === "openai") return /openai|codex|chatgpt/.test(haystack);
  if (filter === "gemini") return /gemini|google|deepmind/.test(haystack);
  return /agent|agents|agentic|codex|claude code/.test(haystack);
}

function importanceScore(item) {
  const tierWeight = item.tier === 1 ? 40 : item.tier === 2 ? 22 : 5;
  const officialEditorial = item.platform === "official" ? 28 : 0;
  return officialEditorial + tierWeight + item.impact * 10 + Math.round(item.confidence * 10);
}

function isPreviewRelease(item) {
  if (item.platform !== "github") return false;
  return /(?:^|[\s._-])(nightly|alpha|dev|canary|snapshot|beta|preview|pre|rc\d*)(?:[\s._-]|$)/i.test(
    item.title,
  );
}

function selectImportantSignals(items) {
  const seenReleaseFamilies = new Set();
  return items
    .filter((item) => item.tier <= 2 && item.impact >= 3 && !isPreviewRelease(item))
    .sort(
      (a, b) =>
        importanceScore(b) - importanceScore(a) || b.publishedAt - a.publishedAt,
    )
    .filter((item) => {
      if (item.platform !== "github") return true;
      const family = `${item.company}:${item.sourceName}`;
      if (seenReleaseFamilies.has(family)) return false;
      seenReleaseFamilies.add(family);
      return true;
    });
}

function formatDate(date) {
  if (Number.isNaN(date.getTime())) return "时间待核验";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

function sourceMark(item) {
  if (/anthropic|claude/i.test(`${item.company} ${item.title}`)) return "AN";
  if (/openai|codex|chatgpt/i.test(`${item.company} ${item.title}`)) return "OA";
  if (/google|gemini|deepmind/i.test(`${item.company} ${item.title}`)) return "GD";
  if (/reddit/i.test(item.platform)) return "RD";
  if (/github/i.test(item.platform)) return "GH";
  return item.company.slice(0, 2).toUpperCase();
}

function SignalInterpretation({ item }) {
  return (
    <div className="interpretation">
      <div>
        <span className="interpretation-label">发生了什么</span>
        <p>{item.summary}</p>
      </div>
      <div>
        <span className="interpretation-label">为什么重要</span>
        <p>{item.why}</p>
      </div>
      <div>
        <span className="interpretation-label">证据与边界</span>
        <p>
          当前判断来自 {item.sourceName}，来源等级为 T{item.tier}。
          {item.tier === 1
            ? "这是官方一手信息，但产品影响仍需后续真实使用与独立证据验证。"
            : "这不是最终事实，需要等待官方来源或多个独立来源交叉验证。"}
        </p>
        {item.evidence.length > 0 && (
          <blockquote>原始依据：{item.evidence[0]}</blockquote>
        )}
      </div>
    </div>
  );
}

function ImportantSignal({ item, index, expanded, onToggle }) {
  return (
    <article className={`important-signal ${expanded ? "is-expanded" : ""}`}>
      <div className="signal-number">{String(index + 1).padStart(2, "0")}</div>
      <div className="signal-source">
        <span className="source-tier">
          T{item.tier} · {item.tier === 1 ? "官方一手" : "一手账号"}
        </span>
        <span className="source-monogram">{sourceMark(item)}</span>
        <span>{item.company}</span>
      </div>
      <div className="signal-body">
        <div className="signal-meta">
          <span>{formatDate(item.publishedAt)}</span>
          <span>可信度 {Math.round(item.confidence * 100)}%</span>
        </div>
        <h3>{item.title}</h3>
        <p className="signal-summary">{item.summary}</p>
        <div className="signal-actions">
          <button className="text-action" type="button" onClick={onToggle}>
            {expanded ? "收起解读" : "展开解读"}
            <CaretDown size={16} weight="bold" aria-hidden />
          </button>
          <a href={item.url} target="_blank" rel="noreferrer">
            查看原文 <ArrowSquareOut size={16} weight="bold" aria-hidden />
          </a>
        </div>
        {expanded && <SignalInterpretation item={item} />}
      </div>
    </article>
  );
}

function LiveSignal({ item }) {
  return (
    <a className="live-signal" href={item.url} target="_blank" rel="noreferrer">
      <time>{formatDate(item.publishedAt)}</time>
      <span className={`live-dot tier-${item.tier}`} aria-hidden />
      <span className="live-monogram">{sourceMark(item)}</span>
      <span className="live-copy">
        <strong>{item.title}</strong>
        <small>
          {item.company} · T{item.tier}
        </small>
      </span>
      <ArrowSquareOut size={17} weight="bold" aria-hidden />
    </a>
  );
}

function SourceManager({ onClose, onCopied }) {
  const [form, setForm] = useState({
    type: "firecrawl",
    name: "",
    url: "",
    company: "",
    topics: "claude, agents",
  });
  const [snippet, setSnippet] = useState("");

  function updateField(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  }

  function generateSnippet(event) {
    event.preventDefault();
    const topics = form.topics
      .split(",")
      .map((topic) => topic.trim())
      .filter(Boolean);
    const id = `web_${(form.company || form.name || "source")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_|_$/g, "")}`;
    const payload =
      form.type === "firecrawl"
        ? {
            id,
            adapter: "firecrawl",
            name: form.name,
            url: form.url,
            company: form.company,
            topics,
            max_results: 30,
            enabled: true,
          }
        : {
            name: form.name,
            url: form.url,
            company: form.company,
            topics,
            enabled: true,
          };
    setSnippet(JSON.stringify(payload, null, 2));
  }

  async function copySnippet() {
    await navigator.clipboard.writeText(snippet);
    onCopied("配置片段已复制");
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="source-manager"
        role="dialog"
        aria-modal="true"
        aria-labelledby="source-manager-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header>
          <div>
            <span className="eyebrow">OWNER ONLY / 第一期</span>
            <h2 id="source-manager-title">添加订阅来源</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="关闭">
            <X size={24} weight="bold" />
          </button>
        </header>
        <p className="manager-note">
          当前公开网站不会保存密钥。这里先帮你生成安全配置；最终的对话 Agent
          会把这一步自动完成。
        </p>
        <form onSubmit={generateSnippet}>
          <label>
            来源类型
            <select name="type" value={form.type} onChange={updateField}>
              {SOURCE_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </label>
          <div className="form-grid">
            <label>
              来源名称
              <input
                required
                name="name"
                value={form.name}
                onChange={updateField}
                placeholder="Anthropic Newsroom"
              />
            </label>
            <label>
              公司
              <input
                required
                name="company"
                value={form.company}
                onChange={updateField}
                placeholder="Anthropic"
              />
            </label>
          </div>
          <label>
            官网 / Feed 地址
            <input
              required
              type="url"
              name="url"
              value={form.url}
              onChange={updateField}
              placeholder="https://example.com/news"
            />
          </label>
          <label>
            关注主题（逗号分隔）
            <input name="topics" value={form.topics} onChange={updateField} />
          </label>
          <button className="primary-button compact" type="submit">
            <Plus size={18} weight="bold" /> 生成配置
          </button>
        </form>
        {snippet && (
          <div className="snippet-box">
            <pre>{snippet}</pre>
            <button type="button" onClick={copySnippet}>
              <Copy size={18} weight="bold" /> 复制
            </button>
          </div>
        )}
        <div className="manager-footer">
          <LockKey size={20} weight="bold" />
          <span>Firecrawl Key 只保存在 GitHub Actions Secret，不进入网页。</span>
          <a href={CONFIG_EDIT_URL} target="_blank" rel="noreferrer">
            打开 GitHub 安全编辑 <GithubLogo size={18} weight="fill" />
          </a>
        </div>
      </section>
    </div>
  );
}

export function App() {
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState("loading");
  const [activeFilter, setActiveFilter] = useState("all");
  const [expanded, setExpanded] = useState(new Set());
  const [importantLimit, setImportantLimit] = useState(6);
  const [liveLimit, setLiveLimit] = useState(10);
  const [managerOpen, setManagerOpen] = useState(false);
  const [toast, setToast] = useState("");
  const [agentPrompt, setAgentPrompt] = useState("");

  useEffect(() => {
    let ignore = false;
    fetch(FEED_URL)
      .then((response) => {
        if (!response.ok) throw new Error(`Feed HTTP ${response.status}`);
        return response.json();
      })
      .then((payload) => {
        if (ignore) return;
        setItems(
          (payload.items || [])
            .map(normalizeItem)
            .sort((a, b) => b.publishedAt - a.publishedAt),
        );
        setStatus("ready");
      })
      .catch(() => {
        if (!ignore) setStatus("error");
      });
    return () => {
      ignore = true;
    };
  }, []);

  const filteredItems = useMemo(
    () => items.filter((item) => matchesFilter(item, activeFilter)),
    [items, activeFilter],
  );
  const importantItems = useMemo(
    () => selectImportantSignals(filteredItems),
    [filteredItems],
  );
  const tickerItems = items.slice(0, 6);

  function notify(message) {
    setToast(message);
    window.setTimeout(() => setToast(""), 2200);
  }

  async function copyLink(url, label) {
    await navigator.clipboard.writeText(url);
    notify(`${label} 地址已复制`);
  }

  function toggleInterpretation(id) {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function selectFilter(id) {
    setActiveFilter(id);
    setImportantLimit(6);
    setLiveLimit(10);
  }

  function previewAgent(event) {
    event.preventDefault();
    if (!agentPrompt.trim()) return;
    notify("订阅 Agent 正在规划中；当前请先用“管理来源”添加");
  }

  return (
    <ClickSpark sparkColor="#c6ff00" sparkSize={8} sparkRadius={22} sparkCount={7}>
      <div className="app-shell">
        <header className="masthead">
          <div className="brand-block">
            <div className="brand-row">
              <Broadcast size={34} weight="fill" />
              <div>
                <strong>AI INTELLIGENCE RADAR</strong>
                <span>AI 行业情报雷达 · 官方更新追踪器</span>
              </div>
            </div>
            <div className="coordinates">
              <span>31.2304° N</span>
              <span>121.4737° E</span>
            </div>
          </div>
          <div className="headline-block">
            <h1>
              <DecryptedText
                text="重要信号，"
                speed={34}
                maxIterations={8}
                animateOn="view"
                sequential
                useOriginalCharsOnly
              />
              <span>不是更多噪音</span>
            </h1>
            <p>追踪 Claude、Codex、Gemini 与顶尖 AI 团队的一手变化。</p>
          </div>
          <div className="dish-art" aria-hidden />
          <Magnet padding={44} magnetStrength={4} wrapperClassName="subscribe-magnet">
            <button
              className="subscribe-hero"
              type="button"
              onClick={() =>
                document.querySelector("#subscribe")?.scrollIntoView({ behavior: "smooth" })
              }
            >
              订阅 <ArrowRight size={28} weight="bold" />
            </button>
          </Magnet>
        </header>

        <div className="signal-ticker" aria-label="实时更新">
          <span className="ticker-label">
            <span className="status-dot" /> LIVE SIGNALS
          </span>
          <div className="ticker-track">
            {tickerItems.map((item) => (
              <a key={item.id} href={item.url} target="_blank" rel="noreferrer">
                {item.title}
                <time>{formatDate(item.publishedAt)}</time>
              </a>
            ))}
          </div>
        </div>

        <section className="control-deck">
          <nav className="filter-nav" aria-label="情报来源筛选">
            {FILTERS.map((filter) => (
              <button
                key={filter.id}
                type="button"
                className={activeFilter === filter.id ? "active" : ""}
                onClick={() => selectFilter(filter.id)}
              >
                {filter.label}
              </button>
            ))}
          </nav>
          <form className="agent-preview" onSubmit={previewAgent}>
            <span className="preview-badge">
              <Sparkle size={18} weight="fill" /> 订阅 Agent 预览
            </span>
            <input
              value={agentPrompt}
              onChange={(event) => setAgentPrompt(event.target.value)}
              placeholder="告诉 Radar 你想关注什么…"
              aria-label="告诉 Radar 你想关注什么"
            />
            <button type="submit" aria-label="提交订阅意图">
              <ArrowRight size={24} weight="bold" />
            </button>
          </form>
        </section>

        <main className="content-grid">
          <section className="important-column">
            <div className="section-heading">
              <div>
                <span className="section-kicker">CURATED / 持续下拉</span>
                <h2>今日重要信号</h2>
              </div>
              <p>不固定三条。官方优先、影响优先；每条都能展开查看判断、证据与边界。</p>
            </div>
            {status === "loading" && <div className="state-box">正在接收信号…</div>}
            {status === "error" && (
              <div className="state-box error">
                Feed 暂时没有响应，请稍后刷新。公开订阅地址不受影响。
              </div>
            )}
            {status === "ready" && importantItems.length === 0 && (
              <div className="state-box">当前筛选下暂无通过重要度门槛的信号。</div>
            )}
            <div className="important-list">
              {importantItems.slice(0, importantLimit).map((item, index) => (
                <ImportantSignal
                  key={item.id}
                  item={item}
                  index={index}
                  expanded={expanded.has(item.id)}
                  onToggle={() => toggleInterpretation(item.id)}
                />
              ))}
            </div>
            {importantLimit < importantItems.length && (
              <button
                className="load-more"
                type="button"
                onClick={() => setImportantLimit((value) => value + 6)}
              >
                继续向下浏览重要信号 <CaretDown size={20} weight="bold" />
              </button>
            )}
          </section>

          <aside className="live-column">
            <div className="section-heading compact-heading">
              <div>
                <span className="section-kicker">CHRONOLOGICAL / 原始流</span>
                <h2>实时情报</h2>
              </div>
              <p>按时间展示全部新内容，不把每条更新都包装成“重要”。</p>
            </div>
            <div className="live-list">
              {filteredItems.slice(0, liveLimit).map((item) => (
                <LiveSignal key={item.id} item={item} />
              ))}
            </div>
            {liveLimit < filteredItems.length && (
              <button
                className="live-more"
                type="button"
                onClick={() => setLiveLimit((value) => value + 10)}
              >
                加载更多实时情报 <CaretDown size={18} weight="bold" />
              </button>
            )}
          </aside>
        </main>

        <section className="subscribe-strip" id="subscribe">
          <div className="subscribe-statement">
            <span>SUBSCRIBE TO THE SIGNAL</span>
            <p>订阅真正重要的官方信号，第一时间送达。</p>
          </div>
          <button type="button" onClick={() => copyLink(RSS_URL, "RSS")}>
            <Rss size={32} weight="fill" />
            <span>
              <small>公开订阅</small>复制 RSS
            </span>
            <Copy size={22} weight="bold" />
          </button>
          <button type="button" onClick={() => copyLink(JSON_URL, "JSON")}>
            <span className="json-mark">{"{}"}</span>
            <span>
              <small>开发者订阅</small>复制 JSON
            </span>
            <Copy size={22} weight="bold" />
          </button>
          <button className="manage-button" type="button" onClick={() => setManagerOpen(true)}>
            <SlidersHorizontal size={28} weight="bold" />
            <span>
              <small>仅维护者</small>管理来源
            </span>
            <ArrowRight size={22} weight="bold" />
          </button>
        </section>

        <footer>
          <span>OPEN SOURCE · SOURCE-LINKED · NO FAKE SIGNALS</span>
          <a
            href="https://github.com/jj1292/AI-Intelligence-Radar"
            target="_blank"
            rel="noreferrer"
          >
            <GithubLogo size={20} weight="fill" /> GitHub
          </a>
          <a href={RSS_URL} target="_blank" rel="noreferrer">
            RSS
          </a>
          <a href={JSON_URL} target="_blank" rel="noreferrer">
            JSON
          </a>
        </footer>

        {managerOpen && (
          <SourceManager onClose={() => setManagerOpen(false)} onCopied={notify} />
        )}
        {toast && (
          <div className="toast" role="status">
            <Check size={20} weight="bold" /> {toast}
          </div>
        )}
      </div>
    </ClickSpark>
  );
}
