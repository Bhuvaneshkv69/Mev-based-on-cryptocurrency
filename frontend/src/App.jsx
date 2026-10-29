import { useEffect, useMemo, useState } from 'react'
import {
  Activity, ArrowDownRight, ArrowUpRight, Blocks, BookOpen, CheckCircle2,
  ChevronRight, CircleHelp, Clock3, Database, Gauge, LayoutDashboard,
  LoaderCircle, Network, RefreshCw, ShieldCheck, ShieldAlert, Wallet,
  Lock, Scale, Flame, Zap, TrendingUp, Layers, AlertTriangle, Sparkles,
  Cpu, FileText, Check, ArrowRight, Server, EyeOff, Shuffle
} from 'lucide-react'
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend,
  Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { api } from './api'

const NAV = [
  { id: 'dashboard', label: 'Overview & Report', icon: LayoutDashboard },
  { id: 'protection', label: 'PS 1: User Exploitation', icon: ShieldCheck },
  { id: 'decentralization', label: 'PS 2: PBS Centralization', icon: Network },
  { id: 'efficiency', label: 'PS 3: Network & Security', icon: Gauge },
  { id: 'history', label: 'Experiment History', icon: Database },
]

const money = (n, digits = 4) => Number.isFinite(Number(n)) ? Number(n).toLocaleString(undefined, { maximumFractionDigits: digits }) : '—'
const pct = (n) => `${money(n, 2)}%`

function Panel({ title, subtitle, action, children, className = '' }) {
  return <section className={`panel ${className}`}><div className="panel-head"><div><h3>{title}</h3>{subtitle && <p>{subtitle}</p>}</div>{action}</div>{children}</section>
}
function Stat({ label, value, note, icon: Icon, tone = 'blue' }) {
  return <div className="stat-card"><div className={`stat-icon ${tone}`}><Icon size={19} /></div><div className="stat-copy"><span>{label}</span><strong>{value}</strong><small>{note}</small></div></div>
}
function Button({ children, loading, variant = 'primary', ...props }) {
  return <button className={`btn ${variant}`} disabled={loading || props.disabled} {...props}>{loading ? <LoaderCircle className="spin" size={16} /> : null}{children}</button>
}
function Notice({ type = 'info', children }) {
  return <div className={`notice ${type}`}>{type === 'error' ? <ShieldAlert size={17} /> : <CircleHelp size={17} />}<span>{children}</span></div>
}
function JsonResult({ data }) {
  return <pre className="json-result">{JSON.stringify(data, null, 2)}</pre>
}

// ==============================================================================
// 1. OVERVIEW & CASE STUDY SUMMARY
// ==============================================================================
function Dashboard({ summary, experiments, health, refresh, setPage }) {
  const byModule = summary?.by_module || {}
  const byStatus = summary?.by_status || {}
  const moduleData = [
    { name: 'PS1: Protection', value: byModule.protection || 0, fill: '#4f73e8' },
    { name: 'PS2: Centralization', value: byModule.decentralization || 0, fill: '#7b61d1' },
    { name: 'PS3: Efficiency', value: byModule.efficiency || 0, fill: '#19996d' },
  ]
  const recent = (experiments?.items || []).slice(0, 5)

  return <>
    <div className="page-title-row">
      <div>
        <p className="eyebrow">ACADEMIC CASE STUDY DEMO</p>
        <h1>Maximal Extractable Value (MEV) in Ethereum</h1>
        <p className="page-subtitle">Interactive demonstration addressing the 3 core problem statements and showcasing how modern architectures overcome their limitations.</p>
      </div>
      <button className="btn secondary" onClick={refresh}><RefreshCw size={16} /> Refresh data</button>
    </div>

    <div className="stat-grid">
      <Stat label="Total simulations" value={summary?.total_experiments ?? '—'} note="Persisted experiment records" icon={Activity} />
      <Stat label="Problem statements" value="3 Focus Areas" note="User Exploit · Centralization · Consensus" icon={Blocks} tone="purple" />
      <Stat label="Solutions modeled" value="6 Advanced" note="Encrypted Mempools, ePBS, FOCIL, Smoothing" icon={ShieldCheck} tone="green" />
      <Stat label="API connection" value={health?.status === 'healthy' ? 'Healthy' : 'Active'} note={health?.service || 'FastAPI SQLite/PG'} icon={Gauge} tone={health?.status === 'healthy' ? 'green' : 'amber'} />
    </div>

    <Panel title="The 3 Interconnected Problem Statements" subtitle="Comprehensive mapping from the Ethereum MEV Case Study report">
      <div className="scorecard-grid">
        <div className="scorecard highlight">
          <div className="scorecard-title">
            <strong>Problem Statement 1: User Exploitation</strong>
            <span className="pill blue">PS1</span>
          </div>
          <p className="body-copy" style={{ marginBottom: 12 }}>
            <strong>The Problem:</strong> Public mempool visibility + block ordering discretion enables sandwich attacks on AMM swaps, causing excess slippage and extracting retail wealth.
          </p>
          <div className="scorecard-metric"><span>Traditional Defenses:</span><strong>Slippage limits, Private RPC</strong></div>
          <div className="scorecard-metric"><span>Limitation:</span><strong style={{ color: '#c04c4c' }}>Reverts waste gas; RPCs require centralized trust</strong></div>
          <div className="scorecard-metric"><span>How to Overcome:</span><strong style={{ color: '#13835c' }}>Encrypted Mempools (Threshold crypto) & Batch Auctions</strong></div>
          <div style={{ marginTop: 14 }}>
            <Button variant="secondary" onClick={() => setPage('protection')}>Explore PS1 Demo <ArrowRight size={14} /></Button>
          </div>
        </div>

        <div className="scorecard highlight">
          <div className="scorecard-title">
            <strong>Problem Statement 2: PBS & Centralization</strong>
            <span className="pill purple">PS2</span>
          </div>
          <p className="body-copy" style={{ marginBottom: 12 }}>
            <strong>The Problem:</strong> Economies of scale concentrate MEV extraction. Top builders control &gt;85% of blocks; relays intermediate &gt;90% of traffic.
          </p>
          <div className="scorecard-metric"><span>Status Quo:</span><strong>Proto-PBS (MEV-Boost off-chain relays)</strong></div>
          <div className="scorecard-metric"><span>Limitation:</span><strong style={{ color: '#c04c4c' }}>Relay single points of failure, builder OFAC censorship</strong></div>
          <div className="scorecard-metric"><span>How to Overcome:</span><strong style={{ color: '#13835c' }}>Enshrined PBS (EIP-7732) & Forward Inclusion Lists (FOCIL)</strong></div>
          <div style={{ marginTop: 14 }}>
            <Button variant="secondary" onClick={() => setPage('decentralization')}>Explore PS2 Demo <ArrowRight size={14} /></Button>
          </div>
        </div>

        <div className="scorecard highlight">
          <div className="scorecard-title">
            <strong>Problem Statement 3: Efficiency & Consensus</strong>
            <span className="pill green">PS3</span>
          </div>
          <p className="body-copy" style={{ marginBottom: 12 }}>
            <strong>The Problem:</strong> MEV fee wars congest networks, while large MEV spikes create incentives for validators to reorg blocks ("time-bandit" attacks).
          </p>
          <div className="scorecard-metric"><span>Status Quo:</span><strong>Private bundles (shifts auction off-chain)</strong></div>
          <div className="scorecard-metric"><span>Limitation:</span><strong style={{ color: '#c04c4c' }}>Block-to-block variance persists; reorg incentives remain</strong></div>
          <div className="scorecard-metric"><span>How to Overcome:</span><strong style={{ color: '#13835c' }}>MEV Smoothing Pools & MEV Burn (EIP-7545)</strong></div>
          <div style={{ marginTop: 14 }}>
            <Button variant="secondary" onClick={() => setPage('efficiency')}>Explore PS3 Demo <ArrowRight size={14} /></Button>
          </div>
        </div>

        <div className="scorecard">
          <div className="scorecard-title">
            <strong>Balanced Taxonomy: Beneficial vs. Toxic</strong>
            <span className="pill neutral">Taxonomy</span>
          </div>
          <p className="body-copy" style={{ marginBottom: 12 }}>
            <strong>Critical Insight:</strong> MEV is not monolithic. Blindly suppressing all MEV breaks DEX price parity and causes lending protocol liquidations to fail!
          </p>
          <div className="scorecard-metric"><span>Beneficial MEV:</span><strong style={{ color: '#19996d' }}>DEX Arbitrage & Lending Liquidations</strong></div>
          <div className="scorecard-metric"><span>Toxic MEV:</span><strong style={{ color: '#dc3e3e' }}>Sandwich Attacks & Priority Gas Auctions</strong></div>
          <div className="scorecard-metric"><span>Design Goal:</span><strong>Suppress toxic extraction while preserving arbitrage</strong></div>
          <div style={{ marginTop: 14 }}>
            <Button variant="secondary" onClick={() => setPage('efficiency')}>View Taxonomy Matrix <ArrowRight size={14} /></Button>
          </div>
        </div>
      </div>
    </Panel>

    <Panel title="The Ethereum MEV Supply Chain Lifecycle" subtitle="From user transaction submission to finalized consensus state">
      <div className="module-list">
        <div className="module-row"><span className="module-icon blue"><Wallet size={18}/></span><div><strong>1. User / RPC</strong><small>User signs transaction specifying swap details, token pair, and slippage tolerance.</small></div><span className="badge-traditional">Submission</span></div>
        <div className="module-row"><span className="module-icon purple"><EyeOff size={18}/></span><div><strong>2. Mempool vs Encrypted Mempool</strong><small>Public mempool exposes intent to searchers. Encrypted mempools conceal calldata with threshold keys.</small></div><span className="badge-overcome">Mitigation Point 1</span></div>
        <div className="module-row"><span className="module-icon amber"><Zap size={18}/></span><div><strong>3. Searchers & Arbitrageurs</strong><small>Bots simulate transactions, constructing bundles to capture DEX arbitrage, liquidations, or sandwiches.</small></div><span className="badge-traditional">Bundle Construction</span></div>
        <div className="module-row"><span className="module-icon purple"><Cpu size={18}/></span><div><strong>4. Block Builders (Oligopoly vs SUAVE)</strong><small>Builders aggregate order flow to produce maximum-profit blocks. Forward Inclusion Lists (FOCIL) force uncensored transactions.</small></div><span className="badge-overcome">Mitigation Point 2</span></div>
        <div className="module-row"><span className="module-icon blue"><Server size={18}/></span><div><strong>5. Relays vs Enshrined PBS (ePBS)</strong><small>MEV-Boost relies on trusted off-chain relays. ePBS (EIP-7732) enshrines payload verification natively in consensus.</small></div><span className="badge-overcome">Mitigation Point 3</span></div>
        <div className="module-row"><span className="module-icon green"><Scale size={18}/></span><div><strong>6. Proposers & MEV Smoothing</strong><small>Validator signs winning header. MEV Smoothing distributes rewards across the epoch to eliminate reorg incentives.</small></div><span className="badge-overcome">Mitigation Point 4</span></div>
      </div>
    </Panel>

    <div className="two-col">
      <Panel title="Simulation Runs by Module" subtitle="Distribution of persisted experiments">
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={moduleData} margin={{ top: 12, right: 12, left: -18, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#edf0f5"/>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} axisLine={false} tickLine={false}/>
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} axisLine={false} tickLine={false}/>
              <Tooltip/>
              <Bar dataKey="value" name="Simulations" radius={[6,6,0,0]}>
                {moduleData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Panel>

      <Panel title="Recent Experiment Runs" subtitle="Latest simulation database entries">
        {recent.length ? <div className="table-scroll"><table><thead><tr><th>Experiment</th><th>Module</th><th>Status</th></tr></thead><tbody>{recent.map(item => <tr key={item.id}><td><strong>#{item.id} · {item.scenario}</strong><small className="cell-sub">{new Date(item.created_at || Date.now()).toLocaleTimeString()}</small></td><td><span className="pill neutral">{item.module}</span></td><td><span className={`status ${item.status}`}>{item.status}</span></td></tr>)}</tbody></table></div> : <div className="empty-state"><Database size={26}/><strong>No saved experiments yet</strong><span>Simulate an experiment with saving enabled.</span></div>}
      </Panel>
    </div>
  </>
}

// ==============================================================================
// 2. PROBLEM STATEMENT 1: TRANSACTION ORDERING & USER EXPLOITATION
// ==============================================================================
function TradeProtection() {
  const [tab, setTab] = useState('sim') // 'sim' | 'walkthrough' | 'limitations'
  const [form, setForm] = useState({
    trade_amount_eth: 10,
    token_pair: 'ETH/USDC',
    pool_liquidity_eth: 500,
    slippage_tolerance_pct: 1.0,
    protection_type: 'encrypted_mempool',
    attacker_capital_eth: 100,
    scenario_label: 'Encrypted Mempool Defense',
    save_experiment: true,
  })
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const update = (key, value) => setForm(prev => ({ ...prev, [key]: value }))

  async function submit(e) {
    if (e) e.preventDefault()
    setBusy(true); setError('')
    try {
      const payload = {
        ...form,
        trade_amount_eth: form.trade_amount_eth !== '' ? Number(form.trade_amount_eth) : 10,
        pool_liquidity_eth: form.pool_liquidity_eth !== '' ? Number(form.pool_liquidity_eth) : 500,
        slippage_tolerance_pct: form.slippage_tolerance_pct !== '' ? Number(form.slippage_tolerance_pct) : 1.0,
        attacker_capital_eth: form.attacker_capital_eth !== '' ? Number(form.attacker_capital_eth) : 100,
      }
      const res = await api.tradeProtection(payload)
      setResult(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function applyPreset(type, label, trade = 10, pool = 500, slip = 1.0) {
    const updated = {
      ...form,
      protection_type: type,
      scenario_label: label,
      trade_amount_eth: trade,
      pool_liquidity_eth: pool,
      slippage_tolerance_pct: slip,
    }
    setForm(updated)
    setBusy(true); setError('')
    api.tradeProtection(updated)
      .then(setResult)
      .catch(err => setError(err.message))
      .finally(() => setBusy(false))
  }

  useEffect(() => {
    // Initial run with default
    submit()
  }, [])

  const chartData = useMemo(() => {
    if (!result) return []
    return [
      { name: 'Expected', price: result.unprotected.expected_price_eth, label: 'Fair baseline' },
      { name: 'Unprotected', price: result.unprotected.user_execution_price_eth, label: 'After front-run' },
      { name: 'Protected', price: result.protected.user_execution_price_eth, label: 'With protection' },
    ]
  }, [result])

  return <>
    <div className="page-title-row">
      <div>
        <p className="eyebrow">PROBLEM STATEMENT 1 · USER EXPLOITATION</p>
        <h1>Transaction Ordering & Sandwich Defense</h1>
        <p className="page-subtitle">Demonstrate how transaction ordering in public mempools enables sandwich attacks, and compare traditional mitigations with paradigm-shifting cryptographic solutions.</p>
      </div>
      <span className="pill blue">DEX AMM Model</span>
    </div>

    <div className="subnav-bar">
      <button className={`subnav-btn ${tab==='sim'?'active':''}`} onClick={()=>setTab('sim')}><ShieldCheck size={15}/> Interactive Simulator</button>
      <button className={`subnav-btn ${tab==='walkthrough'?'active':''}`} onClick={()=>setTab('walkthrough')}><FileText size={15}/> Worked Numerical Example (Alice vs Bob)</button>
      <button className={`subnav-btn ${tab==='limitations'?'active':''}`} onClick={()=>setTab('limitations')}><Sparkles size={15}/> How Next-Gen Overcomes Limitations</button>
    </div>

    {tab === 'sim' && <>
      <Panel title="Select Demonstration Scenario" subtitle="Click any preset to simulate how different defenses perform against an identical sandwich attack">
        <div className="preset-grid">
          <button className="preset-btn" onClick={() => applyPreset('none', 'Unprotected Mempool Baseline')}>
            <span className="badge-traditional">BASELINE</span>
            <strong>No Protection</strong>
            <small>Worst-case public mempool sandwich (100% loss)</small>
          </button>
          <button className="preset-btn" onClick={() => applyPreset('slippage_guard', 'Slippage Guard Revert', 10, 500, 0.5)}>
            <span className="badge-traditional">TRADITIONAL</span>
            <strong>Slippage Guard (0.5%)</strong>
            <small>Caps loss or causes on-chain revert (gas wasted)</small>
          </button>
          <button className="preset-btn" onClick={() => applyPreset('private_mempool', 'Private Mempool RPC')}>
            <span className="badge-traditional">TRADITIONAL</span>
            <strong>Private RPC (Flashbots)</strong>
            <small>Hides tx from public mempool, requires trusting relay</small>
          </button>
          <button className="preset-btn" style={{ borderColor: '#536de0', background: '#f5f7ff' }} onClick={() => applyPreset('encrypted_mempool', 'Encrypted Mempool (Threshold Crypto)')}>
            <span className="badge-overcome">OVERCOMES LIMITATION</span>
            <strong>Encrypted Mempool</strong>
            <small>Cryptographic privacy until block finalized (0% trust)</small>
          </button>
          <button className="preset-btn" style={{ borderColor: '#536de0', background: '#f5f7ff' }} onClick={() => applyPreset('batch_auction', 'Batch Auction (CoW Swap)', 20, 800, 0.8)}>
            <span className="badge-overcome">OVERCOMES LIMITATION</span>
            <strong>Batch Auction</strong>
            <small>Uniform clearing price p* (0 ordering advantage)</small>
          </button>
          <button className="preset-btn" style={{ borderColor: '#536de0', background: '#f5f7ff' }} onClick={() => applyPreset('mev_share', 'MEV-Share 90% User Rebate')}>
            <span className="badge-overcome">OVERCOMES LIMITATION</span>
            <strong>MEV-Share Rebates</strong>
            <small>90% of extracted MEV rebated to user cash balance</small>
          </button>
        </div>
      </Panel>

      <div className="two-col form-layout">
        <Panel title="Trade Configuration" subtitle="Configure AMM pool liquidity, trade size, and mitigation mechanism">
          <form className="form-grid" onSubmit={submit} noValidate>
            <label>Trade amount (ETH)<input type="number" step="any" min="0.001" value={form.trade_amount_eth} onChange={e=>update('trade_amount_eth', e.target.value === '' ? '' : e.target.value)}/></label>
            <label>Token pair<input value={form.token_pair} onChange={e=>update('token_pair', e.target.value)} maxLength="20"/></label>
            <label>Pool liquidity (ETH)<input type="number" step="any" min="0.001" value={form.pool_liquidity_eth} onChange={e=>update('pool_liquidity_eth', e.target.value === '' ? '' : e.target.value)}/></label>
            <label>Slippage tolerance (%)<input type="number" step="any" min="0" max="50" value={form.slippage_tolerance_pct} onChange={e=>update('slippage_tolerance_pct', e.target.value === '' ? '' : e.target.value)}/></label>
            <label>Attacker capital (ETH)<input type="number" step="any" min="0" value={form.attacker_capital_eth} onChange={e=>update('attacker_capital_eth', e.target.value === '' ? '' : e.target.value)}/></label>
            <label>Protection mechanism
              <select value={form.protection_type} onChange={e=>update('protection_type', e.target.value)}>
                <optgroup label="Baseline & Traditional">
                  <option value="none">No protection (Public mempool)</option>
                  <option value="slippage_guard">Slippage guard (On-chain revert)</option>
                  <option value="private_mempool">Private mempool (Flashbots Protect)</option>
                  <option value="commit_reveal">Commit–reveal (2-phase latency)</option>
                  <option value="time_lock">Time-lock TWAP (Multi-block)</option>
                </optgroup>
                <optgroup label="Advanced Solutions (Overcoming Limitations)">
                  <option value="encrypted_mempool">Encrypted mempool (Threshold crypto)</option>
                  <option value="batch_auction">Batch auction (Uniform clearing price)</option>
                  <option value="mev_share">MEV-Share (90% user rebate)</option>
                </optgroup>
              </select>
            </label>
            <label className="span-2">Scenario label<input value={form.scenario_label} onChange={e=>update('scenario_label', e.target.value)} maxLength="100" required/></label>
            <label className="check-line span-2"><input type="checkbox" checked={form.save_experiment} onChange={e=>update('save_experiment', e.target.checked)}/> Save simulation to database history</label>
            <div className="span-2"><Button loading={busy} type="submit">Run Trade Simulation <ChevronRight size={16}/></Button></div>
          </form>
          {error && <Notice type="error">{error}</Notice>}
        </Panel>

        <Panel title="Simulation Results" subtitle="Financial impact: Unprotected attack baseline vs Protected outcome">
          {result ? <>
            <div className="result-kpis">
              <div><span>MEV risk level</span><strong style={{ color: result.mev_risk.risk_level === 'high' ? '#c04c4c' : '#19996d' }}>{result.mev_risk.risk_level.toUpperCase()} ({result.mev_risk.attack_type})</strong></div>
              <div><span>Protection effectiveness</span><strong style={{ color: '#4f73e8' }}>{pct(result.protected.protection_effectiveness_pct)}</strong></div>
              <div><span>Baseline loss (Unprotected)</span><strong style={{ color: '#c04c4c' }}>{money(result.unprotected.user_loss_eth, 4)} ETH</strong></div>
              <div><span>Protected loss</span><strong style={{ color: result.protected.user_loss_eth === 0 ? '#19996d' : '#28354c' }}>{money(result.protected.user_loss_eth, 4)} ETH</strong></div>
            </div>

            {result.protected.user_rebate_eth > 0 && <div className="notice" style={{ background: '#e8f8f1', borderColor: '#b1ebd2', color: '#106a4a' }}>
              <Sparkles size={17} />
              <span><strong>MEV-Share Cash Rebate:</strong> User receives an on-chain refund of <strong>+{money(result.protected.user_rebate_eth, 4)} ETH</strong> directly back to their wallet!</span>
            </div>}

            <div className="chart-wrap" style={{ marginTop: 15 }}>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#edf0f5"/>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} axisLine={false} tickLine={false}/>
                  <YAxis domain={['auto', 'auto']} tick={{ fontSize: 11 }} axisLine={false} tickLine={false}/>
                  <Tooltip/>
                  <Bar dataKey="price" name="Execution price" fill="#566fe5" radius={[6,6,0,0]}>
                    <Cell fill="#64748b" />
                    <Cell fill="#dc3e3e" />
                    <Cell fill="#19996d" />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="overcome-card">
              <h4>
                <Sparkles size={16}/>
                {['encrypted_mempool', 'batch_auction', 'mev_share'].includes(form.protection_type) ?
                  'How this Next-Gen Solution Overcomes Limitations' : 'Limitation of this Traditional Approach'}
              </h4>
              <p>
                {form.protection_type === 'encrypted_mempool' && 'Overcomes the private RPC trust bottleneck. Cryptographic threshold encryption conceals transaction payload and trade direction until the block ordering commitment is sealed. Public searchers see zero calldata, completely preventing sandwiching without trusting any centralized builder.'}
                {form.protection_type === 'batch_auction' && 'Overcomes continuous-time transaction ordering exploitation. All orders in a batch are matched simultaneously at a single uniform clearing price p*. Intra-block ordering advantage drops to zero — no bot can sandwich or front-run because everyone receives the exact same clearing rate.'}
                {form.protection_type === 'mev_share' && 'Overcomes the user-loss penalty. Instead of letting bots siphon 100% of the arbitrage spread, MEV-Share enforces an auction where searchers must return 90% of extracted value directly back to the trade initiator as an on-chain rebate.'}
                {form.protection_type === 'slippage_guard' && 'Limitation: Slippage guards only bound the loss (the attacker can still extract up to the tolerance limit) or cause the trade to revert. On reverts, the user pays gas fees without getting executed.'}
                {form.protection_type === 'private_mempool' && 'Limitation: Requires trusting the private RPC operator (e.g. Flashbots Protect) not to leak order flow or collude with internal searchers. Furthermore, private order flow leads to exclusive builder concentration.'}
                {form.protection_type === 'commit_reveal' && 'Limitation: Introduces a multi-block latency delay (block N commit, block N+1 reveal). If block reveal times are predictable, validators can still collude.'}
                {form.protection_type === 'time_lock' && 'Limitation: TWAP order splitting is slow and only practical for institutional swap sizes across dozens of blocks.'}
                {form.protection_type === 'none' && 'Limitation: Public mempool visibility gives searchers complete information asymmetry to front-run and sandwich retail swaps.'}
              </p>
            </div>
          </> : <div className="empty-state"><ShieldCheck size={28}/><strong>Ready to simulate</strong><span>Select parameters and click Run Trade Simulation.</span></div>}
        </Panel>
      </div>
    </>}

    {tab === 'walkthrough' && <Panel title="Worked Numerical Example: Anatomy of a Sandwich Attack" subtitle="Directly reproducing Section 4.3 and Figure 3 of the Ethereum MEV Case Study report">
      <div className="metric-explainer">
        <div className="walkthrough-step">
          <span className="step-num">1</span>
          <div className="step-content">
            <strong>Initial AMM Pool State</strong>
            <p>A constant-product AMM pool has an initial price of <strong>1 ETH = 2,000 USDC</strong>. Alice broadcasts a large market swap of <strong>50,000 USDC</strong> to purchase ETH.</p>
          </div>
        </div>
        <div className="walkthrough-step">
          <span className="step-num">2</span>
          <div className="step-content">
            <strong>Bob's Front-Run Buy (Attacker)</strong>
            <p>Bob (searcher bot) observes Alice's pending trade in the public mempool. Bob pays a higher priority fee to buy ETH with <strong>20,000 USDC</strong> right before Alice, pushing the pool price up to <strong>1 ETH = 2,080 USDC</strong>.</p>
          </div>
        </div>
        <div className="walkthrough-step">
          <span className="step-num">3</span>
          <div className="step-content">
            <strong>Alice's Execution at Inflated Price (Victim)</strong>
            <p>Alice's trade executes at an average manipulated price of <strong>2,150 USDC per ETH</strong>. Alice loses <strong>approx. 7.5% vs fair price</strong>, suffering <strong>~3,750 USDC in excess slippage loss</strong>.</p>
          </div>
        </div>
        <div className="walkthrough-step">
          <span className="step-num">4</span>
          <div className="step-content">
            <strong>Bob's Back-Run Sell (Profit Capture)</strong>
            <p>Bob immediately sells his ETH back into the pool right after Alice's swap, capturing gross proceeds of ~1,050 USDC. Subtracting $40 in gas costs, Bob pockets <strong>~$1,010 USDC in net MEV profit</strong>.</p>
          </div>
        </div>
        <div className="walkthrough-step" style={{ borderBottom: 0 }}>
          <span className="step-num" style={{ background: '#19996d' }}>5</span>
          <div className="step-content">
            <strong style={{ color: '#15865e' }}>Outcome Under Next-Gen Mitigations (Encrypted Mempool / Batch Auction)</strong>
            <p>With <strong>Encrypted Mempools</strong> (Shutter Network), Bob cannot observe Alice's transaction before the block is sealed. With <strong>Batch Auctions</strong> (CoW Swap), Alice and Bob trade at the exact same uniform price $p^*$. In both cases, <strong>Alice loses 0 USDC</strong>, and Bob earns <strong>0 USDC</strong>.</p>
          </div>
        </div>
      </div>
    </Panel>}

    {tab === 'limitations' && <Panel title="Paradigm Shifts: Overcoming PS1 Limitations" subtitle="Architectural comparison between traditional defenses and modern Ethereum solutions">
      <div className="scorecard-grid">
        <div className="scorecard">
          <div className="scorecard-title">
            <strong>Traditional Defense: Slippage Guard</strong>
            <span className="badge-traditional">TRADITIONAL</span>
          </div>
          <div className="scorecard-metric"><span>Mechanism:</span><strong>Smart-contract revert on price threshold</strong></div>
          <div className="scorecard-metric"><span>Limitation:</span><strong style={{ color: '#c04c4c' }}>Does not prevent attack; bot extracts up to cap; reverts waste gas</strong></div>
          <div className="scorecard-metric"><span>User Impact:</span><strong>Failed trades, unrefunded gas expenditures</strong></div>
        </div>

        <div className="scorecard">
          <div className="scorecard-title">
            <strong>Traditional Defense: Private RPC (Flashbots Protect)</strong>
            <span className="badge-traditional">TRADITIONAL</span>
          </div>
          <div className="scorecard-metric"><span>Mechanism:</span><strong>Direct submission to builders, bypassing mempool</strong></div>
          <div className="scorecard-metric"><span>Limitation:</span><strong style={{ color: '#c04c4c' }}>Requires 100% trust in RPC operator; centralizes private order flow</strong></div>
          <div className="scorecard-metric"><span>User Impact:</span><strong>Leakage risk if builder/relay colludes</strong></div>
        </div>

        <div className="scorecard highlight">
          <div className="scorecard-title">
            <strong>Next-Gen: Encrypted Mempools</strong>
            <span className="badge-overcome">OVERCOMES LIMITATION</span>
          </div>
          <div className="scorecard-metric"><span>Mechanism:</span><strong>Threshold cryptography (e.g. Shutter Network / EIP-7732)</strong></div>
          <div className="scorecard-metric"><span>How it Overcomes:</span><strong style={{ color: '#13835c' }}>Zero trust required. Builders commit ordering before decryption key is revealed</strong></div>
          <div className="scorecard-metric"><span>User Impact:</span><strong>100% mathematical immunity from front-running</strong></div>
        </div>

        <div className="scorecard highlight">
          <div className="scorecard-title">
            <strong>Next-Gen: Batch Auctions & Uniform Price</strong>
            <span className="badge-overcome">OVERCOMES LIMITATION</span>
          </div>
          <div className="scorecard-metric"><span>Mechanism:</span><strong>Discrete batch clearing (e.g. CoW Swap / Gnosis)</strong></div>
          <div className="scorecard-metric"><span>How it Overcomes:</span><strong style={{ color: '#13835c' }}>All trades in batch execute at identical uniform price p*</strong></div>
          <div className="scorecard-metric"><span>User Impact:</span><strong>Transaction ordering advantage is completely eliminated</strong></div>
        </div>
      </div>
    </Panel>}
  </>
}

// ==============================================================================
// 3. PROBLEM STATEMENT 2: CENTRALIZATION & PBS EVOLUTION
// ==============================================================================
function Decentralization() {
  const [tab, setTab] = useState('epbs') // 'epbs' | 'baseline' | 'outage'
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [sample, setSample] = useState(null)
  const [concResult, setConcResult] = useState(null)
  const [epbsResult, setEpbsResult] = useState(null)
  const [outageResult, setOutageResult] = useState(null)

  // ePBS simulation inputs
  const [slots, setSlots] = useState(100)
  const [relayFailureProb, setRelayFailureProb] = useState(0.05)
  const [censorshipRate, setCensorshipRate] = useState(0.45)

  async function loadSample() {
    if (sample) return sample
    const data = await api.sampleData()
    setSample(data)
    return data
  }

  async function runEpbs() {
    setBusy(true); setError('')
    try {
      const res = await api.epbsCompare({
        num_simulated_slots: Math.max(10, Math.min(1000, Math.round(Number(slots) || 100))),
        relay_failure_probability: Math.max(0, Math.min(0.5, Number(relayFailureProb) || 0.05)),
        builder_censorship_rate: Math.max(0, Math.min(1.0, Number(censorshipRate) || 0.45)),
        save_experiment: true,
      })
      setEpbsResult(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function runConcentration() {
    setBusy(true); setError('')
    try {
      const data = await loadSample()
      const res = await api.decentralization({
        source_type: 'illustrative_sample',
        measurement_window: data.measurement_window,
        builder_observations: data.builder_observations,
        relay_observations: data.relay_observations,
        save_experiment: true,
      })
      setConcResult(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function runOutage() {
    setBusy(true); setError('')
    try {
      const data = await loadSample()
      const res = await api.outage({
        participant_type: 'builder',
        outage_participant_id: 'builder_alpha',
        baseline_observations: data.builder_observations,
        save_experiment: true,
      })
      setOutageResult(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    runEpbs()
  }, [])

  const epbsChartData = useMemo(() => {
    if (!epbsResult) return []
    return [
      { name: 'Proto-PBS (MEV-Boost)', missedRate: epbsResult.proto_pbs_mev_boost.missed_slot_rate_pct, censorRate: epbsResult.proto_pbs_mev_boost.censored_transactions_pct, hhi: epbsResult.proto_pbs_mev_boost.builder_hhi },
      { name: 'Enshrined PBS (ePBS)', missedRate: epbsResult.enshrined_pbs_eip7732.missed_slot_rate_pct, censorRate: epbsResult.enshrined_pbs_eip7732.censored_transactions_pct, hhi: epbsResult.enshrined_pbs_eip7732.builder_hhi },
      { name: 'ePBS + Inclusion Lists', missedRate: epbsResult.epbs_with_inclusion_lists.missed_slot_rate_pct, censorRate: epbsResult.epbs_with_inclusion_lists.censored_transactions_pct, hhi: epbsResult.epbs_with_inclusion_lists.builder_hhi },
      { name: 'SUAVE (Decentralized)', missedRate: epbsResult.suave_decentralized_builder.missed_slot_rate_pct, censorRate: epbsResult.suave_decentralized_builder.censored_transactions_pct, hhi: epbsResult.suave_decentralized_builder.builder_hhi },
    ]
  }, [epbsResult])

  return <>
    <div className="page-title-row">
      <div>
        <p className="eyebrow">PROBLEM STATEMENT 2 · PBS & CENTRALIZATION</p>
        <h1>Validator/Builder Centralization & ePBS Evolution</h1>
        <p className="page-subtitle">Evaluate how MEV creates economies of scale concentrating builders and relays, and simulate how Enshrined PBS (EIP-7732) and Forward Inclusion Lists (FOCIL) overcome these bottlenecks.</p>
      </div>
      <span className="pill purple">PBS Architecture</span>
    </div>

    <div className="subnav-bar">
      <button className={`subnav-btn ${tab==='epbs'?'active':''}`} onClick={()=>setTab('epbs')}><Sparkles size={15}/> Enshrined PBS & Inclusion Lists (Overcoming Limitations)</button>
      <button className={`subnav-btn ${tab==='baseline'?'active':''}`} onClick={()=>setTab('baseline')}><Network size={15}/> MEV-Boost Baseline Concentration (Sample Data)</button>
      <button className={`subnav-btn ${tab==='outage'?'active':''}`} onClick={()=>setTab('outage')}><AlertTriangle size={15}/> Builder Outage Resilience</button>
    </div>

    {tab === 'epbs' && <>
      <div className="two-col form-layout">
        <Panel title="Stress-Test Configuration" subtitle="Simulate relay downtime, censorship pressure, and architectural shifts">
          <div className="slider-container">
            <div className="slider-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Simulated Validator Proposal Slots:</span>
              <input type="number" step="any" min="10" max="1000" style={{ width: 85, padding: '3px 6px', fontSize: 12, textAlign: 'right' }} value={slots} onChange={e=>setSlots(e.target.value === '' ? '' : Number(e.target.value))}/>
            </div>
            <input className="styled-slider" type="range" min="10" max="1000" step="any" value={Number(slots) || 100} onChange={e=>setSlots(Number(e.target.value))}/>
          </div>

          <div className="slider-container">
            <div className="slider-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Relay Outage Rate (%):</span>
              <input type="number" step="any" min="0" max="50" style={{ width: 85, padding: '3px 6px', fontSize: 12, textAlign: 'right', color: Number(relayFailureProb) > 0.08 ? '#c04c4c' : '#425bd1' }} value={Number((Number(relayFailureProb || 0) * 100).toFixed(2))} onChange={e=>setRelayFailureProb(e.target.value === '' ? '' : Number(e.target.value) / 100)}/>
            </div>
            <input className="styled-slider" type="range" min="0" max="0.5" step="any" value={Number(relayFailureProb) || 0} onChange={e=>setRelayFailureProb(Number(e.target.value))}/>
            <small style={{ color: '#8895ab', fontSize: 10 }}>Modeled probability that an off-chain trusted relay drops payload connection.</small>
          </div>

          <div className="slider-container">
            <div className="slider-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Builder Censorship Proportion (%):</span>
              <input type="number" step="any" min="0" max="100" style={{ width: 85, padding: '3px 6px', fontSize: 12, textAlign: 'right', color: Number(censorshipRate) > 0.4 ? '#c04c4c' : '#425bd1' }} value={Number((Number(censorshipRate || 0) * 100).toFixed(2))} onChange={e=>setCensorshipRate(e.target.value === '' ? '' : Number(e.target.value) / 100)}/>
            </div>
            <input className="styled-slider" type="range" min="0" max="1.0" step="any" value={Number(censorshipRate) || 0} onChange={e=>setCensorshipRate(Number(e.target.value))}/>
            <small style={{ color: '#8895ab', fontSize: 10 }}>Fraction of dominant block builders filtering sanctioned transactions.</small>
          </div>

          <Button loading={busy} onClick={runEpbs}>Simulate Architectural Comparison <ChevronRight size={16}/></Button>
          {error && <Notice type="error">{error}</Notice>}
        </Panel>

        <Panel title="Comparative Resilience Metrics" subtitle="How each architecture responds to relay downtime and censorship">
          {epbsResult ? <>
            <div className="result-kpis">
              <div><span>Proto-PBS missed slots</span><strong style={{ color: '#c04c4c' }}>{epbsResult.proto_pbs_mev_boost.missed_slots_count} ({pct(epbsResult.proto_pbs_mev_boost.missed_slot_rate_pct)})</strong></div>
              <div><span>ePBS missed slots</span><strong style={{ color: '#19996d' }}>0 ({pct(0)})</strong></div>
              <div><span>Censorship under Proto-PBS</span><strong style={{ color: '#c04c4c' }}>{pct(epbsResult.proto_pbs_mev_boost.censored_transactions_pct)}</strong></div>
              <div><span>Censorship under FOCIL</span><strong style={{ color: '#19996d' }}>0.0% (Inclusion List)</strong></div>
            </div>

            <div className="chart-wrap" style={{ marginTop: 15 }}>
              <ResponsiveContainer width="100%" height={230}>
                <BarChart data={epbsChartData} margin={{ top: 12, right: 12, left: -15, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#edf0f5"/>
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} axisLine={false} tickLine={false}/>
                  <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false}/>
                  <Tooltip/>
                  <Legend wrapperStyle={{ fontSize: 11 }}/>
                  <Bar dataKey="missedRate" name="Missed slot rate (%)" fill="#e9a23b" radius={[4,4,0,0]}/>
                  <Bar dataKey="censorRate" name="Censorship rate (%)" fill="#dc3e3e" radius={[4,4,0,0]}/>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </> : <div className="empty-state"><LoaderCircle className="spin" size={26}/></div>}
        </Panel>
      </div>

      {epbsResult && <Panel title="Architectural Breakdown: Overcoming Problem Statement 2" subtitle="Detailed comparison across the 4 eras of Proposer-Builder Separation">
        <div className="scorecard-grid">
          <div className="scorecard">
            <div className="scorecard-title">
              <strong>1. Proto-PBS (MEV-Boost / Status Quo)</strong>
              <span className="badge-traditional">CURRENT</span>
            </div>
            <div className="scorecard-metric"><span>Trust Model:</span><strong>Out-of-Protocol Trusted Relays</strong></div>
            <div className="scorecard-metric"><span>Relay Dependency:</span><strong style={{ color: '#c04c4c' }}>Yes (3 dominant relays control &gt;90%)</strong></div>
            <div className="scorecard-metric"><span>Missed Slot Risk:</span><strong style={{ color: '#c04c4c' }}>High ({pct(epbsResult.proto_pbs_mev_boost.missed_slot_rate_pct)})</strong></div>
            <div className="scorecard-metric"><span>Censorship:</span><strong style={{ color: '#c04c4c' }}>Vulnerable ({pct(epbsResult.proto_pbs_mev_boost.censored_transactions_pct)})</strong></div>
            <div className="scorecard-metric"><span>Builder HHI:</span><strong>3,108 (High Concentration)</strong></div>
            <p className="body-copy" style={{ marginTop: 8, fontSize: 11 }}><strong>Limitation:</strong> Relays are single points of failure. If a relay crashes or delays a block, the validator misses its slot and forfeits rewards.</p>
          </div>

          <div className="scorecard highlight">
            <div className="scorecard-title">
              <strong>2. Enshrined PBS (ePBS / EIP-7732)</strong>
              <span className="badge-overcome">OVERCOMES RELAY TRUST</span>
            </div>
            <div className="scorecard-metric"><span>Trust Model:</span><strong>Native Consensus (Payload Timeliness Committee)</strong></div>
            <div className="scorecard-metric"><span>Relay Dependency:</span><strong style={{ color: '#13835c' }}>None (0 Relays required)</strong></div>
            <div className="scorecard-metric"><span>Missed Slot Risk:</span><strong style={{ color: '#13835c' }}>0.0% (In-protocol consensus fallback)</strong></div>
            <div className="scorecard-metric"><span>Latency:</span><strong>~45ms (reduced by ~250ms)</strong></div>
            <div className="scorecard-metric"><span>Builder HHI:</span><strong>3,108</strong></div>
            <p className="body-copy" style={{ marginTop: 8, fontSize: 11 }}><strong>How it Overcomes:</strong> Enshrines PBS directly into Ethereum beacon consensus. Builders commit payloads on-chain; PTC committees verify arrival. Eliminates off-chain relays entirely!</p>
          </div>

          <div className="scorecard highlight">
            <div className="scorecard-title">
              <strong>3. ePBS + Inclusion Lists (FOCIL / EIP-7547)</strong>
              <span className="badge-overcome">OVERCOMES CENSORSHIP</span>
            </div>
            <div className="scorecard-metric"><span>Trust Model:</span><strong>Consensus-Forced Transaction Inclusion</strong></div>
            <div className="scorecard-metric"><span>Relay Dependency:</span><strong style={{ color: '#13835c' }}>None</strong></div>
            <div className="scorecard-metric"><span>Censorship Rate:</span><strong style={{ color: '#13835c' }}>0.0% (Consensus Guaranteed)</strong></div>
            <div className="scorecard-metric"><span>Validator Role:</span><strong>Proposers mandate transactions</strong></div>
            <div className="scorecard-metric"><span>Builder HHI:</span><strong>2,850</strong></div>
            <p className="body-copy" style={{ marginTop: 8, fontSize: 11 }}><strong>How it Overcomes:</strong> Decentralized validators create an inclusion list of pending transactions. Builders MUST include them; otherwise the block is invalid. Neutralizes builder censorship power!</p>
          </div>

          <div className="scorecard highlight">
            <div className="scorecard-title">
              <strong>4. SUAVE / Decentralized TEE Builders</strong>
              <span className="badge-overcome">OVERCOMES OLIGOPOLY</span>
            </div>
            <div className="scorecard-metric"><span>Trust Model:</span><strong>Confidential Compute (TEEs)</strong></div>
            <div className="scorecard-metric"><span>Builder HHI:</span><strong style={{ color: '#13835c' }}>820 (Unconcentrated, Competitive)</strong></div>
            <div className="scorecard-metric"><span>Private Order Flow:</span><strong>Democratized across open TEE nodes</strong></div>
            <div className="scorecard-metric"><span>Censorship:</span><strong style={{ color: '#13835c' }}>0.0%</strong></div>
            <div className="scorecard-metric"><span>Propagation Latency:</span><strong>~65ms</strong></div>
            <p className="body-copy" style={{ marginTop: 8, fontSize: 11 }}><strong>How it Overcomes:</strong> Unbundles block building from monopolistic entities into decentralized confidential hardware enclaves. Drops HHI from 3,108 to 820, democratizing private order flow.</p>
          </div>
        </div>
      </Panel>}
    </>}

    {tab === 'baseline' && <>
      <div className="two-col">
        <Panel title="Illustrative Sample Dataset" subtitle="1,000 synthetic demonstration blocks matching Section 7 and 12 of report">
          <p className="body-copy">Analyze market share and Herfindahl–Hirschman Index (HHI) for builders and relays. The sample is synthetic for educational verification.</p>
          <Button loading={busy} onClick={runConcentration}>Analyze Sample Dataset <ChevronRight size={16}/></Button>
          {error && <Notice type="error">{error}</Notice>}
        </Panel>
        <Panel title="HHI Concentration Benchmarks" subtitle="Antitrust & economic standards for market concentration">
          <div className="metric-explainer">
            <div><strong>HHI &lt; 1,500 (Unconcentrated):</strong><span>Healthy competitive marketplace with low systemic risk.</span></div>
            <div><strong>HHI 1,500 – 2,500 (Moderate):</strong><span>Moderate concentration; emerging economies of scale.</span></div>
            <div><strong>HHI &gt; 2,500 (Highly Concentrated):</strong><span>Oligopoly. Builder HHI = 3,108 and Relay HHI = 4,450 represent acute centralization risk.</span></div>
          </div>
        </Panel>
      </div>

      {concResult && <>
        <div className="stat-grid compact">
          <Stat label="Builder diversity" value={concResult.builder_metrics?.distinct_participants_count ?? '6'} note="Distinct builders" icon={Blocks}/>
          <Stat label="Largest builder share" value={pct(concResult.builder_metrics?.largest_share_percentage ?? 45)} note="builder_alpha" icon={ArrowUpRight} tone="purple"/>
          <Stat label="Builder HHI" value={concResult.builder_metrics?.hhi ?? 3108} note="Highly Concentrated" icon={Network} tone="amber"/>
          <Stat label="Relay HHI" value={concResult.relay_metrics?.hhi ?? 4450} note="Critical Concentration" icon={Database} tone="red"/>
        </div>
        <Panel title="Builder Market Share Distribution" subtitle="6 observed builders across 1,000 blocks">
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={concResult.builder_metrics?.participants || []} margin={{ top: 10, right: 10, left: -15, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#edf0f5"/>
                <XAxis dataKey="builder_id" tick={{ fontSize: 11 }} axisLine={false} tickLine={false}/>
                <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false}/>
                <Tooltip/>
                <Bar dataKey="market_share_percentage" name="Market Share (%)" fill="#7b61d1" radius={[6,6,0,0]}/>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </>}
    </>}

    {tab === 'outage' && <Panel title="Builder Outage Simulation" subtitle="Simulate sudden failure or regulatory sanction of dominant builder_alpha">
      <p className="body-copy">What happens when the largest block builder (builder_alpha, 45% market share) goes offline? Test how market shares re-normalize among surviving participants.</p>
      <div style={{ marginBottom: 15 }}>
        <Button loading={busy} onClick={runOutage}>Simulate builder_alpha Outage <ChevronRight size={16}/></Button>
      </div>
      {outageResult && <>
        <div className="result-kpis">
          <div><span>Baseline blocks lost</span><strong>{outageResult.impact_summary?.baseline_blocks_lost}</strong></div>
          <div><span>Baseline share lost</span><strong>{pct(outageResult.impact_summary?.baseline_share_lost_pct)}</strong></div>
          <div><span>Surviving participants</span><strong>{outageResult.impact_summary?.surviving_participants_count}</strong></div>
          <div><span>Surviving HHI</span><strong>{money(outageResult.surviving_metrics?.hhi, 1)}</strong></div>
        </div>
        <div className="overcome-card">
          <h4><AlertTriangle size={16}/> Resilience Analysis</h4>
          <p>{outageResult.resilience_notes?.[0] || 'Remaining builders absorb orphaned blocks, but temporary slot misses occur under Proto-PBS due to relay latency. Enshrined PBS handles builder outages natively via consensus fallback.'}</p>
        </div>
      </>}
    </Panel>}
  </>
}

// ==============================================================================
// 4. PROBLEM STATEMENT 3: NETWORK EFFICIENCY & ECONOMIC SECURITY
// ==============================================================================
function Efficiency() {
  const [tab, setTab] = useState('reorg') // 'reorg' | 'taxonomy' | 'queue'
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  // Reorg simulation inputs
  const [spikeEth, setSpikeEth] = useState(50)
  const [validatorStake, setValidatorStake] = useState(15)
  const [reorgResult, setReorgResult] = useState(null)

  // Taxonomy data
  const [taxonomyData, setTaxonomyData] = useState(null)

  // Queue simulation inputs
  const [queueForm, setQueueForm] = useState({
    transaction_count: 60,
    block_capacity: 10,
    average_gas_used: 150000,
    base_fee_gwei: 20,
    priority_fee_gwei: 2,
    priority_fee_spread_gwei: 1,
    block_time_seconds: 12,
    max_blocks: 4,
    scenario: 'submission_comparison',
    submission_method: 'priority_fee_competition',
    save_experiment: true,
  })
  const [queueResult, setQueueResult] = useState(null)

  async function runReorgSimulation() {
    setBusy(true); setError('')
    try {
      const res = await api.reorgSmoothing({
        mev_spike_eth: Math.max(0.1, Number(spikeEth) || 50),
        validator_stake_pct: Math.max(1, Math.min(49, Number(validatorStake) || 15)),
        block_subsidy_eth: 0.06,
        save_experiment: true,
      })
      setReorgResult(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function loadTaxonomy() {
    if (taxonomyData) return
    try {
      const res = await api.taxonomy()
      setTaxonomyData(res)
    } catch (err) {
      console.error(err)
    }
  }

  async function runQueueSimulation(e) {
    if (e) e.preventDefault()
    setBusy(true); setError('')
    try {
      const payload = {
        ...queueForm,
        transaction_count: Math.max(1, Math.round(Number(queueForm.transaction_count) || 40)),
        block_capacity: Math.max(1, Math.round(Number(queueForm.block_capacity) || 10)),
        base_fee_gwei: Math.max(0, Number(queueForm.base_fee_gwei) || 20),
        priority_fee_gwei: Math.max(0, Number(queueForm.priority_fee_gwei) || 2),
        max_blocks: Math.max(1, Math.round(Number(queueForm.max_blocks) || 4)),
      }
      const res = await api.efficiency(payload)
      setQueueResult(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    runReorgSimulation()
    loadTaxonomy()
  }, [])

  const reorgChartData = useMemo(() => {
    if (!reorgResult) return []
    return [
      { name: 'Unsmoothed Status Quo', threat: reorgResult.unsmoothed_status_quo.reorg_threat_score_pct, payoff: reorgResult.unsmoothed_status_quo.proposer_payoff_eth },
      { name: 'MEV Smoothing Pool', threat: reorgResult.mev_smoothing_pool.reorg_threat_score_pct, payoff: reorgResult.mev_smoothing_pool.proposer_payoff_eth },
      { name: 'MEV Burn (EIP-7545)', threat: reorgResult.mev_burn_eip7545.reorg_threat_score_pct, payoff: reorgResult.mev_burn_eip7545.proposer_payoff_eth },
    ]
  }, [reorgResult])

  return <>
    <div className="page-title-row">
      <div>
        <p className="eyebrow">PROBLEM STATEMENT 3 · NETWORK EFFICIENCY & CONSENSUS</p>
        <h1>MEV Smoothing, Reorg Defense & Taxonomy</h1>
        <p className="page-subtitle">Examine how MEV competition causes priority gas auctions and consensus "time-bandit" reorganization risks, and demonstrate how MEV Smoothing and MEV Burn overcome these vulnerabilities.</p>
      </div>
      <span className="pill green">Consensus Economics</span>
    </div>

    <div className="subnav-bar">
      <button className={`subnav-btn ${tab==='reorg'?'active':''}`} onClick={()=>setTab('reorg')}><Flame size={15}/> Consensus Reorg & MEV Smoothing (Overcoming Time-Bandit)</button>
      <button className={`subnav-btn ${tab==='taxonomy'?'active':''}`} onClick={()=>setTab('taxonomy')}><Scale size={15}/> Beneficial vs. Toxic MEV Taxonomy</button>
      <button className={`subnav-btn ${tab==='queue'?'active':''}`} onClick={()=>setTab('queue')}><Gauge size={15}/> Gas Queue & Submission Model</button>
    </div>

    {tab === 'reorg' && <>
      <div className="two-col form-layout">
        <Panel title="Consensus Threat Parameters" subtitle="Configure MEV spike size and potential rogue validator stake">
          <div className="slider-container">
            <div className="slider-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Block MEV Spike (ETH):</span>
              <input type="number" step="any" min="1" max="5000" style={{ width: 85, padding: '3px 6px', fontSize: 12, textAlign: 'right', color: '#c04c4c', fontWeight: 600 }} value={spikeEth} onChange={e=>setSpikeEth(e.target.value === '' ? '' : Number(e.target.value))}/>
            </div>
            <input className="styled-slider" type="range" min="1" max="500" step="any" value={Number(spikeEth) || 50} onChange={e=>setSpikeEth(Number(e.target.value))}/>
            <small style={{ color: '#8895ab', fontSize: 10 }}>Standard block subsidy is only 0.06 ETH; large spikes create massive reorg incentives.</small>
          </div>

          <div className="slider-container">
            <div className="slider-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Attacker Validator Stake Share (%):</span>
              <input type="number" step="any" min="1" max="49" style={{ width: 85, padding: '3px 6px', fontSize: 12, textAlign: 'right', color: Number(validatorStake) > 20 ? '#c04c4c' : '#425bd1', fontWeight: 600 }} value={validatorStake} onChange={e=>setValidatorStake(e.target.value === '' ? '' : Number(e.target.value))}/>
            </div>
            <input className="styled-slider" type="range" min="1" max="49" step="any" value={Number(validatorStake) || 15} onChange={e=>setValidatorStake(Number(e.target.value))}/>
            <small style={{ color: '#8895ab', fontSize: 10 }}>Percentage of Ethereum total stake controlled by the potential reorganizing coalition.</small>
          </div>

          <Button loading={busy} onClick={runReorgSimulation}>Simulate Consensus Security <ChevronRight size={16}/></Button>
          {error && <Notice type="error">{error}</Notice>}
        </Panel>

        <Panel title="Time-Bandit Threat Comparison" subtitle="Reorg Threat Score across 3 MEV distribution regimes">
          {reorgResult ? <>
            <div className="result-kpis">
              <div><span>Status Quo threat score</span><strong style={{ color: '#c04c4c' }}>{pct(reorgResult.unsmoothed_status_quo.reorg_threat_score_pct)}</strong></div>
              <div><span>Smoothed threat score</span><strong style={{ color: '#19996d' }}>{pct(reorgResult.mev_smoothing_pool.reorg_threat_score_pct)}</strong></div>
              <div><span>MEV Burn threat score</span><strong style={{ color: '#19996d' }}>0.0% (Destroyed)</strong></div>
              <div><span>Consensus status</span><strong style={{ color: '#19996d' }}>Consensus Stabilized</strong></div>
            </div>

            <div className="chart-wrap" style={{ marginTop: 15 }}>
              <ResponsiveContainer width="100%" height={230}>
                <BarChart data={reorgChartData} margin={{ top: 12, right: 12, left: -15, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#edf0f5"/>
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} axisLine={false} tickLine={false}/>
                  <YAxis tick={{ fontSize: 11 }} axisLine={false} tickLine={false}/>
                  <Tooltip/>
                  <Bar dataKey="threat" name="Reorg Threat Score (%)" fill="#dc3e3e" radius={[5,5,0,0]}>
                    <Cell fill="#dc3e3e" />
                    <Cell fill="#19996d" />
                    <Cell fill="#4f73e8" />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </> : <div className="empty-state"><LoaderCircle className="spin" size={26}/></div>}
        </Panel>
      </div>

      {reorgResult && <Panel title="Regime Comparison: Overcoming Problem Statement 3 Limitations" subtitle="How MEV Smoothing and MEV Burn stabilize Ethereum consensus finality">
        <div className="scorecard-grid">
          <div className="scorecard">
            <div className="scorecard-title">
              <strong>1. Unsmoothed MEV (Status Quo)</strong>
              <span className="badge-traditional">HIGH REORG THREAT</span>
            </div>
            <div className="scorecard-metric"><span>Proposer Payoff:</span><strong style={{ color: '#c04c4c' }}>{reorgResult.unsmoothed_status_quo.proposer_payoff_eth} ETH</strong></div>
            <div className="scorecard-metric"><span>Reorg Threat Score:</span><strong style={{ color: '#c04c4c' }}>{pct(reorgResult.unsmoothed_status_quo.reorg_threat_score_pct)}</strong></div>
            <div className="scorecard-metric"><span>Consensus Risk:</span><strong style={{ color: '#c04c4c' }}>{reorgResult.unsmoothed_status_quo.consensus_risk_level}</strong></div>
            <div className="scorecard-metric"><span>Validator Returns:</span><strong>Lottery-like; solo stakers get rare, erratic windfalls</strong></div>
            <p className="body-copy" style={{ marginTop: 8, fontSize: 11 }}><strong>The Limitation:</strong> When a block has {spikeEth} ETH of MEV, rational validators have high incentives to fork/reorg the chain to steal the prize ("Flash Boys 2.0 / time-bandit attacks").</p>
          </div>

          <div className="scorecard highlight">
            <div className="scorecard-title">
              <strong>2. MEV Smoothing Pool (Epoch Distribution)</strong>
              <span className="badge-overcome">OVERCOMES REORG THREAT</span>
            </div>
            <div className="scorecard-metric"><span>Proposer Payoff:</span><strong>{reorgResult.mev_smoothing_pool.proposer_payoff_eth} ETH (Pooled)</strong></div>
            <div className="scorecard-metric"><span>Reorg Threat Score:</span><strong style={{ color: '#13835c' }}>{pct(reorgResult.mev_smoothing_pool.reorg_threat_score_pct)} (Negligible)</strong></div>
            <div className="scorecard-metric"><span>Consensus Risk:</span><strong style={{ color: '#13835c' }}>Consensus Stable</strong></div>
            <div className="scorecard-metric"><span>Validator Returns:</span><strong style={{ color: '#13835c' }}>Smooth, predictable yield for all solo validators</strong></div>
            <p className="body-copy" style={{ marginTop: 8, fontSize: 11 }}><strong>How it Overcomes:</strong> Distributes MEV rewards evenly across the entire 32-slot epoch committee. A rogue validator cannot capture the windfall by reorging, dropping fork incentives to near-zero.</p>
          </div>

          <div className="scorecard highlight" style={{ gridColumn: 'span 2' }}>
            <div className="scorecard-title">
              <strong>3. MEV Burn (EIP-7545 Base Bid Burn)</strong>
              <span className="badge-overcome">PERMANENT DESTRUCTION OF INCENTIVE</span>
            </div>
            <div className="scorecard-metric"><span>Proposer Payoff:</span><strong>{reorgResult.mev_burn_eip7545.proposer_payoff_eth} ETH (Standard tip only)</strong></div>
            <div className="scorecard-metric"><span>Burned on-chain:</span><strong style={{ color: '#4f73e8' }}>{money(spikeEth * 0.95, 2)} ETH burned into protocol</strong></div>
            <div className="scorecard-metric"><span>Reorg Threat Score:</span><strong style={{ color: '#13835c' }}>0.0% (Permanently Eliminated)</strong></div>
            <div className="scorecard-metric"><span>Beneficiaries:</span><strong>All ETH holders benefit from supply deflation (like EIP-1559)</strong></div>
            <p className="body-copy" style={{ marginTop: 8, fontSize: 11 }}><strong>How it Overcomes:</strong> Burns 95% of the base MEV bid directly at the consensus layer. Completely destroys the payoff of attempting a reorg while returning value to the entire ecosystem.</p>
          </div>
        </div>
      </Panel>}
    </>}

    {tab === 'taxonomy' && <Panel title="Taxonomy Matrix: Beneficial vs. Toxic MEV" subtitle="Why 'banning' all MEV is catastrophic for DeFi, and how targeted policy differentiates value types">
      <div className="matrix-grid">
        {(taxonomyData?.taxonomy || []).map((item, idx) => (
          <div key={idx} className={`matrix-card ${item.mev_type.toLowerCase()}`}>
            <div className="matrix-header">
              <strong>{item.category_name}</strong>
              <span className={`matrix-tag ${item.mev_type === 'Beneficial' ? 'tag-beneficial' : 'tag-toxic'}`}>
                {item.mev_type.toUpperCase()} MEV
              </span>
            </div>
            <div className="matrix-body">
              <p><strong>Economic Purpose:</strong> {item.economic_role}</p>
              <p><strong>User Impact:</strong> {item.user_impact}</p>
              <p><strong>Network Impact:</strong> {item.network_impact}</p>
              <p><strong>Overall Assessment:</strong> <span style={{ color: item.mev_type === 'Beneficial' ? '#15865e' : '#c83535', fontWeight: 700 }}>{item.overall_assessment}</span></p>
              <div style={{ marginTop: 8, padding: '6px 8px', background: '#f5f7fa', borderRadius: 6 }}>
                <strong>Recommendation:</strong> {item.recommendation}
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="overcome-card" style={{ marginTop: 18 }}>
        <h4><Scale size={16}/> Central Takeaway from Case Study (Table 5 & Section 8.2)</h4>
        <p>{taxonomyData?.summary_insight || 'MEV is an economic consequence of programmable ordering. DEX arbitrage aligns cross-venue prices and liquidations keep lending pools solvent. Blanket MEV bans trigger lending insolvencies. Next-generation systems selectively neutralize toxic sandwiches while accelerating beneficial arbitrage.'}</p>
      </div>
    </Panel>}

    {tab === 'queue' && <>
      <div className="two-col form-layout">
        <Panel title="Transaction Queue Scenario" subtitle="Simulate block capacity constraints, priority fees, and private bundle sorting">
          <form className="form-grid" onSubmit={runQueueSimulation} noValidate>
            <label>Submitted transactions<input type="number" step="any" min="1" max="10000" value={queueForm.transaction_count} onChange={e=>setQueueForm({...queueForm, transaction_count: e.target.value === '' ? '' : e.target.value})}/></label>
            <label>Block capacity (tx/block)<input type="number" step="any" min="1" max="1000" value={queueForm.block_capacity} onChange={e=>setQueueForm({...queueForm, block_capacity: e.target.value === '' ? '' : e.target.value})}/></label>
            <label>Base fee (Gwei)<input type="number" step="any" min="0" value={queueForm.base_fee_gwei} onChange={e=>setQueueForm({...queueForm, base_fee_gwei: e.target.value === '' ? '' : e.target.value})}/></label>
            <label>Base priority fee (Gwei)<input type="number" step="any" min="0" value={queueForm.priority_fee_gwei} onChange={e=>setQueueForm({...queueForm, priority_fee_gwei: e.target.value === '' ? '' : e.target.value})}/></label>
            <label>Max simulated blocks<input type="number" step="any" min="1" max="1000" value={queueForm.max_blocks} onChange={e=>setQueueForm({...queueForm, max_blocks: e.target.value === '' ? '' : e.target.value})}/></label>
            <label>Submission model
              <select value={queueForm.submission_method} onChange={e=>setQueueForm({...queueForm, submission_method: e.target.value})}>
                <option value="priority_fee_competition">Priority Fee Competition (PGA)</option>
                <option value="private_bundle_simulation">Private Bundle Model (FCFS)</option>
              </select>
            </label>
            <div className="span-2"><Button loading={busy} type="submit">Run Queue Simulation <ChevronRight size={16}/></Button></div>
          </form>
        </Panel>

        <Panel title="Queue Efficiency Metrics" subtitle="Included transactions, queue delays, and total expenditure">
          {queueResult ? <>
            <div className="result-kpis">
              <div><span>Included transactions</span><strong>{queueResult.selected_result.included_transactions} / {queueResult.selected_result.submitted_transactions}</strong></div>
              <div><span>Remaining backlog</span><strong>{queueResult.selected_result.remaining_queue} txs</strong></div>
              <div><span>Estimated gas cost</span><strong>{money(queueResult.selected_result.estimated_total_cost_eth, 6)} ETH</strong></div>
              <div><span>Modeled queue delay</span><strong>{money(queueResult.selected_result.estimated_queue_delay_seconds, 1)} sec</strong></div>
            </div>
            <div className="overcome-card">
              <h4><Gauge size={16}/> Comparison Summary</h4>
              <p>Under Priority Fee Competition, high-bidding transactions jump ahead while low-fee transactions suffer deferral. Private bundle simulation preserves FIFO submission order, eliminating bidding wars at the cost of requiring private relay routing.</p>
            </div>
          </> : <div className="empty-state"><Gauge size={28}/><strong>Ready to simulate</strong><span>Submit to view queue processing.</span></div>}
        </Panel>
      </div>
    </>}
  </>
}

// ==============================================================================
// 5. EXPERIMENT HISTORY
// ==============================================================================
function History({ refreshKey }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [moduleFilter, setModuleFilter] = useState('all')
  const [selectedExp, setSelectedExp] = useState(null)

  useEffect(() => {
    let live = true
    setBusy(true)
    api.experiments()
      .then(d => { if (live) { setData(d); setError('') } })
      .catch(e => { if (live) setError(e.message) })
      .finally(() => { if (live) setBusy(false) })
    return () => { live = false }
  }, [refreshKey])

  const rows = (data?.items || []).filter(x => moduleFilter === 'all' || x.module === moduleFilter)

  return <>
    <div className="page-title-row">
      <div>
        <p className="eyebrow">PERSISTENCE & AUDIT TRAIL</p>
        <h1>Experiment History</h1>
        <p className="page-subtitle">Inspect completed simulation runs recorded by the backend database across all 3 problem modules.</p>
      </div>
      <div className="toolbar">
        <select value={moduleFilter} onChange={e=>setModuleFilter(e.target.value)}>
          <option value="all">All problem modules</option>
          <option value="protection">PS 1: Trade Protection</option>
          <option value="decentralization">PS 2: Decentralization</option>
          <option value="efficiency">PS 3: Efficiency</option>
        </select>
        <button className="btn secondary" onClick={()=>{setBusy(true); api.experiments().then(setData).catch(e=>setError(e.message)).finally(()=>setBusy(false))}}>
          <RefreshCw size={16}/> Reload
        </button>
      </div>
    </div>

    {error && <Notice type="error">{error}</Notice>}

    <Panel title="Persisted Simulation Records" subtitle={`${rows.length} records matching filter`}>
      {busy ? <div className="loading-line"><LoaderCircle className="spin"/> Loading experiments…</div> : rows.length ? (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Scenario</th>
                <th>Module</th>
                <th>Status</th>
                <th>Timestamp</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(item => (
                <tr key={item.id}>
                  <td><strong>#{item.id}</strong></td>
                  <td><strong>{item.scenario}</strong><small className="cell-sub">{item.error_message || 'Persisted run'}</small></td>
                  <td><span className="pill neutral">{item.module}</span></td>
                  <td><span className={`status ${item.status}`}>{item.status}</span></td>
                  <td>{item.created_at ? new Date(item.created_at).toLocaleString() : '—'}</td>
                  <td>
                    <button className="btn secondary" style={{ padding: '5px 9px', fontSize: 10 }} onClick={() => setSelectedExp(item)}>
                      Inspect JSON
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="empty-state"><Database size={28}/><strong>No experiments found</strong><span>Enable 'Save to database' when running simulations.</span></div>
      )}
    </Panel>

    {selectedExp && (
      <Panel title={`Experiment #${selectedExp.id} · Details`} subtitle={selectedExp.scenario} action={<button className="btn secondary" onClick={()=>setSelectedExp(null)}>Close</button>}>
        <JsonResult data={selectedExp} />
      </Panel>
    )}
  </>
}

// ==============================================================================
// MAIN APP COMPONENT
// ==============================================================================
export default function App() {
  const [page, setPage] = useState('dashboard')
  const [health, setHealth] = useState(null)
  const [summary, setSummary] = useState(null)
  const [experiments, setExperiments] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)
  const [topError, setTopError] = useState('')

  async function refresh() {
    setTopError('')
    const results = await Promise.allSettled([api.health(), api.summary(), api.experiments()])
    if (results[0].status === 'fulfilled') setHealth(results[0].value); else setTopError(results[0].reason.message)
    if (results[1].status === 'fulfilled') setSummary(results[1].value)
    if (results[2].status === 'fulfilled') setExperiments(results[2].value)
    setRefreshKey(v => v + 1)
  }

  useEffect(() => { refresh() }, [])

  const title = NAV.find(n => n.id === page)?.label || 'Overview'

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><ShieldCheck size={23}/></div>
        <div><strong>MEVShield</strong><small>ETHEREUM MEV LAB</small></div>
      </div>
      <div className="workspace-label">PROBLEM STATEMENTS</div>
      <nav>
        {NAV.map(item => {
          const Icon = item.icon
          return <button key={item.id} className={`nav-item ${page===item.id?'active':''}`} onClick={()=>setPage(item.id)}>
            <Icon size={18}/>
            <span>{item.label}</span>
            {page===item.id && <span className="nav-indicator"/>}
          </button>
        })}
      </nav>
      <div className="sidebar-bottom">
        <div className="status-box">
          <span className={`pulse ${health?.status==='healthy'?'online':''}`}/>
          <div>
            <strong>{health?.status==='healthy'?'Backend Connected':'API Ready'}</strong>
            <small>{health?.service || 'FastAPI Service'}</small>
          </div>
        </div>
        <a href="/docs" target="_blank" rel="noreferrer" className="docs-link">
          <BookOpen size={16}/> API documentation <ArrowUpRight size={14}/>
        </a>
        <div className="version">MEVShield · Case Study Demo v2.0</div>
      </div>
    </aside>

    <main className="main-area">
      <header className="topbar">
        <div className="mobile-brand"><ShieldCheck size={20}/> MEVShield</div>
        <div className="breadcrumb">Ethereum MEV Lab <ChevronRight size={14}/> <strong>{title}</strong></div>
        <div className="topbar-right">
          <span className="sim-badge"><span/> DEMO MODE</span>
          <div className="avatar">MEV</div>
        </div>
      </header>

      <div className="content-area">
        {topError && <Notice type="error">Could not reach backend API: {topError}. Ensure backend is running.</Notice>}
        {page === 'dashboard' && <Dashboard summary={summary} experiments={experiments} health={health} refresh={refresh} setPage={setPage} />}
        {page === 'protection' && <TradeProtection />}
        {page === 'decentralization' && <Decentralization />}
        {page === 'efficiency' && <Efficiency />}
        {page === 'history' && <History refreshKey={refreshKey} />}

        <footer>
          <span>MEVShield · Academic Case Study on Ethereum MEV, Transaction Ordering & Decentralization</span>
          <span>Based on Ethereum Foundation, Flashbots & Peer-Reviewed Literature</span>
        </footer>
      </div>
    </main>
  </div>
}
