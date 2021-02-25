# This file is part account_product_accounting module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelSQL, fields
from trytond.pyson import Eval
from trytond import backend
from trytond.pool import PoolMeta, Pool
from trytond.tools.multivalue import migrate_property
from trytond.modules.company.model import (
    CompanyMultiValueMixin, CompanyValueMixin)
from trytond.transaction import Transaction

__all__ = ['Template', 'TemplateAccount', 'TemplateCustomerTax',
    'TemplateSupplierTax']


class Template(CompanyMultiValueMixin, metaclass=PoolMeta):
    __name__ = 'product.template'
    accounts_category = fields.Boolean('Use Category\'s accounts',
            help="Check to use the accounts defined on the account category.")
    accounts = fields.One2Many(
        'product.template.account', 'template', "Accounts")
    account_expense = fields.MultiValue(fields.Many2One('account.account',
            'Account Expense', domain=[
                ('type.expense', '=', True),
                ('company', '=', Eval('context', {}).get('company', -1)),
                ],
            states={
                'invisible': (~Eval('context', {}).get('company')
                    | Eval('accounts_category')),
                },
            help=("The account to use instead of the one defined on the "
                "account category."), depends=['accounts_category']))
    account_revenue = fields.MultiValue(fields.Many2One('account.account',
            'Account Revenue', domain=[
                ('type.revenue', '=', True),
                ('company', '=', Eval('context', {}).get('company', -1)),
                ],
            states={
                'invisible': (~Eval('context', {}).get('company')
                    | Eval('accounts_category')),
                },
            help=("The account to use instead of the one defined on the "
                "account category."), depends=['accounts_category']))
    taxes_category = fields.Boolean('Use Category\'s Taxes',
            help="Check to use the taxes defined on the account category.")
    customer_taxes = fields.Many2Many('product.template-customer-account.tax',
        'product', 'tax', 'Customer Taxes',
        order=[('tax.sequence', 'ASC'), ('tax.id', 'ASC')],
        domain=[('parent', '=', None), ['OR',
                ('group', '=', None),
                ('group.kind', 'in', ['sale', 'both']),
                ],
            ],
        states={
            'invisible': (~Eval('context', {}).get('company')
                | Eval('taxes_category')),
            }, depends=['taxes_category'],
        help="The taxes to apply when selling the product.")
    supplier_taxes = fields.Many2Many('product.template-supplier-account.tax',
        'product', 'tax', 'Supplier Taxes',
        order=[('tax.sequence', 'ASC'), ('tax.id', 'ASC')],
        domain=[('parent', '=', None), ['OR',
                ('group', '=', None),
                ('group.kind', 'in', ['purchase', 'both']),
                ],
            ],
        states={
            'invisible': (~Eval('context', {}).get('company')
                | Eval('taxes_category')),
            }, depends=['taxes_category'],
        help="The taxes to apply when purchasing the product.")
    account_depreciation = fields.MultiValue(fields.Many2One('account.account',
            'Account Depreciation', domain=[
                ('type.fixed_asset', '=', True),
                ('company', '=', Eval('context', {}).get('company', -1)),
                ],
            states={
                'invisible': (~Eval('context', {}).get('company')
                    | Eval('accounts_category')),
                }, depends=['accounts_category']))
    account_asset = fields.MultiValue(fields.Many2One('account.account',
            'Account Asset',
            domain=[
                ('type.fixed_asset', '=', True),
                ('company', '=', Eval('context', {}).get('company', -1)),
                ],
            states={
                'invisible': (~Eval('context', {}).get('company')
                    | Eval('accounts_category')),
                }, depends=['accounts_category']))

    @classmethod
    def __setup__(cls):
        super(Template, cls).__setup__()
        cls.account_category.states['required'] = (
            Eval('accounts_category', False) | Eval('taxes_category', False))
        cls.account_category.depends.extend(
            ['accounts_category', 'taxes_category'])

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')
        cursor = Transaction().connection.cursor()
        pool = Pool()
        Category = pool.get('product.category')
        sql_table = cls.__table__()
        category = Category.__table__()
        table = TableHandler(cls, module_name)
        category_exists = table.column_exist('category')

        # Migration from 3.8: rename account_category into accounts_category
        old_table = 'ir_module_module'
        if (TableHandler.table_exist(old_table)
                and table.column_exist('account_category')
                and not table.column_exist('accounts_category')):
            table.column_rename('account_category', 'accounts_category')

        super(Template, cls).__register__(module_name)

        # Migration from 3.8: duplicate category into account_category
        if category_exists:
            # Only accounting category until now
            cursor.execute(*category.update([category.accounting], [True]))
            cursor.execute(*sql_table.update(
                    [sql_table.account_category],
                    [sql_table.category]))

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field in {'account_expense', 'account_revenue',
                'account_depreciation', 'account_asset'}:
            return pool.get('product.template.account')
        return super(Template, cls).multivalue_model(field)

    @classmethod
    def default_account_expense(cls, **pattern):
        Configuration = Pool().get('account.configuration')
        config = Configuration(1)
        account = config.get_multivalue(
            'default_product_account_expense', **pattern)
        return account.id if account else None

    @classmethod
    def default_account_revenue(cls, **pattern):
        Configuration = Pool().get('account.configuration')
        config = Configuration(1)
        account = config.get_multivalue(
            'default_product_account_revenue', **pattern)
        return account.id if account else None

    @classmethod
    def default_accounts_category(cls):
        Config = Pool().get('product.configuration')
        return Config(1).default_accounts_category

    @classmethod
    def default_taxes_category(cls):
        Config = Pool().get('product.configuration')
        return Config(1).default_taxes_category

    def get_account(self, name, **pattern):
        if self.accounts_category:
            return super(Template, self).get_account(name, **pattern)
        else:
            return self.get_multivalue(name[:-5], **pattern)

    def get_taxes(self, name):
        if self.taxes_category:
            #TODO: try to remove set and list
            taxes = super(Template, self).get_taxes(name)
            if taxes:
                return list(set(taxes))
        if name in ('customer_taxes', 'customer_taxes_used'):
            return self.customer_taxes
        else:
            return self.supplier_taxes


class TemplateAccount(ModelSQL, CompanyValueMixin):
    "Product Template Account"
    __name__ = 'product.template.account'
    template = fields.Many2One(
        'product.template', "Template", ondelete='CASCADE', select=True)
    account_expense = fields.Many2One(
        'account.account', "Account Expense",
        domain=[
            ('type.expense', '=', True),
            ('company', '=', Eval('company', -1)),
            ],
        depends=['company'])
    account_revenue = fields.Many2One(
        'account.account', "Account Revenue",
        domain=[
            ('type.revenue', '=', True),
            ('company', '=', Eval('company', -1)),
            ],
        depends=['company'])
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

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')
        exist = TableHandler.table_exist(cls._table)
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


class TemplateCustomerTax(ModelSQL):
    'Product Template - Customer Tax'
    __name__ = 'product.template-customer-account.tax'
    _table = 'product_customer_taxes_rel'
    product = fields.Many2One('product.template', 'Product Template',
            ondelete='CASCADE', select=True, required=True)
    tax = fields.Many2One('account.tax', 'Tax', ondelete='RESTRICT',
            required=True)


class TemplateSupplierTax(ModelSQL):
    'Product Template - Supplier Tax'
    __name__ = 'product.template-supplier-account.tax'
    _table = 'product_supplier_taxes_rel'
    product = fields.Many2One('product.template', 'Product Template',
            ondelete='CASCADE', select=True, required=True)
    tax = fields.Many2One('account.tax', 'Tax', ondelete='RESTRICT',
            required=True)
