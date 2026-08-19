from alembic import op
import sqlalchemy as sa


revision = "0003_add_image_quality_columns"
down_revision = "0002_add_origin_to_celebrities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "celebrity_images",
        sa.Column(
            "quality_score",
            sa.Float(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "celebrity_images",
        "quality_score",
    )