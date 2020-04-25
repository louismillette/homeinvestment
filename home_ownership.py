from classes.Mortgage import Mortgage
from classes.Investment import Investment



def generate_cash_flows():
    pass

'''
rental_property: The money made or lost by an investment property.  
'''
def rental_property(total_years, mortgageable_months, list_price, selling_price_current_year_dollars, sales_tax, monthly_interest_rate,
                    property_tax_rate_yearly, new, down_payment, fixed_closeing_costs, rental_income, percent_time_unit_occupied,taxable_price,
                    maintainance_monthly, condo_fees_monthly, income_tax_rate_company, income_tax_rate_individual):
    M = Mortgage()
    I = Investment()
    variable_closeing_cost_percent = property_tax_rate_yearly / 12 + 0.033 + 0.003 + 0.03
    property_tax_monthly = taxable_price * (property_tax_rate_yearly / 12)
    if down_payment >= 0.2:
        variable_closeing_cost_percent -= 0.03
    if not new:
        sales_tax = 0.0
    first_month_closeing_costs = fixed_closeing_costs + variable_closeing_cost_percent * list_price
    cost = list_price * (1 + sales_tax)
    deductions = maintainance_monthly + property_tax_monthly + condo_fees_monthly
    after_tax_rental_income = rental_income - ((rental_income - deductions) * income_tax_rate_company)
    # (below) interest is calculated elsewhere and already factored in as a cost
    injected_cost_of_home_ownership = (
                                              maintainance_monthly + property_tax_monthly + condo_fees_monthly) - after_tax_rental_income * percent_time_unit_occupied
    _,_,remainint_balance = M.payments(L=cost * (1 - down_payment), c=monthly_interest_rate, n=mortgageable_months )
    cash_flow = M.cash_flows_pad(cost, down_payment, injected_cost_of_home_ownership, monthly_interest_rate, mortgageable_months,
                                d=0, marginal=income_tax_rate_company, total_years=total_years,
                                closing_costs=first_month_closeing_costs)
    i = 0
    zero = [round(ele) for ele in cash_flow][0]
    for ele in [round(ele) for ele in cash_flow][1:]:
        i += 1
        zero += ele
        if zero < 0:
            break
    real_profit = []
    for j in range(len(cash_flow)):
        real_profit += [(-1 * cash_flow[j]) / ((1 + 0.02/12) ** (j + 1))]
    real_profit[-1] += selling_price_current_year_dollars * .95
    real_profit = [round(ele * (1 - income_tax_rate_individual)) for ele in real_profit]
    number_of_months_to_pay_back_initial = i
    nominal_profit = round((sum(cash_flow) * (-1) + selling_price_current_year_dollars * 0.95) * (1 - income_tax_rate_individual))
    I.asset_value(cash_flow, selling_price_current_year_dollars, remainint_balance, income_tax_rate_individual)
    eac_flows_to_consider = [max(ele, 0) for ele in cash_flow]
    '''
    why only consider the cash flow months that are net costs?
    Beacuse the "person" making this investment has to pay those out of pocket.  That person is NOT recieveing any monthly
    payments from net positive months, as those have been re-invested.  So from the perspective of the investor, we only
    consider the times that individual puts money into the investment, or recieves money from it (always, at the very end).
    '''
    eai = round(I.invest(eac_flows_to_consider, real=True)) # equivilent value of investment
    rer = I.re_invested_returns(cash_flow)
    if sum(rer) > 0:
        reinvest = I.invest(I.re_invested_returns(cash_flow))
    else:
        reinvest = sum(rer)
    real_reinvested_profits = round((reinvest + selling_price_current_year_dollars * .95) * (1 - income_tax_rate_individual))
    cash_flow = [(-1) * round(ele) for ele in cash_flow]

    return cash_flow, number_of_months_to_pay_back_initial, nominal_profit, real_profit, eai, real_reinvested_profits


if __name__ == '__main__':
    '''
    These are the closeing costs on a new, $500,000 condo in Toronto
    closing costs:
        - $400-$700 home inspection
        - $1800 in legal fees
        - $300 Title Insurance
        - $1500 Property Survery
        - $1500 Property Tax Adjustment
        - $16950 Land transfer tax
        - $300 Property Tax Adjustment
        - $1200 Tarion fee
        - $13500 CMHC Loan insurance (3%)
    '''

    # cash_flow, number_of_months_to_pay_back_initial, nominal_profit, real_profit, eac, real_reinvested_profits = \
    #     rental_property(total_years=30, mortgageable_months=360, list_price=79000, taxable_price=79000,
    #                 selling_price_current_year_dollars=79000, sales_tax=0.13, monthly_interest_rate=0.0025,
    #                 property_tax_rate_yearly=0.015, new=False, down_payment=0.1,
    #                 fixed_closeing_costs= 400 + 1800 + 300 + 1500 + 1200, rental_income=700, percent_time_unit_occupied=0.75,
    #                 maintainance_monthly=150, condo_fees_monthly=0, income_tax_rate_company=0.15, income_tax_rate_individual=0.2)
    cash_flow, number_of_months_to_pay_back_initial, nominal_profit, real_profit, eac, real_reinvested_profits = \
        rental_property(total_years=30, mortgageable_months=360, list_price=700000, taxable_price=800000,
                    selling_price_current_year_dollars=800000, sales_tax=0.13, monthly_interest_rate=0.0025,
                    property_tax_rate_yearly=0.006, new=False, down_payment=0.1,
                    fixed_closeing_costs= 400 + 1800 + 300 + 1500 + 1200, rental_income=2300, percent_time_unit_occupied=0.95,
                    maintainance_monthly=50, condo_fees_monthly=350, income_tax_rate_company=0.15, income_tax_rate_individual=0.2)

    print(cash_flow)
    print(f'Number of months to pay back initial: {number_of_months_to_pay_back_initial}')
    print(f'NOMINAL profit: {nominal_profit} REAL profit: {sum(real_profit)}')
    print(f'REAL equivelent value of (S&P 500) invested cash flows: {eac}')
    print(f'Real value of reinvested profits, after they cover the down payment cost, plus end cost of apartment: {real_reinvested_profits}')


