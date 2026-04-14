from . import models


def post_init_hook(env):
    """Habilitar la extensión unaccent en PostgreSQL y configurar Odoo."""
    env.cr.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
    env["ir.config_parameter"]._ensure_unaccent()

