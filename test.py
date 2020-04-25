import awslambda
import unittest
import home_ownership

class TestRentalProperty(unittest.TestCase):
    cash_flow, number_of_months_to_pay_back_initial, nominal_profit, real_profit, eac, real_reinvested_profits = \
        rental_property(total_years=30, mortgageable_months=360, list_price=700000, taxable_price=800000,
                        selling_price_current_year_dollars=800000, sales_tax=0.13, monthly_interest_rate=0.0025,
                        property_tax_rate_yearly=0.006, new=False, down_payment=0.1,
                        fixed_closeing_costs=400 + 1800 + 300 + 1500 + 1200, rental_income=2300,
                        percent_time_unit_occupied=0.95,
                        maintainance_monthly=50, condo_fees_monthly=350, income_tax_rate_company=0.15,
                        income_tax_rate_individual=0.2)

    pprint.pprint(cash_flow)
    print(f'Number of months to pay back initial: {number_of_months_to_pay_back_initial}')
    print(f'NOMINAL profit: {nominal_profit} REAL profit: {sum(real_profit)}')
    print(f'REAL equivelent value of (S&P 500) invested cash flows: {eac}')
    print(
        f'Real value of reinvested profits, after they cover the down payment cost, plus end cost of apartment: {real_reinvested_profits}')

class Test(unittest.TestCase):
    def test_regular_cases(self):
        event = {
            'queryStringParameters': {
                'callback': 'func(10,20,',
                'home_price': 240000,
                'down_percent': 0.2,
                'coho': 50,
                'c': 0.00417,
                'n': 420,
                'd': 200,
                'marginal': 0.30,
                'metric': 'median',
                'quartile': 20,
                'state': 'Ohio',
                'fee': 0.0005,
                'filing': 'single',
                'real': True
            }
        }
        print(awslambda.lambda_handler(event,None))

if __name__ == '__main__':
    T = Test()
    for attribute in dir(Test):
        stringattr = str(attribute)
        if len(stringattr) < 4:
            continue
        elif stringattr[:4] == 'test':
            print('[TEST] Calling {}'.format(stringattr))
            getattr(T, stringattr)()