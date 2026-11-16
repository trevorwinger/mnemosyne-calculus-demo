"""stable ordering for exported chat transcripts

Revision ID: 0014_chat_message_sequence
Revises: 0013_exercise_automatic_check
"""
from alembic import op
import sqlalchemy as sa


revision = "0014_chat_message_sequence"
down_revision = "0013_exercise_automatic_check"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("chat_messages", sa.Column("sequence", sa.Integer(), nullable=True))
    op.execute("""
        WITH numbered AS (
            SELECT id, row_number() OVER (PARTITION BY session_id ORDER BY created_at, id) AS message_sequence
            FROM chat_messages
        )
        UPDATE chat_messages SET sequence = numbered.message_sequence FROM numbered WHERE chat_messages.id = numbered.id
    """)
    op.alter_column("chat_messages", "sequence", nullable=False)
    op.create_unique_constraint("uq_message_session_sequence", "chat_messages", ["session_id", "sequence"])


def downgrade():
    op.drop_constraint("uq_message_session_sequence", "chat_messages", type_="unique")
    op.drop_column("chat_messages", "sequence")
