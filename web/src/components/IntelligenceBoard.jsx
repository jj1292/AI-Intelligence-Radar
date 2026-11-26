import { useEffect, useState } from "react";

const TIME = new Intl.DateTimeFormat("zh-CN", {
  timeZone: "Asia/Taipei", month: "2-digit", day: "2-digit",
  hour: "2-digit", minute: "2-digit", hour12: false,
});

const SOURCE_KIND = { x: "X", wechat: "公众号", official: "机构发布" };
const morningLink = ({ date, id }) => `?edition=${date}#morning-${id}`;

function References({ sources }) {
  return (
    <div className="radar-references" aria-label="原始来源">
      {sources.map(({ url, source, kind }) => (
        <a key={url} href={url} target="_blank" rel="noreferrer">
          {SOURCE_KIND[kind] ? `${SOURCE_KIND[kind]} · ` : ""}{source} ↗
        </a>
      ))}
    </div>
  );
}

function ResearchTrends({ data }) {
  return (
    <section className="morning-edition radar-trends" id="research-trends" aria-labelledby="research-trends-title">
      <h2 id="research-trends-title">医疗 AI 研究趋势</h2>
      {data ? (
        <>
          <p>{data.start} 至 {data.end} · 指定期刊 {data.available.includes("journal") ? `${data.totals.journal} 篇` : "暂缺"} ·
            预印本 {data.available.includes("preprint") ? `${data.totals.preprint} 篇` : "暂缺"} · 检索样本</p>
          {Object.values(data.coverage || {}).some((entry) => entry.sources_ok < entry.sources_total || entry.retrieved < entry.matched)
            && <p>本期为部分来源或限额内样本。</p>}
          {!data.themes.length && <p>本期暂无满足条件的研究样本。</p>}
          <div className="morning-grid">
            {data.themes.map((theme) => (
              <article className="morning-lane" key={theme.label}>
                <h3>{theme.label}</h3>
                <p>期刊 {data.available.includes("journal") ? theme.journal : "—"} · 预印本 {data.available.includes("preprint") ? theme.preprint : "—"}</p>
                <details>
                  <summary>代表研究</summary>
                  <ul>
                    {theme.examples.map((example) => (
                      <li key={example.url}>
                        <a href={example.url} target="_blank" rel="noreferrer">{example.title}</a>
                        {example.kind === "preprint" && " · 预印本"}
                      </li>
                    ))}
                  </ul>
                </details>
              </article>
            ))}
          </div>
        </>
      ) : <p>暂无研究趋势。</p>}
    </section>
  );
}

function Watchlists({ groups }) {
  const [index, setIndex] = useState(0);
  if (!groups?.length) return null;
  const group = groups[index] || groups[0];
  return (
    <section className="morning-edition radar-trends" id="watchlists" aria-labelledby="watchlists-title">
      <h2 id="watchlists-title">重点跟踪</h2>
      <nav className="morning-tabs" aria-label="重点跟踪栏目">
        {groups.map((entry, position) => (
          <button key={entry.id} type="button" aria-pressed={group.id === entry.id}
            onClick={() => setIndex(position)}>{entry.label}</button>
        ))}
      </nav>
      <div className="morning-grid">
        {group.subjects.map((subject) => (
          <article className="morning-lane" key={subject.name}>
            <h3><a href={subject.url} target="_blank" rel="noreferrer">{subject.name} ↗</a></h3>
            {subject.reference && <p>
              <time>{subject.reference.date}</time>{" · "}
              <a href={subject.reference.url} target="_blank" rel="noreferrer">{subject.reference.title}</a>
            </p>}
            {subject.stories.length > 0 ? (
              <ul>{subject.stories.map((story) => (
                <li key={story.url}>
                  <a href={story.url} target="_blank" rel="noreferrer">{story.title}</a>
                  {" · "}{story.type}{" · "}{story.source}
                </li>
              ))}</ul>
            ) : <small>近一周暂无新增报道。</small>}
          </article>
        ))}
      </div>
    </section>
  );
}

export default function IntelligenceBoard() {
  const [data, setData] = useState(null);
  const [research, setResearch] = useState(null);
  const [status, setStatus] = useState("loading");
  const [category, setCategory] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    async function load(path) {
      const response = await fetch(path, { signal: controller.signal });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    }
    load("./intelligence.json").then((value) => {
      setData(value);
      setStatus("ready");
    }).catch(() => {
      if (!controller.signal.aborted) setStatus("unavailable");
    });
    load("./research-trends.json").then(setResearch).catch(() => {});
    return () => controller.abort();
  }, []);

  const matches = (row) => !category || row.category === category;
  const signals = (data?.signals || []).filter(matches);
  const live = (data?.live || []).filter(matches);
  const categories = Object.entries(data?.categories || {})
    .filter(([key]) => key !== "research" || data.signals.some((row) => row.category === key));

  return (
    <main>
      <Watchlists groups={data?.watchlists} />
      <div className="radar-filter morning-tabs" aria-label="情报栏目">
        <button type="button" aria-pressed={!category} onClick={() => setCategory("")}>全部情报</button>
        {categories.map(([key, label]) => (
          <button type="button" key={key} aria-pressed={category === key} onClick={() => setCategory(key)}>
            {label}
          </button>
        ))}
      </div>
      <div className="content-grid">
        <section className="important-column" id="important-signals">
          <div className="section-heading compact-heading"><div>
            <span className="section-kicker">CURATED SIGNALS</span><h2>重要信号</h2>
          </div></div>
          {status === "ready" && !signals.length && <p className="state-box">当前栏目暂无重要信号。</p>}
          {signals.map((row) => (
            <article className="radar-story" key={row.id}>
              <small>{data.categories[row.category]}{row.region && ` · ${row.region}`}
                {row.reports > 1 && ` · ${row.reports} 家发布方`}</small>
              <h3>{row.title}</h3>
              {row.insight && (<>
                <p>{row.insight.digest}</p>
                <details>
                  <summary>展开分析</summary>
                  <dl><dt>分析</dt><dd>{row.insight.analysis}</dd><dt>输出</dt><dd>{row.insight.takeaway}</dd></dl>
                </details>
              </>)}
              <References sources={row.sources} />
              <div className="radar-references">
                {row.morning && <a href={morningLink(row.morning)}>晨报 · {row.morning.date}</a>}
                {row.event_id && <a href={`#live-${row.event_id}`}>查看实时条目</a>}
              </div>
            </article>
          ))}
        </section>
        <aside className="live-column" id="live-intelligence">
          <div className="section-heading compact-heading"><div>
            <span className="section-kicker">HOURLY HEADLINES</span><h2 id="live-intelligence-title">实时情报</h2>
          </div></div>
          {data && <p className="radar-timestamp">最近采集 {TIME.format(new Date(data.updated_at))} · 台北时间</p>}
          {status === "loading" && <p role="status">情报加载中…</p>}
          {status === "unavailable" && <p role="status">暂无实时情报。</p>}
          {status === "ready" && !live.length && <p className="state-box">当前栏目暂无实时情报。</p>}
          {live.length > 0 && (
            <div className="radar-live-window" role="region" aria-labelledby="live-intelligence-title" tabIndex={0}>
              {live.map((row) => (
                <article className="radar-story" id={`live-${row.id}`} key={row.id}>
                  <small>{TIME.format(new Date(row.published_at))} · {data.categories[row.category]}{row.region && ` · ${row.region}`}</small>
                  <h3><a href={row.sources[0].url} target="_blank" rel="noreferrer">{row.title} ↗</a></h3>
                  <References sources={row.sources} />
                  {row.morning && <a className="radar-morning-link" href={morningLink(row.morning)}>晨报收录 · {row.morning.date}</a>}
                </article>
              ))}
            </div>
          )}
        </aside>
      </div>
      {data?.agent_themes?.length > 0 && <section className="morning-edition radar-trends" id="agent-trends">
        <h2>个人 Agent 趋势</h2>
        <div className="morning-grid">
          {data.agent_themes.map((theme) => (
            <article className="morning-lane" key={theme.title}>
              <h3>{theme.title}</h3>
              <p>{theme.question}</p>
              <ul>{theme.links.map(({ title, source, url }) => (
                <li key={url}><a href={url} target="_blank" rel="noreferrer">{title}</a> · {source}</li>
              ))}</ul>
            </article>
          ))}
        </div>
      </section>}
      <ResearchTrends data={research} />
    </main>
  );
}
