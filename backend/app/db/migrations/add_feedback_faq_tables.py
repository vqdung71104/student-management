"""Add feedback and FAQ tables

Revision ID: add_feedback_faq_tables
Revises: 
Create Date: 2025-09-14

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create feedback table
    op.create_table('feedbacks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.Enum('BUG', 'FEATURE', 'UI', 'PERFORMANCE', 'CONTENT', 'OTHER', name='feedbacksubject'), nullable=False),
        sa.Column('feedback', sa.Text(), nullable=False),
        sa.Column('suggestions', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'RESOLVED', name='feedbackstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feedbacks_id'), 'feedbacks', ['id'], unique=False)

    # Create FAQ table
    op.create_table('faqs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_faqs_id'), 'faqs', ['id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_faqs_id'), table_name='faqs')
    op.drop_table('faqs')
    op.drop_index(op.f('ix_feedbacks_id'), table_name='feedbacks')
    op.drop_table('feedbacks')