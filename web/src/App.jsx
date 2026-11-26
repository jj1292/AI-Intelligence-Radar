import { useState } from "react";
import {
  ArrowRight,
  Broadcast,
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
import MorningEdition from "./components/MorningEdition";
import IntelligenceBoard from "./components/IntelligenceBoard";

const RSS_URL = "https://jj1292.github.io/AI-Intelligence-Radar/feed.xml";
const JSON_URL = "https://jj1292.github.io/AI-Intelligence-Radar/feed.json";
const CONFIG_EDIT_URL =
  "https://github.com/jj1292/AI-Intelligence-Radar/edit/main/config/subscriptions.json";

const SOURCE_TYPES = [
  { value: "firecrawl", label: "博客 / 新闻网站（Firecrawl）" },
  { value: "rss", label: "RSS / Atom" },
  { value: "github", label: "GitHub Releases" },
  { value: "reddit", label: "Reddit 社区" },
];

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
            <span className="eyebrow">SOURCE MANAGER</span>
            <h2 id="source-manager-title">添加订阅来源</h2>
          </div>
          <button className="icon-button" type="button" onClick={onClose} aria-label="关闭">
            <X size={24} weight="bold" />
          </button>
        </header>
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
  const [managerOpen, setManagerOpen] = useState(false);
  const [toast, setToast] = useState("");
  const [agentPrompt, setAgentPrompt] = useState("");

  function notify(message) {
    setToast(message);
    window.setTimeout(() => setToast(""), 2200);
  }

  async function copyLink(url, label) {
    await navigator.clipboard.writeText(url);
    notify(`${label} 地址已复制`);
  }

  function previewAgent(event) {
    event.preventDefault();
    if (!agentPrompt.trim()) return;
    setManagerOpen(true);
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
                <span>AI 情报站 · 每日晨报与实时情报</span>
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
                text="AI 情报站"
                speed={34}
                maxIterations={8}
                animateOn="view"
                sequential
                useOriginalCharsOnly
              />
              <span>每日重要信号</span>
            </h1>
            <p>中美 AI 热点、个人 Agent、医疗研究趋势与产品实践。</p>
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

        <MorningEdition />

        <section className="control-deck">
          <form className="agent-preview" onSubmit={previewAgent}>
            <span className="preview-badge">
              <Sparkle size={18} weight="fill" /> 智能订阅
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

        <IntelligenceBoard />

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
              <small>来源设置</small>管理来源
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
