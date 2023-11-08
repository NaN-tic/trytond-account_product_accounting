# This file is part account_product_accounting module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pyson import Eval
from trytond.pool import PoolMeta


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'
    account_depreciation = fields.MultiValue(
            fields.Many2One('account.account', "Account Depreciation",
            domain=[
                ('type.fixed_asset', '=', True),
                ('company', '=', Eval('context', {}).get('company', -1)),
            ], states={
                'invisible': (~Eval('context', {}).get('company')
                    | Eval('accounts_category')),
            }, depends=['accounts_category']))
    account_asset = fields.MultiValue(
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
    account_depreciation = fields.Many2One(
            'account.account', "Account Depreciation",
            domain=[
                ('type.fixed_asset', '=', True),
                ('company', '=', Eval('company', -1)),
                ],
            depends=['company'])
    account_asset = fields.Many2One(
            'account.account', "Account Asset",
            domain=[
                ('type.fixed_asset', '=', True),
                ('company', '=', Eval('company', -1)),
                ],
            depends=['company'])


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'
