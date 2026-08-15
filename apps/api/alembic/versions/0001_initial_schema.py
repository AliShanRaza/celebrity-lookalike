"""Initial schema with celebrities, celebrity_images, celebrity_embeddings and pgvector HNSW index

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import pgvector

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Create celebrities table
    op.create_table(
        'celebrities',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('gender', sa.String(length=20), nullable=False), # male, female, non_binary
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_celebrities_gender'), 'celebrities', ['gender'], unique=False)
    op.create_index(op.f('ix_celebrities_name'), 'celebrities', ['name'], unique=False)
    op.create_index(op.f('ix_celebrities_is_active'), 'celebrities', ['is_active'], unique=False)

    # 3. Create celebrity_images table
    op.create_table(
        'celebrity_images',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('celebrity_id', sa.UUID(), nullable=False),
        sa.Column('image_url', sa.String(length=1024), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['celebrity_id'], ['celebrities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_celebrity_images_celebrity_id'), 'celebrity_images', ['celebrity_id'], unique=False)
    op.create_index(op.f('ix_celebrity_images_is_active'), 'celebrity_images', ['is_active'], unique=False)

    # 4. Create celebrity_embeddings table
    op.create_table(
        'celebrity_embeddings',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('celebrity_id', sa.UUID(), nullable=False),
        sa.Column('celebrity_image_id', sa.UUID(), nullable=False),
        sa.Column('model_version', sa.String(length=100), nullable=False, server_default='fake_v1'),
        sa.Column('embedding', pgvector.sqlalchemy.Vector(512), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['celebrity_id'], ['celebrities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['celebrity_image_id'], ['celebrity_images.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_celebrity_embeddings_celebrity_id'), 'celebrity_embeddings', ['celebrity_id'], unique=False)
    op.create_index(op.f('ix_celebrity_embeddings_celebrity_image_id'), 'celebrity_embeddings', ['celebrity_image_id'], unique=False)
    op.create_index(op.f('ix_celebrity_embeddings_model_version'), 'celebrity_embeddings', ['model_version'], unique=False)
    op.create_index(op.f('ix_celebrity_embeddings_is_active'), 'celebrity_embeddings', ['is_active'], unique=False)

    # 5. Create HNSW Cosine Index
    op.execute(
        "CREATE INDEX idx_celebrity_embeddings_hnsw ON celebrity_embeddings USING hnsw (embedding vector_cosine_ops);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_celebrity_embeddings_hnsw;")
    op.drop_index(op.f('ix_celebrity_embeddings_is_active'), table_name='celebrity_embeddings')
    op.drop_index(op.f('ix_celebrity_embeddings_model_version'), table_name='celebrity_embeddings')
    op.drop_index(op.f('ix_celebrity_embeddings_celebrity_image_id'), table_name='celebrity_embeddings')
    op.drop_index(op.f('ix_celebrity_embeddings_celebrity_id'), table_name='celebrity_embeddings')
    op.drop_table('celebrity_embeddings')
    
    op.drop_index(op.f('ix_celebrity_images_is_active'), table_name='celebrity_images')
    op.drop_index(op.f('ix_celebrity_images_celebrity_id'), table_name='celebrity_images')
    op.drop_table('celebrity_images')

    op.drop_index(op.f('ix_celebrities_is_active'), table_name='celebrities')
    op.drop_index(op.f('ix_celebrities_name'), table_name='celebrities')
    op.drop_index(op.f('ix_celebrities_gender'), table_name='celebrities')
    op.drop_table('celebrities')
