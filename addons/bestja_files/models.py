# -*- coding: utf-8 -*-

from openerp import models, fields


class FileCategory(models.Model):
    _name = 'bestja.file_category'
    _order = 'name'

    name = fields.Char(required=True, string=u"Nazwa")


class File(models.Model):
    _name = 'bestja.file'
    _inherit = ['message_template.mixin']

    name = fields.Char(required=True, string=u"Nazwa")
    category = fields.Many2one('bestja.file_category', string=u"Kategoria")
    attachment = fields.Binary(required=True, string=u"Plik")
    filename = fields.Char()
