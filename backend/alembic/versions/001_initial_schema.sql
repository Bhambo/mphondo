-- =============================================================
-- Mphondo v3 — Schema inicial completo
-- Migration: 001_initial_schema
-- =============================================================
-- Ejecutar como superuser o con rol que tenga CREATE EXTENSION
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Supabase Realtime requires its own schema
CREATE SCHEMA IF NOT EXISTS _realtime;
CREATE ROLE supabase_realtime_admin NOINHERIT CREATEROLE;
GRANT ALL PRIVILEGES ON SCHEMA _realtime TO mphondo;

-- =============================================================
-- ENUMS
-- =============================================================

CREATE TYPE account_type AS ENUM (
  'mpesa',           -- M-Pesa MZ
  'bank_es',         -- Cuenta bancaria España
  'cash_mz',         -- Efectivo MZ
  'cash_es',         -- Efectivo España
  'xitiqui',         -- Grupo xitiqui (ahorro rotativo)
  'virtual_income',  -- Cuenta virtual de ingresos (double-entry)
  'virtual_expense'  -- Cuenta virtual de gastos (double-entry)
);

CREATE TYPE currency_code AS ENUM ('EUR', 'MZN');

CREATE TYPE module_context AS ENUM ('es', 'mz');

CREATE TYPE transaction_status AS ENUM (
  'confirmed',
  'pending',       -- pendente de confirmação (import não confirmado)
  'reconciled',    -- reconciliado com extracto
  'voided'
);

CREATE TYPE entry_direction AS ENUM ('debit', 'credit');

CREATE TYPE mpesa_import_status AS ENUM (
  'uploaded',
  'parsed',
  'review',        -- aguarda confirmação do utilizador
  'imported',
  'failed'
);

CREATE TYPE loan_direction AS ENUM ('given', 'received');

CREATE TYPE xitique_role AS ENUM ('member', 'admin');

-- =============================================================
-- USERS (gerido pelo Supabase Auth — apenas perfil extra)
-- =============================================================

CREATE TABLE profiles (
  id            UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name  TEXT NOT NULL,
  email         TEXT NOT NULL,
  avatar_url    TEXT,
  default_currency currency_code NOT NULL DEFAULT 'EUR',
  salary_eur    NUMERIC(20,4),            -- usado pelo Controlo Orçamental
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================================================
-- ACCOUNTS
-- =============================================================

CREATE TABLE accounts (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  module_context  module_context NOT NULL,   -- 'es' ou 'mz'
  name            TEXT NOT NULL,
  account_type    account_type NOT NULL,
  currency        currency_code NOT NULL,
  iban            TEXT,                      -- IBAN para cuentas bancarias ES
  phone           TEXT,                      -- teléfono para cuentas M-Pesa
  initial_balance NUMERIC(20,4) NOT NULL DEFAULT 0,
  current_balance NUMERIC(20,4) NOT NULL DEFAULT 0,  -- mantido por trigger
  is_default      BOOLEAN NOT NULL DEFAULT false,
  is_active       BOOLEAN NOT NULL DEFAULT true,
  sort_order      INT NOT NULL DEFAULT 0,
  icon            TEXT,
  color           TEXT,
  notes           TEXT,
  deleted_at      TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_accounts_user ON accounts(user_id);
CREATE INDEX idx_accounts_module ON accounts(user_id, module_context);
CREATE INDEX idx_accounts_active ON accounts(user_id, deleted_at) WHERE deleted_at IS NULL;

-- =============================================================
-- CATEGORIES (hierárquicas, separadas por módulo)
-- =============================================================

CREATE TABLE categories (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id     UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  module      module_context NOT NULL,
  parent_id   UUID REFERENCES categories(id) ON DELETE SET NULL,
  name        TEXT NOT NULL,
  icon        TEXT,
  color       TEXT,
  is_income   BOOLEAN NOT NULL DEFAULT false,   -- true = categoria de entrada
  is_system   BOOLEAN NOT NULL DEFAULT false,   -- categorias pré-definidas
  sort_order  INT NOT NULL DEFAULT 0,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_categories_user_module ON categories(user_id, module);

-- =============================================================
-- CATEGORY AUTO-RULES (para banking ES — auto-categorização)
-- =============================================================

CREATE TABLE category_rules (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id       UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  category_id   UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  match_field   TEXT NOT NULL CHECK (match_field IN ('description', 'merchant', 'amount_exact', 'amount_range')),
  match_value   TEXT NOT NULL,          -- regex ou valor exacto
  priority      INT NOT NULL DEFAULT 0, -- maior = mais prioritário
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================================================
-- CONTACTS (pessoas ligadas a transações MZ)
-- =============================================================

CREATE TABLE contacts (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id     UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  phone       TEXT,                      -- número M-Pesa
  relation    TEXT,                      -- "Mamã", "João", etc.
  is_readonly_user BOOLEAN DEFAULT false, -- perfil read-only partilhado
  readonly_token   TEXT UNIQUE,          -- token para link de leitura
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_contacts_user ON contacts(user_id);

-- =============================================================
-- FX RATES (snapshot diário EUR/MZN)
-- =============================================================

CREATE TABLE fx_rates (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  from_currency currency_code NOT NULL,
  to_currency   currency_code NOT NULL,
  rate          NUMERIC(20,8) NOT NULL,
  rate_date     DATE NOT NULL,
  source        TEXT NOT NULL DEFAULT 'exchangerate.host',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (from_currency, to_currency, rate_date)
);

CREATE INDEX idx_fx_rates_date ON fx_rates(from_currency, to_currency, rate_date DESC);

-- =============================================================
-- TRANSACTIONS (cabeçalho — double-entry)
-- =============================================================

CREATE TABLE transactions (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  module          module_context NOT NULL,
  status          transaction_status NOT NULL DEFAULT 'confirmed',
  occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  description     TEXT NOT NULL,
  reference       TEXT,                        -- referencia libre (M-Pesa ref, nº factura…)
  merchant        TEXT,                        -- establecimiento (ES)
  contact_id      UUID REFERENCES contacts(id) ON DELETE SET NULL,  -- para MZ
  category_id     UUID REFERENCES categories(id) ON DELETE SET NULL,
  currency        currency_code NOT NULL,
  fx_rate_id      UUID REFERENCES fx_rates(id) ON DELETE SET NULL,
  fx_rate_snapshot NUMERIC(20,8),              -- tipo de câmbio no momento
  notes           TEXT,
  tags            TEXT[],                      -- etiquetas livres
  is_transfer     BOOLEAN NOT NULL DEFAULT false,  -- transferência interna
  transfer_pair_id UUID,                       -- aponta para o outro lado
  deleted_at      TIMESTAMPTZ,                 -- soft delete
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tx_user_module ON transactions(user_id, module);
CREATE INDEX idx_tx_occurred ON transactions(user_id, occurred_at DESC);
CREATE INDEX idx_tx_category ON transactions(category_id, occurred_at DESC);
CREATE INDEX idx_tx_contact ON transactions(contact_id);
CREATE INDEX idx_tx_active ON transactions(user_id, deleted_at) WHERE deleted_at IS NULL;

-- =============================================================
-- ENTRIES (linhas double-entry — a soma deve ser 0)
-- =============================================================

CREATE TABLE entries (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  transaction_id  UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
  account_id      UUID NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
  direction       entry_direction NOT NULL,
  amount          NUMERIC(20,4) NOT NULL CHECK (amount > 0),
  -- amount sempre positivo; direction indica o sentido
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_entries_transaction ON entries(transaction_id);
CREATE INDEX idx_entries_account ON entries(account_id);

-- =============================================================
-- TRIGGER: validar double-entry (sum créditos - débitos = 0)
-- =============================================================

CREATE OR REPLACE FUNCTION validate_double_entry()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
  v_sum NUMERIC;
BEGIN
  SELECT COALESCE(
    SUM(CASE WHEN direction = 'credit' THEN amount ELSE -amount END), 0
  ) INTO v_sum
  FROM entries
  WHERE transaction_id = COALESCE(NEW.transaction_id, OLD.transaction_id);

  IF v_sum <> 0 THEN
    RAISE EXCEPTION 'Double-entry violation: entries sum to % (must be 0)', v_sum;
  END IF;
  RETURN NEW;
END;
$$;

-- Disparado após INSERT/UPDATE/DELETE numa entry, no fim da instrução
CREATE CONSTRAINT TRIGGER trg_double_entry
AFTER INSERT OR UPDATE OR DELETE ON entries
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION validate_double_entry();

-- =============================================================
-- TRIGGER: actualizar current_balance em accounts
-- =============================================================

CREATE OR REPLACE FUNCTION update_account_balance()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
  v_account_id UUID;
  v_delta      NUMERIC;
BEGIN
  IF TG_OP = 'DELETE' THEN
    v_account_id := OLD.account_id;
    v_delta := CASE WHEN OLD.direction = 'credit' THEN -OLD.amount ELSE OLD.amount END;
  ELSE
    v_account_id := NEW.account_id;
    v_delta := CASE WHEN NEW.direction = 'credit' THEN NEW.amount ELSE -NEW.amount END;
    IF TG_OP = 'UPDATE' THEN
      -- reverter o valor anterior
      v_delta := v_delta + CASE WHEN OLD.direction = 'credit' THEN -OLD.amount ELSE OLD.amount END;
    END IF;
  END IF;

  UPDATE accounts
  SET current_balance = current_balance + v_delta,
      updated_at = now()
  WHERE id = v_account_id;

  RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE TRIGGER trg_account_balance
AFTER INSERT OR UPDATE OR DELETE ON entries
FOR EACH ROW EXECUTE FUNCTION update_account_balance();

-- =============================================================
-- M-PESA STATEMENTS (PDFs carregados)
-- =============================================================

CREATE TABLE mpesa_statements (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  filename        TEXT NOT NULL,
  storage_path    TEXT NOT NULL,          -- path no Supabase Storage
  file_hash       TEXT NOT NULL,          -- SHA-256 para detectar duplicados
  period_start    DATE,
  period_end      DATE,
  status          mpesa_import_status NOT NULL DEFAULT 'uploaded',
  parse_errors    JSONB,                  -- erros do parser, se houver
  raw_count       INT,                    -- nº de transações extraídas
  imported_count  INT,                    -- nº confirmadas e importadas
  uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  parsed_at       TIMESTAMPTZ,
  imported_at     TIMESTAMPTZ,
  UNIQUE (user_id, file_hash)
);

CREATE INDEX idx_mpesa_stmt_user ON mpesa_statements(user_id, uploaded_at DESC);

-- =============================================================
-- M-PESA RAW TRANSACTIONS (resultado do parser, antes de confirmar)
-- =============================================================

CREATE TABLE mpesa_raw_transactions (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  statement_id    UUID REFERENCES mpesa_statements(id) ON DELETE CASCADE,
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  -- campos extraídos do PDF / SMS
  raw_ref         TEXT,                   -- referência M-Pesa (ex: ABC123XYZ)
  raw_type        TEXT,                   -- tipo bruto ("Envio", "Xitiqui"…)
  raw_amount      NUMERIC(20,4),
  raw_fee         NUMERIC(20,4),
  raw_balance     NUMERIC(20,4),
  raw_party       TEXT,                   -- nome/telefone da contraparte
  raw_date        TIMESTAMPTZ,
  raw_description TEXT,
  -- mapeamento proposto (editável pelo utilizador antes de confirmar)
  suggested_category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
  suggested_contact_id  UUID REFERENCES contacts(id) ON DELETE SET NULL,
  -- estado
  is_duplicate    BOOLEAN NOT NULL DEFAULT false,
  transaction_id  UUID REFERENCES transactions(id) ON DELETE SET NULL,  -- preenchido após confirmar
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_mpesa_raw_stmt ON mpesa_raw_transactions(statement_id);
CREATE INDEX idx_mpesa_raw_user ON mpesa_raw_transactions(user_id);
CREATE UNIQUE INDEX idx_mpesa_raw_ref ON mpesa_raw_transactions(user_id, raw_ref) WHERE raw_ref IS NOT NULL;

-- =============================================================
-- XITIQUE (grupos de poupança rotativo)
-- =============================================================

CREATE TABLE xitique_groups (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id       UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,
  description   TEXT,
  currency      currency_code NOT NULL DEFAULT 'MZN',
  contribution  NUMERIC(20,4) NOT NULL,   -- valor por membro por ciclo
  frequency     TEXT NOT NULL DEFAULT 'monthly' CHECK (frequency IN ('weekly','biweekly','monthly')),
  member_count  INT NOT NULL DEFAULT 2,
  is_active     BOOLEAN NOT NULL DEFAULT true,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE xitique_members (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  group_id    UUID NOT NULL REFERENCES xitique_groups(id) ON DELETE CASCADE,
  contact_id  UUID REFERENCES contacts(id) ON DELETE SET NULL,
  name        TEXT NOT NULL,
  position    INT NOT NULL,              -- posição na rotação (1-based)
  role        xitique_role NOT NULL DEFAULT 'member',
  UNIQUE (group_id, position)
);

CREATE TABLE xitique_cycles (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  group_id      UUID NOT NULL REFERENCES xitique_groups(id) ON DELETE CASCADE,
  cycle_number  INT NOT NULL,
  beneficiary_position INT NOT NULL,
  start_date    DATE NOT NULL,
  end_date      DATE NOT NULL,
  expected_date DATE NOT NULL,           -- data prevista de pagamento ao beneficiário
  total_amount  NUMERIC(20,4) NOT NULL,  -- contribution * member_count
  status        TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed','partial')),
  closed_at     TIMESTAMPTZ,
  UNIQUE (group_id, cycle_number)
);

CREATE TABLE xitique_contributions (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  cycle_id      UUID NOT NULL REFERENCES xitique_cycles(id) ON DELETE CASCADE,
  member_id     UUID NOT NULL REFERENCES xitique_members(id) ON DELETE CASCADE,
  transaction_id UUID REFERENCES transactions(id) ON DELETE SET NULL,
  amount        NUMERIC(20,4) NOT NULL,
  fee           NUMERIC(20,4) NOT NULL DEFAULT 0,
  paid_at       TIMESTAMPTZ,
  is_paid       BOOLEAN NOT NULL DEFAULT false,
  UNIQUE (cycle_id, member_id)
);

CREATE INDEX idx_xitique_cycles_group ON xitique_cycles(group_id, cycle_number DESC);
CREATE INDEX idx_xitique_contrib_cycle ON xitique_contributions(cycle_id);

-- =============================================================
-- LOANS (empréstimos dados/recebidos)
-- =============================================================

CREATE TABLE loans (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  module          module_context NOT NULL,
  direction       loan_direction NOT NULL,   -- 'given' (dei) ou 'received' (recebi)
  contact_id      UUID REFERENCES contacts(id) ON DELETE SET NULL,
  description     TEXT NOT NULL,
  currency        currency_code NOT NULL,
  principal       NUMERIC(20,4) NOT NULL,
  interest_rate   NUMERIC(6,4) NOT NULL DEFAULT 0,   -- % mensal
  start_date      DATE NOT NULL,
  due_date        DATE,
  amount_paid     NUMERIC(20,4) NOT NULL DEFAULT 0,
  is_settled      BOOLEAN NOT NULL DEFAULT false,
  settled_at      TIMESTAMPTZ,
  notes           TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_loans_user ON loans(user_id, is_settled);

-- =============================================================
-- BUDGETS (orçamentos mensais por categoria)
-- =============================================================

CREATE TABLE budgets (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id       UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  module        module_context NOT NULL,
  category_id   UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  currency      currency_code NOT NULL,
  amount        NUMERIC(20,4) NOT NULL,
  period_year   INT NOT NULL,
  period_month  INT NOT NULL CHECK (period_month BETWEEN 1 AND 12),
  alert_pct     INT NOT NULL DEFAULT 80,    -- alerta quando gasto >= 80%
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, category_id, period_year, period_month)
);

CREATE INDEX idx_budgets_user_period ON budgets(user_id, period_year, period_month);

-- =============================================================
-- BANK CONNECTIONS (Enable Banking PSD2)
-- =============================================================

CREATE TABLE bank_connections (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id           UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  account_id        UUID REFERENCES accounts(id) ON DELETE SET NULL,
  provider          TEXT NOT NULL DEFAULT 'enable_banking',
  bank_name         TEXT NOT NULL,
  requisition_id    TEXT NOT NULL UNIQUE,      -- ID Enable Banking
  access_token      TEXT,                       -- cifrado com pgcrypto
  refresh_token     TEXT,
  token_expires_at  TIMESTAMPTZ,
  requisition_expires_at TIMESTAMPTZ,          -- 90 dias PSD2
  last_sync_at      TIMESTAMPTZ,
  is_active         BOOLEAN NOT NULL DEFAULT true,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Cifrar tokens sensíveis
-- access_token guardado como: pgp_sym_encrypt(token, current_setting('app.encryption_key'))

-- =============================================================
-- AUDIT LOG (imutável — todas as mutações críticas)
-- =============================================================

CREATE TABLE audit_log (
  id          BIGSERIAL,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  user_id     UUID,
  table_name  TEXT NOT NULL,
  record_id   UUID NOT NULL,
  operation   TEXT NOT NULL CHECK (operation IN ('INSERT','UPDATE','DELETE')),
  old_data    JSONB,
  new_data    JSONB,
  ip_address  INET,
  PRIMARY KEY (id, occurred_at)
) PARTITION BY RANGE (occurred_at);

-- Partições por ano (criar anualmente)
CREATE TABLE audit_log_2026 PARTITION OF audit_log
  FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
CREATE TABLE audit_log_2027 PARTITION OF audit_log
  FOR VALUES FROM ('2027-01-01') TO ('2028-01-01');

CREATE INDEX idx_audit_user ON audit_log(user_id, occurred_at DESC);
CREATE INDEX idx_audit_table ON audit_log(table_name, record_id);

-- Função genérica de audit
CREATE OR REPLACE FUNCTION fn_audit()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  INSERT INTO audit_log (user_id, table_name, record_id, operation, old_data, new_data)
  VALUES (
    COALESCE(
      (current_setting('request.jwt.claims', true)::jsonb->>'sub')::uuid,
      NULL
    ),
    TG_TABLE_NAME,
    COALESCE(NEW.id, OLD.id),
    TG_OP,
    CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE to_jsonb(OLD) END,
    CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE to_jsonb(NEW) END
  );
  RETURN COALESCE(NEW, OLD);
END;
$$;

-- Audit nas tabelas críticas
CREATE TRIGGER trg_audit_transactions
AFTER INSERT OR UPDATE OR DELETE ON transactions
FOR EACH ROW EXECUTE FUNCTION fn_audit();

CREATE TRIGGER trg_audit_entries
AFTER INSERT OR UPDATE OR DELETE ON entries
FOR EACH ROW EXECUTE FUNCTION fn_audit();

CREATE TRIGGER trg_audit_accounts
AFTER INSERT OR UPDATE OR DELETE ON accounts
FOR EACH ROW EXECUTE FUNCTION fn_audit();

-- =============================================================
-- ROW LEVEL SECURITY
-- =============================================================

ALTER TABLE profiles          ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts          ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories        ENABLE ROW LEVEL SECURITY;
ALTER TABLE category_rules    ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts          ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions      ENABLE ROW LEVEL SECURITY;
ALTER TABLE entries           ENABLE ROW LEVEL SECURITY;
ALTER TABLE mpesa_statements  ENABLE ROW LEVEL SECURITY;
ALTER TABLE mpesa_raw_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE xitique_groups    ENABLE ROW LEVEL SECURITY;
ALTER TABLE xitique_members   ENABLE ROW LEVEL SECURITY;
ALTER TABLE xitique_cycles    ENABLE ROW LEVEL SECURITY;
ALTER TABLE xitique_contributions ENABLE ROW LEVEL SECURITY;
ALTER TABLE loans             ENABLE ROW LEVEL SECURITY;
ALTER TABLE budgets           ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_connections  ENABLE ROW LEVEL SECURITY;

-- Helper: extrai user_id do JWT Supabase
CREATE OR REPLACE FUNCTION auth.uid_uuid() RETURNS UUID AS $$
  SELECT (current_setting('request.jwt.claims', true)::jsonb->>'sub')::uuid;
$$ LANGUAGE sql STABLE;

-- Políticas: cada utilizador só vê os seus dados
DO $$ DECLARE
  t TEXT;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'profiles','accounts','categories','category_rules','contacts',
    'transactions','mpesa_statements','mpesa_raw_transactions',
    'xitique_groups','loans','budgets','bank_connections'
  ] LOOP
    EXECUTE format(
      'CREATE POLICY policy_%s_owner ON %s
       USING (user_id = auth.uid_uuid())
       WITH CHECK (user_id = auth.uid_uuid());', t, t
    );
  END LOOP;
END $$;

-- entries: acesso via transaction (join)
CREATE POLICY policy_entries_owner ON entries
  USING (
    EXISTS (
      SELECT 1 FROM transactions t
      WHERE t.id = entries.transaction_id
        AND t.user_id = auth.uid_uuid()
    )
  );

-- xitique_members, cycles, contributions: acesso via group
CREATE POLICY policy_xitique_members_owner ON xitique_members
  USING (EXISTS (SELECT 1 FROM xitique_groups g WHERE g.id = xitique_members.group_id AND g.user_id = auth.uid_uuid()));

CREATE POLICY policy_xitique_cycles_owner ON xitique_cycles
  USING (EXISTS (SELECT 1 FROM xitique_groups g WHERE g.id = xitique_cycles.group_id AND g.user_id = auth.uid_uuid()));

CREATE POLICY policy_xitique_contributions_owner ON xitique_contributions
  USING (EXISTS (
    SELECT 1 FROM xitique_cycles cy
    JOIN xitique_groups g ON g.id = cy.group_id
    WHERE cy.id = xitique_contributions.cycle_id AND g.user_id = auth.uid_uuid()
  ));

-- fx_rates: público (leitura)
ALTER TABLE fx_rates ENABLE ROW LEVEL SECURITY;
CREATE POLICY policy_fx_public ON fx_rates FOR SELECT USING (true);

-- audit_log: só leitura pelo próprio
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY policy_audit_owner ON audit_log FOR SELECT
  USING (user_id = auth.uid_uuid());

-- =============================================================
-- DADOS INICIAIS: Categorias de sistema
-- =============================================================

-- Função chamada no registo do utilizador (via Supabase trigger)
CREATE OR REPLACE FUNCTION fn_seed_default_categories(p_user_id UUID)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  -- --------------------------------------------------------
  -- MÓDULO ESPAÑA (EUR) — Saídas (compras diárias + fixas)
  -- --------------------------------------------------------
  INSERT INTO categories (user_id, module, name, icon, color, is_income, is_system) VALUES

  -- Compras e consumo diário
  (p_user_id, 'es', 'Supermercado',              'shopping-cart',  '#4CAF50', false, true),
  (p_user_id, 'es', 'Restaurantes / Cafés',       'utensils',       '#FF9800', false, true),
  (p_user_id, 'es', 'Takeaway / Delivery',        'package',        '#FF5722', false, true),
  (p_user_id, 'es', 'Compras online',             'globe',          '#9C27B0', false, true),
  (p_user_id, 'es', 'Ropa y calzado',             'shirt',          '#E91E63', false, true),
  (p_user_id, 'es', 'Farmacia / Salud',           'heart-pulse',    '#F44336', false, true),
  (p_user_id, 'es', 'Belleza / Cuidado personal', 'sparkles',       '#EC4899', false, true),
  (p_user_id, 'es', 'Hogar / Menaje',             'home',           '#795548', false, true),

  -- Transporte
  (p_user_id, 'es', 'Transporte público',         'train',          '#2196F3', false, true),
  (p_user_id, 'es', 'Coche (combustible)',        'fuel',           '#607D8B', false, true),
  (p_user_id, 'es', 'Coche (seguro / ITV)',       'shield-check',   '#455A64', false, true),
  (p_user_id, 'es', 'Taxi / Cabify / Uber',       'car',            '#00BCD4', false, true),
  (p_user_id, 'es', 'Vuelos / Viajes',            'plane',          '#03A9F4', false, true),

  -- Vivienda y suministros
  (p_user_id, 'es', 'Alquiler',                   'building',       '#673AB7', false, true),
  (p_user_id, 'es', 'Electricidad / Gas',         'zap',            '#FFEB3B', false, true),
  (p_user_id, 'es', 'Agua',                       'droplets',       '#00BCD4', false, true),
  (p_user_id, 'es', 'Internet / Móvil',           'wifi',           '#3F51B5', false, true),

  -- Ocio y bienestar
  (p_user_id, 'es', 'Ocio / Entretenimiento',     'gamepad-2',      '#9C27B0', false, true),
  (p_user_id, 'es', 'Suscripciones digitales',    'monitor',        '#673AB7', false, true),
  (p_user_id, 'es', 'Gimnasio / Deporte',         'dumbbell',       '#4CAF50', false, true),
  (p_user_id, 'es', 'Cultura / Libros',           'book-open',      '#795548', false, true),

  -- Finanzas y obligaciones
  (p_user_id, 'es', 'Dívida / Empréstimos',       'credit-card',    '#F44336', false, true),
  (p_user_id, 'es', 'Seguros',                    'shield',         '#607D8B', false, true),
  (p_user_id, 'es', 'Impuestos / Tasas',          'landmark',       '#9E9E9E', false, true),

  -- Remesas y transferencias
  (p_user_id, 'es', 'Remesa a Mozambique',        'send',           '#C0392B', false, true),
  (p_user_id, 'es', 'Transferencia interna',      'arrows-left-right', '#607D8B', false, true),
  (p_user_id, 'es', 'Compras / otros',            'shopping-bag',   '#9E9E9E', false, true),

  -- Entradas (España)
  (p_user_id, 'es', 'Salario',                    'briefcase',      '#4CAF50', true,  true),
  (p_user_id, 'es', 'Devolución / Reembolso',     'rotate-ccw',     '#00BCD4', true,  true),
  (p_user_id, 'es', 'Ingreso extra',              'plus-circle',    '#8BC34A', true,  true),
  (p_user_id, 'es', 'Transferencia recibida',     'arrow-down-circle', '#2196F3', true, true),

  -- --------------------------------------------------------
  -- MÓDULO MOZAMBIQUE (MZN) — Operações M-Pesa
  -- --------------------------------------------------------

  -- Saídas MZ
  (p_user_id, 'mz', 'Xitiqui',                   'users',          '#C0392B', false, true),
  (p_user_id, 'mz', 'Dívida / Empréstimo dado',  'hand-coins',     '#E53935', false, true),
  (p_user_id, 'mz', 'Envio/Transferência',        'send',           '#FF5722', false, true),
  (p_user_id, 'mz', 'Compras pessoais MZ',        'shopping-cart',  '#FF9800', false, true),
  (p_user_id, 'mz', 'Gasto família',              'heart',          '#E91E63', false, true),
  (p_user_id, 'mz', 'Serviços (luz, água…)',      'zap',            '#9C27B0', false, true),
  (p_user_id, 'mz', 'Taxa M-Pesa',               'percent',        '#607D8B', false, true),
  (p_user_id, 'mz', 'Saída diversa',             'circle-minus',   '#9E9E9E', false, true),

  -- Entradas MZ
  (p_user_id, 'mz', 'Ingresso / Depósito',        'arrow-up-circle','#4CAF50', true,  true),
  (p_user_id, 'mz', 'Devolução recebida',         'rotate-ccw',     '#00BCD4', true,  true),
  (p_user_id, 'mz', 'Recebido de terceiro',       'arrow-down-circle','#2196F3',true, true),
  (p_user_id, 'mz', 'Xitiqui recebido',           'users',          '#8BC34A', true,  true),
  (p_user_id, 'mz', 'Entrada diversa',            'circle-plus',    '#9E9E9E', true,  true);

END;
$$;

-- Trigger: chamar ao criar perfil
CREATE OR REPLACE FUNCTION fn_on_profile_created()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  PERFORM fn_seed_default_categories(NEW.id);
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_seed_categories
AFTER INSERT ON profiles
FOR EACH ROW EXECUTE FUNCTION fn_on_profile_created();

-- =============================================================
-- VIEWS úteis
-- =============================================================

-- Saldo por conta com nome do módulo
CREATE VIEW v_account_balances AS
SELECT
  a.id,
  a.user_id,
  a.module_context,
  a.name,
  a.account_type,
  a.currency,
  a.iban,
  a.phone,
  a.current_balance AS balance,
  a.initial_balance,
  a.color,
  a.icon,
  a.is_active,
  a.sort_order,
  a.created_at
FROM accounts a
WHERE a.deleted_at IS NULL
ORDER BY a.module_context, a.sort_order, a.name;

-- Resumo mensal por módulo
CREATE VIEW v_monthly_summary AS
SELECT
  t.user_id,
  t.module,
  t.currency,
  date_trunc('month', t.occurred_at) AS month,
  SUM(CASE WHEN c.is_income THEN e.amount ELSE 0 END)  AS total_income,
  SUM(CASE WHEN NOT c.is_income AND NOT t.is_transfer THEN e.amount ELSE 0 END) AS total_expenses,
  COUNT(DISTINCT t.id) AS transaction_count
FROM transactions t
JOIN entries e ON e.transaction_id = t.id AND e.direction = 'credit'
LEFT JOIN categories c ON c.id = t.category_id
WHERE t.deleted_at IS NULL
  AND t.status = 'confirmed'
GROUP BY t.user_id, t.module, t.currency, date_trunc('month', t.occurred_at);

-- =============================================================
-- UPDATED_AT auto-update
-- =============================================================

CREATE OR REPLACE FUNCTION fn_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$;

CREATE TRIGGER trg_profiles_updated_at   BEFORE UPDATE ON profiles   FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_accounts_updated_at   BEFORE UPDATE ON accounts   FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_transactions_updated_at BEFORE UPDATE ON transactions FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
CREATE TRIGGER trg_loans_updated_at      BEFORE UPDATE ON loans      FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- Auto-create profile row when a new user signs up via Supabase Auth
CREATE OR REPLACE FUNCTION fn_create_profile_on_signup()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  INSERT INTO public.profiles (id, display_name, email, default_currency)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1)),
    NEW.email,
    'EUR'
  ) ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_create_profile_on_signup
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION fn_create_profile_on_signup();
