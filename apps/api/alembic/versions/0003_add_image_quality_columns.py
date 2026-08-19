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

    op.add_column(
        "celebrity_images",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    op.create_index(
        "ix_celebrity_images_is_active",
        "celebrity_images",
        ["is_active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_celebrity_images_is_active",
        table_name="celebrity_images",
    )

    op.drop_column("celebrity_images", "is_active")
    op.drop_column("celebrity_images", "quality_score")