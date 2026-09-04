export interface BBox { x0: number; y0: number; x1: number; y1: number }
export interface EvidenceLocation { page: number; bbox?: BBox; span_id?: string; coord_system?: 'pdf_top_left'; resolution_status?: 'resolved' | 'fuzzy_fallback' | 'page_only' | 'unresolved' }
export interface ReviewEvidence {
  evidence_id: string
  risk_id?: string
  document_id: string
  version_id: string
  quote: string
  locations: EvidenceLocation[]
  match_type: 'id_exact' | 'offset_exact' | 'fuzzy_legacy' | 'page_only'
  confidence: number
}
export interface IngestionStatus {
  status: string
  document_id?: string | null
  version_id?: string | null
  parser?: string | null
  quality_score?: number | null
  warnings?: Array<Record<string, unknown>>
}
