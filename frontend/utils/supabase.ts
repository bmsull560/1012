// Supabase Client Configuration
import { createClient } from '@supabase/supabase-js';

// Database types
export interface ValueModel {
  id: string;
  user_id: string;
  company_name: string;
  industry: string;
  stage: string;
  inputs: Record<string, number>;
  results: {
    totalBenefits: number;
    totalCosts: number;
    netBenefit: number;
    npv: number;
    payback: number;
    roi: number;
  };
  created_at: string;
  updated_at: string;
}

export interface SharedLink {
  id: string;
  model_id: string;
  short_code: string;
  expires_at: string;
  views: number;
  created_at: string;
}

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';

// For development, we'll use mock values if not configured
const isDevelopment = process.env.NODE_ENV === 'development';

// In production, throw error if Supabase is not configured
if (!isDevelopment && (!supabaseUrl || !supabaseAnonKey)) {
  throw new Error('Supabase configuration is required in production. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables.');
}

export const supabase = supabaseUrl && supabaseAnonKey 
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

// Helper functions for database operations
export const db = {
  // Save a value model
  async saveModel(model: Partial<ValueModel>): Promise<ValueModel | null> {
    if (!supabase) {
      // Fallback to localStorage in development
      if (isDevelopment) {
        const models = JSON.parse(localStorage.getItem('value_models') || '[]');
        const newModel = {
          ...model,
          id: model.id || crypto.randomUUID(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        } as ValueModel;
        models.push(newModel);
        localStorage.setItem('value_models', JSON.stringify(models));
        return newModel;
      }
      return null;
    }

    const { data, error } = await supabase
      .from('value_models')
      .upsert(model)
      .select()
      .single();

    if (error) {
      console.error('Error saving model:', error);
      return null;
    }

    return data;
  },

  // Load user's models
  async loadModels(userId: string): Promise<ValueModel[]> {
    if (!supabase) {
      if (isDevelopment) {
        const models = JSON.parse(localStorage.getItem('value_models') || '[]');
        return models.filter((m: ValueModel) => m.user_id === userId);
      }
      return [];
    }

    const { data, error } = await supabase
      .from('value_models')
      .select('*')
      .eq('user_id', userId)
      .order('updated_at', { ascending: false });

    if (error) {
      console.error('Error loading models:', error);
      return [];
    }

    return data || [];
  },

  // Load a specific model
  async loadModel(modelId: string): Promise<ValueModel | null> {
    if (!supabase) {
      if (isDevelopment) {
        const models = JSON.parse(localStorage.getItem('value_models') || '[]');
        return models.find((m: ValueModel) => m.id === modelId) || null;
      }
      return null;
    }

    const { data, error } = await supabase
      .from('value_models')
      .select('*')
      .eq('id', modelId)
      .single();

    if (error) {
      console.error('Error loading model:', error);
      return null;
    }

    return data;
  },

  // Create a shareable link
  async createShareLink(modelId: string, expiresInDays = 30): Promise<string | null> {
    const shortCode = Math.random().toString(36).substring(2, 8);
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + expiresInDays);

    if (!supabase) {
      if (isDevelopment) {
        const links = JSON.parse(localStorage.getItem('shared_links') || '[]');
        links.push({
          id: crypto.randomUUID(),
          model_id: modelId,
          short_code: shortCode,
          expires_at: expiresAt.toISOString(),
          views: 0,
          created_at: new Date().toISOString()
        });
        localStorage.setItem('shared_links', JSON.stringify(links));
        return `${window.location.origin}/share/${shortCode}`;
      }
      return null;
    }

    const { data, error } = await supabase
      .from('shared_links')
      .insert({
        model_id: modelId,
        short_code: shortCode,
        expires_at: expiresAt.toISOString()
      })
      .select()
      .single();

    if (error) {
      console.error('Error creating share link:', error);
      return null;
    }

    return `${window.location.origin}/share/${shortCode}`;
  },

  // Load model from share link
  async loadSharedModel(shortCode: string): Promise<ValueModel | null> {
    if (!supabase) {
      if (isDevelopment) {
        const links = JSON.parse(localStorage.getItem('shared_links') || '[]');
        const link = links.find((l: SharedLink) => l.short_code === shortCode);
        if (!link) return null;
        
        const models = JSON.parse(localStorage.getItem('value_models') || '[]');
        return models.find((m: ValueModel) => m.id === link.model_id) || null;
      }
      return null;
    }

    // First get the link
    const { data: linkData, error: linkError } = await supabase
      .from('shared_links')
      .select('*')
      .eq('short_code', shortCode)
      .single();

    if (linkError || !linkData) {
      console.error('Error loading shared link:', linkError);
      return null;
    }

    // Check if expired
    if (new Date(linkData.expires_at) < new Date()) {
      console.error('Share link has expired');
      return null;
    }

    // Increment view count
    await supabase
      .from('shared_links')
      .update({ views: linkData.views + 1 })
      .eq('id', linkData.id);

    // Load the model
    return this.loadModel(linkData.model_id);
  }
};

// Auth helper functions
export const auth = {
  async signUp(email: string, password: string) {
    if (!supabase) {
      if (isDevelopment) {
        // Mock auth for development
        const user = { id: crypto.randomUUID(), email };
        localStorage.setItem('current_user', JSON.stringify(user));
        return { user, error: null };
      }
      return { user: null, error: 'Supabase not configured' };
    }

    return await supabase.auth.signUp({ email, password });
  },

  async signIn(email: string, password: string) {
    if (!supabase) {
      if (isDevelopment) {
        // Mock auth for development
        const user = { id: crypto.randomUUID(), email };
        localStorage.setItem('current_user', JSON.stringify(user));
        return { user, error: null };
      }
      return { user: null, error: 'Supabase not configured' };
    }

    return await supabase.auth.signInWithPassword({ email, password });
  },

  async signOut() {
    if (!supabase) {
      if (isDevelopment) {
        localStorage.removeItem('current_user');
        return { error: null };
      }
      return { error: 'Supabase not configured' };
    }

    return await supabase.auth.signOut();
  },

  async getUser() {
    if (!supabase) {
      if (isDevelopment) {
        const user = localStorage.getItem('current_user');
        return user ? JSON.parse(user) : null;
      }
      return null;
    }

    const { data: { user } } = await supabase.auth.getUser();
    return user;
  }
};
