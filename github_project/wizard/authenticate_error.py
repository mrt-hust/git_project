from odoo import api, fields, models


class AuthenticateError(models.TransientModel):
    _name = "popup.authenticate_error"
    message = fields.Char(readonly=True)
