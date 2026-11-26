import { useEffect, useState } from "react";

const EDITION_DATE = /^\d{4}-\d{2}-\d{2}$/;
const KIND = {
  official: "机构发布",
  news: "报道或实践",
  paper: "期刊研究",
  preprint: "预印本",
  x: "X 原帖",
};
const dateFormat = new Intl.DateTimeFormat("zh-CN", {
  timeZone: "Asia/Taipei",
  month: "2-digit",
  day: "2-digit",
});

async function readJson(path, signal) {
  const response = await fetch(path, { signal });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

export default function MorningEdition() {
  const requested = new URLSearchParams(window.location.search).get("edition") || "";
  const [date, setDate] = useState(EDITION_DATE.test(requested) ? requested : "");
  const [dates, setDates] = useState([]);
  const [edition, setEdition] = useState(null);
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    const controller = new AbortController();
    readJson("./morning-archive.json", controller.signal)
      .then((result) => setDates(result.filter((entry) => EDITION_DATE.test(entry))))
      .catch(() => {});
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    const path = date ? `./editions/${date}.json` : "./morning-edition.json";
    setStatus("loading");
    readJson(path, controller.signal)
      .then((result) => {
        setEdition(result);
        setStatus("ready");
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("unavailable");
      });
    return () => controller.abort();
  }, [date]);

  function selectDate(value) {
    const url = new URL(window.location.href);
    if (value) url.searchParams.set("edition", value);
    else url.searchParams.delete("edition");
    window.history.replaceState(null, "", url);
    setDate(value);
    setCategory("");
  }

  const rows = edition?.items || [];
  const sections = Object.entries(edition?.categories || {});
  const availableDates = date && !dates.includes(date) ? [date, ...dates] : dates;
  return (
    <section className="morning-edition" id="morning-edition" aria-labelledby="morning-title">
      <header className="morning-header">
        <div>
          <span className="section-kicker">MORNING BRIEF</span>
          <h2 id="morning-title">AI 情报晨报</h2>
          {status === "ready" && <p><time>{edition.date}</time> · {rows.length} 条精选</p>}
        </div>
        <div className="morning-controls">
          <label>
            往期晨报
            <select value={date} onChange={(event) => selectDate(event.target.value)}>
              <option value="">最新一期</option>
              {availableDates.map((entry) => <option key={entry}>{entry}</option>)}
            </select>
          </label>
          <a href="./morning-edition.xml">订阅晨报 RSS ↗</a>
        </div>
      </header>
      {status === "loading" && <p role="status">晨报加载中…</p>}
      {status === "unavailable" && <p role="status">{date ? "该日期暂无晨报。" : "暂无晨报。"}</p>}
      {status === "ready" && (
        <>
          <nav className="morning-tabs" aria-label="晨报栏目">
            <button type="button" aria-pressed={!category} onClick={() => setCategory("")}>全部 · {rows.length}</button>
            {sections.map(([key, label]) => (
              <button type="button" key={key} aria-pressed={category === key} onClick={() => setCategory(key)}>
                {label} · {rows.filter((row) => row.category === key).length}
              </button>
            ))}
          </nav>
          <div className="morning-grid">
            {sections.filter(([key]) => !category || key === category).map(([key, label]) => {
              const entries = rows.filter((row) => row.category === key);
              return (
                <section key={key} className="morning-lane">
                  <h3>{label}</h3>
                  {entries.length === 0 && <p>本期暂无入选条目。</p>}
                  {entries.map((row) => (
                    <article key={row.id} className="morning-story">
                      <small>{row.source} · {KIND[row.kind]} · {dateFormat.format(new Date(row.published_at))}</small>
                      <h4><a href={row.url} target="_blank" rel="noreferrer">{row.title} ↗</a></h4>
                      {row.insight ? (
                        <details>
                          <summary>展开分析</summary>
                          <dl>
                            <dt>提炼</dt><dd>{row.insight.digest}</dd>
                            <dt>分析</dt><dd>{row.insight.analysis}</dd>
                            <dt>输出</dt><dd>{row.insight.takeaway}</dd>
                          </dl>
                        </details>
                      ) : row.summary ? (
                        <details>
                          <summary>查看来源摘要</summary>
                          <p>{row.summary}</p>
                        </details>
                      ) : null}
                    </article>
                  ))}
                </section>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}
