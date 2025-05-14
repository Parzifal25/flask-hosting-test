from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'xxxx'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(length=120), nullable=False, server_default='default_name'))
        batch_op.add_column(sa.Column('DOB', sa.String(length=120), nullable=False, server_default='1970-01-01'))

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('name', server_default=None)
        batch_op.alter_column('DOB', server_default=None)

def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('DOB')
        batch_op.drop_column('name')
