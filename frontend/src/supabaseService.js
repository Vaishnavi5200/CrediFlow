import { supabase } from './supabase';

/**
 * Fetch or create profile for authenticated user
 */
export async function fetchUserProfile(userId, email, fullName) {
  try {
    const { data, error } = await supabase
      .from('user_profiles')
      .select('*')
      .eq('id', userId)
      .maybeSingle();

    if (error) {
      console.warn('Error fetching user profile:', error.message);
      return null;
    }

    if (!data) {
      // Create default profile if not exists
      const { data: newProfile, error: insertErr } = await supabase
        .from('user_profiles')
        .insert({
          id: userId,
          email: email || '',
          full_name: fullName || email?.split('@')[0] || 'Finance Operator',
          company_name: 'CrediFlow Enterprise Ltd',
          buyer_gstin: '27AAACB0987A1Z1'
        })
        .select()
        .single();

      if (insertErr) {
        console.warn('Error creating profile:', insertErr.message);
        return null;
      }
      return newProfile;
    }

    return data;
  } catch (err) {
    console.warn('fetchUserProfile exception:', err);
    return null;
  }
}export async function updateUserProfile(userId, updates) {
  try {
    if (!userId) return null;
    const { data, error } = await supabase
      .from('user_profiles')
      .update({
        ...updates,
        updated_at: new Date().toISOString()
      })
      .eq('id', userId)
      .select()
      .single();

    if (error) {
      console.warn('Error updating user profile:', error.message);
      return null;
    }
    return data;
  } catch (err) {
    console.warn('updateUserProfile exception:', err);
    return null;
  }
}

/**
 * Fetch all audits for current user
 */
export async function fetchUserAudits(userId) {
  try {
    const { data, error } = await supabase
      .from('audit_sessions')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false });

    if (error) {
      console.warn('Error fetching user audits:', error.message);
      return [];
    }
    return data || [];
  } catch (err) {
    console.warn('fetchUserAudits exception:', err);
    return [];
  }
}

/**
 * Fetch discrepancies for current user
 */
export async function fetchUserDiscrepancies(userId) {
  try {
    const { data, error } = await supabase
      .from('discrepancies')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false });

    if (error) {
      console.warn('Error fetching user discrepancies:', error.message);
      return [];
    }
    return data || [];
  } catch (err) {
    console.warn('fetchUserDiscrepancies exception:', err);
    return [];
  }
}

/**
 * Fetch vendor scorecards for current user
 */
export async function fetchUserVendorScorecards(userId) {
  try {
    const { data, error } = await supabase
      .from('vendor_scorecards')
      .select('*')
      .eq('user_id', userId)
      .order('compliance_score', { ascending: true });

    if (error) {
      console.warn('Error fetching vendor scorecards:', error.message);
      return [];
    }
    return data || [];
  } catch (err) {
    console.warn('fetchUserVendorScorecards exception:', err);
    return [];
  }
}

/**
 * Save an audit session with invoices and discrepancies to Supabase
 */
export async function saveAuditToSupabase(userId, auditPayload) {
  try {
    if (!userId) return null;

    // 1. Insert audit session
    const { data: auditSession, error: auditErr } = await supabase
      .from('audit_sessions')
      .insert({
        user_id: userId,
        audit_ref: auditPayload.audit_id || `AUDIT-${Date.now()}`,
        status: 'COMPLETED',
        total_invoices: auditPayload.total_invoices || auditPayload.stats?.totalInvoices || 0,
        matched_invoices: auditPayload.matched || auditPayload.stats?.matched || 0,
        discrepancy_count: auditPayload.discrepancies?.length || auditPayload.stats?.discrepancies || 0,
        exposure_risk_rupees: auditPayload.exposure_risk_rupees || auditPayload.stats?.exposureRisk || 0,
        exposure_recovered_rupees: auditPayload.exposure_recovered_rupees || auditPayload.stats?.exposureRecovered || 0,
        pending_human_gate: auditPayload.pending_human_gate || auditPayload.stats?.pendingHumanGate || 0
      })
      .select()
      .single();

    if (auditErr) {
      console.warn('Error saving audit session:', auditErr.message);
      return null;
    }

    const sessionId = auditSession.id;

    // 2. Insert Discrepancies if any
    if (auditPayload.discrepancies && auditPayload.discrepancies.length > 0) {
      const discRows = auditPayload.discrepancies.map(d => ({
        user_id: userId,
        audit_session_id: sessionId,
        invoice_number: d.invoice_number,
        supplier_name: d.supplier_name || 'Vendor',
        supplier_gstin: d.supplier_gstin || '27XXXXX0000X1Z1',
        mismatch_type: d.mismatch_type || 'AMOUNT_MISMATCH',
        itc_exposure_rupees: d.itc_exposure_rupees || 0,
        root_cause_classification: d.root_cause_classification || 'UNKNOWN',
        statutory_rule: d.statutory_rule || 'Rule 60 CGST & Section 16(2)(aa)',
        details: d.details || d.reason || '',
        status: 'FLAGGED'
      }));

      await supabase.from('discrepancies').insert(discRows);
    }

    // 3. Upsert Vendor Scorecards
    if (auditPayload.scorecards && auditPayload.scorecards.length > 0) {
      const scorecardRows = auditPayload.scorecards.map(s => ({
        user_id: userId,
        supplier_name: s.supplier_name || s.vendor_name,
        supplier_gstin: s.supplier_gstin || s.gstin,
        phone_number: s.phone_number || s.phone || '+91 98765 43210',
        total_invoices: s.total_invoices || 0,
        matched_invoices: s.matched_invoices || 0,
        mismatch_count: s.mismatch_count || s.mismatches || 0,
        compliance_score: s.compliance_score || 100,
        risk_level: s.compliance_score >= 80 ? 'LOW' : s.compliance_score >= 60 ? 'MEDIUM' : 'HIGH'
      }));

      await supabase.from('vendor_scorecards').upsert(scorecardRows, {
        onConflict: 'user_id,supplier_gstin'
      });
    }

    return auditSession;
  } catch (err) {
    console.warn('saveAuditToSupabase exception:', err);
    return null;
  }
}

/**
 * Record human decision and update discrepancy status
 */
export async function saveHumanDecisionToSupabase(userId, decision) {
  try {
    if (!userId) return;

    // 1. Insert decision log
    await supabase.from('human_decisions').insert({
      user_id: userId,
      invoice_number: decision.invoice_number,
      action: decision.action,
      statutory_note: decision.statutory_note || decision.reason || '',
      operator_name: decision.operator_name || 'Vaishnavi Dwivedi'
    });

    // 2. Update discrepancy status if found
    const newStatus = decision.action === 'APPROVE' ? 'HUMAN_APPROVED' : decision.action === 'DISMISS' ? 'DISMISSED' : 'RESOLVED';
    await supabase
      .from('discrepancies')
      .update({ status: newStatus })
      .eq('user_id', userId)
      .eq('invoice_number', decision.invoice_number);
  } catch (err) {
    console.warn('saveHumanDecisionToSupabase exception:', err);
  }
}

/**
 * Record notice dispatch (WhatsApp or PDF)
 */
export async function saveNoticeDispatchToSupabase(userId, dispatch) {
  try {
    if (!userId) return;

    await supabase.from('notice_dispatches').insert({
      user_id: userId,
      invoice_number: dispatch.invoice_number,
      supplier_gstin: dispatch.supplier_gstin || '27XXXXX0000X1Z1',
      recipient_phone: dispatch.phone || '+91 98765 43210',
      channel: dispatch.channel || 'WHATSAPP',
      status: 'SENT',
      message_language: dispatch.language || 'EN',
      statutory_reference: 'Rule 60 CGST'
    });
  } catch (err) {
    console.warn('saveNoticeDispatchToSupabase exception:', err);
  }
}
