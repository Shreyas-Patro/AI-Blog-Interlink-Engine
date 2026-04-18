"""add_title_phrases_and_phrase_offsets

Revision ID: b33f248bf1d6
Revises: 67d20f5d65e4
Create Date: 2026-04-17 14:30:40.914973

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b33f248bf1d6'
down_revision: Union[str, Sequence[str], None] = '67d20f5d65e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # All new columns were already added during a prior partial run.
    # Only the unique-constraint swap on `matches` remains.
    with op.batch_alter_table('matches', schema=None) as batch_op:
        batch_op.drop_constraint('uq_match_pair', type_='unique')
        batch_op.create_unique_constraint(
            'uq_match_pair_phrase',
            ['source_chunk_id', 'target_chunk_id', 'matched_phrase'],
        )


def downgrade() -> None:
    with op.batch_alter_table('matches', schema=None) as batch_op:
        batch_op.drop_constraint('uq_match_pair_phrase', type_='unique')
        batch_op.create_unique_constraint(
            'uq_match_pair',
            ['source_chunk_id', 'target_chunk_id'],
        )
        batch_op.drop_column('matched_title_phrase')
        batch_op.drop_column('phrase_char_end')
        batch_op.drop_column('phrase_char_start')
        batch_op.drop_column('matched_phrase')

    with op.batch_alter_table('articles', schema=None) as batch_op:
        batch_op.drop_column('representation_hash')
        batch_op.drop_column('representation_model')
        batch_op.drop_column('representation_vector')
        batch_op.drop_column('title_phrases_json')