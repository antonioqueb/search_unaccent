import logging
import re
import unicodedata

from odoo import api, models
from odoo.osv import expression

_logger = logging.getLogger(__name__)


def _normalize_search_value(value):
    """Quita acentos, comas y puntos de un valor de búsqueda."""
    if not isinstance(value, str):
        return value
    # Quitar acentos
    nfkd = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in nfkd if not unicodedata.combining(c))
    # Quitar comas y puntos
    value = value.replace(",", "").replace(".", "")
    return value


# Operadores de texto donde aplica la normalización
_TEXT_OPERATORS = {"ilike", "not ilike", "like", "not like", "=like", "=ilike"}


class BaseModel(models.AbstractModel):
    _inherit = "base"

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, count=False):
        """Override global de _search para normalizar valores de texto en el dominio."""
        domain = _normalize_domain(domain)
        return super()._search(
            domain, offset=offset, limit=limit, order=order, count=count
        )


def _normalize_domain(domain):
    """Recorre el dominio y normaliza valores string en operadores de texto."""
    if not domain:
        return domain
    new_domain = []
    for leaf in domain:
        if isinstance(leaf, (list, tuple)) and len(leaf) == 3:
            field, operator, value = leaf
            if operator in _TEXT_OPERATORS and isinstance(value, str):
                value = _normalize_search_value(value)
            new_domain.append((field, operator, value))
        else:
            new_domain.append(leaf)
    return new_domain


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    @api.model
    def _ensure_unaccent(self):
        """Asegurar que unaccent esté habilitado en la config de Odoo."""
        self.env.cr.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
        # Verificar que el parámetro de sistema exista
        param = self.sudo().search([("key", "=", "base.unaccent")], limit=1)
        if not param:
            self.sudo().create({"key": "base.unaccent", "value": "True"})
        elif param.value != "True":
            param.sudo().write({"value": "True"})
