from classes.Mortgage import Mortgage
from classes.Investment import Investment



def payback_time(cash_flow):
    number_of_months_to_pay_back_initial = 0
    zero = [round(ele) for ele in cash_flow][0]
    for ele in [round(ele) for ele in cash_flow][1:]:
        number_of_months_to_pay_back_initial += 1
        zero += ele
        if zero >= 0:
            break
    return number_of_months_to_pay_back_initial

def determine_real_profit(cash_flow, selling_price_current_year_dollars, income_tax_rate_individual):
    real_profit = []
    for j in range(len(cash_flow)):
        real_profit += [cash_flow[j] / ((1 + 0.02 / 12) ** (j + 1))]
    real_profit[-1] += selling_price_current_year_dollars * .95
    real_profit = [round(ele * (1 - income_tax_rate_individual)) for ele in real_profit]
    return sum(real_profit)

'''
rental_property: The money made or lost by an investment property.  
'''
def rental_property(total_years, mortgageable_months, list_price, selling_price_current_year_dollars, sales_tax, monthly_interest_rate,
                    property_tax_rate_yearly, new, down_payment, fixed_closeing_costs, rental_income, percent_time_unit_occupied,taxable_price,
                    maintainance_monthly, home_insurance_monthly, condo_fees_monthly, income_tax_rate_company, income_tax_rate_individual):
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
    injected_cost_of_home_ownership = (home_insurance_monthly + maintainance_monthly + property_tax_monthly + condo_fees_monthly) - after_tax_rental_income * percent_time_unit_occupied
    _,_,remainint_balance = M.payments(L=cost * (1 - down_payment), c=monthly_interest_rate, n=mortgageable_months )
    cash_flow = M.cash_flows_pad(cost, down_payment, injected_cost_of_home_ownership, monthly_interest_rate, mortgageable_months,
                                d=0, marginal=income_tax_rate_company, total_years=total_years,
                                closing_costs=first_month_closeing_costs)
    number_of_months_to_pay_back_initial = payback_time(cash_flow)
    real_profit = determine_real_profit(cash_flow, selling_price_current_year_dollars, income_tax_rate_individual)
    nominal_profit = round((sum(cash_flow) + selling_price_current_year_dollars * 0.95) * (1 - income_tax_rate_individual))
    eai = round(I.invest([max((-1) * ele, 0) for ele in cash_flow], real=True))  # equivilent value of investment
    rer = I.invest([max(ele, 0) for ele in cash_flow])
    cash_flow = [round(ele) for ele in cash_flow]
    real_reinvested_profits = round((rer + selling_price_current_year_dollars * .95) * (1 - income_tax_rate_individual))

    # I.asset_value(cash_flow, selling_price_current_year_dollars, remainint_balance, income_tax_rate_individual)

    return cash_flow, number_of_months_to_pay_back_initial, nominal_profit, real_profit, eai, real_reinvested_profits


