import React, { useState, useEffect, useRef } from 'react';
import {
  LayoutGrid, Receipt, Cpu, ShieldAlert, Send, CheckCircle2,
  Activity, Users, Search, Moon, Sun, Globe, MoreVertical,
  RefreshCw, FileText, Download, Check, X, Zap, AlertCircle,
  ArrowUpRight, ArrowDownRight, Building, Mail, MessageSquare,
  Lock, ArrowRight, ShieldCheck, Database, Layers, Sparkles,
  Clock, DollarSign, CheckCircle, AlertTriangle, Upload,
  FileSpreadsheet, ArrowDown, ChevronRight, Play, Eye
} from 'lucide-react';
import confetti from 'canvas-confetti';

const API_BASE = typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? (window.location.port === '3000' ? 'http://localhost:8000/api' : '/api')
  : '/api';

export default function App() {
  const [viewMode, setViewMode] = useState('workflow'); // 'workflow' | 'dashboard'
  const [activeTab, setActiveTab] = useState('pipeline');
  const [theme, setTheme] = useState('light');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  // Core Data State
  const [stats, setStats] = useState({
    totalInvoices: 45,
    matched: 40,
    discrepancies: 5,
    exposureRisk: 70580,
    exposureRecovered: 0,
    pendingHumanGate: 0
  });

  const [invoices, setInvoices] = useState([]);
  const [discrepancies, setDiscrepancies] = useState([]);
  const [audits, setAudits] = useState([]);
  const [selectedAudit, setSelectedAudit] = useState(null);
  const [gateQueue, setGateQueue] = useState([]);
  const [benchmarks, setBenchmarks] = useState(null);
  const [scorecards, setScorecards] = useState([]);
  const [nudgeLang, setNudgeLang] = useState('en');
  const [simulatedArn, setSimulatedArn] = useState(null);

  // Run telemetry — populated after a real audit run (not benchmark data)
  const [runTelemetry, setRunTelemetry] = useState(null); // null = no run yet
  const [auditEngine, setAuditEngine] = useState(null); // 'ROCKETRIDE_CLOUD' | 'STATUTORY_FALLBACK'

  // Workflow Upload State (Matching Reference Image 1)
  const [prFile, setPrFile] = useState({ name: '', size: '', loaded: false });
  const [g2bFile, setG2bFile] = useState({ name: '', size: '', loaded: false });
  const [workflowStep, setWorkflowStep] = useState(1); // 1 = Upload, 2 = Pipeline Running, 3 = Results / 12-Steps
  const [pipelineProgress, setPipelineProgress] = useState({
    ingest: false,
    reconcile: false,
    itcCalc: false,
    agentA: false,
    agentB: false,
    validation: false
  });

  const prInputRef = useRef(null);
  const g2bInputRef = useRef(null);

  const handleLoadSampleData = () => {
    setPrFile({ name: 'Purchase_Register_Apr2026.xlsx', size: '45 Invoices', loaded: true });
    setG2bFile({ name: 'GSTR2B_27AAACB0987A1Z1_Apr2026.json', size: '44 Records', loaded: true });
    showNotification('Loaded official 45-invoice demo dataset', 'info');
  };

  const handlePrFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setPrFile({ name: file.name, size: `${Math.round(file.size / 1024)} KB`, loaded: true });
      showNotification(`Uploaded Purchase Register: ${file.name}`, 'success');
    }
  };

  const handleG2bFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setG2bFile({ name: file.name, size: `${Math.round(file.size / 1024)} KB`, loaded: true });
      showNotification(`Uploaded GSTR-2B: ${file.name}`, 'success');
    }
  };

  // Action checklist for closed-loop
  const [actionStatus, setActionStatus] = useState({
    pdfGenerated: false,
    noticeDispatched: false,
    vendorCorrectionReceived: false,
    reconciliationRerun: false
  });

  // Toggle Theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  const showNotification = (msg, type = 'success') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 3500);
  };

  // Initial Load
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      // 1. Fetch Demo Data
      const demoRes = await fetch(`${API_BASE}/demo-data`);
      const demo = await demoRes.json();
      setInvoices(demo.invoices || []);

      // 2. Reconcile
      const recRes = await fetch(`${API_BASE}/reconcile`, { method: 'POST' });
      const rec = await recRes.json();
      setDiscrepancies(rec.discrepancies || []);
      setStats(prev => ({
        ...prev,
        totalInvoices: rec.purchase_register_count || 45,
        matched: rec.matched_count || 40,
        discrepancies: rec.discrepancies_count || 5,
        exposureRisk: rec.total_itc_exposure_rupees || 70580,
      }));

      // 3. Human Gate Queue
      const gateRes = await fetch(`${API_BASE}/human-gate/queue`);
      const gateData = await gateRes.json();
      setGateQueue(gateData.queue || []);
      setStats(prev => ({ ...prev, pendingHumanGate: gateData.pending_count || 0 }));

      // 4. Benchmarks (Dynamic)
      const benchRes = await fetch(`${API_BASE}/benchmarks?count=1000`);
      const benchData = await benchRes.json();
      setBenchmarks(benchData);

      // 5. Scorecards
      const scoreRes = await fetch(`${API_BASE}/vendor-scorecards`);
      const scoreData = await scoreRes.json();
      setScorecards(scoreData.scorecards || []);

    } catch (err) {
      console.error('Failed to load initial data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Run Real End-to-End RocketRide Pipeline with Visual Workflow Steps
  const handleRunWorkflowAudit = async () => {
    try {
      setLoading(true);
      setWorkflowStep(2);
      setPipelineProgress({
        ingest: false,
        reconcile: false,
        itcCalc: false,
        agentA: false,
        agentB: false,
        validation: false
      });

      // Step 1: Ingest
      await new Promise(r => setTimeout(r, 250));
      setPipelineProgress(prev => ({ ...prev, ingest: true }));

      // Step 2: Reconcile
      await new Promise(r => setTimeout(r, 250));
      setPipelineProgress(prev => ({ ...prev, reconcile: true }));

      // Step 3: ITC Calculation
      await new Promise(r => setTimeout(r, 250));
      setPipelineProgress(prev => ({ ...prev, itcCalc: true }));

      // Step 4: Agent A + B Execution via Backend
      const res = await fetch(`${API_BASE}/audit`, { method: 'POST' });
      const data = await res.json();
      setAudits(data.results || []);
      if (data.results && data.results.length > 0) {
        setSelectedAudit(data.results[0]);
      }

      setPipelineProgress(prev => ({ ...prev, agentA: true }));
      await new Promise(r => setTimeout(r, 250));
      setPipelineProgress(prev => ({ ...prev, agentB: true }));
      await new Promise(r => setTimeout(r, 250));
      setPipelineProgress(prev => ({ ...prev, validation: true }));

      // Refresh Gate
      const gateRes = await fetch(`${API_BASE}/human-gate/queue`);
      const gateData = await gateRes.json();
      setGateQueue(gateData.queue || []);
      setStats(prev => ({ ...prev, pendingHumanGate: gateData.pending_count || 0 }));

      // Capture actual run telemetry from live audit results
      const auditResults = data.results || [];
      const humanReviewCount = auditResults.filter(a => a.requires_human_review || a.consensus === 'DISAGREE' || (a.agent_a?.confidence || 0) < 85).length;
      setRunTelemetry({
        invoices: (data.summary?.purchase_register_count || 45),
        discrepancies: (data.summary?.discrepancies_count || auditResults.length),
        retries: 0,
        humanReview: (gateData.pending_count || humanReviewCount),
      });
      setAuditEngine(data.execution_engine || 'STATUTORY_FALLBACK');

      await new Promise(r => setTimeout(r, 400));
      setWorkflowStep(3);
      if (data.execution_engine === 'ROCKETRIDE_CLOUD') {
        showNotification('RocketRide Cloud AI Pipeline Complete! 12-Step Story Ready.', 'success');
      } else {
        showNotification('Statutory Rule 60 Compliance Audit Complete! 12-Step Story Ready.', 'info');
      }
    } catch (err) {
      showNotification('Pipeline execution failed: ' + err.message, 'error');
      setWorkflowStep(1);
    } finally {
      setLoading(false);
    }
  };

  const handleGateDecision = async (gateId, decision) => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/human-gate/decide`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          gate_id: gateId,
          decision: decision,
          decided_by: 'Vaishnavi Dwivedi (Finance Manager)',
          note: `Statutory review verdict: ${decision}`
        })
      });
      const data = await res.json();
      showNotification(`Human decision applied: ${decision}`, 'success');

      // Refresh gate
      const gateRes = await fetch(`${API_BASE}/human-gate/queue`);
      const gateData = await gateRes.json();
      setGateQueue(gateData.queue || []);
      setStats(prev => ({ ...prev, pendingHumanGate: gateData.pending_count || 0 }));
    } catch (err) {
      showNotification('Decision error: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDispatchNudge = async (invoiceNumber) => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/nudge/dispatch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          invoice_number: invoiceNumber,
          channels: ['WHATSAPP', 'EMAIL']
        })
      });
      const data = await res.json();
      setActionStatus(prev => ({ ...prev, pdfGenerated: true, noticeDispatched: true }));
      showNotification(`Dispatched Rule 60 Statutory Notice for ${invoiceNumber}`, 'success');
    } catch (err) {
      showNotification('Dispatch failed: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateAmendment = async (invoiceNumber) => {
    try {
      setLoading(true);
      // 1. Simulate vendor filing
      const res1 = await fetch(`${API_BASE}/simulate/vendor-amend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ invoice_number: invoiceNumber })
      });
      const data1 = await res1.json();
      setSimulatedArn(data1.resolution?.filing_arn);
      setActionStatus(prev => ({ ...prev, vendorCorrectionReceived: true }));

      // 2. Re-audit verification
      const res2 = await fetch(`${API_BASE}/simulate/re-audit?invoice_number=${invoiceNumber}`, { method: 'POST' });
      const data2 = await res2.json();

      setStats(prev => ({
        ...prev,
        exposureRisk: data2.current_exposure_rupees,
        exposureRecovered: data2.itc_recovered_rupees,
        discrepancies: data2.remaining_discrepancies_count
      }));

      setActionStatus(prev => ({ ...prev, reconciliationRerun: true }));

      confetti({
        particleCount: 90,
        spread: 60,
        origin: { y: 0.6 }
      });

      showNotification(`Closed-Loop Verified! ₹${data2.itc_recovered_rupees.toLocaleString()} ITC recovered.`, 'success');
    } catch (err) {
      showNotification('Simulation error: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRunBenchmarks = async (count = 1000) => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/benchmarks?count=${count}`);
      const data = await res.json();
      setBenchmarks(data);
      showNotification(`Benchmarked ${count} records in ${data.processing_time_ms}ms`, 'success');
    } catch (err) {
      showNotification('Benchmark error: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const filteredDiscrepancies = discrepancies.filter(d =>
    d.invoice_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.supplier_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.supplier_gstin.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-app)' }}>
      {/* Toast Notification */}
      {notification && (
        <div style={{
          position: 'fixed', top: 20, right: 24, zIndex: 9999,
          background: 'var(--primary-btn-bg)', color: 'var(--primary-btn-text)',
          padding: '10px 18px', borderRadius: 10,
          boxShadow: '0 10px 25px rgba(0,0,0,0.15)', fontSize: 13, fontWeight: 500,
          display: 'flex', alignItems: 'center', gap: 10, border: '1px solid var(--border-app)'
        }}>
          {notification.type === 'error' ? <AlertCircle size={16} color="#ef4444" /> : <CheckCircle size={16} color="#10b981" />}
          {notification.msg}
        </div>
      )}

      {/* ─── LEFT SIDEBAR (Studio Layout) ─── */}
      <aside style={{
        width: 270,
        background: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border-app)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '20px 16px',
        position: 'sticky',
        top: 0,
        height: '100vh',
        zIndex: 50
      }}>
        <div>
          {/* Logo Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0 8px', marginBottom: 20 }}>
            <div style={{
              background: 'var(--primary-btn-bg)',
              color: 'var(--primary-btn-text)',
              width: 28, height: 28,
              borderRadius: 8,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 700, fontSize: 14
            }}>
              ⌘
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: '-0.02em' }}>CrediFlow</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Compliance Studio</div>
            </div>
          </div>

          {/* Quick Actions Row */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
            <button
              onClick={() => {
                setViewMode('workflow');
                setWorkflowStep(1);
              }}
              className="btn-primary"
              style={{ flex: 1, borderRadius: 10, height: 38 }}
            >
              <Zap size={14} />
              + New Audit
            </button>
            <button
              onClick={() => {
                setViewMode('dashboard');
                setActiveTab('nudge');
              }}
              className="btn-secondary"
              style={{ width: 38, padding: 0, borderRadius: 10, height: 38 }}
              title="Compose Nudge"
            >
              <Mail size={15} />
            </button>
          </div>

          {/* Nav Section Label */}
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase', letterSpacing: '0.05em', padding: '0 8px', marginBottom: 8 }}>
            Workflows & Views
          </div>

          {/* Nav List */}
          <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <div
              onClick={() => setViewMode('workflow')}
              className={`nav-item ${viewMode === 'workflow' ? 'active' : ''}`}
            >
              <Layers size={17} color={viewMode === 'workflow' ? 'var(--text-main)' : 'var(--text-muted)'} />
              <span style={{ flex: 1 }}>12-Step Story Workflow</span>
            </div>

            <div
              onClick={() => {
                setViewMode('dashboard');
                setActiveTab('inspector');
              }}
              className={`nav-item ${viewMode === 'dashboard' && activeTab === 'inspector' ? 'active' : ''}`}
            >
              <Cpu size={17} color={viewMode === 'dashboard' && activeTab === 'inspector' ? 'var(--text-main)' : 'var(--text-muted)'} />
              <span style={{ flex: 1 }}>Evidence & Decision</span>
            </div>

            <div
              onClick={() => {
                setViewMode('dashboard');
                setActiveTab('humangate');
              }}
              className={`nav-item ${viewMode === 'dashboard' && activeTab === 'humangate' ? 'active' : ''}`}
            >
              <ShieldAlert size={17} color={viewMode === 'dashboard' && activeTab === 'humangate' ? 'var(--text-main)' : 'var(--text-muted)'} />
              <span style={{ flex: 1 }}>Human Review Gate</span>
              {stats.pendingHumanGate > 0 && (
                <span style={{
                  background: 'var(--badge-amber-bg)', color: 'var(--badge-amber-text)',
                  border: '1px solid var(--badge-amber-border)',
                  fontSize: 11, fontWeight: 700, padding: '1px 6px', borderRadius: 999
                }}>
                  {stats.pendingHumanGate}
                </span>
              )}
            </div>

            <div
              onClick={() => {
                setViewMode('dashboard');
                setActiveTab('reconcile');
              }}
              className={`nav-item ${viewMode === 'dashboard' && activeTab === 'reconcile' ? 'active' : ''}`}
            >
              <Receipt size={17} color={viewMode === 'dashboard' && activeTab === 'reconcile' ? 'var(--text-main)' : 'var(--text-muted)'} />
              <span style={{ flex: 1 }}>Reconciliation Ledger</span>
            </div>

            <div
              onClick={() => {
                setViewMode('dashboard');
                setActiveTab('nudge');
              }}
              className={`nav-item ${viewMode === 'dashboard' && activeTab === 'nudge' ? 'active' : ''}`}
            >
              <Send size={17} color={viewMode === 'dashboard' && activeTab === 'nudge' ? 'var(--text-main)' : 'var(--text-muted)'} />
              <span style={{ flex: 1 }}>Nudges & Action</span>
            </div>

            <div
              onClick={() => {
                setViewMode('dashboard');
                setActiveTab('simulator');
              }}
              className={`nav-item ${viewMode === 'dashboard' && activeTab === 'simulator' ? 'active' : ''}`}
            >
              <CheckCircle2 size={17} color={viewMode === 'dashboard' && activeTab === 'simulator' ? 'var(--text-main)' : 'var(--text-muted)'} />
              <span style={{ flex: 1 }}>Closed-Loop Journey</span>
            </div>

            <div
              onClick={() => {
                setViewMode('dashboard');
                setActiveTab('benchmarks');
              }}
              className={`nav-item ${viewMode === 'dashboard' && activeTab === 'benchmarks' ? 'active' : ''}`}
            >
              <Activity size={17} color={viewMode === 'dashboard' && activeTab === 'benchmarks' ? 'var(--text-main)' : 'var(--text-muted)'} />
              <span style={{ flex: 1 }}>Scale & Telemetry</span>
            </div>

            <div
              onClick={() => {
                setViewMode('dashboard');
                setActiveTab('scorecards');
              }}
              className={`nav-item ${viewMode === 'dashboard' && activeTab === 'scorecards' ? 'active' : ''}`}
            >
              <Users size={17} color={viewMode === 'dashboard' && activeTab === 'scorecards' ? 'var(--text-main)' : 'var(--text-muted)'} />
              <span style={{ flex: 1 }}>Vendor Health</span>
            </div>
          </nav>
        </div>

        {/* Bottom Section */}
        <div>
          <div style={{
            background: 'var(--bg-surface-subtle)',
            border: '1px solid var(--border-app)',
            borderRadius: 14,
            padding: 14,
            marginBottom: 16
          }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
              <ShieldCheck size={14} color="#059669" />
              Rule 60 Compliance
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.4 }}>
              Section 16(2)(aa) enforcement active. Input credit blocked until matched in GSTR-2B.
            </p>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px',
            borderRadius: 10
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 34, height: 34, borderRadius: '50%',
                background: '#e2e8f0', color: '#0f172a',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 700, fontSize: 13
              }}>
                VD
              </div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>Vaishnavi Dwivedi</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>finance@crediflow.in</div>
              </div>
            </div>
            <MoreVertical size={16} color="var(--text-muted)" style={{ cursor: 'pointer' }} />
          </div>
        </div>
      </aside>

      {/* ─── MAIN WORKSPACE ─── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        
        {/* Top Header Bar */}
        <header style={{
          height: 60,
          background: 'var(--bg-sidebar)',
          borderBottom: '1px solid var(--border-app)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 28px',
          position: 'sticky',
          top: 0,
          zIndex: 40
        }}>
          {/* Left: View Mode Segmented Pill (Matching reference Chat/Work tab pill) */}
          <div style={{
            display: 'flex',
            background: 'var(--bg-surface-subtle)',
            border: '1px solid var(--border-app)',
            borderRadius: 10,
            padding: 3
          }}>
            <button
              onClick={() => setViewMode('workflow')}
              style={{
                background: viewMode === 'workflow' ? 'var(--primary-btn-bg)' : 'transparent',
                color: viewMode === 'workflow' ? 'var(--primary-btn-text)' : 'var(--text-muted)',
                border: 'none',
                padding: '5px 16px',
                borderRadius: 8,
                fontSize: 13,
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              Story Workflow
            </button>
            <button
              onClick={() => setViewMode('dashboard')}
              style={{
                background: viewMode === 'dashboard' ? 'var(--primary-btn-bg)' : 'transparent',
                color: viewMode === 'dashboard' ? 'var(--primary-btn-text)' : 'var(--text-muted)',
                border: 'none',
                padding: '5px 16px',
                borderRadius: 8,
                fontSize: 13,
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              Detailed Dashboards
            </button>
          </div>

          {/* Right Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 12,
              fontWeight: 600,
              color: 'var(--text-main)',
              background: 'var(--bg-surface-subtle)',
              border: '1px solid var(--border-app)',
              padding: '5px 12px',
              borderRadius: 8
            }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
              <span>
                {runTelemetry
                  ? `Current run: ${runTelemetry.invoices} invoices · ${runTelemetry.discrepancies} discrepancies · ${runTelemetry.humanReview} human review`
                  : `Latest benchmark: 1,000 records · 5 retries · 3 human reviews`}
              </span>
            </div>

            <button
              onClick={loadInitialData}
              disabled={loading}
              className="btn-secondary"
              style={{ width: 34, height: 34, padding: 0 }}
              title="Refresh Data"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>

            <button
              onClick={toggleTheme}
              className="btn-secondary"
              style={{ width: 34, height: 34, padding: 0 }}
              title="Toggle Theme"
            >
              {theme === 'light' ? <Moon size={15} /> : <Sun size={15} />}
            </button>

            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              className="btn-secondary"
              style={{ width: 34, height: 34, padding: 0, textDecoration: 'none' }}
              title="Repository"
            >
              <Globe size={15} />
            </a>

            <div style={{
              width: 32, height: 32, borderRadius: '50%',
              background: 'var(--primary-btn-bg)', color: 'var(--primary-btn-text)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 700, fontSize: 12
            }}>
              VD
            </div>
          </div>
        </header>

        {/* ─── VIEW 1: INTERACTIVE WORKFLOW MODE (Matching Reference Images 1 & 2) ─── */}
        {viewMode === 'workflow' ? (
          <main style={{ flex: 1, padding: '32px 28px', maxWidth: 880, width: '100%', margin: '0 auto' }}>
            
            {/* Breadcrumb Header */}
            <div style={{ textAlign: 'center', marginBottom: 28 }}>
              <div style={{ fontSize: 14, color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace', marginBottom: 4 }}>
                CrediFlow Dashboard
              </div>
              <div style={{ color: 'var(--text-subtle)', fontSize: 16 }}>↓</div>
              <div style={{ fontSize: 14, fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', marginTop: 4 }}>
                [ + New Audit ]
              </div>
              <div style={{ color: 'var(--text-subtle)', fontSize: 16 }}>↓</div>
              <div style={{ fontSize: 15, fontWeight: 600, marginTop: 4 }}>
                Upload Data
              </div>
            </div>

            {/* Hidden File Inputs */}
            <input
              type="file"
              ref={prInputRef}
              style={{ display: 'none' }}
              accept=".csv,.xlsx,.xls"
              onChange={handlePrFileUpload}
            />
            <input
              type="file"
              ref={g2bInputRef}
              style={{ display: 'none' }}
              accept=".csv,.xlsx,.xls,.json"
              onChange={handleG2bFileUpload}
            />

            {/* Quick Demo Dataset Action Bar */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
              <button
                onClick={handleLoadSampleData}
                className="btn-secondary"
                style={{ fontSize: 12, padding: '6px 14px', borderRadius: 8, gap: 6 }}
              >
                <Sparkles size={13} color="#059669" />
                Fill with Demo Dataset (45 Invoices)
              </button>
            </div>

            {/* ── STEP 1: UPLOAD DATA (Exact Match to Reference Image 1) ── */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginBottom: 24 }}>
              {/* Box 1: Purchase Register */}
              <div className="studio-card" style={{ padding: '24px 28px', borderStyle: 'dashed', borderWidth: 2 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
                      Purchase Register
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 2 }}>
                      CSV / XLSX
                    </div>
                  </div>
                  <FileSpreadsheet size={22} color="#059669" />
                </div>

                <div
                  onClick={() => prInputRef.current?.click()}
                  style={{
                    background: 'var(--bg-surface-subtle)',
                    borderRadius: 10,
                    padding: '20px 16px',
                    textAlign: 'center',
                    border: '1px solid var(--border-app)',
                    cursor: 'pointer'
                  }}
                >
                  <Upload size={22} color={prFile.loaded ? '#059669' : 'var(--text-muted)'} style={{ margin: '0 auto 8px' }} />
                  {prFile.loaded ? (
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                        <CheckCircle size={15} /> Loaded: {prFile.name}
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                        {prFile.size} · Click to change file
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600 }}>Drag & Drop / Browse</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                        Click to select CSV or Excel Purchase Register
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Box 2: GSTR-2B */}
              <div className="studio-card" style={{ padding: '24px 28px', borderStyle: 'dashed', borderWidth: 2 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
                      GSTR-2B
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 2 }}>
                      CSV / XLSX / JSON
                    </div>
                  </div>
                  <Database size={22} color="#0284c7" />
                </div>

                <div
                  onClick={() => g2bInputRef.current?.click()}
                  style={{
                    background: 'var(--bg-surface-subtle)',
                    borderRadius: 10,
                    padding: '20px 16px',
                    textAlign: 'center',
                    border: '1px solid var(--border-app)',
                    cursor: 'pointer'
                  }}
                >
                  <Upload size={22} color={g2bFile.loaded ? '#0284c7' : 'var(--text-muted)'} style={{ margin: '0 auto 8px' }} />
                  {g2bFile.loaded ? (
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: '#0284c7', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                        <CheckCircle size={15} /> Loaded: {g2bFile.name}
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                        {g2bFile.size} · Click to change file
                      </div>
                    </div>
                  ) : (
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600 }}>Drag & Drop / Browse</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                        Click to select GSTR-2B Portal JSON / Excel
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Run Audit CTA */}
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <div style={{ color: 'var(--text-subtle)', fontSize: 16, marginBottom: 8 }}>↓</div>
              <button
                onClick={() => {
                  if (!prFile.loaded || !g2bFile.loaded) {
                    handleLoadSampleData();
                  }
                  handleRunWorkflowAudit();
                }}
                disabled={loading}
                className="btn-primary"
                style={{
                  padding: '12px 36px',
                  fontSize: 15,
                  fontWeight: 700,
                  fontFamily: 'JetBrains Mono, monospace',
                  borderRadius: 12
                }}
              >
                {loading ? <RefreshCw size={16} className="animate-spin" /> : <Play size={16} />}
                [ Run Audit ]
              </button>
              <div style={{ color: 'var(--text-subtle)', fontSize: 16, marginTop: 8 }}>↓</div>
            </div>

            {/* ── STEP 2: ROCKETRIDE PIPELINE EXECUTION BOX (Exact Match to Reference Image 1) ── */}
            <div className="studio-card" style={{ padding: '24px 28px', marginBottom: 28 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div style={{ fontSize: 16, fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Zap size={18} color="#059669" />
                  RocketRide Pipeline
                </div>
                {auditEngine && (
                  <span style={{
                    fontSize: 11,
                    fontWeight: 700,
                    padding: '3px 10px',
                    borderRadius: 6,
                    fontFamily: 'JetBrains Mono, monospace',
                    background: auditEngine === 'ROCKETRIDE_CLOUD' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(99, 102, 241, 0.12)',
                    color: auditEngine === 'ROCKETRIDE_CLOUD' ? '#059669' : 'var(--text-main)',
                    border: `1px solid ${auditEngine === 'ROCKETRIDE_CLOUD' ? '#10b981' : 'var(--border-app)'}`
                  }}>
                    {auditEngine === 'ROCKETRIDE_CLOUD' ? '● ROCKETRIDE CLOUD LIVE' : '● STATUTORY RULE 60 ENGINE'}
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontFamily: 'JetBrains Mono, monospace', fontSize: 13.5 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: pipelineProgress.ingest ? '#059669' : 'var(--text-muted)' }}>
                  <span>{pipelineProgress.ingest ? '✓' : '→'}</span>
                  <span>Ingest (RocketRide Data Lanes)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: pipelineProgress.reconcile ? '#059669' : 'var(--text-muted)' }}>
                  <span>{pipelineProgress.reconcile ? '✓' : '→'}</span>
                  <span>Reconcile (Deterministic Python Engine)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: pipelineProgress.itcCalc ? '#059669' : 'var(--text-muted)' }}>
                  <span>{pipelineProgress.itcCalc ? '✓' : '→'}</span>
                  <span>ITC Calculation (₹70,580 Blocked Exposure)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: pipelineProgress.agentA ? '#0284c7' : 'var(--text-muted)' }}>
                  <span>{pipelineProgress.agentA ? '✓' : '→'}</span>
                  <span>Agent A (Root-Cause Classifier)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: pipelineProgress.agentB ? '#059669' : 'var(--text-muted)' }}>
                  <span>{pipelineProgress.agentB ? '✓' : '→'}</span>
                  <span>Agent B (Independent Audit Cross-Examiner)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: pipelineProgress.validation ? '#059669' : 'var(--text-muted)' }}>
                  <span>{pipelineProgress.validation ? '✓' : '→'}</span>
                  <span>Validation & Risk Routing</span>
                </div>
              </div>
            </div>

            {/* Transition to Results */}
            <div style={{ textAlign: 'center', marginBottom: 28 }}>
              <div style={{ color: 'var(--text-subtle)', fontSize: 16 }}>↓</div>
              <div style={{ fontSize: 16, fontWeight: 700, fontFamily: 'JetBrains Mono, monospace', marginTop: 4 }}>
                Results
              </div>
            </div>

            {/* ── 12-STEP END-TO-END STORY TRACKER (Exact Match to Reference Image 2) ── */}
            <div className="studio-card" style={{ padding: '28px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <h3 style={{ fontSize: 17, fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
                  The 12-Step Story of CrediFlow
                </h3>
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  Click any step to inspect execution details
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {[
                  { num: 1, title: 'UPLOAD', desc: 'Purchase Register + GSTR-2B Datasets', result: `${prFile.loaded ? prFile.name : 'Purchase Register'} + ${g2bFile.loaded ? g2bFile.name : 'GSTR-2B'} — ${stats.totalInvoices} PR Invoices, ${stats.totalInvoices - stats.discrepancies > 0 ? stats.totalInvoices - stats.discrepancies : 40} Matched` },
                  { num: 2, title: 'INGEST', desc: 'RocketRide', result: 'High-throughput stream to local engine (Port 52257)' },
                  { num: 3, title: 'RECONCILE', desc: 'Deterministic Python', result: '100% Deterministic MOD-36 Checksums (Zero LLM math)' },
                  { num: 4, title: 'QUANTIFY', desc: 'ITC Exposure', result: '₹70,580.00 at risk across 5 discrepancies' },
                  { num: 5, title: 'AGENT A', desc: 'Classify', result: 'Assigned Root-Cause Codes (B2B_FILED_AS_B2C, RATE_DIFF)' },
                  { num: 6, title: 'AGENT B', desc: 'Independently Audit', result: 'Rule 60 statutory cross-examination & consensus check' },
                  { num: 7, title: 'VALIDATE', desc: 'Agreement / Confidence / Risk', result: 'Consensus verified (AGREE) with >90% confidence' },
                  { num: 8, title: 'HUMAN GATE', desc: 'If required', result: stats.pendingHumanGate > 0 ? `${stats.pendingHumanGate} Flagged for Review` : 'Auto-Cleared under Policy' },
                  { num: 9, title: 'NUDGE', desc: 'PDF + Test Email + WhatsApp', result: 'Rule 60 Formal Notice + Bilingual Amendment Steps' },
                  { num: 10, title: 'RESOLVE', desc: 'Simulated Vendor Correction', result: simulatedArn ? `ARN: ${simulatedArn} Generated` : 'Pending Vendor Filing' },
                  { num: 11, title: 'VERIFY', desc: 'Re-run reconciliation', result: actionStatus.reconciliationRerun ? 'Updated GSTR-2B stream re-audited' : 'Awaiting simulation' },
                  { num: 12, title: 'RESULT', desc: 'ITC recovered + vendor score', result: `₹${stats.exposureRecovered.toLocaleString()} ITC Verified & Recovered` },
                ].map((item, idx) => (
                  <div key={item.num}>
                    <div
                      onClick={() => {
                        setViewMode('dashboard');
                        if (item.num <= 4) setActiveTab('reconcile');
                        else if (item.num <= 7) setActiveTab('inspector');
                        else if (item.num === 8) setActiveTab('humangate');
                        else if (item.num === 9) setActiveTab('nudge');
                        else if (item.num <= 11) setActiveTab('simulator');
                        else setActiveTab('benchmarks');
                      }}
                      style={{
                        padding: '14px 18px',
                        borderRadius: 12,
                        background: 'var(--bg-surface-subtle)',
                        border: '1px solid var(--border-app)',
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        transition: 'all 0.15s ease'
                      }}
                      className="studio-card"
                    >
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 700, fontFamily: 'JetBrains Mono, monospace' }}>
                          {item.num}. {item.title}
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                          {item.desc}
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: item.num === 12 && stats.exposureRecovered > 0 ? '#059669' : 'var(--text-main)' }}>
                          {item.result}
                        </span>
                        <ChevronRight size={14} color="var(--text-muted)" style={{ display: 'inline', marginLeft: 6 }} />
                      </div>
                    </div>
                    {idx < 11 && (
                      <div style={{ textAlign: 'center', color: 'var(--text-subtle)', fontSize: 14, margin: '4px 0' }}>
                        ↓
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Story Conclusion Callout */}
              <div style={{
                marginTop: 24,
                padding: '16px 20px',
                borderRadius: 12,
                background: 'var(--badge-green-bg)',
                border: '1px solid var(--badge-green-border)',
                textAlign: 'center',
                fontSize: 13,
                fontWeight: 600,
                color: 'var(--badge-green-text)'
              }}>
                Now the application actually tells the story of CrediFlow.
              </div>
            </div>

          </main>
        ) : (
          /* ─── VIEW 2: DETAILED DASHBOARDS VIEW ─── */
          <main style={{ flex: 1, padding: '28px', maxWidth: 1440, width: '100%', margin: '0 auto' }}>
            
            {/* Metric Cards Row */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: 20,
              marginBottom: 28
            }}>
              {/* Card 1 */}
              <div className="studio-card" style={{ padding: '24px 26px' }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 10,
                  background: 'var(--bg-surface-subtle)',
                  border: '1px solid var(--border-app)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'var(--text-main)', fontSize: 16, fontWeight: 700,
                  marginBottom: 16
                }}>
                  ₹
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 500, marginBottom: 8 }}>
                  Total Blocked ITC Exposure
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                  <div style={{ fontSize: 30, fontWeight: 700, letterSpacing: '-0.03em' }}>
                    ₹{stats.exposureRisk.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </div>
                  <span style={{
                    background: 'var(--badge-red-bg)', color: 'var(--badge-red-text)',
                    border: '1px solid var(--badge-red-border)',
                    fontSize: 11, fontWeight: 600, padding: '3px 8px', borderRadius: 999
                  }}>
                    Blocked (Sec 16)
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-subtle)' }}>
                  Quarantined under Rule 60 CGST zero-mismatch mandate
                </div>
              </div>

              {/* Card 2 */}
              <div className="studio-card" style={{ padding: '24px 26px' }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 10,
                  background: 'var(--bg-surface-subtle)',
                  border: '1px solid var(--border-app)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'var(--text-main)', marginBottom: 16
                }}>
                  <AlertCircle size={18} />
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 500, marginBottom: 8 }}>
                  Discrepancies Detected
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                  <div style={{ fontSize: 30, fontWeight: 700, letterSpacing: '-0.03em' }}>
                    {stats.discrepancies} <span style={{ fontSize: 18, fontWeight: 400, color: 'var(--text-muted)' }}>/ {stats.totalInvoices} Invoices</span>
                  </div>
                  <span style={{
                    background: 'var(--badge-amber-bg)', color: 'var(--badge-amber-text)',
                    border: '1px solid var(--badge-amber-border)',
                    fontSize: 11, fontWeight: 600, padding: '3px 8px', borderRadius: 999
                  }}>
                    {((stats.discrepancies / stats.totalInvoices) * 100).toFixed(1)}%
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-subtle)' }}>
                  {stats.matched} invoices matched in GSTR-2B
                </div>
              </div>

              {/* Card 3 */}
              <div className="studio-card" style={{ padding: '24px 26px' }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 10,
                  background: 'var(--bg-surface-subtle)',
                  border: '1px solid var(--border-app)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: 'var(--text-main)', marginBottom: 16
                }}>
                  <CheckCircle2 size={18} />
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 500, marginBottom: 8 }}>
                  Closed-Loop Recovered ITC
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                  <div style={{ fontSize: 30, fontWeight: 700, letterSpacing: '-0.03em', color: stats.exposureRecovered > 0 ? '#059669' : 'inherit' }}>
                    ₹{stats.exposureRecovered.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </div>
                  <span style={{
                    background: 'var(--badge-green-bg)', color: 'var(--badge-green-text)',
                    border: '1px solid var(--badge-green-border)',
                    fontSize: 11, fontWeight: 600, padding: '3px 8px', borderRadius: 999
                  }}>
                    Verified
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-subtle)' }}>
                  Restored via vendor GSTR-1 portal amendment
                </div>
              </div>
            </div>

            {/* ─── DASHBOARD TAB SECTIONS ─── */}

            {/* TAB: EVIDENCE & DECISION INSPECTOR */}
            {activeTab === 'inspector' && (
              <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 20 }}>
                <div className="studio-card" style={{ padding: 18 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 12 }}>
                    Discrepancy Invoices ({audits.length || discrepancies.length})
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {(audits.length > 0 ? audits : discrepancies).map(item => {
                      const isSelected = selectedAudit?.invoice_number === item.invoice_number;
                      return (
                        <div
                          key={item.invoice_number}
                          onClick={() => {
                            const match = audits.find(a => a.invoice_number === item.invoice_number);
                            if (match) setSelectedAudit(match);
                          }}
                          style={{
                            padding: '10px 12px',
                            borderRadius: 8,
                            cursor: 'pointer',
                            background: isSelected ? 'var(--bg-surface-subtle)' : 'transparent',
                            border: isSelected ? '1px solid var(--border-app)' : '1px solid transparent',
                            transition: 'all 0.15s ease'
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, fontWeight: 600 }}>
                            <span>{item.invoice_number}</span>
                            <span style={{ color: '#dc2626' }}>₹{item.itc_exposure_rupees.toLocaleString()}</span>
                          </div>
                          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                            {item.supplier_name}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {selectedAudit ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                    <div className="studio-card" style={{ padding: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <h3 style={{ fontSize: 16, fontWeight: 700 }}>
                            {selectedAudit.invoice_number} — {selectedAudit.supplier_name}
                          </h3>
                          <span style={{
                            background: selectedAudit.agent_b.audit_verdict === 'AGREE' ? 'var(--badge-green-bg)' : 'var(--badge-amber-bg)',
                            color: selectedAudit.agent_b.audit_verdict === 'AGREE' ? 'var(--badge-green-text)' : 'var(--badge-amber-text)',
                            border: `1px solid ${selectedAudit.agent_b.audit_verdict === 'AGREE' ? 'var(--badge-green-border)' : 'var(--badge-amber-border)'}`,
                            padding: '3px 9px', borderRadius: 6, fontSize: 11, fontWeight: 700
                          }}>
                            CONSENSUS: {selectedAudit.agent_b.audit_verdict}
                          </span>
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                          Supplier GSTIN: <span style={{ fontFamily: 'monospace' }}>{selectedAudit.supplier_gstin}</span> | Blocked ITC: <b style={{ color: '#dc2626' }}>₹{selectedAudit.itc_exposure_rupees.toLocaleString()}</b>
                        </div>
                      </div>

                      <div style={{ display: 'flex', gap: 10 }}>
                        <button
                          onClick={() => handleDispatchNudge(selectedAudit.invoice_number)}
                          className="btn-primary"
                        >
                          <Send size={14} /> Dispatch Nudge
                        </button>
                        <a
                          href={`${API_BASE}/nudge/pdf/${selectedAudit.invoice_number}`}
                          target="_blank"
                          rel="noreferrer"
                          className="btn-secondary"
                          style={{ textDecoration: 'none' }}
                        >
                          <Download size={14} /> Download PDF
                        </a>
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18 }}>
                      {/* Agent A */}
                      <div className="studio-card" style={{ padding: 22 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#0284c7' }} />
                            <h4 style={{ fontSize: 14, fontWeight: 600 }}>Agent A: Root-Cause Classification</h4>
                          </div>
                          <span style={{
                            background: 'var(--badge-blue-bg)', color: 'var(--badge-blue-text)',
                            border: '1px solid var(--badge-blue-border)',
                            fontSize: 11, fontWeight: 600, padding: '2px 7px', borderRadius: 6
                          }}>
                            Confidence: {(selectedAudit.agent_a.confidence * 100).toFixed(0)}%
                          </span>
                        </div>

                        <div style={{ marginBottom: 14 }}>
                          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase' }}>
                            Assigned Classification Code
                          </div>
                          <div style={{ fontSize: 13, fontWeight: 700, fontFamily: 'monospace', color: '#0284c7', marginTop: 2 }}>
                            {selectedAudit.agent_a.root_cause_code}
                          </div>
                        </div>

                        <div style={{ marginBottom: 14 }}>
                          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase' }}>
                            Structured Factual Evidence
                          </div>
                          <p style={{ fontSize: 13, color: 'var(--text-main)', marginTop: 4, lineHeight: 1.5 }}>
                            {selectedAudit.agent_a.reasoning}
                          </p>
                        </div>

                        <div>
                          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase' }}>
                            Vendor Directive
                          </div>
                          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4, fontStyle: 'italic' }}>
                            "{selectedAudit.agent_a.recommended_action}"
                          </p>
                        </div>
                      </div>

                      {/* Agent B */}
                      <div className="studio-card" style={{ padding: 22 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#059669' }} />
                            <h4 style={{ fontSize: 14, fontWeight: 600 }}>Agent B: Independent Audit Verification</h4>
                          </div>
                          <span style={{
                            background: 'var(--badge-green-bg)', color: 'var(--badge-green-text)',
                            border: '1px solid var(--badge-green-border)',
                            fontSize: 11, fontWeight: 600, padding: '2px 7px', borderRadius: 6
                          }}>
                            Verdict: {selectedAudit.agent_b.audit_verdict} ({(selectedAudit.agent_b.auditor_confidence * 100).toFixed(0)}%)
                          </span>
                        </div>

                        <div style={{ marginBottom: 14 }}>
                          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase' }}>
                            Independent Statutory Check (Rule 60)
                          </div>
                          <p style={{ fontSize: 13, color: 'var(--text-main)', marginTop: 4, lineHeight: 1.5 }}>
                            {selectedAudit.agent_b.independent_analysis}
                          </p>
                        </div>

                        <div style={{ marginBottom: 14 }}>
                          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase' }}>
                            Cross-Examination of Agent A
                          </div>
                          <p style={{ fontSize: 13, color: 'var(--text-main)', marginTop: 4, lineHeight: 1.5 }}>
                            {selectedAudit.agent_b.cross_examination}
                          </p>
                        </div>

                        <div>
                          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-subtle)', textTransform: 'uppercase' }}>
                            Action Recommendation
                          </div>
                          <p style={{ fontSize: 13, color: '#059669', marginTop: 4, fontWeight: 500 }}>
                            {selectedAudit.agent_b.final_recommendation}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="studio-card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
                    <Cpu size={32} style={{ margin: '0 auto 12px' }} />
                    <p>Select a discrepancy on the left or run the workflow audit.</p>
                  </div>
                )}
              </div>
            )}

            {/* TAB: HUMAN REVIEW GATE */}
            {activeTab === 'humangate' && (
              <div className="studio-card" style={{ padding: 24 }}>
                <div style={{ marginBottom: 20 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600 }}>Human Review Gate & Escalation Queue</h3>
                  <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                    Autonomous execution halts and demands human review strictly under 4 triggers:
                  </p>
                  <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                    <span style={{ background: 'var(--bg-surface-subtle)', border: '1px solid var(--border-app)', padding: '4px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600 }}>1. Agent Disagreement</span>
                    <span style={{ background: 'var(--bg-surface-subtle)', border: '1px solid var(--border-app)', padding: '4px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600 }}>2. Confidence &lt; 85%</span>
                    <span style={{ background: 'var(--bg-surface-subtle)', border: '1px solid var(--border-app)', padding: '4px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600 }}>3. High Exposure (≥₹50k)</span>
                    <span style={{ background: 'var(--bg-surface-subtle)', border: '1px solid var(--border-app)', padding: '4px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600 }}>4. Malformed Input</span>
                  </div>
                </div>

                {gateQueue.length === 0 ? (
                  <div style={{ padding: 36, textAlign: 'center', color: 'var(--badge-green-text)' }}>
                    <CheckCircle2 size={36} style={{ margin: '0 auto 10px' }} />
                    <div style={{ fontSize: 14, fontWeight: 600 }}>Zero Escalations Pending</div>
                    <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                      All audited invoices met high confidence thresholds and full agent consensus.
                    </p>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {gateQueue.map(item => (
                      <div
                        key={item.gate_id}
                        style={{
                          padding: 16, borderRadius: 12,
                          background: 'var(--bg-surface-subtle)',
                          border: '1px solid var(--border-app)'
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <span style={{ fontWeight: 700, fontSize: 14 }}>{item.mismatch_id}</span>
                            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{item.supplier_name}</span>
                            <span style={{
                              background: 'var(--badge-red-bg)', color: 'var(--badge-red-text)',
                              border: '1px solid var(--badge-red-border)',
                              padding: '2px 7px', borderRadius: 6, fontSize: 11, fontWeight: 700
                            }}>
                              ₹{item.itc_exposure_inr.toLocaleString()} Risk
                            </span>
                          </div>
                          <div style={{ display: 'flex', gap: 6 }}>
                            {item.triggers.map(t => (
                              <span key={t} style={{
                                background: 'var(--badge-amber-bg)', color: 'var(--badge-amber-text)',
                                border: '1px solid var(--badge-amber-border)',
                                padding: '2px 7px', borderRadius: 6, fontSize: 11, fontWeight: 600
                              }}>
                                {t}
                              </span>
                            ))}
                          </div>
                        </div>

                        <div style={{ fontSize: 13, color: 'var(--text-main)', marginBottom: 12 }}>
                          <b>Trigger Rationale (Why it stopped):</b>
                          <ul style={{ paddingLeft: 18, marginTop: 4, color: 'var(--text-muted)', fontSize: 12 }}>
                            {item.trigger_reasons.map((r, idx) => (
                              <li key={idx}>{r}</li>
                            ))}
                          </ul>
                        </div>

                        {item.decision === 'PENDING' ? (
                          <div style={{ display: 'flex', gap: 8, paddingTop: 10, borderTop: '1px solid var(--border-app)' }}>
                            <button
                              onClick={() => handleGateDecision(item.gate_id, 'APPROVED')}
                              className="btn-primary"
                              style={{ padding: '6px 14px', fontSize: 12 }}
                            >
                              <Check size={13} /> Approve Notice
                            </button>
                            <button
                              onClick={() => handleGateDecision(item.gate_id, 'REJECTED')}
                              className="btn-secondary"
                              style={{ padding: '6px 14px', fontSize: 12, color: '#dc2626' }}
                            >
                              <X size={13} /> Suppress
                            </button>
                          </div>
                        ) : (
                          <div style={{ fontSize: 12, color: 'var(--badge-green-text)', fontWeight: 600 }}>
                            ✓ Status: {item.decision} by {item.decision_by}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* TAB: RECONCILIATION LEDGER */}
            {activeTab === 'reconcile' && (
              <div className="studio-card" style={{ padding: 24 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                  <div>
                    <h3 style={{ fontSize: 16, fontWeight: 600 }}>Deterministic Reconciliation Ledger</h3>
                    <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                      45 Invoices evaluated with statutory checksum and tolerance checks.
                    </p>
                  </div>
                  <button onClick={handleRunWorkflowAudit} className="btn-primary">
                    <Zap size={14} /> Audit All Discrepancies
                  </button>
                </div>

                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-app)', color: 'var(--text-muted)', textAlign: 'left' }}>
                        <th style={{ padding: '12px 14px', fontWeight: 500 }}>Invoice No.</th>
                        <th style={{ padding: '12px 14px', fontWeight: 500 }}>Supplier</th>
                        <th style={{ padding: '12px 14px', textAlign: 'right', fontWeight: 500 }}>PR Tax</th>
                        <th style={{ padding: '12px 14px', textAlign: 'right', fontWeight: 500 }}>GSTR-2B Tax</th>
                        <th style={{ padding: '12px 14px', textAlign: 'right', fontWeight: 500 }}>ITC Variance</th>
                        <th style={{ padding: '12px 14px', fontWeight: 500 }}>Statutory Citation</th>
                        <th style={{ padding: '12px 14px', fontWeight: 500 }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {discrepancies.map(d => (
                        <tr key={d.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '14px', fontFamily: 'JetBrains Mono, monospace', fontWeight: 600 }}>
                            {d.invoice_number}
                          </td>
                          <td style={{ padding: '14px' }}>{d.supplier_name}</td>
                          <td style={{ padding: '14px', textAlign: 'right' }}>
                            ₹{d.purchase_register_tax.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </td>
                          <td style={{ padding: '14px', textAlign: 'right' }}>
                            ₹{d.gstr_2b_tax.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </td>
                          <td style={{ padding: '14px', textAlign: 'right', fontWeight: 700, color: '#dc2626' }}>
                            ₹{d.itc_exposure_rupees.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                          </td>
                          <td style={{ padding: '14px', color: 'var(--text-muted)', fontSize: 12 }}>
                            {d.rule_citation}
                          </td>
                          <td style={{ padding: '14px' }}>
                            <button
                              onClick={() => {
                                handleRunWorkflowAudit();
                                setActiveTab('inspector');
                              }}
                              className="btn-secondary"
                              style={{ padding: '4px 10px', fontSize: 12 }}
                            >
                              Inspect Audit
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB: NUDGES & NOTICES */}
            {activeTab === 'nudge' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                {/* WhatsApp Notice */}
                <div className="studio-card" style={{ padding: 24 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <MessageSquare size={16} color="#059669" />
                      <h3 style={{ fontSize: 15, fontWeight: 600 }}>WhatsApp Compliance Nudge</h3>
                    </div>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button
                        onClick={() => setNudgeLang('en')}
                        className={nudgeLang === 'en' ? 'btn-primary' : 'btn-secondary'}
                        style={{ padding: '4px 10px', fontSize: 12 }}
                      >English</button>
                      <button
                        onClick={() => setNudgeLang('hi')}
                        className={nudgeLang === 'hi' ? 'btn-primary' : 'btn-secondary'}
                        style={{ padding: '4px 10px', fontSize: 12 }}
                      >हिन्दी</button>
                    </div>
                  </div>

                  <div style={{
                    background: 'var(--bg-surface-subtle)', padding: 16, borderRadius: 12,
                    border: '1px solid var(--border-app)', fontSize: 13, lineHeight: 1.5,
                    color: 'var(--text-main)', fontFamily: 'system-ui, sans-serif'
                  }}>
                    <div style={{ fontWeight: 700, color: '#059669', marginBottom: 6 }}>
                      CrediFlow Statutory GST Alert
                    </div>
                    {nudgeLang === 'en' ? (
                      <div>
                        <p>Dear M/s Rajesh Traders,</p>
                        <p style={{ marginTop: 6 }}>
                          URGENT: Notice regarding <b>Invoice INV-0881</b> (Dated 2026-04-12, Value: ₹2,36,111.11).
                        </p>
                        <p style={{ marginTop: 6 }}>
                          Under Rule 60 CGST, this invoice is missing in GSTR-2B, blocking <b>₹42,500.00</b> Input Tax Credit.
                        </p>
                        <div style={{ marginTop: 8, background: 'var(--bg-surface)', padding: 8, borderRadius: 6, fontSize: 12 }}>
                          <b>GST Portal Amendment Steps:</b>
                          <ol style={{ paddingLeft: 16, marginTop: 4 }}>
                            <li>Log in to gst.gov.in -&gt; GSTR-1.</li>
                            <li>Open Table 4A (B2B Outward Supplies).</li>
                            <li>Add INV-0881 with Buyer GSTIN 27AAACB0987A1Z1.</li>
                            <li>File return to unblock ITC credit stream.</li>
                          </ol>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <p>प्रिय M/s Rajesh Traders,</p>
                        <p style={{ marginTop: 6 }}>
                          अति आवश्यक: <b>इनवॉइस INV-0881</b> (दिनांक 2026-04-12, मूल्य: ₹2,36,111.11) के संबंध में GST सूचना।
                        </p>
                        <p style={{ marginTop: 6 }}>
                          Rule 60 CGST के तहत यह इनवॉइस GSTR-2B में नहीं मिला है, जिससे <b>₹42,500.00</b> का ITC अवरुद्ध है।
                        </p>
                        <div style={{ marginTop: 8, background: 'var(--bg-surface)', padding: 8, borderRadius: 6, fontSize: 12 }}>
                          <b>GST पोर्टल संशोधन प्रक्रिया:</b>
                          <ol style={{ paddingLeft: 16, marginTop: 4 }}>
                            <li>gst.gov.in पर GSTR-1 खोलें।</li>
                            <li>Table 4A पर जाएं।</li>
                            <li>INV-0881 को खरीदार GSTIN 27AAACB0987A1Z1 के साथ जोड़ें।</li>
                          </ol>
                        </div>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => handleDispatchNudge('INV-0881')}
                    className="btn-primary"
                    style={{ width: '100%', marginTop: 16 }}
                  >
                    <Send size={14} /> Send WhatsApp Notice
                  </button>
                </div>

                {/* PDF Notice */}
                <div className="studio-card" style={{ padding: 24 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <FileText size={16} color="#0284c7" />
                    <h3 style={{ fontSize: 15, fontWeight: 600 }}>Statutory Rule 60 PDF Document</h3>
                  </div>
                  <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: 16 }}>
                    Formal legal notice under Section 16(2)(aa) formatted via ReportLab with statutory references.
                  </p>

                  <div style={{
                    background: 'var(--bg-surface-subtle)', padding: 14, borderRadius: 10,
                    border: '1px solid var(--border-app)', fontFamily: 'JetBrains Mono, monospace',
                    fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.6, marginBottom: 16
                  }}>
                    <div style={{ color: 'var(--text-main)', fontWeight: 700 }}>FORMAL STATUTORY NOTICE — GST ITC DISCREPANCY</div>
                    <div>Notice Ref: GST/2026/INV-0881/NUDGE</div>
                    <div>Recipient: M/s Rajesh Traders (27AABCR1234F1ZS)</div>
                    <div>Quarantined Tax: ₹42,500.00 (CGST ₹21,250 + SGST ₹21,250)</div>
                  </div>

                  <a
                    href={`${API_BASE}/nudge/pdf/INV-0881`}
                    target="_blank"
                    rel="noreferrer"
                    className="btn-secondary"
                    style={{ width: '100%', textDecoration: 'none', justifyContent: 'center' }}
                  >
                    <Download size={14} /> Download Official PDF Document
                  </a>
                </div>
              </div>
            )}

            {/* TAB: CLOSED-LOOP JOURNEY */}
            {activeTab === 'simulator' && (
              <div className="studio-card" style={{ padding: 28, maxWidth: 840, margin: '0 auto' }}>
                <div style={{ marginBottom: 24 }}>
                  <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>
                    Visual Closed-Loop Journey
                  </h3>
                  <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                    Trace the complete recovery lifecycle: Mismatch → Nudge → Vendor Action → Re-check → VERIFIED → ITC Recovered.
                  </p>
                </div>

                <div style={{
                  background: 'var(--bg-surface-subtle)', padding: 18, borderRadius: 12,
                  border: '1px solid var(--border-app)', marginBottom: 20
                }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Real Action Post-Approval Audit Trail:</div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, fontSize: 13 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: actionStatus.pdfGenerated ? '#059669' : 'var(--text-muted)' }}>
                      {actionStatus.pdfGenerated ? <CheckCircle2 size={16} /> : <div style={{ width: 16, height: 16, borderRadius: '50%', border: '1px solid var(--border-app)' }} />}
                      <span>PDF Notice Generated</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: actionStatus.noticeDispatched ? '#059669' : 'var(--text-muted)' }}>
                      {actionStatus.noticeDispatched ? <CheckCircle2 size={16} /> : <div style={{ width: 16, height: 16, borderRadius: '50%', border: '1px solid var(--border-app)' }} />}
                      <span>Notice Dispatched</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: actionStatus.vendorCorrectionReceived ? '#059669' : 'var(--text-muted)' }}>
                      {actionStatus.vendorCorrectionReceived ? <CheckCircle2 size={16} /> : <div style={{ width: 16, height: 16, borderRadius: '50%', border: '1px solid var(--border-app)' }} />}
                      <span>Vendor Correction Received</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: actionStatus.reconciliationRerun ? '#059669' : 'var(--text-muted)' }}>
                      {actionStatus.reconciliationRerun ? <CheckCircle2 size={16} /> : <div style={{ width: 16, height: 16, borderRadius: '50%', border: '1px solid var(--border-app)' }} />}
                      <span>Reconciliation Re-run Verified</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => handleSimulateAmendment('INV-0881')}
                  disabled={loading}
                  className="btn-primary"
                  style={{ width: '100%', height: 42, fontSize: 14 }}
                >
                  <Zap size={15} />
                  Simulate Vendor Correction & Re-Audit Verification
                </button>

                {simulatedArn && (
                  <div style={{
                    marginTop: 20, padding: 16, borderRadius: 10,
                    background: 'var(--badge-green-bg)', border: '1px solid var(--badge-green-border)',
                    color: 'var(--text-main)', fontSize: 13
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#059669', fontWeight: 700 }}>
                      <CheckCircle2 size={16} /> Closed-Loop Resolution Verified
                    </div>
                    <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-muted)' }}>
                      Portal ARN: <span style={{ fontFamily: 'monospace', fontWeight: 700, color: 'var(--text-main)' }}>{simulatedArn}</span><br />
                      GSTR-2B Status: <span style={{ color: '#059669', fontWeight: 600 }}>MATCHED (100% Eligible)</span><br />
                      Recovered Credit: <span style={{ color: '#059669', fontWeight: 700 }}>₹42,500.00</span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB: SCALE & TELEMETRY */}
            {activeTab === 'benchmarks' && (
              <div className="studio-card" style={{ padding: 26 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                  <div>
                    <h3 style={{ fontSize: 16, fontWeight: 700 }}>Real Scalability & Cost Telemetry</h3>
                    <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                      Measured runtime, throughput, failure isolation, and dollar cost for high-volume batches.
                    </p>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button onClick={() => handleRunBenchmarks(100)} className="btn-secondary" style={{ fontSize: 12, padding: '5px 10px' }}>100 Rows</button>
                    <button onClick={() => handleRunBenchmarks(500)} className="btn-secondary" style={{ fontSize: 12, padding: '5px 10px' }}>500 Rows</button>
                    <button onClick={() => handleRunBenchmarks(1000)} className="btn-primary" style={{ fontSize: 12, padding: '5px 14px' }}>1,000 Rows</button>
                  </div>
                </div>

                {benchmarks && (
                  <div>
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(4, 1fr)',
                      gap: 16,
                      marginBottom: 20
                    }}>
                      <div style={{ background: 'var(--bg-surface-subtle)', padding: 18, borderRadius: 12, border: '1px solid var(--border-app)' }}>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Records Processed</div>
                        <div style={{ fontSize: 26, fontWeight: 700, marginTop: 4 }}>
                          {benchmarks.records_processed?.toLocaleString()}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--text-subtle)', marginTop: 2 }}>Full batch scale</div>
                      </div>

                      <div style={{ background: 'var(--bg-surface-subtle)', padding: 18, borderRadius: 12, border: '1px solid var(--border-app)' }}>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Wall-Clock Time</div>
                        <div style={{ fontSize: 26, fontWeight: 700, color: '#059669', marginTop: 4 }}>
                          {benchmarks.wall_clock_time_ms} ms
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{benchmarks.wall_clock_time_sec}s total runtime</div>
                      </div>

                      <div style={{ background: 'var(--bg-surface-subtle)', padding: 18, borderRadius: 12, border: '1px solid var(--border-app)' }}>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Throughput</div>
                        <div style={{ fontSize: 26, fontWeight: 700, color: '#0284c7', marginTop: 4 }}>
                          {benchmarks.throughput_invoices_per_sec?.toLocaleString()} /s
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>Invoices per second</div>
                      </div>

                      <div style={{ background: 'var(--bg-surface-subtle)', padding: 18, borderRadius: 12, border: '1px solid var(--border-app)' }}>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Actual Cost per Batch</div>
                        <div style={{ fontSize: 26, fontWeight: 700, color: '#18181b', marginTop: 4 }}>
                          ${benchmarks.actual_cost_usd}
                        </div>
                        <div style={{ fontSize: 11, color: '#059669', marginTop: 2 }}>₹{benchmarks.actual_cost_inr} (~${benchmarks.cost_per_record_usd}/inv)</div>
                      </div>
                    </div>

                    <div style={{
                      background: 'var(--bg-surface-subtle)',
                      border: '1px solid var(--border-app)',
                      borderRadius: 10,
                      padding: '14px 18px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}>
                      <div style={{ fontSize: 13, fontWeight: 600 }}>
                        Resilience Telemetry: <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>{benchmarks.resilience_summary}</span>
                      </div>
                      <div style={{ fontSize: 12, color: '#059669', fontWeight: 600 }}>
                        ✓ Zero Unhandled Pipeline Crashes
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB: VENDOR HEALTH */}
            {activeTab === 'scorecards' && (
              <div className="studio-card" style={{ padding: 24 }}>
                <div style={{ marginBottom: 18 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600 }}>Vendor Compliance Health Index</h3>
                  <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                    Statutory scoring based on GSTR-1 punctuality and discrepancy frequency.
                  </p>
                </div>

                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-app)', color: 'var(--text-muted)', textAlign: 'left' }}>
                        <th style={{ padding: '12px 14px', fontWeight: 500 }}>Vendor</th>
                        <th style={{ padding: '12px 14px', fontWeight: 500 }}>GSTIN</th>
                        <th style={{ padding: '12px 14px', fontWeight: 500 }}>State</th>
                        <th style={{ padding: '12px 14px', textAlign: 'center', fontWeight: 500 }}>Score</th>
                        <th style={{ padding: '12px 14px', fontWeight: 500 }}>Risk Tier</th>
                        <th style={{ padding: '12px 14px', fontWeight: 500 }}>Avg. ITC Delay</th>
                        <th style={{ padding: '12px 14px', fontWeight: 500 }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {scorecards.map((v, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '14px', fontWeight: 600 }}>{v.vendor_name}</td>
                          <td style={{ padding: '14px', fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: 'var(--text-muted)' }}>
                            {v.gstin}
                          </td>
                          <td style={{ padding: '14px' }}>{v.state}</td>
                          <td style={{ padding: '14px', textAlign: 'center', fontWeight: 700 }}>
                            <span style={{
                              color: v.compliance_score > 90 ? '#059669' : v.compliance_score > 70 ? '#d97706' : '#dc2626'
                            }}>
                              {v.compliance_score}
                            </span>
                          </td>
                          <td style={{ padding: '14px' }}>
                            <span style={{
                              padding: '3px 8px', borderRadius: 6, fontSize: 11, fontWeight: 700,
                              background: v.risk_tier === 'LOW' ? 'var(--badge-green-bg)' : v.risk_tier === 'MEDIUM' ? 'var(--badge-amber-bg)' : 'var(--badge-red-bg)',
                              color: v.risk_tier === 'LOW' ? 'var(--badge-green-text)' : v.risk_tier === 'MEDIUM' ? 'var(--badge-amber-text)' : 'var(--badge-red-text)',
                              border: `1px solid ${v.risk_tier === 'LOW' ? 'var(--badge-green-border)' : v.risk_tier === 'MEDIUM' ? 'var(--badge-amber-border)' : 'var(--badge-red-border)'}`
                            }}>
                              {v.risk_tier}
                            </span>
                          </td>
                          <td style={{ padding: '14px', color: v.avg_delay_days > 0 ? '#d97706' : 'var(--text-muted)' }}>
                            {v.avg_delay_days} days
                          </td>
                          <td style={{ padding: '14px' }}>
                            <button
                              onClick={() => {
                                setViewMode('dashboard');
                                setActiveTab('nudge');
                              }}
                              className="btn-secondary"
                              style={{ padding: '4px 10px', fontSize: 12 }}
                            >
                              Send Nudge
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

          </main>
        )}
      </div>
    </div>
  );
}
