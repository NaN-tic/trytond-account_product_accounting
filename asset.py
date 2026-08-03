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
            }))
    account_asset = fields.MultiValue(
            fields.Many2One('account.account', "Account Asset",
            domain=[
                ('type.fixed_asset', '=', True),
                ('company', '=', Eval('context', {}).get('company', -1)),
            ], states={
                'invisible': (~Eval('context', {}).get('company')
                    | Eval('accounts_category')),
            }))


class TemplateAccount(metaclass=PoolMeta):
    __name__ = 'product.template.account'
    account_depreciation = fields.Many2One(
            'account.account', "Account Depreciation",
            domain=[
                ('type.fixed_asset', '=', True),
                ('company', '=', Eval('company', -1)),
                ])
    account_asset = fields.Many2One(
            'account.account', "Account Asset",
            domain=[
                ('type.fixed_asset', '=', True),
                ('company', '=', Eval('company', -1)),
                ])


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'


class Asset(metaclass=PoolMeta):
    __name__ = 'account.asset'

    def get_closing_move(self, account, date=None):
        from trytond.modules.analytic_invoice.asset import Asset as AnalyticAsset

        move = super(AnalyticAsset, self).get_closing_move(account, date=date)
        if not self.analytic_accounts:
            return move
        if not account:
            square_amount = (
                self.value
                - self.get_depreciated_amount()
                - self.depreciated_amount)
            if not square_amount:
                return move
            if square_amount < 0:
                account = self.product.account_revenue_used
            else:
                account = self.product.account_expense_used
        self.set_analytic_lines(move, account)
        return move
