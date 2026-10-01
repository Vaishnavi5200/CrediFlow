import React, { useState, useEffect } from 'react';
import {
  ShieldAlert, CheckCircle2, ArrowRight, Bot, Building,
  Send, Database, ShieldCheck, Zap, Lock, Sparkles,
  ChevronRight, Check, X, HelpCircle, FileText, AlertTriangle,
  Play, Globe, Star, Upload, Cpu
} from 'lucide-react';
import { supabase } from './supabase';

export default function LandingPage({ onEnterApp, onOpenAuth, session }) {
  // Always scroll to top when page is loaded or refreshed
  useEffect(() => {
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }
    if (window.location.hash) {
      window.history.replaceState(null, '', window.location.pathname);
    }
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });

    // Ensure it sticks to top even after images and child elements finish rendering
    const timer = setTimeout(() => {
      window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    }, 50);
    return () => clearTimeout(timer);
  }, []);

  const scrollToSection = (e, sectionId) => {
    if (e) e.preventDefault();
    const elem = document.getElementById(sectionId);
    if (elem) {
      elem.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'signup'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState(null);
  const [authSuccess, setAuthSuccess] = useState(null);

  const openAuth = (mode = 'login') => {
    setAuthMode(mode);
    setAuthError(null);
    setAuthSuccess(null);
    setAuthModalOpen(true);
  };

  const handleGoogleSignIn = async () => {
    try {
      setAuthLoading(true);
      setAuthError(null);
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: window.location.origin
        }
      });
      if (error) throw error;
    } catch (err) {
      setAuthError(err.message || 'Failed to sign in with Google');
      setAuthLoading(false);
    }
  };

  const handleResendConfirmation = async () => {
    if (!email) {
      setAuthError('Please enter your email above to resend the confirmation link.');
      return;
    }
    try {
      setAuthLoading(true);
      setAuthError(null);
      const { error } = await supabase.auth.resend({
        type: 'signup',
        email: email,
        options: {
          emailRedirectTo: window.location.origin
        }
      });
      if (error) throw error;
      setAuthSuccess('Confirmation email resent! Please check your Inbox and Spam/Junk folder.');
    } catch (err) {
      setAuthError(err.message || 'Unable to resend email. Please use Google Sign-In or Enter Direct Access.');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleEmailAuth = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setAuthError('Please enter both email and password.');
      return;
    }

    try {
      setAuthLoading(true);
      setAuthError(null);
      setAuthSuccess(null);

      if (authMode === 'signup') {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: window.location.origin
          }
        });
        if (error) {
          if (error.message?.toLowerCase().includes('already registered')) {
            setAuthError('Account is already registered. If not yet confirmed via email, you can resend confirmation or sign in with Google.');
          } else {
            throw error;
          }
        } else if (data.user && !data.session) {
          setAuthSuccess('Registration submitted! Please check your email inbox & spam folder for the confirmation link.');
        } else {
          setAuthSuccess('Account created successfully! Redirecting...');
          setTimeout(() => {
            setAuthModalOpen(false);
            if (onEnterApp) onEnterApp();
          }, 1000);
        }
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password
        });
        if (error) {
          if (error.message?.toLowerCase().includes('invalid login credentials')) {
            setAuthError('Invalid credentials or email not confirmed yet. Please verify your email via the confirmation link or sign in with Google.');
          } else {
            throw error;
          }
        } else {
          setAuthSuccess('Login successful! Welcome back to CrediFlow.');
          setTimeout(() => {
            setAuthModalOpen(false);
            if (onEnterApp) onEnterApp();
          }, 800);
        }
      }
    } catch (err) {
      setAuthError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setAuthLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#ffffff', color: '#0f172a', fontFamily: "'Inter', -apple-system, sans-serif" }}>
      {/* ─── PUBLIC NAVBAR (Dark Forest Green - Dashboard Sidebar Theme) ─── */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: '#0b1a17',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid #162c26',
        padding: '0 32px',
        height: 70,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <img
            src="/crediflow-icon.png"
            alt="CrediFlow Logo"
            style={{ width: 36, height: 36, objectFit: 'contain', borderRadius: 9, background: '#ffffff', padding: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.2)' }}
          />
          <div>
            <div style={{ fontSize: 18, fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em', lineHeight: 1.2 }}>
              CrediFlow
            </div>
            <div style={{ fontSize: 11.5, fontWeight: 500, color: '#cbd5e1', marginTop: 2, letterSpacing: '0.01em' }}>
              Compliance flows. Business grows.
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 32, fontSize: 14.5, fontWeight: 600, color: '#f8fafc' }}>
          <button
            onClick={(e) => scrollToSection(e, 'features')}
            style={{ background: 'none', border: 'none', color: '#f8fafc', fontSize: 14.5, fontWeight: 600, cursor: 'pointer', padding: 0, transition: 'all 0.15s ease' }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#34d399'}
            onMouseLeave={(e) => e.currentTarget.style.color = '#f8fafc'}
          >
            Features
          </button>
          <button
            onClick={(e) => scrollToSection(e, 'how-it-works')}
            style={{ background: 'none', border: 'none', color: '#f8fafc', fontSize: 14.5, fontWeight: 600, cursor: 'pointer', padding: 0, transition: 'all 0.15s ease' }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#34d399'}
            onMouseLeave={(e) => e.currentTarget.style.color = '#f8fafc'}
          >
            How It Works
          </button>
          <button
            onClick={(e) => scrollToSection(e, 'comparison')}
            style={{ background: 'none', border: 'none', color: '#f8fafc', fontSize: 14.5, fontWeight: 600, cursor: 'pointer', padding: 0, transition: 'all 0.15s ease' }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#34d399'}
            onMouseLeave={(e) => e.currentTarget.style.color = '#f8fafc'}
          >
            Why CrediFlow
          </button>
          <button
            onClick={(e) => scrollToSection(e, 'faq')}
            style={{ background: 'none', border: 'none', color: '#f8fafc', fontSize: 14.5, fontWeight: 600, cursor: 'pointer', padding: 0, transition: 'all 0.15s ease' }}
            onMouseEnter={(e) => e.currentTarget.style.color = '#34d399'}
            onMouseLeave={(e) => e.currentTarget.style.color = '#f8fafc'}
          >
            FAQ
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          {session ? (
            <button
              onClick={onEnterApp}
              style={{
                background: '#059669', color: '#ffffff', border: 'none',
                padding: '10px 22px', borderRadius: 10, fontSize: 14, fontWeight: 700,
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8,
                boxShadow: '0 2px 12px rgba(5, 150, 105, 0.4)', transition: 'all 0.15s ease'
              }}
            >
              Open Dashboard <ArrowRight size={16} />
            </button>
          ) : (
            <>
              <button
                onClick={() => openAuth('login')}
                style={{
                  background: 'rgba(255, 255, 255, 0.1)', color: '#ffffff', border: '1px solid rgba(255, 255, 255, 0.22)',
                  padding: '9px 20px', borderRadius: 10, fontSize: 14, fontWeight: 600,
                  cursor: 'pointer', transition: 'all 0.15s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.18)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'}
              >
                Sign In
              </button>
              <button
                onClick={() => openAuth('signup')}
                style={{
                  background: '#059669', color: '#ffffff', border: 'none',
                  padding: '10px 22px', borderRadius: 10, fontSize: 14, fontWeight: 700,
                  cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
                  boxShadow: '0 2px 12px rgba(5, 150, 105, 0.4)', transition: 'all 0.15s ease'
                }}
              >
                Get Started Free <ArrowRight size={15} />
              </button>
            </>
          )}
        </div>
      </nav>

      {/* ─── HERO SECTION ─── */}
      <section style={{
        padding: '70px 32px 60px',
        maxWidth: 1200,
        margin: '0 auto',
        textAlign: 'center',
        background: 'radial-gradient(ellipse at top, #f0f7f4 0%, #ffffff 65%)'
      }}>
        {/* Hero Headline */}
        <h1 className="font-display" style={{
          fontSize: 'clamp(36px, 5.5vw, 58px)',
          fontWeight: 800,
          lineHeight: 1.14,
          color: '#0a1e19',
          letterSpacing: '-0.03em',
          maxWidth: 950,
          margin: '0 auto 20px'
        }}>
          Recover Lost Input Tax Credit.<br />
          <span style={{
            background: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            Protect MSME Cashflow on Autopilot.
          </span>
        </h1>

        <p style={{
          fontSize: 17,
          color: '#475569',
          lineHeight: 1.65,
          maxWidth: 720,
          margin: '0 auto 36px'
        }}>
          Reconcile thousands of Purchase Register and GSTR-2B records in milliseconds.
          100% deterministic mathematical precision with AI bilingual WhatsApp statutory notices to close the loop with non-compliant suppliers.
        </p>

        {/* Hero Action Buttons */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 14, flexWrap: 'wrap', marginBottom: 50 }}>
          <button
            onClick={() => openAuth('signup')}
            style={{
              background: '#059669', color: '#ffffff', border: 'none',
              padding: '14px 34px', borderRadius: 12, fontSize: 15.5, fontWeight: 700,
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10,
              boxShadow: '0 4px 14px rgba(5, 150, 105, 0.35)', transition: 'all 0.15s ease'
            }}
          >
            Get Started for Free <ArrowRight size={18} />
          </button>

          <button
            onClick={() => openAuth('login')}
            style={{
              background: '#ffffff', color: '#0a1e19', border: '1px solid #d4ded8',
              padding: '14px 28px', borderRadius: 12, fontSize: 15, fontWeight: 600,
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8,
              boxShadow: '0 2px 6px rgba(0,0,0,0.03)', transition: 'all 0.15s ease'
            }}
          >
            Sign In
          </button>
        </div>

        {/* Key Metrics Strip */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16,
          background: 'linear-gradient(135deg, #f0f7f4 0%, #e2eeea 100%)',
          border: '1px solid #d8e5df', borderRadius: 18, padding: '24px 28px',
          maxWidth: 1000, margin: '0 auto 60px',
          boxShadow: '0 1px 4px rgba(11,26,23,0.04)'
        }}>
          <div>
            <div className="font-mono tabular-nums" style={{ fontSize: 26, fontWeight: 800, color: '#059669' }}>100%</div>
            <div style={{ fontSize: 12.5, fontWeight: 600, color: '#164e3f', marginTop: 2 }}>Deterministic Accuracy</div>
          </div>
          <div>
            <div className="font-display" style={{ fontSize: 24, fontWeight: 800, color: '#0b1a17' }}>Section 16(2)(aa)</div>
            <div style={{ fontSize: 12.5, fontWeight: 600, color: '#164e3f', marginTop: 2 }}>Statutory Rule 60 Verified</div>
          </div>
          <div>
            <div className="font-display" style={{ fontSize: 24, fontWeight: 800, color: '#059669' }}>Bilingual Nudges</div>
            <div style={{ fontSize: 12.5, fontWeight: 600, color: '#164e3f', marginTop: 2 }}>English & Hindi WhatsApp Ready</div>
          </div>
          <div>
            <div className="font-mono tabular-nums" style={{ fontSize: 26, fontWeight: 800, color: '#0b1a17' }}>&lt; 50ms</div>
            <div style={{ fontSize: 12.5, fontWeight: 600, color: '#164e3f', marginTop: 2 }}>1,000+ Invoices Processed</div>
          </div>
        </div>

        {/* Hero Interactive App Mockup Preview */}
        <div style={{
          background: '#0b1a17',
          borderRadius: 22,
          padding: '12px',
          boxShadow: '0 25px 50px -12px rgba(11, 26, 23, 0.45)',
          border: '1px solid #162c26',
          maxWidth: 1060,
          margin: '0 auto'
        }}>
          <div style={{
            background: '#ffffff',
            borderRadius: 16,
            overflow: 'hidden',
            border: '1px solid rgba(255,255,255,0.1)'
          }}>
            {/* Fake browser topbar */}
            <div style={{
              background: '#f1f5f3', padding: '10px 16px', display: 'flex', alignItems: 'center',
              gap: 8, borderBottom: '1px solid #e5eae7'
            }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444' }} />
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#f59e0b' }} />
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#10b981' }} />
              <div className="font-mono" style={{
                background: '#ffffff', borderRadius: 6, padding: '3px 14px', fontSize: 11,
                color: '#64748b', margin: '0 auto', border: '1px solid #e2e8f0'
              }}>
                app.crediflow.in/audit/live-reconciliation
              </div>
            </div>

            {/* Mockup Preview Content */}
            <div style={{ padding: '24px 28px', background: '#f8fafc', textAlign: 'left' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 20 }}>
                <div style={{ background: '#ffffff', padding: 14, borderRadius: 10, border: '1px solid #e5eae7' }}>
                  <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600 }}>Total Invoices</div>
                  <div className="font-mono tabular-nums" style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginTop: 2 }}>45 Invoices</div>
                </div>
                <div style={{ background: '#ffffff', padding: 14, borderRadius: 10, border: '1px solid #e5eae7' }}>
                  <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600 }}>Matched & Safe</div>
                  <div className="font-mono tabular-nums" style={{ fontSize: 20, fontWeight: 800, color: '#059669', marginTop: 2 }}>39 (86.7%)</div>
                </div>
                <div style={{ background: '#ffffff', padding: 14, borderRadius: 10, border: '1px solid #e5eae7' }}>
                  <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600 }}>Blocked ITC Risk</div>
                  <div className="font-mono tabular-nums" style={{ fontSize: 20, fontWeight: 800, color: '#dc2626', marginTop: 2 }}>₹1,54,200</div>
                </div>
                <div style={{ background: '#ffffff', padding: 14, borderRadius: 10, border: '1px solid #e5eae7' }}>
                  <div style={{ fontSize: 11, color: '#64748b', fontWeight: 600 }}>Human Review Gate</div>
                  <div className="font-mono tabular-nums" style={{ fontSize: 20, fontWeight: 800, color: '#059669', marginTop: 2 }}>2 Pending</div>
                </div>
              </div>

              {/* Sample Discrepancy Card */}
              <div style={{
                background: '#ffffff', border: '1px solid #e5eae7', borderRadius: 12, padding: 16,
                display: 'flex', justifyContent: 'space-between', alignItems: 'center'
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span className="font-mono" style={{ fontWeight: 800, fontSize: 14 }}>INV-57741</span>
                    <span style={{ background: '#fee2e2', color: '#dc2626', padding: '2px 8px', borderRadius: 6, fontSize: 11, fontWeight: 700 }}>
                      MISSING IN GSTR-2B
                    </span>
                  </div>
                  <div style={{ fontSize: 12.5, color: '#475569', marginTop: 4 }}>
                    Titan Company Limited · Blocked ITC: <strong className="font-mono tabular-nums">₹8,808.06</strong> under Sec 16(2)(aa)
                  </div>
                </div>
                <button
                  onClick={session ? onEnterApp : () => openAuth('signup')}
                  style={{
                    background: '#059669', color: '#fff', border: 'none', borderRadius: 8,
                    padding: '8px 16px', fontSize: 12, fontWeight: 700, cursor: 'pointer'
                  }}
                >
                  Review & Nudge ➜
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── 4 STATUTORY PILLARS (FEATURES) ─── */}
      <section id="features" style={{ padding: '80px 32px', background: '#f4f8f6', borderTop: '1px solid #e5eae7', scrollMarginTop: 80 }}>
        <div style={{ maxWidth: 1160, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 50 }}>
            <div style={{ fontSize: 12.5, fontWeight: 800, color: '#059669', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Enterprise Compliance Architecture
            </div>
            <h2 className="font-display" style={{ fontSize: 34, fontWeight: 800, color: '#0a1e19', marginTop: 6, letterSpacing: '-0.025em' }}>
              Engineered to Protect Every Rupee of ITC
            </h2>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 20 }}>
            {/* Pillar 1 */}
            <div style={{ background: '#ffffff', border: '1px solid #e5eae7', borderRadius: 16, padding: '28px 24px', boxShadow: '0 1px 3px rgba(0,0,0,0.02)' }}>
              <div style={{ width: 44, height: 44, borderRadius: 10, background: '#ecfdf5', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#059669', marginBottom: 18 }}>
                <Zap size={22} />
              </div>
              <h3 style={{ fontSize: 17, fontWeight: 800, color: '#0a1e19', marginBottom: 8 }}>100% Deterministic Engine</h3>
              <p style={{ fontSize: 13.5, color: '#475569', lineHeight: 1.6 }}>
                Zero LLM arithmetic. Exact statutory rules for Section 16(2)(aa), Rule 86B (1% cash tax threshold), and Section 16(4) time-barring.
              </p>
            </div>

            {/* Pillar 2 */}
            <div style={{ background: '#ffffff', border: '1px solid #e5eae7', borderRadius: 16, padding: '28px 24px', boxShadow: '0 1px 3px rgba(0,0,0,0.02)' }}>
              <div style={{ width: 44, height: 44, borderRadius: 10, background: '#ecfdf5', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#059669', marginBottom: 18 }}>
                <ShieldAlert size={22} />
              </div>
              <h3 style={{ fontSize: 17, fontWeight: 800, color: '#0a1e19', marginBottom: 8 }}>Human-in-the-Loop Gate</h3>
              <p style={{ fontSize: 13.5, color: '#475569', lineHeight: 1.6 }}>
                Finance Managers retain complete control. High-exposure and malformed discrepancies are routed to the approval gate before notice dispatch.
              </p>
            </div>

            {/* Pillar 3 */}
            <div style={{ background: '#ffffff', border: '1px solid #e5eae7', borderRadius: 16, padding: '28px 24px', boxShadow: '0 1px 3px rgba(0,0,0,0.02)' }}>
              <div style={{ width: 44, height: 44, borderRadius: 10, background: '#ecfdf5', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#059669', marginBottom: 18 }}>
                <Bot size={22} />
              </div>
              <h3 style={{ fontSize: 17, fontWeight: 800, color: '#0a1e19', marginBottom: 8 }}>Bilingual WhatsApp Nudges</h3>
              <p style={{ fontSize: 13.5, color: '#475569', lineHeight: 1.6 }}>
                Generates polite, legally sound statutory notices in English and Hindi. Dispatches instantly via WhatsApp Business API or wa.me deep links.
              </p>
            </div>

            {/* Pillar 4 */}
            <div style={{ background: '#ffffff', border: '1px solid #e5eae7', borderRadius: 16, padding: '28px 24px', boxShadow: '0 1px 3px rgba(0,0,0,0.02)' }}>
              <div style={{ width: 44, height: 44, borderRadius: 10, background: '#ecfdf5', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#059669', marginBottom: 18 }}>
                <CheckCircle2 size={22} />
              </div>
              <h3 style={{ fontSize: 17, fontWeight: 800, color: '#0a1e19', marginBottom: 8 }}>Closed-Loop Recovery</h3>
              <p style={{ fontSize: 13.5, color: '#475569', lineHeight: 1.6 }}>
                Track vendor GSTR-1 amendment filings and re-run reconciliation to verify that blocked ITC drops to ₹0.00 with proof.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS (4-STEP LIFECYCLE) ─── */}
      <section id="how-it-works" style={{ padding: '80px 32px', background: '#ffffff', borderTop: '1px solid #e5eae7', scrollMarginTop: 80 }}>
        <div style={{ maxWidth: 1160, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 50 }}>
            <div style={{ fontSize: 12.5, fontWeight: 800, color: '#059669', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Autonomous 4-Step Lifecycle
            </div>
            <h2 style={{ fontSize: 34, fontWeight: 900, color: '#0a1e19', marginTop: 6, letterSpacing: '-0.02em' }}>
              How CrediFlow Eliminates Mismatches
            </h2>
            <p style={{ fontSize: 15, color: '#475569', marginTop: 8, maxWidth: 640, margin: '8px auto 0' }}>
              From file ingestion to statutory supplier resolution in four seamless steps.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 24, position: 'relative' }}>
            {/* Step 1 */}
            <div style={{
              background: '#f8fafc',
              border: '1px solid #e5eae7',
              borderRadius: 18,
              padding: '28px 24px',
              position: 'relative'
            }}>
              <div style={{
                position: 'absolute', top: -14, left: 24,
                background: '#059669', color: '#ffffff',
                fontSize: 12, fontWeight: 800, padding: '4px 12px',
                borderRadius: 999, boxShadow: '0 2px 6px rgba(5,150,105,0.3)'
              }}>
                STEP 01
              </div>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: '#ecfdf5', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#059669', margin: '8px 0 16px' }}>
                <Upload size={22} />
              </div>
              <h3 style={{ fontSize: 17, fontWeight: 800, color: '#0a1e19', marginBottom: 8 }}>
                Ingest & Auto-Map
              </h3>
              <p style={{ fontSize: 13.5, color: '#475569', lineHeight: 1.6 }}>
                Upload Purchase Register and GSTR-2B files in CSV, Excel, or JSON. CrediFlow automatically normalizes schemas across Tally, Zoho, and GSTN.
              </p>
            </div>

            {/* Step 2 */}
            <div style={{
              background: '#f8fafc',
              border: '1px solid #e5eae7',
              borderRadius: 18,
              padding: '28px 24px',
              position: 'relative'
            }}>
              <div style={{
                position: 'absolute', top: -14, left: 24,
                background: '#0b1a17', color: '#34d399',
                fontSize: 12, fontWeight: 800, padding: '4px 12px',
                borderRadius: 999, boxShadow: '0 2px 6px rgba(11,26,23,0.3)'
              }}>
                STEP 02
              </div>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: '#ecfdf5', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#059669', margin: '8px 0 16px' }}>
                <Cpu size={22} />
              </div>
              <h3 style={{ fontSize: 17, fontWeight: 800, color: '#0a1e19', marginBottom: 8 }}>
                Sub-50ms Audit Engine
              </h3>
              <p style={{ fontSize: 13.5, color: '#475569', lineHeight: 1.6 }}>
                Pure deterministic math matches invoice identifiers, validates ≤ ₹2 rounding tolerances, flags tax-head switches, and calculates blocked ITC exposure.
              </p>
            </div>

            {/* Step 3 */}
            <div style={{
              background: '#f8fafc',
              border: '1px solid #e5eae7',
              borderRadius: 18,
              padding: '28px 24px',
              position: 'relative'
            }}>
              <div style={{
                position: 'absolute', top: -14, left: 24,
                background: '#0f2e26', color: '#ffffff',
                fontSize: 12, fontWeight: 800, padding: '4px 12px',
                borderRadius: 999, boxShadow: '0 2px 6px rgba(15,46,38,0.3)'
              }}>
                STEP 03
              </div>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: '#ecfdf5', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#059669', margin: '8px 0 16px' }}>
                <ShieldAlert size={22} />
              </div>
              <h3 style={{ fontSize: 17, fontWeight: 800, color: '#0a1e19', marginBottom: 8 }}>
                Human Review Gate
              </h3>
              <p style={{ fontSize: 13.5, color: '#475569', lineHeight: 1.6 }}>
                High-exposure discrepancies (&gt; ₹50,000) are placed in the review queue. Finance Managers can customize statutory tone before sending notices.
              </p>
            </div>

            {/* Step 4 */}
            <div style={{
              background: '#f8fafc',
              border: '1px solid #e5eae7',
              borderRadius: 18,
              padding: '28px 24px',
              position: 'relative'
            }}>
              <div style={{
                position: 'absolute', top: -14, left: 24,
                background: '#059669', color: '#ffffff',
                fontSize: 12, fontWeight: 800, padding: '4px 12px',
                borderRadius: 999, boxShadow: '0 2px 6px rgba(5,150,105,0.3)'
              }}>
                STEP 04
              </div>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: '#ecfdf5', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#059669', margin: '8px 0 16px' }}>
                <Send size={22} />
              </div>
              <h3 style={{ fontSize: 17, fontWeight: 800, color: '#0a1e19', marginBottom: 8 }}>
                Nudge & Closed-Loop Fix
              </h3>
              <p style={{ fontSize: 13.5, color: '#475569', lineHeight: 1.6 }}>
                Dispatches bilingual WhatsApp nudges with Table 9A filing instructions. When the vendor amends GSTR-1, the engine re-reconciles to ₹0 risk.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── COMPARISON MATRIX ─── */}
      <section id="comparison" style={{ padding: '80px 32px', background: '#f4f8f6', borderTop: '1px solid #e5eae7', scrollMarginTop: 80 }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 44 }}>
            <h2 style={{ fontSize: 32, fontWeight: 900, color: '#0a1e19', letterSpacing: '-0.02em' }}>
              Why Indian MSMEs Switch to CrediFlow
            </h2>
            <p style={{ fontSize: 15, color: '#475569', marginTop: 6 }}>Manual Excel reconciliation wastes 40+ hours every month and misses critical ITC deadlines.</p>
          </div>

          <div style={{ background: '#ffffff', border: '1px solid #e5eae7', borderRadius: 16, overflow: 'hidden', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.03)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13.5 }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e5eae7', color: '#0a1e19', fontSize: 12.5, fontWeight: 700, textTransform: 'uppercase' }}>
                  <th style={{ padding: '16px 20px', textAlign: 'left' }}>Capability</th>
                  <th style={{ padding: '16px 20px', textAlign: 'center', color: '#64748b' }}>Manual Excel Spreadsheets</th>
                  <th style={{ padding: '16px 20px', textAlign: 'center', background: '#ecfdf5', color: '#059669' }}>CrediFlow Engine</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { feature: 'Reconciliation Speed', manual: '3 - 5 days per filing cycle', credi: '< 100 milliseconds' },
                  { feature: 'Statutory Rule 60 Logic', manual: 'Manual VLOOKUP formulas', credi: '100% Deterministic Engine' },
                  { feature: 'Section 16(2)(aa) Check', manual: 'Prone to human omission', credi: 'Automated exact matching' },
                  { feature: 'Supplier Notice Dispatch', manual: 'Manual email drafting', credi: 'Bilingual WhatsApp & PDF Nudges' },
                  { feature: 'Vendor Compliance Health', manual: 'None (Untracked)', credi: 'Automated VCS Risk Scorecards' },
                  { feature: 'Immutable Audit Trail', manual: 'Easily overwritten files', credi: 'Cryptographic SQLite/Postgres Logs' }
                ].map((row, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #e5eae7' }}>
                    <td style={{ padding: '15px 20px', fontWeight: 600, color: '#0f172a' }}>{row.feature}</td>
                    <td style={{ padding: '15px 20px', textAlign: 'center', color: '#64748b' }}>{row.manual}</td>
                    <td style={{ padding: '15px 20px', textAlign: 'center', fontWeight: 700, color: '#059669', background: '#f0fdf4' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                        <Check size={16} color="#059669" />
                        {row.credi}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ─── FAQ SECTION ─── */}
      <section id="faq" style={{ padding: '70px 32px 90px', background: '#ffffff', borderTop: '1px solid #e5eae7', scrollMarginTop: 80 }}>
        <div style={{ maxWidth: 860, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 40 }}>
            <h2 style={{ fontSize: 30, fontWeight: 900, color: '#0a1e19' }}>Frequently Asked Questions</h2>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {[
              {
                q: 'How does CrediFlow guarantee 100% mathematical accuracy?',
                a: 'CrediFlow uses a deterministic statutory engine written in pure Python/FastAPI. It calculates tax amounts, GSTIN checksums, Rule 86B ratios, and Section 16(2)(aa) matches with pure arithmetic — never relying on AI approximations for numbers.'
              },
              {
                q: 'What formats can I upload for Purchase Register and GSTR-2B?',
                a: 'You can upload CSV, XLSX, XLS, and JSON files. The smart column mapper automatically recognizes Tally, Zoho Books, Busy, SAP, and official GST portal exports.'
              },
              {
                q: 'How does the WhatsApp notice dispatch work?',
                a: 'Once a discrepancy is flagged, CrediFlow prepares a formal statutory notice in English and Hindi. Upon Finance Manager approval, you can dispatch it directly via WhatsApp Business API or one-click wa.me deep links.'
              },
              {
                q: 'Is my financial data secure?',
                a: 'Yes. CrediFlow uses Supabase PostgreSQL with Row-Level Security (RLS). Every user’s financial records are isolated, encrypted in transit (TLS 1.3), and never shared.'
              }
            ].map((faq, i) => (
              <div key={i} style={{ background: '#ffffff', border: '1px solid #e5eae7', borderRadius: 12, padding: '20px 24px' }}>
                <div style={{ fontSize: 15, fontWeight: 700, color: '#0f172a', display: 'flex', alignItems: 'center', gap: 10 }}>
                  <HelpCircle size={17} color="#059669" />
                  {faq.q}
                </div>
                <div style={{ fontSize: 13.5, color: '#475569', marginTop: 8, lineHeight: 1.6, paddingLeft: 27 }}>
                  {faq.a}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── PUBLIC FOOTER ─── */}
      <footer style={{
        background: '#0b1a17', color: '#8fa8a1', padding: '36px 32px 28px',
        borderTop: '1px solid #162c26', textAlign: 'center', fontSize: 13
      }}>
        <div style={{ maxWidth: 1000, margin: '0 auto', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
          <div style={{ fontSize: 13.5, color: '#cbd5e1', fontWeight: 500 }}>
            Made in India 🇮🇳 · Designed for MSME Growth & Statutory Compliance
          </div>
          <div style={{ fontSize: 11.5, color: '#66827a', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 12, width: '100%' }}>
            © 2026 CrediFlow. Compliant with CBIC GST Rules & Section 16 of CGST Act.
          </div>
        </div>
      </footer>

      {/* ─── BRANDED SUPABASE AUTH MODAL ─── */}
      {authModalOpen && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(11, 26, 23, 0.75)', zIndex: 100,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          backdropFilter: 'blur(8px)', padding: 24
        }}>
          <div style={{
            background: '#ffffff',
            borderRadius: 24,
            width: '100%',
            maxWidth: 520,
            boxShadow: '0 25px 60px -12px rgba(11,26,23,0.35), 0 0 0 1px rgba(229,234,231,0.8)',
            border: '1px solid #e5eae7',
            overflow: 'hidden'
          }}>
            {/* Modal Header */}
            <div style={{
              background: '#0b1a17', padding: '30px 36px', color: '#ffffff',
              display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start'
            }}>
              <div>
                <div style={{ fontSize: 12.5, fontWeight: 800, color: '#34d399', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                  CrediFlow Cloud Portal
                </div>
                <div className="font-display" style={{ fontSize: 24, fontWeight: 800, marginTop: 6, letterSpacing: '-0.02em' }}>
                  {authMode === 'login' ? 'Welcome Back' : 'Create MSME Account'}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setAuthModalOpen(false)}
                style={{
                  background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 10,
                  width: 36, height: 36, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  cursor: 'pointer', color: '#ffffff', transition: 'background 0.15s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.2)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '32px 36px 30px' }}>
              {/* Google OAuth Button */}
              <button
                type="button"
                onClick={handleGoogleSignIn}
                disabled={authLoading}
                style={{
                  width: '100%',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
                  background: '#ffffff', border: '1.5px solid #cbd5e1', borderRadius: 12,
                  padding: '13.5px 16px', fontSize: 15, fontWeight: 700, color: '#0f172a',
                  cursor: 'pointer', boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = '#f8fafc'; e.currentTarget.style.borderColor = '#94a3b8'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = '#ffffff'; e.currentTarget.style.borderColor = '#cbd5e1'; }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                </svg>
                Continue with Google
              </button>

              <div style={{ display: 'flex', alignItems: 'center', gap: 14, margin: '22px 0 20px' }}>
                <div style={{ flex: 1, height: 1.5, background: '#cbd5e1' }} />
                <span style={{ fontSize: 12, color: '#334155', fontWeight: 800, letterSpacing: '0.08em' }}>OR EMAIL</span>
                <div style={{ flex: 1, height: 1.5, background: '#cbd5e1' }} />
              </div>

              {/* Feedback messages */}
              {authError && (
                <div style={{ background: '#fef2f2', border: '1.5px solid #fecaca', color: '#991b1b', padding: '12px 16px', borderRadius: 10, fontSize: 13, fontWeight: 600, marginBottom: 18 }}>
                  <div>{authError}</div>
                  <div style={{ marginTop: 8, display: 'flex', gap: 10, alignItems: 'center' }}>
                    <button
                      type="button"
                      onClick={handleResendConfirmation}
                      style={{ background: 'none', border: 'none', color: '#047857', fontWeight: 800, fontSize: 12.5, cursor: 'pointer', padding: 0, textDecoration: 'underline' }}
                    >
                      Resend Confirmation Email
                    </button>
                    <span style={{ color: '#94a3b8' }}>•</span>
                    <button
                      type="button"
                      onClick={() => { setAuthModalOpen(false); if (onEnterApp) onEnterApp(); }}
                      style={{ background: 'none', border: 'none', color: '#1d4ed8', fontWeight: 800, fontSize: 12.5, cursor: 'pointer', padding: 0, textDecoration: 'underline' }}
                    >
                      Enter Directly (Demo Mode)
                    </button>
                  </div>
                </div>
              )}
              {authSuccess && (
                <div style={{ background: '#f0fdf4', border: '1.5px solid #bbf7d0', color: '#15803d', padding: '12px 16px', borderRadius: 10, fontSize: 13, fontWeight: 600, marginBottom: 18 }}>
                  <div>{authSuccess}</div>
                  <div style={{ marginTop: 8 }}>
                    <button
                      type="button"
                      onClick={() => { setAuthModalOpen(false); if (onEnterApp) onEnterApp(); }}
                      style={{ background: 'none', border: 'none', color: '#047857', fontWeight: 800, fontSize: 12.5, cursor: 'pointer', padding: 0, textDecoration: 'underline' }}
                    >
                      Skip to Workspace Now →
                    </button>
                  </div>
                </div>
              )}

              {/* Email/Password Form */}
              <form onSubmit={handleEmailAuth} style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 14, fontWeight: 700, color: '#0f172a', marginBottom: 7 }}>
                    Business Email
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="finance@yourcompany.com"
                    style={{
                      width: '100%', padding: '13px 16px', borderRadius: 10,
                      border: '1.5px solid #94a3b8', fontSize: 14.5, fontWeight: 600, color: '#0f172a',
                      outline: 'none', boxSizing: 'border-box', transition: 'all 0.15s ease'
                    }}
                    onFocus={(e) => { e.currentTarget.style.borderColor = '#059669'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(5,150,105,0.15)'; }}
                    onBlur={(e) => { e.currentTarget.style.borderColor = '#94a3b8'; e.currentTarget.style.boxShadow = 'none'; }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 14, fontWeight: 700, color: '#0f172a', marginBottom: 7 }}>
                    Password
                  </label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    style={{
                      width: '100%', padding: '13px 16px', borderRadius: 10,
                      border: '1.5px solid #94a3b8', fontSize: 14.5, fontWeight: 600, color: '#0f172a',
                      outline: 'none', boxSizing: 'border-box', transition: 'all 0.15s ease'
                    }}
                    onFocus={(e) => { e.currentTarget.style.borderColor = '#059669'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(5,150,105,0.15)'; }}
                    onBlur={(e) => { e.currentTarget.style.borderColor = '#94a3b8'; e.currentTarget.style.boxShadow = 'none'; }}
                  />
                </div>

                <button
                  type="submit"
                  disabled={authLoading}
                  style={{
                    width: '100%', background: '#059669', color: '#ffffff',
                    border: 'none', padding: '14.5px', borderRadius: 12,
                    fontSize: 15.5, fontWeight: 800, cursor: 'pointer',
                    marginTop: 6, boxShadow: '0 4px 14px rgba(5,150,105,0.35)',
                    letterSpacing: '0.01em', transition: 'all 0.15s ease'
                  }}
                >
                  {authLoading ? 'Processing...' : (authMode === 'login' ? 'Sign In' : 'Create Account')}
                </button>
              </form>

              {/* Mode Toggle */}
              <div style={{ textAlign: 'center', marginTop: 24, fontSize: 14, color: '#1e293b', fontWeight: 600 }}>
                {authMode === 'login' ? (
                  <span>Don't have an account? <strong onClick={() => { setAuthMode('signup'); setAuthError(null); setAuthSuccess(null); }} style={{ color: '#059669', fontWeight: 800, cursor: 'pointer', marginLeft: 4 }}>Sign up free</strong></span>
                ) : (
                  <span>Already have an account? <strong onClick={() => { setAuthMode('login'); setAuthError(null); setAuthSuccess(null); }} style={{ color: '#059669', fontWeight: 800, cursor: 'pointer', marginLeft: 4 }}>Sign in</strong></span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
