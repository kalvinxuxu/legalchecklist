"""Create unified document provenance tables."""
from alembic import op
import sqlalchemy as sa

revision = "001_unified_document_provenance"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("document_records", sa.Column("id", sa.String(36), primary_key=True), sa.Column("contract_id", sa.String(36), nullable=False), sa.Column("file_hash", sa.String(64), nullable=False), sa.Column("file_name", sa.String(255), nullable=False), sa.Column("mime_type", sa.String(100), nullable=False), sa.Column("file_size", sa.Integer), sa.Column("current_version_id", sa.String(36)), sa.Column("created_at", sa.DateTime, nullable=False), sa.Column("updated_at", sa.DateTime, nullable=False))
    op.create_table("document_versions", sa.Column("id", sa.String(36), primary_key=True), sa.Column("document_id", sa.String(36), nullable=False), sa.Column("version_number", sa.Integer, nullable=False), sa.Column("parser_name", sa.String(100), nullable=False), sa.Column("parser_version", sa.String(100), nullable=False), sa.Column("coord_system", sa.String(50), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("parse_quality", sa.Float), sa.Column("warnings", sa.JSON), sa.Column("ast_snapshot", sa.JSON), sa.Column("completed_at", sa.String(40)), sa.Column("created_at", sa.DateTime, nullable=False), sa.Column("updated_at", sa.DateTime, nullable=False))

def downgrade():
    op.drop_table("document_versions")
    op.drop_table("document_records")
