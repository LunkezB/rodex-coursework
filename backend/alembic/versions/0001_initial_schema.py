"""Initial Rodex schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-02
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    sex = sa.Enum("male", "female", "unknown", name="sex")
    relationship_kind = sa.Enum("parent_child", name="relationship_kind")
    parent_role = sa.Enum("father", "mother", "unknown", name="parent_role")

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "persons",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("surname", sa.String(length=100), nullable=True),
        sa.Column("given_name", sa.String(length=100), nullable=False),
        sa.Column("patronymic", sa.String(length=100), nullable=True),
        sa.Column("name_variants", sa.Text(), nullable=True),
        sa.Column("sex", sex, nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("birth_place", sa.String(length=255), nullable=True),
        sa.Column("death_date", sa.Date(), nullable=True),
        sa.Column("death_place", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_persons_owner_id"), "persons", ["owner_id"], unique=False)
    op.create_index(op.f("ix_persons_surname"), "persons", ["surname"], unique=False)
    op.create_index(op.f("ix_persons_given_name"), "persons", ["given_name"], unique=False)
    op.create_index(op.f("ix_persons_patronymic"), "persons", ["patronymic"], unique=False)

    op.create_table(
        "sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("archive_reference", sa.String(length=255), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("reliability_comment", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sources_owner_id"), "sources", ["owner_id"], unique=False)
    op.create_index(op.f("ix_sources_title"), "sources", ["title"], unique=False)

    op.create_table(
        "relationships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column("kind", relationship_kind, nullable=False),
        sa.Column("parent_role", parent_role, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["child_id"], ["persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["persons.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "parent_id", "child_id", "kind", name="uq_relationship_parent_child_kind"
        ),
    )
    op.create_index(op.f("ix_relationships_owner_id"), "relationships", ["owner_id"], unique=False)
    op.create_index(
        op.f("ix_relationships_parent_id"), "relationships", ["parent_id"], unique=False
    )
    op.create_index(op.f("ix_relationships_child_id"), "relationships", ["child_id"], unique=False)

    op.create_table(
        "person_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("person_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["person_id"], ["persons.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_person_sources_person_id"), "person_sources", ["person_id"], unique=False
    )
    op.create_index(
        op.f("ix_person_sources_source_id"), "person_sources", ["source_id"], unique=False
    )

    op.create_table(
        "relationship_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("relationship_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["relationship_id"], ["relationships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_relationship_sources_relationship_id"),
        "relationship_sources",
        ["relationship_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_relationship_sources_source_id"),
        "relationship_sources",
        ["source_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_relationship_sources_source_id"), table_name="relationship_sources")
    op.drop_index(
        op.f("ix_relationship_sources_relationship_id"), table_name="relationship_sources"
    )
    op.drop_table("relationship_sources")

    op.drop_index(op.f("ix_person_sources_source_id"), table_name="person_sources")
    op.drop_index(op.f("ix_person_sources_person_id"), table_name="person_sources")
    op.drop_table("person_sources")

    op.drop_index(op.f("ix_relationships_child_id"), table_name="relationships")
    op.drop_index(op.f("ix_relationships_parent_id"), table_name="relationships")
    op.drop_index(op.f("ix_relationships_owner_id"), table_name="relationships")
    op.drop_table("relationships")

    op.drop_index(op.f("ix_sources_title"), table_name="sources")
    op.drop_index(op.f("ix_sources_owner_id"), table_name="sources")
    op.drop_table("sources")

    op.drop_index(op.f("ix_persons_patronymic"), table_name="persons")
    op.drop_index(op.f("ix_persons_given_name"), table_name="persons")
    op.drop_index(op.f("ix_persons_surname"), table_name="persons")
    op.drop_index(op.f("ix_persons_owner_id"), table_name="persons")
    op.drop_table("persons")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    sa.Enum(name="parent_role").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="relationship_kind").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="sex").drop(op.get_bind(), checkfirst=True)
