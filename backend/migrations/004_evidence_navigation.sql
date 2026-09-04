-- Evidence IDs are stored in clause_locations.extra_data for backward compatibility.
CREATE INDEX IF NOT EXISTS ix_clause_locations_evidence_id
ON clause_locations ((extra_data->>'evidence_id'));
