import logging
import unicodedata

from odoo import api, models

_logger = logging.getLogger(__name__)


def _normalize_search_value(value):
    """Quita acentos, comas y puntos de un valor de búsqueda."""
    if not isinstance(value, str):
        return value
    nfkd = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in nfkd if not unicodedata.combining(c))
    value = value.replace(",", "").replace(".", "")
    return value


_TEXT_OPERATORS = {"ilike", "not ilike", "like", "not like", "=like", "=ilike"}


class BaseModel(models.AbstractModel):
    _inherit = "base"

    @api.model
    def _search(self, domain, *args, **kwargs):
        # Solo normalizar listas planas de Python, no objetos Domain de Odoo 19
        if isinstance(domain, list):
            domain = _normalize_domain(domain)
        return super()._search(domain, *args, **kwargs)


def _normalize_domain(domain):
    if not domain:
        return domain
    new_domain = []
    for leaf in domain:
        if (
            isinstance(leaf, (list, tuple))
            and len(leaf) == 3
            and isinstance(leaf[1], str)
            and leaf[1] in _TEXT_OPERATORS
            and isinstance(leaf[2], str)
        ):
            field, operator, value = leaf
            value = _normalize_search_value(value)
            new_domain.append((field, operator, value))
        else:
            new_domain.append(leaf)
    return new_domain


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    @api.model
    def _ensure_unaccent(self):
        self.env.cr.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
        param = self.sudo().search([("key", "=", "base.unaccent")], limit=1)
        if not param:
            self.sudo().create({"key": "base.unaccent", "value": "True"})
        elif param.value != "True":
            param.sudo().write({"value": "True"})