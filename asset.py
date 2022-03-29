# This file is part account_product_accounting module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pyson import Eval
from trytond import backend
from trytond.pool import PoolMeta
from trytond.tools.multivalue import migrate_property


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'

    @classmethod
    def __setup__(cls):
        super(Template, cls).__setup__()

        cls.account_depreciation = fields.MultiValue(
                fields.Many2One('account.account', "Account Depreciation",
                domain=[
                    ('type.fixed_asset', '=', True),
                    ('company', '=', Eval('context', {}).get('company', -1)),
                ], states={
                    'invisible': (~Eval('context', {}).get('company')
                        | Eval('accounts_category')),
                }, depends=['accounts_category']))

        cls.account_asset = fields.MultiValue(
                fields.Many2One('account.account', "Account Asset",
                domain=[
                    ('type.fixed_asset', '=', True),
                    ('company', '=', Eval('context', {}).get('company', -1)),
                ], states={
                    'invisible': (~Eval('context', {}).get('company')
                        | Eval('accounts_category')),
                }, depends=['accounts_category']))

class TemplateAccount(metaclass=PoolMeta):
    __name__ = 'product.template.account'

    @classmethod
    def __setup__(cls):
        super(TemplateAccount, cls).__setup__()
        cls.account_depreciation = fields.Many2One(
                'account.account', "Account Depreciation",
                domain=[
                    ('type.fixed_asset', '=', True),
                    ('company', '=', Eval('company', -1)),
                    ],
                depends=['company'])
        cls.account_asset = fields.Many2One(
                'account.account', "Account Asset",
                domain=[
                    ('type.fixed_asset', '=', True),
                    ('company', '=', Eval('company', -1)),
                    ],
                depends=['company'])

    @classmethod
    def __register__(cls, module_name):
        exist = backend.TableHandler.table_exist(cls._table)
        if exist:
            table = cls.__table_handler__(module_name)
            exist &= (table.column_exist('account_depreciation')
                and table.column_exist('account_asset'))
        super(TemplateAccount, cls).__register__(module_name)

        if not exist:
            cls._migrate_property([], [], [])

    @classmethod
    def _migrate_property(cls, field_names, value_names, fields):
        field_names.extend(['account_expense', 'account_revenue',
                'account_depreciation', 'account_asset'])
        value_names.extend(['account_expense', 'account_revenue',
                'account_depreciation', 'account_asset'])
        fields.append('company')
        migrate_property(
            'product.template', field_names, cls, value_names,
            parent='template', fields=fields)
