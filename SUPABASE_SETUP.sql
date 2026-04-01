-- Xenitide Platform - Supabase Database Setup
-- Execute this script in Supabase SQL Editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Users Table (Extended from Supabase Auth)
-- Note: Supabase already creates auth.users, we extend it
CREATE TABLE IF NOT EXISTS public.users (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  username TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Projects Table
CREATE TABLE IF NOT EXISTS public.projects (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  owner_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Project Members (Collaboration)
CREATE TABLE IF NOT EXISTS public.project_members (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
  user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
  role TEXT CHECK (role IN ('owner','editor','viewer')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(project_id, user_id)
);

-- 4. Repository System (Mini GitHub)

-- 4.1 Repositories
CREATE TABLE IF NOT EXISTS public.repositories (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4.2 Files
CREATE TABLE IF NOT EXISTS public.files (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  repository_id UUID REFERENCES public.repositories(id) ON DELETE CASCADE,
  path TEXT NOT NULL, -- /src/index.js
  content TEXT,
  file_size INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(repository_id, path)
);

-- 4.3 Commits
CREATE TABLE IF NOT EXISTS public.commits (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  repository_id UUID REFERENCES public.repositories(id) ON DELETE CASCADE,
  message TEXT,
  author_id UUID REFERENCES public.users(id),
  commit_hash TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4.4 Commit Files (Snapshot Mapping)
CREATE TABLE IF NOT EXISTS public.commit_files (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  commit_id UUID REFERENCES public.commits(id) ON DELETE CASCADE,
  file_id UUID REFERENCES public.files(id) ON DELETE CASCADE,
  content_snapshot TEXT,
  operation TEXT CHECK (operation IN ('add','modify','delete')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Deployment System (Mini Vercel)

-- 5.1 Deployments
CREATE TABLE IF NOT EXISTS public.deployments (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
  status TEXT CHECK (status IN ('pending','building','success','failed','cancelled')),
  url TEXT,
  branch TEXT DEFAULT 'main',
  commit_id UUID REFERENCES public.commits(id),
  build_start_time TIMESTAMP WITH TIME ZONE,
  build_end_time TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5.2 Build Logs
CREATE TABLE IF NOT EXISTS public.logs (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  deployment_id UUID REFERENCES public.deployments(id) ON DELETE CASCADE,
  level TEXT CHECK (level IN ('info','warn','error','debug')),
  message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Environment Variables
CREATE TABLE IF NOT EXISTS public.env_variables (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
  key TEXT NOT NULL,
  value TEXT,
  is_secret BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(project_id, key)
);

-- 7. Database Builder (Mini Supabase)

-- 7.1 Custom Tables
CREATE TABLE IF NOT EXISTS public.db_tables (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  schema JSONB NOT NULL, -- column definitions
  row_count INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(project_id, name)
);

-- 7.2 Table Rows (Flexible Data)
CREATE TABLE IF NOT EXISTS public.db_rows (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  table_id UUID REFERENCES public.db_tables(id) ON DELETE CASCADE,
  data JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. Storage System
CREATE TABLE IF NOT EXISTS public.storage_files (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
  file_name TEXT NOT NULL,
  file_url TEXT NOT NULL,
  file_type TEXT,
  file_size INTEGER,
  mime_type TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. Payments System (Mini Xendit)

-- 9.1 Payment Links
CREATE TABLE IF NOT EXISTS public.payment_links (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
  amount DECIMAL(10,2) NOT NULL,
  description TEXT,
  currency TEXT DEFAULT 'PHP',
  status TEXT CHECK (status IN ('active','expired','paused')),
  expires_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9.2 Transactions
CREATE TABLE IF NOT EXISTS public.transactions (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  payment_link_id UUID REFERENCES public.payment_links(id),
  transaction_id TEXT UNIQUE, -- External payment processor ID
  user_email TEXT,
  amount DECIMAL(10,2) NOT NULL,
  currency TEXT DEFAULT 'PHP',
  status TEXT CHECK (status IN ('pending','paid','failed','refunded')),
  payment_method TEXT,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. AI Actions
CREATE TABLE IF NOT EXISTS public.ai_actions (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
  user_id UUID REFERENCES public.users(id),
  action_type TEXT CHECK (action_type IN ('code_review','debug','explain','generate')),
  input TEXT,
  output TEXT,
  tokens_used INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 11. Audit Log (for security)
CREATE TABLE IF NOT EXISTS public.audit_logs (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES public.users(id),
  project_id UUID REFERENCES public.projects(id),
  action TEXT NOT NULL,
  table_name TEXT,
  record_id UUID,
  old_values JSONB,
  new_values JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create updated_at triggers
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER set_users_timestamp BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();
CREATE TRIGGER set_projects_timestamp BEFORE UPDATE ON public.projects FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();
CREATE TRIGGER set_repositories_timestamp BEFORE UPDATE ON public.repositories FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();
CREATE TRIGGER set_files_timestamp BEFORE UPDATE ON public.files FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();
CREATE TRIGGER set_env_variables_timestamp BEFORE UPDATE ON public.env_variables FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();
CREATE TRIGGER set_db_tables_timestamp BEFORE UPDATE ON public.db_tables FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();
CREATE TRIGGER set_db_rows_timestamp BEFORE UPDATE ON public.db_rows FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();
CREATE TRIGGER set_transactions_timestamp BEFORE UPDATE ON public.transactions FOR EACH ROW EXECUTE FUNCTION trigger_set_timestamp();

-- Create critical indexes
CREATE INDEX IF NOT EXISTS idx_projects_owner ON public.projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_project_members_project ON public.project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user ON public.project_members(user_id);
CREATE INDEX IF NOT EXISTS idx_repositories_project ON public.repositories(project_id);
CREATE INDEX IF NOT EXISTS idx_files_repo ON public.files(repository_id);
CREATE INDEX IF NOT EXISTS idx_files_path ON public.files(path);
CREATE INDEX IF NOT EXISTS idx_commits_repo ON public.commits(repository_id);
CREATE INDEX IF NOT EXISTS idx_commit_files_commit ON public.commit_files(commit_id);
CREATE INDEX IF NOT EXISTS idx_deployments_project ON public.deployments(project_id);
CREATE INDEX IF NOT EXISTS idx_logs_deployment ON public.logs(deployment_id);
CREATE INDEX IF NOT EXISTS idx_env_variables_project ON public.env_variables(project_id);
CREATE INDEX IF NOT EXISTS idx_db_tables_project ON public.db_tables(project_id);
CREATE INDEX IF NOT EXISTS idx_db_rows_table ON public.db_rows(table_id);
CREATE INDEX IF NOT EXISTS idx_storage_project ON public.storage_files(project_id);
CREATE INDEX IF NOT EXISTS idx_payment_links_project ON public.payment_links(project_id);
CREATE INDEX IF NOT EXISTS idx_transactions_payment_link ON public.transactions(payment_link_id);
CREATE INDEX IF NOT EXISTS idx_ai_actions_project ON public.ai_actions(project_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_project ON public.audit_logs(project_id);

-- Create GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_db_tables_schema_gin ON public.db_tables USING GIN(schema);
CREATE INDEX IF NOT EXISTS idx_db_rows_data_gin ON public.db_rows USING GIN(data);
CREATE INDEX IF NOT EXISTS idx_transactions_metadata_gin ON public.transactions USING GIN(metadata);

-- Row Level Security (RLS) Policies
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.repositories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.commits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.deployments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.env_variables ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.db_tables ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.db_rows ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.storage_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Users can only view their own profile
CREATE POLICY "Users can view own profile" ON public.users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
  FOR UPDATE USING (auth.uid() = id);

-- Projects policies
CREATE POLICY "Users can view own projects" ON public.projects
  FOR SELECT USING (
    owner_id = auth.uid() OR
    id IN (
      SELECT project_id FROM public.project_members WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create own projects" ON public.projects
  FOR INSERT WITH CHECK (owner_id = auth.uid());

CREATE POLICY "Project owners can update projects" ON public.projects
  FOR UPDATE USING (owner_id = auth.uid());

CREATE POLICY "Project owners can delete projects" ON public.projects
  FOR DELETE USING (owner_id = auth.uid());

-- Project members policies
CREATE POLICY "Users can view project memberships" ON public.project_members
  FOR SELECT USING (
    user_id = auth.uid() OR
    project_id IN (
      SELECT id FROM public.projects WHERE owner_id = auth.uid()
    )
  );

CREATE POLICY "Project owners can manage members" ON public.project_members
  FOR ALL USING (
    project_id IN (
      SELECT id FROM public.projects WHERE owner_id = auth.uid()
    )
  );

-- Repositories policies (inherit from project)
CREATE POLICY "Project members can view repositories" ON public.repositories
  FOR SELECT USING (
    project_id IN (
      SELECT id FROM public.projects WHERE 
        owner_id = auth.uid() OR
        id IN (SELECT project_id FROM public.project_members WHERE user_id = auth.uid())
    )
  );

CREATE POLICY "Project owners and editors can manage repositories" ON public.repositories
  FOR ALL USING (
    project_id IN (
      SELECT id FROM public.projects WHERE 
        owner_id = auth.uid() OR
        id IN (SELECT project_id FROM public.project_members WHERE user_id = auth.uid() AND role IN ('owner', 'editor'))
    )
  );

-- Files policies (inherit from repository)
CREATE POLICY "Project members can view files" ON public.files
  FOR SELECT USING (
    repository_id IN (
      SELECT id FROM public.repositories WHERE 
        project_id IN (
          SELECT id FROM public.projects WHERE 
            owner_id = auth.uid() OR
            id IN (SELECT project_id FROM public.project_members WHERE user_id = auth.uid())
        )
    )
  );

CREATE POLICY "Project owners and editors can manage files" ON public.files
  FOR ALL USING (
    repository_id IN (
      SELECT id FROM public.repositories WHERE 
        project_id IN (
          SELECT id FROM public.projects WHERE 
            owner_id = auth.uid() OR
            id IN (SELECT project_id FROM public.project_members WHERE user_id = auth.uid() AND role IN ('owner', 'editor'))
        )
    )
  );

-- Similar policies for other tables...
-- (For brevity, showing pattern - apply similar logic to all tables)

-- Create helpful database functions

-- Function to get user's accessible projects
CREATE OR REPLACE FUNCTION get_user_projects(user_uuid UUID DEFAULT auth.uid())
RETURNS TABLE (
  project_id UUID,
  project_name TEXT,
  user_role TEXT,
  owner_email TEXT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    p.id,
    p.name,
    'owner'::TEXT,
    u.email
  FROM public.projects p
  JOIN public.users u ON p.owner_id = u.id
  WHERE p.owner_id = user_uuid
  
  UNION ALL
  
  SELECT 
    p.id,
    p.name,
    pm.role::TEXT,
    u.email
  FROM public.project_members pm
  JOIN public.projects p ON pm.project_id = p.id
  JOIN public.users u ON p.owner_id = u.id
  WHERE pm.user_id = user_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user has project permission
CREATE OR REPLACE FUNCTION has_project_permission(
  project_uuid UUID,
  required_role TEXT DEFAULT 'viewer',
  user_uuid UUID DEFAULT auth.uid()
)
RETURNS BOOLEAN AS $$
DECLARE
  user_role TEXT;
BEGIN
  -- Check if user is owner
  SELECT 'owner' INTO user_role
  FROM public.projects
  WHERE id = project_uuid AND owner_id = user_uuid;
  
  -- If not owner, check membership
  IF user_role IS NULL THEN
    SELECT role INTO user_role
    FROM public.project_members
    WHERE project_id = project_uuid AND user_id = user_uuid;
  END IF;
  
  -- Role hierarchy: owner > editor > viewer
  IF required_role = 'viewer' THEN
    RETURN user_role IN ('owner', 'editor', 'viewer');
  ELSIF required_role = 'editor' THEN
    RETURN user_role IN ('owner', 'editor');
  ELSIF required_role = 'owner' THEN
    RETURN user_role = 'owner';
  END IF;
  
  RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.audit_logs (user_id, project_id, action, table_name, record_id, old_values, new_values)
  VALUES (
    auth.uid(),
    COALESCE(NEW.project_id, OLD.project_id),
    TG_OP,
    TG_TABLE_NAME,
    COALESCE(NEW.id, OLD.id),
    CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE NULL END,
    CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) ELSE NULL END
  );
  
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to critical tables
CREATE TRIGGER audit_projects_trigger AFTER INSERT OR UPDATE OR DELETE ON public.projects
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_repositories_trigger AFTER INSERT OR UPDATE OR DELETE ON public.repositories
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_files_trigger AFTER INSERT OR UPDATE OR DELETE ON public.files
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Insert sample data for testing (optional)
-- This would be removed in production

-- Create a storage bucket for file uploads
-- This needs to be done via Supabase dashboard or API
-- INSERT INTO storage.buckets (id, name) VALUES ('project-files', 'project-files');

-- Set up storage policies
-- These would be created via Supabase dashboard or API

COMMIT;
