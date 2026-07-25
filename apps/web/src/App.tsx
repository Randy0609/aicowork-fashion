import { useEffect, useMemo, useState } from 'react';
import {
  loadArtifacts,
  loadCategories,
  loadStatus,
  loadWorkflows,
  runProductContent,
} from './api';
import type {
  Artifact,
  Category,
  ProductContent,
  ProductInput,
  WorkbenchStatus,
  WorkflowManifest,
} from './types';

type Section = 'workbench' | 'artifacts' | 'framework';

const EMPTY_FORM: ProductInput = {
  category: '',
  product_name: '',
  material: '',
  target_customer: '',
  selling_points: '',
  tone: '克制专业',
};

function formatTime(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

function ResultCard({ content }: { content: ProductContent }) {
  return (
    <article className="result-card">
      <div className="result-heading">
        <div>
          <span className="eyebrow">生成结果</span>
          <h2>{content.product_title}</h2>
        </div>
        <span className="mode-chip">
          {content.generation_mode === 'demo' ? '模拟引擎' : '已配置模型'}
        </span>
      </div>

      <section className="result-section">
        <h3>核心卖点</h3>
        <ul className="point-list">
          {content.selling_points.map((point, index) => (
            <li key={`${point}-${index}`}>{point}</li>
          ))}
        </ul>
      </section>

      <section className="result-section">
        <h3>社媒文案草稿</h3>
        <p className="copy-block">{content.social_post}</p>
      </section>

      <section className="result-section">
        <h3>短视频脚本</h3>
        <div className="scene-list">
          {content.short_video_script.map((scene, index) => (
            <div className="scene" key={`${scene.scene}-${index}`}>
              <span>{String(index + 1).padStart(2, '0')}</span>
              <div>
                <strong>{scene.scene}</strong>
                <p>画面：{scene.visual}</p>
                <p>口播：{scene.voiceover}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="review-box">
        <strong>发布前核验</strong>
        <ul>
          {content.review_notes.map((note, index) => (
            <li key={`${note}-${index}`}>{note}</li>
          ))}
        </ul>
      </section>
    </article>
  );
}

export function App() {
  const [section, setSection] = useState<Section>('workbench');
  const [categories, setCategories] = useState<Category[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowManifest[]>([]);
  const [status, setStatus] = useState<WorkbenchStatus | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<Artifact | null>(null);
  const [form, setForm] = useState<ProductInput>(EMPTY_FORM);
  const [provider, setProvider] = useState<'demo' | 'configured'>('demo');
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      loadStatus(),
      loadCategories(),
      loadWorkflows(),
      loadArtifacts(),
    ])
      .then(([nextStatus, nextCategories, nextWorkflows, nextArtifacts]) => {
        if (cancelled) return;
        setStatus(nextStatus);
        setCategories(nextCategories);
        setWorkflows(nextWorkflows);
        setArtifacts(nextArtifacts);
        if (nextCategories[0]) setForm(nextCategories[0].example);
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setLoadError(error instanceof Error ? error.message : '工作台加载失败');
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedCategory = useMemo(
    () => categories.find((item) => item.example.category === form.category),
    [categories, form.category],
  );

  const updateField = <K extends keyof ProductInput>(
    field: K,
    value: ProductInput[K],
  ) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const loadExample = (category: Category) => {
    setForm(category.example);
    setRunError(null);
  };

  const handleRun = async () => {
    setBusy(true);
    setRunError(null);
    try {
      const response = await runProductContent(form, provider);
      setSelectedArtifact(response.artifact);
      setArtifacts(await loadArtifacts());
    } catch (error) {
      setRunError(error instanceof Error ? error.message : '任务执行失败');
    } finally {
      setBusy(false);
    }
  };

  const openArtifacts = () => {
    setSection('artifacts');
    if (!selectedArtifact && artifacts[0]) setSelectedArtifact(artifacts[0]);
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">A</span>
          <div>
            <strong>AiCowork</strong>
            <small>Fashion Community</small>
          </div>
        </div>

        <button className="new-task" onClick={() => setSection('workbench')}>
          <span>＋</span> 新建商品任务
        </button>

        <nav>
          <button
            className={section === 'workbench' ? 'active' : ''}
            onClick={() => setSection('workbench')}
          >
            <span>⌂</span> 工作台
          </button>
          <button
            className={section === 'artifacts' ? 'active' : ''}
            onClick={openArtifacts}
          >
            <span>□</span> 产物库
            <em>{artifacts.length}</em>
          </button>
          <button
            className={section === 'framework' ? 'active' : ''}
            onClick={() => setSection('framework')}
          >
            <span>◇</span> 框架说明
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="status-dot" />
          <div>
            <strong>v0.1-alpha</strong>
            <small>本地优先 · 社区框架</small>
          </div>
        </div>
      </aside>

      <main>
        {loadError ? (
          <div className="fatal-error">
            <strong>后端连接失败</strong>
            <p>{loadError}</p>
          </div>
        ) : section === 'workbench' ? (
          <div className="workspace">
            <header className="hero">
              <span className="hero-badge">服饰行业 AI 工作台</span>
              <h1>今天要为商品做什么？</h1>
              <p>把已经确认的商品事实，变成可审核、可保存、可继续修改的内容资产。</p>
            </header>

            <div className="workspace-grid">
              <section className="task-panel">
                <div className="panel-title">
                  <div>
                    <span className="eyebrow">工作流 01</span>
                    <h2>商品内容生成</h2>
                  </div>
                  <span className="stable-chip">Stable</span>
                </div>

                <div className="example-row">
                  <span>载入模拟案例</span>
                  <div>
                    {categories.map((category) => (
                      <button
                        key={category.id}
                        className={
                          selectedCategory?.id === category.id ? 'selected' : ''
                        }
                        onClick={() => loadExample(category)}
                      >
                        {category.name}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="form-grid">
                  <label>
                    <span>品类</span>
                    <input
                      value={form.category}
                      onChange={(event) => updateField('category', event.target.value)}
                      placeholder="例如：女装上衣"
                    />
                  </label>
                  <label>
                    <span>商品名称</span>
                    <input
                      value={form.product_name}
                      onChange={(event) =>
                        updateField('product_name', event.target.value)
                      }
                      placeholder="填写商品名称"
                    />
                  </label>
                  <label className="full">
                    <span>材质与工艺</span>
                    <input
                      value={form.material}
                      onChange={(event) => updateField('material', event.target.value)}
                      placeholder="只填写已经核实的信息"
                    />
                  </label>
                  <label className="full">
                    <span>目标顾客</span>
                    <input
                      value={form.target_customer}
                      onChange={(event) =>
                        updateField('target_customer', event.target.value)
                      }
                      placeholder="描述使用场景和关注点，不编造人群数据"
                    />
                  </label>
                  <label className="full">
                    <span>已核实卖点</span>
                    <textarea
                      value={form.selling_points}
                      onChange={(event) =>
                        updateField('selling_points', event.target.value)
                      }
                      rows={5}
                      placeholder="每条卖点用分号或换行分隔"
                    />
                  </label>
                  <label>
                    <span>表达风格</span>
                    <select
                      value={form.tone}
                      onChange={(event) =>
                        updateField('tone', event.target.value as ProductInput['tone'])
                      }
                    >
                      <option>克制专业</option>
                      <option>轻松自然</option>
                      <option>简洁有力</option>
                    </select>
                  </label>
                  <label>
                    <span>生成引擎</span>
                    <select
                      value={provider}
                      onChange={(event) =>
                        setProvider(event.target.value as 'demo' | 'configured')
                      }
                    >
                      <option value="demo">模拟引擎 · 无需密钥</option>
                      <option
                        value="configured"
                        disabled={!status?.configured_model_ready}
                      >
                        {status?.configured_model_ready
                          ? `已配置模型 · ${status.configured_model}`
                          : '真实模型 · 尚未配置'}
                      </option>
                    </select>
                  </label>
                </div>

                {runError && <div className="inline-error">{runError}</div>}

                <div className="task-actions">
                  <span>AI 输出必须由商家审核后再发布</span>
                  <button
                    className="primary-action"
                    disabled={busy}
                    onClick={handleRun}
                  >
                    {busy ? '正在生成…' : '生成商品内容 →'}
                  </button>
                </div>
              </section>

              <section className="result-panel">
                {selectedArtifact ? (
                  <ResultCard content={selectedArtifact.content} />
                ) : (
                  <div className="empty-result">
                    <span>✦</span>
                    <h2>等待第一次产出</h2>
                    <p>使用左侧模拟案例即可跑通完整任务，不需要配置模型密钥。</p>
                  </div>
                )}
              </section>
            </div>
          </div>
        ) : section === 'artifacts' ? (
          <div className="library-page">
            <header className="page-header">
              <span className="eyebrow">Local artifacts</span>
              <h1>产物库</h1>
              <p>每次工作流的结果都保存在本机 SQLite 中。</p>
            </header>
            <div className="library-grid">
              <aside className="artifact-list">
                {artifacts.length === 0 ? (
                  <p className="empty-list">还没有产物，先运行一次商品内容任务。</p>
                ) : (
                  artifacts.map((artifact) => (
                    <button
                      key={artifact.id}
                      className={
                        selectedArtifact?.id === artifact.id ? 'active' : ''
                      }
                      onClick={() => setSelectedArtifact(artifact)}
                    >
                      <strong>{artifact.title}</strong>
                      <span>{formatTime(artifact.created_at)}</span>
                    </button>
                  ))
                )}
              </aside>
              <section className="artifact-preview">
                {selectedArtifact ? (
                  <ResultCard content={selectedArtifact.content} />
                ) : (
                  <div className="empty-result">
                    <span>□</span>
                    <h2>选择一个产物</h2>
                  </div>
                )}
              </section>
            </div>
          </div>
        ) : (
          <div className="framework-page">
            <header className="page-header">
              <span className="eyebrow">Open framework</span>
              <h1>一个能跑起来的工作台骨架</h1>
              <p>它不是完整业务系统，而是商家和技术服务商可以继续改造的公共底座。</p>
            </header>

            <div className="framework-cards">
              <article>
                <span>01</span>
                <h2>模型适配层</h2>
                <p>默认模拟引擎；配置后端环境变量后，调用兼容聊天补全接口的模型服务。</p>
              </article>
              <article>
                <span>02</span>
                <h2>工作流注册器</h2>
                <p>后端自动发现工作流清单、提示词和处理器，不需要把所有场景写进主程序。</p>
              </article>
              <article>
                <span>03</span>
                <h2>任务与产物</h2>
                <p>每次运行都留下任务状态和结构化产物，便于后续增加评价、版本和团队协作。</p>
              </article>
              <article>
                <span>04</span>
                <h2>品类配置</h2>
                <p>服装、眼镜和鞋包以独立配置存在，可以继续添加饰品、珠宝和其他细分品类。</p>
              </article>
            </div>

            <section className="runtime-card">
              <div>
                <span className="eyebrow">当前运行状态</span>
                <h2>{status?.configured_model_ready ? '真实模型已就绪' : '模拟模式可用'}</h2>
              </div>
              <dl>
                <div>
                  <dt>版本</dt>
                  <dd>{status?.version ?? '加载中'}</dd>
                </div>
                <div>
                  <dt>存储</dt>
                  <dd>{status?.data_store ?? '加载中'}</dd>
                </div>
                <div>
                  <dt>工作流</dt>
                  <dd>{workflows.length}</dd>
                </div>
                <div>
                  <dt>品类模板</dt>
                  <dd>{categories.length}</dd>
                </div>
              </dl>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
