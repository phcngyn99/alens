// API Types

export type UserRole = 'admin' | 'user';

export interface Token {
  access_token: string;
  token_type: string;
}

export interface TokenWithUser extends Token {
  username: string;
  role: UserRole;
}

export interface User {
  id: string;
  username: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface UserCreate {
  username: string;
  password: string;
  role: UserRole;
  is_active: boolean;
}

export interface UserUpdate {
  role?: UserRole;
  is_active?: boolean;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface Connection {
  id: string;
  name: string;
  db_type: 'postgresql' | 'sqlserver' | 'db2';
  host: string;
  port: number;
  database_name: string;
  username: string;
  schema_whitelist: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface ConnectionCreate {
  name: string;
  db_type: 'postgresql' | 'sqlserver' | 'db2';
  host: string;
  port: number;
  database_name: string;
  username: string;
  password: string;
  schema_whitelist?: string[];
}

export interface DriverStatus {
  driver_name: string;
  is_installed: boolean;
  version: string | null;
  install_instructions: string | null;
}

export interface Column {
  name: string;
  data_type: string;
  nullable: boolean;
  is_primary_key: boolean;
  is_foreign_key: boolean;
  default_value: string | null;
  comment: string | null;
}

export interface ForeignKey {
  name: string;
  columns: string[];
  referenced_schema: string;
  referenced_table: string;
  referenced_columns: string[];
}

export interface Table {
  schema_name: string;
  name: string;
  columns: Column[];
  foreign_keys: ForeignKey[];
  approximate_row_count: number | null;
  has_timestamp_columns: boolean;
  fk_count: number;
  hint: 'event-like' | 'reference-like' | null;
}

export interface Schema {
  name: string;
  tables: Table[];
}

export interface TableDataPreview {
  schema_name: string;
  table_name: string;
  columns: string[];
  rows: (string | number | boolean | null)[][];
  row_count: number;
}

export interface TableOfInterest {
  name: string;
  is_likely_fact: boolean;
  is_likely_dimension: boolean;
  description?: string;
}

export interface Intent {
  id: string;
  connection_id: string;
  version: number;
  business_domain: string;
  analytical_goal: 'reporting' | 'bi' | 'ad-hoc';
  time_grain: 'daily' | 'weekly' | 'monthly';
  key_metrics: string[];
  tables_of_interest: TableOfInterest[];
  exclusions: string[];
  created_at: string;
}

export interface IntentCreate {
  connection_id: string;
  business_domain: string;
  analytical_goal: 'reporting' | 'bi' | 'ad-hoc';
  time_grain: 'daily' | 'weekly' | 'monthly';
  key_metrics: string[];
  tables_of_interest: TableOfInterest[];
  exclusions: string[];
}

export interface AIOutput {
  id: string;
  intent_id: string;
  version: number;
  model_explanation: string;
  dimension_details: Record<string, unknown>;
  assumptions: string;
  dimensional_dbml: string;
  ai_provider: string;
  ai_model: string;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  created_at: string;
}

export type AIProviderType = 'openai' | 'anthropic' | 'azure_openai' | 'azure_anthropic';

export interface AICredential {
  id: string;
  provider: AIProviderType;
  model_name: string;
  max_tokens: number;
  endpoint_url: string | null;
  deployment_name: string | null;
  api_version: string | null;
  created_at: string;
}

export interface AICredentialCreate {
  provider: AIProviderType;
  api_key: string;
  model_name: string;
  max_tokens: number;
  // Azure-specific fields (required for azure_* providers)
  endpoint_url?: string;
  deployment_name?: string;
  api_version?: string;
}
