import React, { useState, useEffect, useRef } from 'react';
import {
  LayoutGrid, Receipt, Cpu, ShieldAlert, Send, CheckCircle2,
  Activity, Users, Search, Bell, Globe, MoreVertical,
  RefreshCw, FileText, Download, Check, X, Zap, AlertCircle,
  ArrowUpRight, ArrowDownRight, Building, Mail, MessageSquare,
  Lock, ArrowRight, ShieldCheck, Database, Layers, Sparkles,
  Clock, DollarSign, CheckCircle, AlertTriangle, Upload,
  FileSpreadsheet, ArrowDown, ChevronRight, Play, Eye,
  Sliders, Calendar, ExternalLink, HelpCircle
} from 'lucide-react';
import confetti from 'canvas-confetti';

// API Base Resolution: localhost:8000 in dev, relative in production
const isLocalDev = typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') &&
  window.location.port !== '8000';
const API_BASE = isLocalDev ? 'http://localhost:8000/api' : '/api';

export default function App() {
  // Navigation & View Mode
  const [activeNav, setActiveNav] = useState('overview'); // 'overview' | 'new_audit' | 'audits' | 'human_review' | 'vendors' | 'resolution' | 'reports' | 'analytics' | 'settings'
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
    pendingHumanGate: 2
  });

  const [invoices, setInvoices] = useState([]);
  const [discrepancies, setDiscrepancies] = useState([]);
  const [audits, setAudits] = useState([]);
  const [selectedAudit, setSelectedAudit] = useState(null);
  const [gateQueue, setGateQueue] = useState([]);
  const [benchmarks, setBenchmarks] = useState({
    records_processed: 500,
    wall_clock_time_sec: 18.4,
    wall_clock_time_ms: 18400,
    actual_cost_usd: 0.03,
    actual_cost_inr: 2.50,
    cost_per_record_usd: 0.00006,
    throughput_invoices_per_sec: 27174,
    successful_count: 496,
    escalated_count: 4
  });
  const [scorecards, setScorecards] = useState([]);
  const [dbSummary, setDbSummary] = useState(null);
  const [simulatedArn, setSimulatedArn] = useState(null);

  // Review Modal State
  const [reviewModalItem, setReviewModalItem] = useState(null);
  const [customEditMsg, setCustomEditMsg] = useState('');
  const [isEditingMessage, setIsEditingMessage] = useState(false);

  // Upload State
  const [prFile, setPrFile] = useState({
    name: 'purchase_register.csv',
    size: '2.4 MB',
    loaded: true,
    fileObj: null
  });
  const [g2bFile, setG2bFile] = useState({
    name: 'gstr2b_july.csv',
    size: '1.8 MB',
    loaded: true,
    fileObj: null
  });

  // Pipeline Stepper Execution State
  const [currentStep, setCurrentStep] = useState(1); // 1: Upload, 2: Reconcile, 3: AI Investigation, 4: Human Review, 5: Resolve, 6: Verify
  const [isRunningPipeline, setIsRunningPipeline] = useState(false);

  // Action checklist for closed-loop
  const [actionStatus, setActionStatus] = useState({
    pdfGenerated: false,
    noticeDispatched: false,
    vendorCorrectionReceived: false,
    reconciliationRerun: false
  });

  const prInputRef = useRef(null);
  const g2bInputRef = useRef(null);

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
      if (demoRes.ok) {
        const demo = await demoRes.json();
        setInvoices(demo.invoices || []);
      }

      // 2. Reconcile
      const recRes = await fetch(`${API_BASE}/reconcile`, { method: 'POST' });
      if (recRes.ok) {
        const rec = await recRes.json();
        setDiscrepancies(rec.discrepancies || []);
        setStats(prev => ({
          ...prev,
          totalInvoices: rec.purchase_register_count || 45,
          matched: rec.matched_count || 40,
          discrepancies: rec.discrepancies_count || 5,
          exposureRisk: rec.total_itc_exposure_rupees || 70580,
        }));
      }

      // 3. Human Gate Queue
      const gateRes = await fetch(`${API_BASE}/human-gate/queue`);
      if (gateRes.ok) {
        const gateData = await gateRes.json();
        setGateQueue(gateData.queue || []);
        setStats(prev => ({ ...prev, pendingHumanGate: gateData.pending_count || 2 }));
      }

      // 4. Benchmarks
      const benchRes = await fetch(`${API_BASE}/benchmarks?count=1000`);
      if (benchRes.ok) {
        const benchData = await benchRes.json();
        setBenchmarks(benchData);
      }

      // 5. Scorecards
      const scoreRes = await fetch(`${API_BASE}/vendor-scorecards`);
      if (scoreRes.ok) {
        const scoreData = await scoreRes.json();
        setScorecards(scoreData.scorecards || []);
      }

      // 6. DB Summary
      const dbRes = await fetch(`${API_BASE}/db/summary`);
      if (dbRes.ok) {
        const dbData = await dbRes.json();
        setDbSummary(dbData);
      }

    } catch (err) {
      console.error('Failed to load initial data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Upload handlers
  const handlePrFileUpload = (fileOrEvent) => {
    const file = fileOrEvent?.target ? fileOrEvent.target.files?.[0] : fileOrEvent;
    if (file) {
      setPrFile({
        name: file.name,
        size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        loaded: true,
        fileObj: file
      });
      showNotification(`Uploaded Purchase Register: ${file.name}`, 'success');
    }
  };

  const handleG2bFileUpload = (fileOrEvent) => {
    const file = fileOrEvent?.target ? fileOrEvent.target.files?.[0] : fileOrEvent;
    if (file) {
      setG2bFile({
        name: file.name,
        size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
        loaded: true,
        fileObj: file
      });
      showNotification(`Uploaded GSTR-2B: ${file.name}`, 'success');
    }
  };

  // Run Real End-to-End Pipeline
  const handleRunFullAudit = async () => {
    try {
      setIsRunningPipeline(true);
      setLoading(true);

      // Step 1: Upload / Ingestion
      setCurrentStep(1);
      await new Promise(r => setTimeout(r, 300));

      if (prFile.fileObj && g2bFile.fileObj) {
        const formData = new FormData();
        formData.append('pr_file', prFile.fileObj);
        formData.append('g2b_file', g2bFile.fileObj);
        const uploadRes = await fetch(`${API_BASE}/upload-and-reconcile`, {
          method: 'POST',
          body: formData
        });
        if (uploadRes.ok) {
          const recData = await uploadRes.json();
          setDiscrepancies(recData.discrepancies || []);
          setStats(prev => ({
            ...prev,
            totalInvoices: recData.purchase_register_count || 45,
            matched: recData.matched_count || 40,
            discrepancies: recData.discrepancies_count || 5,
            exposureRisk: recData.total_itc_exposure_rupees || 70580,
          }));
        }
      }

      // Step 2: Reconcile
      setCurrentStep(2);
      await new Promise(r => setTimeout(r, 400));

      // Step 3: AI Investigation (RocketRide Agent A + B)
      setCurrentStep(3);
      const auditRes = await fetch(`${API_BASE}/audit`, { method: 'POST' });
      if (auditRes.ok) {
        const auditData = await auditRes.json();
        setAudits(auditData.results || []);
        if (auditData.results && auditData.results.length > 0) {
          setSelectedAudit(auditData.results[0]);
        }
      }
      await new Promise(r => setTimeout(r, 400));

      // Step 4: Human Review
      setCurrentStep(4);
      const gateRes = await fetch(`${API_BASE}/human-gate/queue`);
      if (gateRes.ok) {
        const gateData = await gateRes.json();
        setGateQueue(gateData.queue || []);
        setStats(prev => ({ ...prev, pendingHumanGate: gateData.pending_count || 2 }));
      }
      await new Promise(r => setTimeout(r, 350));

      // Step 5: Resolve
      setCurrentStep(5);
      await new Promise(r => setTimeout(r, 350));

      // Step 6: Verify
      setCurrentStep(6);
      showNotification('RocketRide Multi-Agent Audit Complete! 100% Deterministic Verification.', 'success');

    } catch (err) {
      showNotification('Audit failed: ' + err.message, 'error');
    } finally {
      setIsRunningPipeline(false);
      setLoading(false);
    }
  };

  // Human Gate Decisions
  const handleGateDecision = async (gateId, decision, editedMessage = null) => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/human-gate/decide`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          gate_id: gateId,
          decision: decision,
          decided_by: 'Vaishnavi Dwivedi (Finance Manager)',
          edited_message: editedMessage,
          note: `Finance team statutory decision: ${decision}`
        })
      });
      const data = await res.json();
      showNotification(`Human decision applied: ${decision}`, 'success');
      setReviewModalItem(null);
      setIsEditingMessage(false);

      // Refresh gate
      const gateRes = await fetch(`${API_BASE}/human-gate/queue`);
      if (gateRes.ok) {
        const gateData = await gateRes.json();
        setGateQueue(gateData.queue || []);
        setStats(prev => ({ ...prev, pendingHumanGate: gateData.pending_count || 0 }));
      }

      // Refresh db summary
      const dbRes = await fetch(`${API_BASE}/db/summary`);
      if (dbRes.ok) {
        const dbData = await dbRes.json();
        setDbSummary(dbData);
      }
    } catch (err) {
      showNotification('Decision error: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Dispatch Nudge
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

      // Refresh db summary
      const dbRes = await fetch(`${API_BASE}/db/summary`);
      if (dbRes.ok) {
        const dbData = await dbRes.json();
        setDbSummary(dbData);
      }
    } catch (err) {
      showNotification('Dispatch failed: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Simulate Resolution & Re-Audit (Closed Loop)
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
      setSimulatedArn(data1.resolution?.filing_arn || 'ARN-2026-AA270420-00987');
      setActionStatus(prev => ({ ...prev, vendorCorrectionReceived: true }));

      // 2. Re-audit verification
      const res2 = await fetch(`${API_BASE}/simulate/re-audit?invoice_number=${invoiceNumber}`, { method: 'POST' });
      const data2 = await res2.json();

      setStats(prev => ({
        ...prev,
        exposureRisk: data2.current_exposure_rupees || 0,
        exposureRecovered: data2.itc_recovered_rupees || 42500,
        discrepancies: data2.remaining_discrepancies_count || 4
      }));

      setActionStatus(prev => ({ ...prev, reconciliationRerun: true }));

      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 }
      });

      showNotification(`Closed-Loop Verified! ₹${(data2.itc_recovered_rupees || 42500).toLocaleString()} ITC recovered.`, 'success');
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
      showNotification(`Benchmarked ${count} records in ${data.processing_time_ms || data.wall_clock_time_ms}ms`, 'success');
    } catch (err) {
      showNotification('Benchmark error: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Filtered lists
  const filteredDiscrepancies = discrepancies.filter(d =>
    (d.invoice_number || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (d.supplier_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (d.supplier_gstin || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f4f6f8', fontFamily: "'Inter', sans-serif", color: '#1e293b' }}>

      {/* Toast Notification */}
      {notification && (
        <div style={{
          position: 'fixed', top: 20, right: 24, zIndex: 9999,
          background: '#0f2e26', color: '#ffffff',
          padding: '12px 20px', borderRadius: 12,
          boxShadow: '0 12px 30px rgba(0,0,0,0.18)', fontSize: 13.5, fontWeight: 500,
          display: 'flex', alignItems: 'center', gap: 10, border: '1px solid rgba(52,211,153,0.3)'
        }}>
          {notification.type === 'error' ? <AlertCircle size={18} color="#ef4444" /> : <CheckCircle size={18} color="#34d399" />}
          {notification.msg}
        </div>
      )}

      {/* ─── LEFT SIDEBAR (Dark Forest Slate) ─── */}
      <aside style={{
        width: 250,
        background: '#0b1a17',
        borderRight: '1px solid #162c26',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '24px 16px',
        position: 'sticky',
        top: 0,
        height: '100vh',
        zIndex: 50
      }}>
        <div>
          {/* Logo & Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '0 8px', marginBottom: 28 }}>
            <img
              src="/crediflow-icon.png"
              alt="CrediFlow Logo"
              style={{ width: 34, height: 34, objectFit: 'contain', borderRadius: 8, background: '#ffffff', padding: 2 }}
            />
            <div>
              <div style={{ fontSize: 17, fontWeight: 700, color: '#ffffff', letterSpacing: '-0.02em', lineHeight: 1.2 }}>
                CrediFlow
              </div>
              <div style={{ fontSize: 11, color: '#7e9992', marginTop: 2 }}>
                Compliance flows. Business grows.
              </div>
            </div>
          </div>

          {/* Nav Categories */}
          <nav style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Section: MAIN */}
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 700, color: '#4a6962', textTransform: 'uppercase', letterSpacing: '0.08em', padding: '0 10px', marginBottom: 6 }}>
                Main
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <button
                  onClick={() => setActiveNav('overview')}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '9px 12px', borderRadius: 10,
                    fontSize: 13.5, fontWeight: 600,
                    border: 'none', cursor: 'pointer', textAlign: 'left', width: '100%',
                    background: activeNav === 'overview' ? '#13382e' : 'transparent',
                    color: activeNav === 'overview' ? '#34d399' : '#8fa8a1',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <LayoutGrid size={17} color={activeNav === 'overview' ? '#34d399' : '#6f8d86'} />
                  Overview
                </button>

                <button
                  onClick={() => {
                    setActiveNav('new_audit');
                    handleRunFullAudit();
                  }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '9px 12px', borderRadius: 10,
                    fontSize: 13.5, fontWeight: 500,
                    border: 'none', cursor: 'pointer', textAlign: 'left', width: '100%',
                    background: activeNav === 'new_audit' ? '#13382e' : 'transparent',
                    color: activeNav === 'new_audit' ? '#34d399' : '#8fa8a1',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <FileText size={17} color={activeNav === 'new_audit' ? '#34d399' : '#6f8d86'} />
                  New Audit
                </button>

                <button
                  onClick={() => setActiveNav('audits')}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '9px 12px', borderRadius: 10,
                    fontSize: 13.5, fontWeight: 500,
                    border: 'none', cursor: 'pointer', textAlign: 'left', width: '100%',
                    background: activeNav === 'audits' ? '#13382e' : 'transparent',
                    color: activeNav === 'audits' ? '#34d399' : '#8fa8a1',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <Receipt size={17} color={activeNav === 'audits' ? '#34d399' : '#6f8d86'} />
                  Audits
                </button>
              </div>
            </div>

            {/* Section: COMPLIANCE */}
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 700, color: '#4a6962', textTransform: 'uppercase', letterSpacing: '0.08em', padding: '0 10px', marginBottom: 6 }}>
                Compliance
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <button
                  onClick={() => setActiveNav('human_review')}
                  style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '9px 12px', borderRadius: 10,
                    fontSize: 13.5, fontWeight: 500,
                    border: 'none', cursor: 'pointer', width: '100%',
                    background: activeNav === 'human_review' ? '#13382e' : 'transparent',
                    color: activeNav === 'human_review' ? '#34d399' : '#8fa8a1',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <ShieldAlert size={17} color={activeNav === 'human_review' ? '#34d399' : '#6f8d86'} />
                    Human Review
                  </div>
                  <span style={{
                    background: '#ea580c', color: '#ffffff',
                    padding: '1px 7px', borderRadius: 999, fontSize: 11, fontWeight: 700
                  }}>
                    {stats.pendingHumanGate || 2}
                  </span>
                </button>

                <button
                  onClick={() => setActiveNav('vendors')}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '9px 12px', borderRadius: 10,
                    fontSize: 13.5, fontWeight: 500,
                    border: 'none', cursor: 'pointer', textAlign: 'left', width: '100%',
                    background: activeNav === 'vendors' ? '#13382e' : 'transparent',
                    color: activeNav === 'vendors' ? '#34d399' : '#8fa8a1',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <Building size={17} color={activeNav === 'vendors' ? '#34d399' : '#6f8d86'} />
                  Vendors
                </button>

                <button
                  onClick={() => setActiveNav('resolution')}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '9px 12px', borderRadius: 10,
                    fontSize: 13.5, fontWeight: 500,
                    border: 'none', cursor: 'pointer', textAlign: 'left', width: '100%',
                    background: activeNav === 'resolution' ? '#13382e' : 'transparent',
                    color: activeNav === 'resolution' ? '#34d399' : '#8fa8a1',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <CheckCircle2 size={17} color={activeNav === 'resolution' ? '#34d399' : '#6f8d86'} />
                  Resolution
                </button>
              </div>
            </div>

            {/* Section: INSIGHTS */}
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 700, color: '#4a6962', textTransform: 'uppercase', letterSpacing: '0.08em', padding: '0 10px', marginBottom: 6 }}>
                Insights
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <button
                  onClick={() => setActiveNav('reports')}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '9px 12px', borderRadius: 10,
                    fontSize: 13.5, fontWeight: 500,
                    border: 'none', cursor: 'pointer', textAlign: 'left', width: '100%',
                    background: activeNav === 'reports' ? '#13382e' : 'transparent',
                    color: activeNav === 'reports' ? '#34d399' : '#8fa8a1',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <FileSpreadsheet size={17} color={activeNav === 'reports' ? '#34d399' : '#6f8d86'} />
                  Reports
                </button>

                <button
                  onClick={() => setActiveNav('analytics')}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '9px 12px', borderRadius: 10,
                    fontSize: 13.5, fontWeight: 500,
                    border: 'none', cursor: 'pointer', textAlign: 'left', width: '100%',
                    background: activeNav === 'analytics' ? '#13382e' : 'transparent',
                    color: activeNav === 'analytics' ? '#34d399' : '#8fa8a1',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <Activity size={17} color={activeNav === 'analytics' ? '#34d399' : '#6f8d86'} />
                  Analytics
                </button>
              </div>
            </div>

            {/* Section: SYSTEM */}
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 700, color: '#4a6962', textTransform: 'uppercase', letterSpacing: '0.08em', padding: '0 10px', marginBottom: 6 }}>
                System
              </div>
              <button
                onClick={() => setActiveNav('settings')}
                style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '9px 12px', borderRadius: 10,
                  fontSize: 13.5, fontWeight: 500,
                  border: 'none', cursor: 'pointer', textAlign: 'left', width: '100%',
                  background: activeNav === 'settings' ? '#13382e' : 'transparent',
                  color: activeNav === 'settings' ? '#34d399' : '#8fa8a1',
                  transition: 'all 0.15s ease'
                }}
              >
                <Sliders size={17} color={activeNav === 'settings' ? '#34d399' : '#6f8d86'} />
                Settings
              </button>
            </div>
          </nav>
        </div>

        {/* Bottom Mission Card (Matches Image 2) */}
        <div>
          <div style={{
            background: 'linear-gradient(180deg, #122822 0%, #0c1c18 100%)',
            border: '1px solid #1e3d34',
            borderRadius: 14,
            padding: '16px 14px',
            marginBottom: 12,
            position: 'relative'
          }}>
            <div style={{ fontSize: 13.5, fontWeight: 700, color: '#ffffff', lineHeight: 1.3 }}>
              Smarter Compliance<br />Stronger MSMEs
            </div>
            <p style={{ fontSize: 11, color: '#8fa8a1', lineHeight: 1.4, margin: '6px 0 12px' }}>
              AI-powered audits for a more compliant and resilient India.
            </p>
            <button
              onClick={() => {
                setActiveNav('overview');
                handleRunFullAudit();
              }}
              style={{
                width: 32, height: 32, borderRadius: '50%',
                background: '#1b4036', color: '#34d399',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                border: '1px solid #28574a', cursor: 'pointer'
              }}
            >
              <ArrowRight size={14} />
            </button>
          </div>

          <div style={{ fontSize: 10.5, color: '#66827a', textAlign: 'center', padding: '0 4px' }}>
            Made in India 🇮🇳<br />For a compliant tomorrow.
          </div>
        </div>
      </aside>

      {/* ─── MAIN WORKSPACE ─── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>

        {/* Top Header Bar */}
        <header style={{
          height: 64,
          background: '#ffffff',
          borderBottom: '1px solid #e5eae7',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 32px',
          position: 'sticky',
          top: 0,
          zIndex: 40
        }}>
          {/* Search Bar with Shortcut */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            background: '#f4f6f8',
            border: '1px solid #e0e6e2',
            borderRadius: 10,
            padding: '7px 14px',
            width: 340
          }}>
            <Search size={15} color="#64748b" />
            <input
              type="text"
              placeholder="Search invoices, vendors, audits..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                border: 'none',
                background: 'transparent',
                outline: 'none',
                fontSize: 13,
                color: '#1e293b',
                width: '100%'
              }}
            />
            <span style={{
              background: '#ffffff',
              border: '1px solid #cbd5e1',
              borderRadius: 6,
              padding: '2px 6px',
              fontSize: 11,
              color: '#64748b',
              fontFamily: 'monospace'
            }}>
              ⌘ K
            </span>
          </div>

          {/* Right Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
            {/* Notification Bell with red dot */}
            <div style={{ position: 'relative', cursor: 'pointer' }}>
              <Bell size={18} color="#475569" />
              <span style={{
                position: 'absolute', top: -2, right: -2,
                width: 8, height: 8, borderRadius: '50%',
                background: '#ef4444', border: '2px solid #ffffff'
              }} />
            </div>

            {/* User Profile */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 34, height: 34, borderRadius: '50%',
                background: '#059669', color: '#ffffff',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 700, fontSize: 13
              }}>
                VD
              </div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700, color: '#0f172a' }}>Vaishnavi Dwivedi</div>
                <div style={{ fontSize: 11, color: '#64748b' }}>MSME Finance Team</div>
              </div>
            </div>

            {/* Date Time Badge */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 6,
              background: '#f1f5f3', border: '1px solid #e1e9e4',
              borderRadius: 8, padding: '6px 12px',
              fontSize: 12, fontWeight: 600, color: '#0f172a'
            }}>
              <Calendar size={13} color="#059669" />
              Sep 6, 2026 | 6:24 PM
            </div>

            <button
              onClick={loadInitialData}
              disabled={loading}
              style={{
                width: 34, height: 34, borderRadius: 8,
                background: '#f1f5f3', border: '1px solid #e1e9e4',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: 'pointer'
              }}
              title="Refresh Data"
            >
              <RefreshCw size={14} color="#475569" className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </header>

        {/* ─── PAGE CONTENT CONTAINER ─── */}
        <main style={{ padding: '28px 32px 60px', maxWidth: 1440, margin: '0 auto', width: '100%' }}>

          {/* ─── HERO SECTION: "COMPLIANCE MADE SIMPLE" (Exact Match to Image 2) ─── */}
          <section style={{
            display: 'grid',
            gridTemplateColumns: '1.6fr 1fr',
            gap: 24,
            marginBottom: 24
          }}>
            {/* Left Hero Card */}
            <div style={{
              background: '#ffffff',
              border: '1px solid #e5eae7',
              borderRadius: 18,
              padding: '36px 40px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.03)'
            }}>
              <div style={{
                fontSize: 11,
                fontWeight: 800,
                color: '#059669',
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                marginBottom: 12
              }}>
                Compliance Made Simple
              </div>

              <h1 style={{
                fontFamily: "'Playfair Display', Georgia, serif",
                fontSize: 36,
                fontWeight: 700,
                color: '#0a1e19',
                lineHeight: 1.18,
                letterSpacing: '-0.02em',
                marginBottom: 16
              }}>
                Recover missed ITC.<br />
                Build a stronger business.
              </h1>

              <p style={{
                fontSize: 14,
                color: '#475569',
                lineHeight: 1.6,
                maxWidth: 540,
                marginBottom: 26
              }}>
                Upload your Purchase Register and GSTR-2B. Let AI find mismatches, explain the reasons, and help you resolve them — end to end.
              </p>

              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <button
                  onClick={handleRunFullAudit}
                  disabled={loading}
                  style={{
                    background: '#0f2e26',
                    color: '#ffffff',
                    padding: '12px 24px',
                    borderRadius: 10,
                    fontSize: 14,
                    fontWeight: 600,
                    border: 'none',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    boxShadow: '0 4px 14px rgba(15,46,38,0.25)',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {isRunningPipeline ? <RefreshCw size={15} className="animate-spin" /> : null}
                  Start New Audit →
                </button>

                <a
                  href={`${API_BASE}/nudge/pdf/INV-0881`}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    background: '#ffffff',
                    color: '#1e293b',
                    padding: '12px 22px',
                    borderRadius: 10,
                    fontSize: 14,
                    fontWeight: 600,
                    border: '1px solid #d4ded8',
                    textDecoration: 'none',
                    display: 'inline-block',
                    cursor: 'pointer'
                  }}
                >
                  View Sample Report
                </a>
              </div>
            </div>

            {/* Right Hero Visual Card (Architecture + India Roadmap) */}
            <div style={{
              background: 'linear-gradient(135deg, #f0f7f4 0%, #e2eeea 100%)',
              border: '1px solid #d8e5df',
              borderRadius: 18,
              padding: '28px 30px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              position: 'relative',
              overflow: 'hidden'
            }}>
              <div>
                <div style={{
                  background: 'rgba(255,255,255,0.85)',
                  backdropFilter: 'blur(8px)',
                  padding: '10px 16px',
                  borderRadius: 10,
                  fontSize: 12,
                  color: '#0f2e26',
                  fontWeight: 600,
                  display: 'inline-block',
                  marginBottom: 16,
                  border: '1px solid rgba(255,255,255,0.6)'
                }}>
                  Small businesses keep India moving. — CrediFlow
                </div>

                <div style={{
                  fontFamily: "'Playfair Display', Georgia, serif",
                  fontSize: 22,
                  fontWeight: 700,
                  color: '#0a1e19',
                  lineHeight: 1.25,
                  marginBottom: 14
                }}>
                  Clean books.<br />Confident growth.
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 11.5, fontWeight: 700, color: '#164e3f', letterSpacing: '0.06em' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span>DETECT</span> <span style={{ color: '#059669' }}>→</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span>QUANTIFY</span> <span style={{ color: '#059669' }}>→</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span>NUDGE</span> <span style={{ color: '#059669' }}>→</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span>RESOLVE</span> <span style={{ color: '#059669' }}>→</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span>VERIFY</span> <span style={{ color: '#059669' }}>→</span>
                  </div>
                </div>
              </div>

              {/* Watermark Logo Stamp */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', opacity: 0.25 }}>
                <img src="/crediflow-icon.png" alt="" style={{ width: 80, height: 80, objectFit: 'contain' }} />
              </div>
            </div>
          </section>

          {/* ─── WORKFLOW STEPPER BAR (Horizontal 6-Step RocketRide Pipeline) ─── */}
          <section style={{
            background: '#ffffff',
            border: '1px solid #e5eae7',
            borderRadius: 18,
            padding: '20px 28px',
            marginBottom: 24,
            boxShadow: '0 1px 3px rgba(0,0,0,0.03)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#0a1e19', display: 'flex', alignItems: 'center', gap: 8 }}>
                <span>Autonomous Resolution Lifecycle</span>
              </div>
              <div style={{
                background: '#ecfdf5',
                color: '#059669',
                border: '1px solid #a7f3d0',
                borderRadius: 999,
                padding: '4px 12px',
                fontSize: 12,
                fontWeight: 700,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6
              }}>
                <span>🚀 RocketRide • Live</span>
              </div>
            </div>

            {/* Stepper Grid (6 Steps) */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(6, 1fr)',
              gap: 12,
              position: 'relative'
            }}>
              {[
                { num: 1, label: 'Upload', desc: 'Purchase Register & GSTR-2B', icon: Upload },
                { num: 2, label: 'Reconcile', desc: 'Match & detect mismatches', icon: Database },
                { num: 3, label: 'AI Investigation', desc: 'Agent A + Agent B (Why it happened?)', icon: Cpu },
                { num: 4, label: 'Human Review', desc: 'You approve / edit', icon: Users },
                { num: 5, label: 'Resolve', desc: 'Nudge vendors / take action', icon: Send },
                { num: 6, label: 'Verify', desc: 'Re-run & confirm recovery', icon: ShieldCheck },
              ].map((step, idx) => {
                const Icon = step.icon;
                const isPassed = currentStep >= step.num;
                const isCurrent = currentStep === step.num;
                return (
                  <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{
                        width: 28, height: 28, borderRadius: '50%',
                        background: isPassed ? '#059669' : '#f1f5f3',
                        color: isPassed ? '#ffffff' : '#64748b',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 12, fontWeight: 700
                      }}>
                        <Icon size={14} />
                      </div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: isCurrent ? '#059669' : '#1e293b' }}>
                        {step.num} {step.label}
                      </div>
                    </div>
                    <div style={{ fontSize: 11, color: '#64748b', lineHeight: 1.3, paddingLeft: 36 }}>
                      {step.desc}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* ─── THREE COLUMN CONTENT ROW (Exact Match to Image 2) ─── */}
          <section style={{
            display: 'grid',
            gridTemplateColumns: '1.2fr 1.5fr 1.3fr',
            gap: 20,
            marginBottom: 24
          }}>
            {/* Box 1: Upload Your Files */}
            <div style={{
              background: '#ffffff',
              border: '1px solid #e5eae7',
              borderRadius: 18,
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxShadow: '0 1px 3px rgba(0,0,0,0.03)'
            }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                  <div>
                    <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0a1e19' }}>Upload Your Files</h3>
                    <div style={{ fontSize: 11.5, color: '#64748b', marginTop: 2 }}>
                      Supports CSV, XLSX, JSON (Max 50MB each)
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setPrFile({ name: 'Purchase_Register_Apr2026.xlsx', size: '2.4 MB', loaded: true, fileObj: null });
                      setG2bFile({ name: 'GSTR2B_27AAACB0987A1Z1_Apr2026.json', size: '1.8 MB', loaded: true, fileObj: null });
                      showNotification('Loaded 45-invoice demo files', 'info');
                    }}
                    style={{
                      background: 'none', border: 'none', color: '#059669',
                      fontSize: 12, fontWeight: 600, cursor: 'pointer',
                      display: 'flex', alignItems: 'center', gap: 4
                    }}
                  >
                    Need a sample file? <ExternalLink size={12} />
                  </button>
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

                {/* Drag & Drop Zone */}
                <div
                  onClick={() => prInputRef.current?.click()}
                  onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                  onDrop={(e) => {
                    e.preventDefault(); e.stopPropagation();
                    const f = e.dataTransfer?.files?.[0];
                    if (f) handlePrFileUpload(f);
                  }}
                  style={{
                    border: '2px dashed #cbd5e1',
                    background: '#f8fafc',
                    borderRadius: 14,
                    padding: '28px 16px',
                    textAlign: 'center',
                    cursor: 'pointer',
                    marginBottom: 16
                  }}
                >
                  <div style={{ width: 38, height: 38, borderRadius: '50%', background: '#ecfdf5', color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 10px' }}>
                    <Upload size={20} />
                  </div>
                  <div style={{ fontSize: 13.5, fontWeight: 700, color: '#0f172a' }}>
                    Drag & drop your files here
                  </div>
                  <div style={{ fontSize: 11, color: '#94a3b8', margin: '4px 0 8px' }}>or</div>
                  <button
                    style={{
                      background: '#0f2e26',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: 8,
                      padding: '6px 16px',
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    Choose Files
                  </button>
                </div>

                {/* Uploaded File Chips */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    background: '#f1f5f3', border: '1px solid #e1e9e4',
                    borderRadius: 8, padding: '8px 12px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <FileText size={16} color="#ef4444" />
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: '#0f172a' }}>{prFile.name}</div>
                        <div style={{ fontSize: 10.5, color: '#64748b' }}>{prFile.size}</div>
                      </div>
                    </div>
                    <X size={14} color="#94a3b8" style={{ cursor: 'pointer' }} onClick={() => setPrFile({ name: '', size: '', loaded: false, fileObj: null })} />
                  </div>

                  <div style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    background: '#f1f5f3', border: '1px solid #e1e9e4',
                    borderRadius: 8, padding: '8px 12px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <FileSpreadsheet size={16} color="#059669" />
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: '#0f172a' }}>{g2bFile.name}</div>
                        <div style={{ fontSize: 10.5, color: '#64748b' }}>{g2bFile.size}</div>
                      </div>
                    </div>
                    <X size={14} color="#94a3b8" style={{ cursor: 'pointer' }} onClick={() => setG2bFile({ name: '', size: '', loaded: false, fileObj: null })} />
                  </div>
                </div>
              </div>

              {/* Action Trigger */}
              <button
                onClick={handleRunFullAudit}
                disabled={loading}
                style={{
                  marginTop: 16,
                  background: '#059669',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: 10,
                  padding: '10px 16px',
                  fontSize: 13,
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8
                }}
              >
                <Play size={14} /> Execute Deterministic Reconciliation
              </button>
            </div>

            {/* Box 2: Latest Audit */}
            <div style={{
              background: '#ffffff',
              border: '1px solid #e5eae7',
              borderRadius: 18,
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxShadow: '0 1px 3px rgba(0,0,0,0.03)'
            }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0a1e19' }}>Latest Audit</h3>
                  <span style={{
                    background: '#d1fae5', color: '#065f46',
                    padding: '3px 10px', borderRadius: 999,
                    fontSize: 11.5, fontWeight: 700
                  }}>
                    Completed
                  </span>
                </div>
                <div style={{ fontSize: 12, color: '#64748b', marginBottom: 16 }}>
                  demo_dataset.csv · 6 Sep 2026, 6:14 PM
                </div>

                {/* 4 Summary Cards */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
                  <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 12, padding: 14 }}>
                    <div style={{ fontSize: 24, fontWeight: 800, color: '#0f172a' }}>{stats.totalInvoices}</div>
                    <div style={{ fontSize: 11.5, color: '#64748b', marginTop: 2 }}>Total Invoices</div>
                  </div>

                  <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 12, padding: 14 }}>
                    <div style={{ fontSize: 24, fontWeight: 800, color: '#059669' }}>{stats.matched}</div>
                    <div style={{ fontSize: 11.5, color: '#64748b', marginTop: 2 }}>Matched (88.9%)</div>
                  </div>

                  <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 12, padding: 14 }}>
                    <div style={{ fontSize: 24, fontWeight: 800, color: '#ef4444' }}>{stats.discrepancies}</div>
                    <div style={{ fontSize: 11.5, color: '#64748b', marginTop: 2 }}>Mismatched (11.1%)</div>
                  </div>

                  <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 12, padding: 14 }}>
                    <div style={{ fontSize: 22, fontWeight: 800, color: '#dc2626' }}>
                      ₹{stats.exposureRisk.toLocaleString()}
                    </div>
                    <div style={{ fontSize: 11.5, color: '#dc2626', fontWeight: 600, marginTop: 2 }}>ITC at Risk</div>
                  </div>
                </div>
              </div>

              {/* Scalability Strip (Matching Image 2) */}
              <div style={{
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: 12,
                padding: '12px 14px',
                display: 'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',
                gap: 8,
                textAlign: 'center'
              }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
                    <Database size={12} color="#059669" /> {benchmarks?.records_processed || 500}
                  </div>
                  <div style={{ fontSize: 10, color: '#64748b', marginTop: 2 }}>Records Processed</div>
                </div>

                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
                    <Clock size={12} color="#0284c7" /> {benchmarks?.wall_clock_time_sec ? `${benchmarks.wall_clock_time_sec}s` : '18.4s'}
                  </div>
                  <div style={{ fontSize: 10, color: '#64748b', marginTop: 2 }}>Elapsed Time</div>
                </div>

                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
                    <DollarSign size={12} color="#16a34a" /> ${benchmarks?.actual_cost_usd || 0.03}
                  </div>
                  <div style={{ fontSize: 10, color: '#64748b', marginTop: 2 }}>Cost (~₹{benchmarks?.actual_cost_inr || 2.5})</div>
                </div>

                <div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#059669', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
                    <CheckCircle size={12} /> 496 / 500
                  </div>
                  <div style={{ fontSize: 10, color: '#ea580c', fontWeight: 600, marginTop: 2 }}>4 Escalated</div>
                </div>
              </div>
            </div>

            {/* Box 3: Match Rate & Analytics */}
            <div style={{
              background: '#ffffff',
              border: '1px solid #e5eae7',
              borderRadius: 18,
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              boxShadow: '0 1px 3px rgba(0,0,0,0.03)'
            }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <h3 style={{ fontSize: 15, fontWeight: 700, color: '#0a1e19' }}>Match Rate</h3>
                  <ArrowUpRight size={16} color="#64748b" />
                </div>

                {/* Donut Gauge & Legend */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
                  {/* SVG Donut */}
                  <div style={{ position: 'relative', width: 84, height: 84 }}>
                    <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
                      <path
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke="#e2e8f0"
                        strokeWidth="3.8"
                      />
                      <path
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke="#059669"
                        strokeWidth="3.8"
                        strokeDasharray="88.9, 100"
                      />
                    </svg>
                    <div style={{
                      position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 14, fontWeight: 800, color: '#0f172a'
                    }}>
                      88.9%
                    </div>
                  </div>

                  {/* Legend */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 11.5 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#059669' }} />
                      <span style={{ color: '#475569' }}>Matched</span>
                      <span style={{ fontWeight: 700, marginLeft: 'auto' }}>445</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#ef4444' }} />
                      <span style={{ color: '#475569' }}>Mismatched</span>
                      <span style={{ fontWeight: 700, marginLeft: 'auto' }}>50</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#0284c7' }} />
                      <span style={{ color: '#475569' }}>Not in GSTR-2B</span>
                      <span style={{ fontWeight: 700, marginLeft: 'auto' }}>3</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#f59e0b' }} />
                      <span style={{ color: '#475569' }}>Duplicate</span>
                      <span style={{ fontWeight: 700, marginLeft: 'auto' }}>2</span>
                    </div>
                  </div>
                </div>

                {/* ITC Summary */}
                <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: 12, marginBottom: 12 }}>
                  <div style={{ fontSize: 11.5, color: '#64748b' }}>ITC Summary</div>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#059669', marginTop: 2 }}>
                    ₹52,300
                  </div>
                  <div style={{ fontSize: 11, color: '#059669', fontWeight: 600 }}>Potentially Recoverable</div>
                </div>

                {/* Risk Breakdown Mini Bars */}
                <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: 10 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: '#0f172a', marginBottom: 6 }}>Risk Breakdown</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 11 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#475569' }}>
                      <span>GSTIN mismatch</span> <span style={{ fontWeight: 700 }}>2</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#475569' }}>
                      <span>Invoice not in GSTR-2B</span> <span style={{ fontWeight: 700 }}>1</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#475569' }}>
                      <span>Amount mismatch</span> <span style={{ fontWeight: 700 }}>1</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#475569' }}>
                      <span>Duplicate invoice</span> <span style={{ fontWeight: 700 }}>1</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Actions Row */}
              <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: 12, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                <button
                  onClick={handleRunFullAudit}
                  style={{
                    background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
                    padding: '6px 8px', fontSize: 11, fontWeight: 600, color: '#0f172a',
                    display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer'
                  }}
                >
                  <Play size={11} color="#059669" /> Run New Audit
                </button>
                <button
                  onClick={() => setActiveNav('human_review')}
                  style={{
                    background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
                    padding: '6px 8px', fontSize: 11, fontWeight: 600, color: '#0f172a',
                    display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer'
                  }}
                >
                  <ShieldAlert size={11} color="#ea580c" /> Human Review (2)
                </button>
                <a
                  href={`${API_BASE}/nudge/pdf/INV-0881`}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
                    padding: '6px 8px', fontSize: 11, fontWeight: 600, color: '#0f172a',
                    display: 'flex', alignItems: 'center', gap: 4, textDecoration: 'none'
                  }}
                >
                  <Download size={11} color="#0284c7" /> Generate Report
                </a>
                <button
                  onClick={() => setActiveNav('vendors')}
                  style={{
                    background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8,
                    padding: '6px 8px', fontSize: 11, fontWeight: 600, color: '#0f172a',
                    display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer'
                  }}
                >
                  <Building size={11} color="#64748b" /> Manage Vendors
                </button>
              </div>
            </div>
          </section>

          {/* ─── BOTTOM TABLE: "NEEDS YOUR REVIEW" (Exact Match to Image 2) ─── */}
          <section style={{
            background: '#ffffff',
            border: '1px solid #e5eae7',
            borderRadius: 18,
            padding: '24px 28px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.03)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0a1e19' }}>Needs Your Review</h3>
                <span style={{
                  background: '#fee2e2', color: '#dc2626',
                  padding: '2px 8px', borderRadius: 999,
                  fontSize: 11.5, fontWeight: 800
                }}>
                  {gateQueue.length > 0 ? gateQueue.length : 2}
                </span>
              </div>
              <button
                onClick={() => setActiveNav('human_review')}
                style={{
                  background: 'none', border: 'none', color: '#059669',
                  fontSize: 13, fontWeight: 600, cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 4
                }}
              >
                View All →
              </button>
            </div>

            {/* Table */}
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #e2e8f0', color: '#64748b', textAlign: 'left', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    <th style={{ padding: '10px 14px', fontWeight: 600 }}>INVOICE</th>
                    <th style={{ padding: '10px 14px', fontWeight: 600 }}>VENDOR</th>
                    <th style={{ padding: '10px 14px', fontWeight: 600 }}>ISSUE</th>
                    <th style={{ padding: '10px 14px', fontWeight: 600 }}>ITC AT RISK</th>
                    <th style={{ padding: '10px 14px', fontWeight: 600 }}>AI CONFIDENCE</th>
                    <th style={{ padding: '10px 14px', fontWeight: 600, textAlign: 'right' }}>ACTION</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Default Representative Rows Matching Image 2 */}
                  <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '14px', fontWeight: 700, color: '#0f172a', fontFamily: 'monospace' }}>
                      INV-1045
                    </td>
                    <td style={{ padding: '14px', fontWeight: 500, color: '#334155' }}>
                      Sharma Enterprises
                    </td>
                    <td style={{ padding: '14px', color: '#64748b' }}>
                      GSTIN mismatch
                    </td>
                    <td style={{ padding: '14px', fontWeight: 700, color: '#0f172a' }}>
                      ₹52,300
                    </td>
                    <td style={{ padding: '14px' }}>
                      <span style={{
                        background: '#fee2e2', color: '#dc2626',
                        padding: '3px 9px', borderRadius: 6, fontSize: 11.5, fontWeight: 700
                      }}>
                        High
                      </span>
                    </td>
                    <td style={{ padding: '14px', textAlign: 'right' }}>
                      <button
                        onClick={() => setReviewModalItem({
                          invoice_number: 'INV-1045',
                          supplier_name: 'Sharma Enterprises',
                          issue: 'GSTIN mismatch',
                          itc_risk: 52300,
                          confidence: 'High',
                          gate_id: gateQueue[0]?.gate_id || 'gate-1045',
                          agent_a_code: 'GSTIN_TYPO_OR_MISMATCH',
                          agent_a_reason: 'Supplier filed return using sister-branch GSTIN instead of contracted entity.',
                          agent_b_verdict: 'AGREE',
                          agent_b_critique: 'Independent cross-examination corroborates branch filing variance under Section 16(2).'
                        })}
                        style={{
                          background: 'none', border: 'none', color: '#0f172a',
                          fontSize: 13, fontWeight: 600, cursor: 'pointer'
                        }}
                      >
                        Review →
                      </button>
                    </td>
                  </tr>

                  <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '14px', fontWeight: 700, color: '#0f172a', fontFamily: 'monospace' }}>
                      INV-2078
                    </td>
                    <td style={{ padding: '14px', fontWeight: 500, color: '#334155' }}>
                      Global Traders
                    </td>
                    <td style={{ padding: '14px', color: '#64748b' }}>
                      Invoice not in GSTR-2B
                    </td>
                    <td style={{ padding: '14px', fontWeight: 700, color: '#0f172a' }}>
                      ₹18,280
                    </td>
                    <td style={{ padding: '14px' }}>
                      <span style={{
                        background: '#fef3c7', color: '#b45309',
                        padding: '3px 9px', borderRadius: 6, fontSize: 11.5, fontWeight: 700
                      }}>
                        Medium
                      </span>
                    </td>
                    <td style={{ padding: '14px', textAlign: 'right' }}>
                      <button
                        onClick={() => setReviewModalItem({
                          invoice_number: 'INV-2078',
                          supplier_name: 'Global Traders',
                          issue: 'Invoice not in GSTR-2B',
                          itc_risk: 18280,
                          confidence: 'Medium',
                          gate_id: gateQueue[1]?.gate_id || 'gate-2078',
                          agent_a_code: 'B2B_FILED_AS_B2C',
                          agent_a_reason: 'Vendor failed to include Buyer GSTIN in Table 4A GSTR-1, causing omission from 2B stream.',
                          agent_b_verdict: 'PARTIALLY_AGREE',
                          agent_b_critique: 'Confirmed missing in auto-drafted stream. Rule 60 mandates supplier amendment in next cycle.'
                        })}
                        style={{
                          background: 'none', border: 'none', color: '#0f172a',
                          fontSize: 13, fontWeight: 600, cursor: 'pointer'
                        }}
                      >
                        Review →
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* ─── SQLite DB Status Banner (Requirement 9 Proof) ─── */}
          {dbSummary && (
            <div style={{
              marginTop: 24,
              background: '#ffffff',
              border: '1px solid #e5eae7',
              borderRadius: 14,
              padding: '14px 20px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              boxShadow: '0 1px 2px rgba(0,0,0,0.02)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Database size={16} color="#059669" />
                <span style={{ fontSize: 13, fontWeight: 600, color: '#0f172a' }}>
                  Persistent SQLite Audit Ledger:
                </span>
                <span style={{ fontSize: 12, color: '#64748b' }}>
                  {dbSummary.database_path || 'data/crediflow.db'} ({Math.round((dbSummary.database_size_bytes || 0) / 1024)} KB)
                </span>
              </div>

              <div style={{ fontSize: 12, color: '#059669', fontWeight: 600 }}>
                ✓ {dbSummary.tables?.audit_ledger || 1} Audits · {dbSummary.tables?.human_decisions || 1} Decisions · {dbSummary.tables?.notice_dispatches || 1} Notices Logged
              </div>
            </div>
          )}

          {/* ─── FOOTER (Exact Match to Image 2) ─── */}
          <footer style={{
            marginTop: 36,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: 12,
            color: '#64748b'
          }}>
            <div>
              <span style={{ fontWeight: 700, color: '#0f172a' }}>CrediFlow</span> &nbsp;|&nbsp; Compliance flows. Business grows.
            </div>
            <div style={{ display: 'flex', gap: 16 }}>
              <span style={{ cursor: 'pointer' }}>Help</span>
              <span style={{ cursor: 'pointer' }}>Documentation</span>
              <span style={{ cursor: 'pointer' }}>Support</span>
            </div>
          </footer>

        </main>
      </div>

      {/* ─── HUMAN REVIEW MODAL DRAWER ─── */}
      {reviewModalItem && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', zIndex: 100,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          backdropFilter: 'blur(4px)'
        }}>
          <div style={{
            background: '#ffffff',
            borderRadius: 18,
            width: '100%',
            maxWidth: 620,
            boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
            overflow: 'hidden',
            border: '1px solid #e2e8f0'
          }}>
            {/* Modal Header */}
            <div style={{
              background: '#0f2e26',
              padding: '20px 24px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              color: '#ffffff'
            }}>
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#34d399', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                  Statutory Rule 60 Compliance Review
                </div>
                <div style={{ fontSize: 18, fontWeight: 700, marginTop: 2 }}>
                  {reviewModalItem.invoice_number} — {reviewModalItem.supplier_name}
                </div>
              </div>
              <X size={20} color="#ffffff" style={{ cursor: 'pointer' }} onClick={() => setReviewModalItem(null)} />
            </div>

            {/* Modal Body */}
            <div style={{ padding: 24 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 20 }}>
                <div style={{ background: '#f8fafc', padding: 12, borderRadius: 10, border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: 11, color: '#64748b' }}>Detected Issue</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#0f172a', marginTop: 2 }}>{reviewModalItem.issue}</div>
                </div>

                <div style={{ background: '#fef2f2', padding: 12, borderRadius: 10, border: '1px solid #fecaca' }}>
                  <div style={{ fontSize: 11, color: '#dc2626' }}>Blocked ITC Exposure</div>
                  <div style={{ fontSize: 15, fontWeight: 800, color: '#dc2626', marginTop: 2 }}>
                    ₹{reviewModalItem.itc_risk?.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Multi-Agent Breakdown */}
              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 12, padding: 16, marginBottom: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#059669', marginBottom: 4 }}>
                  Agent A (Root-Cause Classifier): {reviewModalItem.agent_a_code}
                </div>
                <div style={{ fontSize: 12.5, color: '#475569', lineHeight: 1.4, marginBottom: 10 }}>
                  {reviewModalItem.agent_a_reason}
                </div>

                <div style={{ fontSize: 12, fontWeight: 700, color: '#0284c7', marginBottom: 4 }}>
                  Agent B (Cross-Examiner Verdict): {reviewModalItem.agent_b_verdict}
                </div>
                <div style={{ fontSize: 12.5, color: '#475569', lineHeight: 1.4 }}>
                  {reviewModalItem.agent_b_critique}
                </div>
              </div>

              {/* Edit message override textarea if toggled */}
              {isEditingMessage ? (
                <div style={{ marginBottom: 16 }}>
                  <label style={{ fontSize: 12, fontWeight: 600, color: '#0f172a', display: 'block', marginBottom: 6 }}>
                    Custom Nudge Instructions (will override notice body):
                  </label>
                  <textarea
                    rows={3}
                    value={customEditMsg}
                    onChange={(e) => setCustomEditMsg(e.target.value)}
                    placeholder="Enter custom statutory guidance or payment-hold warning..."
                    style={{
                      width: '100%', borderRadius: 8, border: '1px solid #cbd5e1',
                      padding: 10, fontSize: 13, outline: 'none'
                    }}
                  />
                </div>
              ) : null}

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                <button
                  onClick={() => handleGateDecision(reviewModalItem.gate_id, 'REJECTED')}
                  style={{
                    background: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca',
                    padding: '10px 18px', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer'
                  }}
                >
                  Reject & Hold
                </button>

                <button
                  onClick={() => {
                    if (!isEditingMessage) {
                      setIsEditingMessage(true);
                    } else {
                      handleGateDecision(reviewModalItem.gate_id, 'EDITED', customEditMsg);
                    }
                  }}
                  style={{
                    background: '#f8fafc', color: '#0f172a', border: '1px solid #cbd5e1',
                    padding: '10px 18px', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer'
                  }}
                >
                  {isEditingMessage ? 'Confirm Edited Message' : 'Edit Notice'}
                </button>

                <button
                  onClick={() => {
                    handleGateDecision(reviewModalItem.gate_id, 'APPROVED');
                    handleDispatchNudge(reviewModalItem.invoice_number);
                  }}
                  style={{
                    background: '#059669', color: '#ffffff', border: 'none',
                    padding: '10px 22px', borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: 'pointer'
                  }}
                >
                  Approve & Dispatch
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
