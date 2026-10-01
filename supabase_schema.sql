-- ==============================================================================
-- CrediFlow Multi-Tenant Cloud Database Schema (Supabase PostgreSQL)
-- Multi-Tenant Isolation via Row Level Security (RLS) & Auth Integration
-- Statutory GST Reconciliation Engine (Rule 60 CGST & Section 16(2)(aa))
-- ==============================================================================

-- 1. Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- Table 1: user_profiles
-- Stores multi-tenant company details, GSTIN, and profile settings for each user
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    company_name TEXT DEFAULT 'CrediFlow Enterprise Ltd',
    buyer_gstin TEXT DEFAULT '27AAACB0987A1Z1',
    phone_number TEXT,
    compliance_threshold NUMERIC(10, 2) DEFAULT 2.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- Table 2: audit_sessions
-- Represents individual reconciliation audit runs per user/tenant
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.audit_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    audit_ref TEXT NOT NULL,
    status TEXT DEFAULT 'COMPLETED', -- 'IN_PROGRESS', 'COMPLETED', 'FAILED'
    total_invoices INT DEFAULT 0,
    matched_invoices INT DEFAULT 0,
    discrepancy_count INT DEFAULT 0,
    exposure_risk_rupees NUMERIC(15, 2) DEFAULT 0.00,
    exposure_recovered_rupees NUMERIC(15, 2) DEFAULT 0.00,
    pending_human_gate INT DEFAULT 0,
    execution_time_ms INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- Table 3: invoices
-- Line-item invoice records from Purchase Register & GSTR-2B
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    audit_session_id UUID REFERENCES public.audit_sessions(id) ON DELETE CASCADE,
    invoice_number TEXT NOT NULL,
    supplier_name TEXT NOT NULL,
    supplier_gstin TEXT NOT NULL,
    invoice_date DATE,
    taxable_amount_rupees NUMERIC(15, 2) DEFAULT 0.00,
    cgst_rupees NUMERIC(15, 2) DEFAULT 0.00,
    sgst_rupees NUMERIC(15, 2) DEFAULT 0.00,
    igst_rupees NUMERIC(15, 2) DEFAULT 0.00,
    total_amount_rupees NUMERIC(15, 2) DEFAULT 0.00,
    itc_amount_rupees NUMERIC(15, 2) DEFAULT 0.00,
    source_type TEXT NOT NULL, -- 'PURCHASE_REGISTER' or 'GSTR_2B'
    match_status TEXT DEFAULT 'UNMATCHED', -- 'MATCHED', 'DISCREPANT', 'PENDING'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- Table 4: discrepancies
-- Identified mismatches with statutory root cause classifications
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.discrepancies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    audit_session_id UUID REFERENCES public.audit_sessions(id) ON DELETE CASCADE,
    invoice_number TEXT NOT NULL,
    supplier_name TEXT NOT NULL,
    supplier_gstin TEXT NOT NULL,
    mismatch_type TEXT NOT NULL, -- 'MISSING_IN_2B', 'AMOUNT_MISMATCH', 'TAX_HEAD_MISMATCH', 'GSTIN_INCORRECT'
    itc_exposure_rupees NUMERIC(15, 2) DEFAULT 0.00,
    root_cause_classification TEXT, -- 'TIMING_DIFFERENCE', 'SUPPLIER_DEFAULT_UNFILED', 'RATE_ERROR', etc.
    statutory_rule TEXT DEFAULT 'Rule 60 CGST & Section 16(2)(aa)',
    details TEXT,
    status TEXT DEFAULT 'FLAGGED', -- 'FLAGGED', 'HUMAN_APPROVED', 'RESOLVED', 'DISMISSED'
    suggested_action TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- Table 5: human_decisions
-- Audit log of human operator approvals, overrides, and notes
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.human_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    audit_session_id UUID REFERENCES public.audit_sessions(id) ON DELETE CASCADE,
    discrepancy_id UUID REFERENCES public.discrepancies(id) ON DELETE SET NULL,
    invoice_number TEXT NOT NULL,
    action TEXT NOT NULL, -- 'APPROVE', 'EDIT', 'DISMISS'
    statutory_note TEXT,
    operator_name TEXT DEFAULT 'Finance Operator',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- Table 6: vendor_scorecards
-- Vendor compliance scorecards aggregated per user tenant
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.vendor_scorecards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    supplier_name TEXT NOT NULL,
    supplier_gstin TEXT NOT NULL,
    phone_number TEXT,
    total_invoices INT DEFAULT 0,
    matched_invoices INT DEFAULT 0,
    mismatch_count INT DEFAULT 0,
    compliance_score NUMERIC(5, 2) DEFAULT 100.00,
    risk_level TEXT DEFAULT 'LOW', -- 'LOW', 'MEDIUM', 'HIGH'
    last_audit_date TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_vendor_per_user UNIQUE(user_id, supplier_gstin)
);

-- ==============================================================================
-- Table 7: notice_dispatches
-- Records of WhatsApp and PDF notices dispatched to vendors
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.notice_dispatches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    invoice_number TEXT NOT NULL,
    supplier_gstin TEXT NOT NULL,
    recipient_phone TEXT NOT NULL,
    channel TEXT DEFAULT 'WHATSAPP', -- 'WHATSAPP', 'EMAIL', 'PDF_DOWNLOAD'
    status TEXT DEFAULT 'SENT', -- 'QUEUED', 'SENT', 'DELIVERED', 'READ', 'FAILED'
    message_language TEXT DEFAULT 'EN', -- 'EN', 'HI'
    statutory_reference TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==============================================================================
-- Performance Indexes (Tenant-isolated queries)
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_audit_sessions_user ON public.audit_sessions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_invoices_user ON public.invoices(user_id, audit_session_id);
CREATE INDEX IF NOT EXISTS idx_invoices_number ON public.invoices(user_id, invoice_number);
CREATE INDEX IF NOT EXISTS idx_discrepancies_user ON public.discrepancies(user_id, status);
CREATE INDEX IF NOT EXISTS idx_human_decisions_user ON public.human_decisions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vendor_scorecards_user ON public.vendor_scorecards(user_id, supplier_gstin);
CREATE INDEX IF NOT EXISTS idx_notice_dispatches_user ON public.notice_dispatches(user_id, created_at DESC);

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Strict multi-tenant data isolation: Each user only accesses their own rows
-- ==============================================================================

-- Enable RLS on all tables
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.discrepancies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.human_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vendor_scorecards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notice_dispatches ENABLE ROW LEVEL SECURITY;

-- 1. user_profiles Policies
CREATE POLICY "Users can view own profile"
    ON public.user_profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON public.user_profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.user_profiles FOR UPDATE
    USING (auth.uid() = id);

-- 2. audit_sessions Policies
CREATE POLICY "Users can manage own audit_sessions"
    ON public.audit_sessions FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 3. invoices Policies
CREATE POLICY "Users can manage own invoices"
    ON public.invoices FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 4. discrepancies Policies
CREATE POLICY "Users can manage own discrepancies"
    ON public.discrepancies FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 5. human_decisions Policies
CREATE POLICY "Users can manage own human_decisions"
    ON public.human_decisions FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 6. vendor_scorecards Policies
CREATE POLICY "Users can manage own vendor_scorecards"
    ON public.vendor_scorecards FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- 7. notice_dispatches Policies
CREATE POLICY "Users can manage own notice_dispatches"
    ON public.notice_dispatches FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- ==============================================================================
-- Automatic User Profile Creation Trigger on Sign Up
-- ==============================================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', SPLIT_PART(NEW.email, '@', 1))
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop trigger if already exists and recreate
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
