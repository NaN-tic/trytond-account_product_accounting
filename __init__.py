# This file is part account_product_accounting module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import product

def register():
    Pool.register(
        product.Template,
        product.TemplateAccount,
        product.TemplateCustomerTax,
        product.TemplateSupplierTax,
        module='account_product_accounting', type_='model')
