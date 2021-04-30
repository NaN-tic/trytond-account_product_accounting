# This file is part account_product_accounting module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest
from decimal import Decimal

import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool
from trytond.exceptions import UserError

from trytond.modules.company.tests import create_company, set_company
from trytond.modules.account.tests import create_chart


class AccountProductAccountingTestCase(ModuleTestCase):
    'Test Account Product Accounting module'
    module = 'account_product_accounting'

    @with_transaction()
    def test_account_used(self):
        'Test account used'
        pool = Pool()
        ProductTemplate = pool.get('product.template')
        ProductCategory = pool.get('product.category')
        Uom = pool.get('product.uom')
        Account = pool.get('account.account')
        Tax = pool.get('account.tax')

        company = create_company()
        with set_company(company):
            create_chart(company)

            unit, = Uom.search([
                    ('name', '=', 'Unit'),
                    ])
            account_expense, = Account.search([
                    ('type.expense', '=', True),
                    ])
            account_expense2, = Account.copy([account_expense])
            account_revenue, = Account.search([
                    ('type.revenue', '=', True),
                    ])

            account_tax, = Account.search([
                    ('name', '=', 'Main Tax'),
                    ])
            tax, tax2 = Tax.create([{
                    'name': 'Tax 1',
                    'description': 'Tax 1',
                    'type': 'percentage',
                    'rate': Decimal('.10'),
                    'invoice_account': account_tax.id,
                    'credit_note_account': account_tax.id,
                    }, {
                    'name': 'Tax 2',
                    'description': 'Tax 2',
                    'type': 'percentage',
                    'rate': Decimal('.20'),
                    'invoice_account': account_tax.id,
                    'credit_note_account': account_tax.id,
                    }])
            # raise when empty
            template = ProductTemplate(
                name='test account used',
                list_price=Decimal(10),
                default_uom=unit.id,
                products=[],
                accounts_category=False,
                taxes_category=False,
                )
            template.save()

            # check that has not account and taxes
            with self.assertRaises(UserError):
                template.account_expense_used

            self.assertEqual(len(template.customer_taxes_used), 0)

            # set account and taxes on product
            template.customer_taxes = [tax2]
            template.account_expense = account_expense2
            template.save()

            # check that product has account and taxes
            self.assertEqual(template.account_expense_used, account_expense2)
            self.assertEqual(len(template.customer_taxes_used), 1)
            self.assertEqual(template.customer_taxes_used[0], tax2)

            # with account on category
            category = ProductCategory(
                name='test account used',
                accounting=True,
                account_expense=account_expense,
                customer_taxes=[tax],
                )
            category.save()

            # set accounts and taxes from category
            template.account_category = category
            template.accounts_category = True
            template.taxes_category = True
            template.save()

            # check that product has account and taxes
            self.assertEqual(template.account_expense_used, account_expense)
            self.assertEqual(len(template.customer_taxes_used), 1)
            self.assertEqual(template.customer_taxes_used[0], tax)

            # with account on grant category
            parent_category = ProductCategory(
                name='parent account used',
                accounting=True,
                account_expense=account_expense,
                customer_taxes=[tax],
                )
            parent_category.save()
            category.account_expense = None
            category.account_parent = True
            category.taxes_parent = True
            category.parent = parent_category
            category.save()

            self.assertEqual(template.account_expense_used, account_expense)
            self.assertEqual(category.account_expense_used, account_expense)

            # raise only at direct usage
            categories = ProductCategory.create([{
                        'name': 'test with account',
                        'accounting': True,
                        'account_expense': account_expense.id,
                        }, {
                        'name': 'test without account',
                        'accounting': True,
                        'account_expense': None,
                        }])

            self.assertEqual(categories[0].account_expense_used.id,
                account_expense.id)

            with self.assertRaises(UserError):
                categories[1].account_expense_used

            template.account_category = category
            template.accounts_category = False
            template.account_revenue = account_revenue
            template.account_expense = account_expense
            template.taxes_category = False
            template.save()

            self.assertEqual(template.account_revenue_used, account_revenue)
            self.assertEqual(len(template.customer_taxes), 1)
            self.assertEqual(len(template.customer_taxes_used), 1)

def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            AccountProductAccountingTestCase))
    return suite
