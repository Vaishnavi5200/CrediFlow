import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || 'https://qedfngoyeagcdrjylgsv.supabase.co';
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFlZGZuZ295ZWFnY2RyanlsZ3N2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA3OTA2NTMsImV4cCI6MjEwNjM2NjY1M30.9lNYrpVVRlzcnCRH3hzyzvpSuwwmF-Lt-DxKhcqlSRI';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

