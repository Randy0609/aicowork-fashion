export interface ProductInput {
  category: string;
  product_name: string;
  material: string;
  target_customer: string;
  selling_points: string;
  tone: '克制专业' | '轻松自然' | '简洁有力';
}

export interface Category {
  id: string;
  name: string;
  description: string;
  focus_fields: string[];
  example: ProductInput;
  config_file: string;
}

export interface WorkflowManifest {
  id: string;
  name: string;
  version: string;
  status: string;
  description: string;
  input_fields: Array<Record<string, unknown>>;
  output_fields: string[];
}

export interface WorkbenchStatus {
  version: string;
  default_provider: string;
  configured_model_ready: boolean;
  configured_model: string | null;
  data_store: string;
}

export interface VideoScene {
  scene: string;
  visual: string;
  voiceover: string;
}

export interface ProductContent {
  product_title: string;
  selling_points: string[];
  social_post: string;
  short_video_script: VideoScene[];
  review_notes: string[];
  generation_mode?: string;
}

export interface Task {
  id: string;
  workflow_id: string;
  provider: string;
  status: 'running' | 'completed' | 'failed';
  inputs: ProductInput;
  artifact_id: string | null;
  error: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface Artifact {
  id: string;
  task_id: string;
  workflow_id: string;
  title: string;
  content: ProductContent;
  created_at: string;
}

export interface RunWorkflowResponse {
  task: Task;
  artifact: Artifact;
}
