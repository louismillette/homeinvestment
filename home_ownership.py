from plugin import plugin
import statistics
import numpy as np
import itertools
import os
import copy
import math
import statistics
from itertools import zip_longest
import pprint

class Mortgage(object):
    '''
    Mortgage calculates the cash flows associated with home ownership, in NOMINAL dollars (ie literal amount taken out every period, unadjusted), accounting for taxes.
    *** a note about cost of home ownership:  In accordance to the nominal dollar policy stated above, COHO will have to be adjusted up for inflation each year.
        This will be done by calculating each nth year inflation (for each span of 40 yearls, lets say, whats the average 27th year infl rate?)
    '''
    def __init__(self):
        pass

    '''
    infl(self): creates a file of inflation indicies, each index represents that years average inflation.  IOW:
        for year 27, given 219 years of inflation data, looking at every possible 27 year span, what is the average amount of inflation?
    '''
    @staticmethod
    def generate_infl():
        scriptDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(scriptDir, 'inflation.csv'), 'r') as csvFile:
            lines = [ele.replace('\n', '').split(',') for ele in csvFile.readlines()]
            inflation = [float(ele[2].replace('%', ''))/100 for ele in lines[135:]]
        inflation_len,data = len(inflation),[]
        for i in range(1,61):
            iterables = [itertools.islice(iter(copy.deepcopy(inflation)),j,j+i) for j in range(0,inflation_len-i)]
            iterables = [[1 + ele for ele in iterator] for iterator in iterables]
            geometric_means = [(np.product(np.array(iterable)) ** (1/i)) - 1 for iterable in iterables]
            arithmetic_mean = statistics.mean(geometric_means)
            data.append([i,arithmetic_mean])
            print('[+] Done {}'.format(i))
        with open(os.path.join(scriptDir, 'inflation_compounded.csv'), 'w') as csvFile:
            csvFile.write('Compounded Years, Inflation\n')
            for datapoint in data:
                csvFile.write('{}, {}\n'.format(*datapoint))

    '''
        infl(self): pulls from a file of inflation indicies, each index represents that years average inflation.  IOW:
            for year 27, given 219 years of inflation data, looking at every possible 27 year span, what is the average amount of inflation?
    '''
    def infl(self, years):
        scriptDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(scriptDir, 'inflation_compounded.csv'), 'r') as csvFile:
            line = [ele.replace('\n', '').split(',') for ele in csvFile.readlines()][years]
            # print(line[0])
            return ((1 + float(line[1])) ** years)

    '''
    monthly_payments(L,c,n) returns float that is mortgage payment per month.  Actual amount paid, not real dollars 
        L(int): loan ammount
        c(float): interest rate monthly (APR), 5%(yearly) -> 0.00417
        n: number of months
    '''
    def monthly_payments(self,L,c,n):
        return L * ((c * (1+c)**n)/((1+c)**n - 1))

    '''
    payments(L,c,n,d) returns three lists of length <= n (in nominal amounts):
        interest payments: a list of floats that are the amount of interest payed each month
        principle payments: a list of floats that are the amount of principle payed against the outstanding loan each month
        remaining balance: a list of the remaining balance each month 
    payments takes arguments:
        L(int): loan ammount
        c(float): interest rate monthly (APR), 5%(yearly) -> 0.00417
        n(int): number of months
        d(float): additional monthly contributiond to go againt the principle
    '''
    def payments(self,L,c,n,d=0):
        p = self.monthly_payments(L,c,n)
        interest_payments, principle_payments,balance_left,balance_running,period = [], [], [L],L,1
        while balance_running > 0 and period < n+1:
            interest_payment = balance_running * c
            principle_payment = p - interest_payment + d
            balance_running = balance_running - principle_payment
            principle_payments.append(principle_payment)
            interest_payments.append(interest_payment)
            balance_left.append(balance_running)
            period += 1
        return interest_payments, principle_payments,balance_left

    '''
     cash_flows(self,home_price,down_percent,coho,c,n,d=0) returns the list of length <= n (in nominal amounts):
         The amount of money paid each month for the home
     payments takes arguments:
         home_price(int): price of the home
         down_percent(float): down payment percent (20% -> 0.20)
         coho(float): cost of home ownership, per month
         c(float): interest rate monthly (APR), 5%(yearly) -> 0.00417
         n(int): number of months
         d(float): additional monthly contributiond to go againt the principle
         marginal(float): marginal tax rate used for mortgage interest deduction
     Will return a list of length n+1, n monthly payments proceeding a downpayment (the real first payment)
     '''
    def cash_flows(self,home_price,down_percent,coho,c,n,d=0,marginal=0.5,closing_costs=0):
        down = home_price * down_percent
        principle = home_price * (1 - down_percent)
        interest_payments,principle_payments,_ = self.payments(principle,c,n,d)
        total_payments = [(interest_payments[i])*(1-marginal) + principle_payments[i] + self.infl((i // 12) + 1) * coho
                          for i in range(len(interest_payments))]
        total_payments[0] += down
        total_payments[0] += closing_costs
        return total_payments

    '''
     cash_flows_pad(self,home_price,down_percent,coho,c,n,d=0,total_years) returns the list of length = total_years (in nominal amounts):
         The amount of money paid each month for the home, for the duration of total_years.  After the home has been paid off, the remaining outflows are equal to coho.
     payments takes arguments:
         home_price(int): price of the home
         down_percent(float): down payment percent (20% -> 0.20)
         coho(float): cost of home ownership, per month
         c(float): interest rate monthly (APR), 5%(yearly) -> 0.00417
         n(int): number of months in mortgage
         d(float): additional monthly contributiond to go againt the principle
         marginal(float): marginal tax rate used for mortgage interest deduction
     '''
    def cash_flows_pad(self,home_price,down_percent,coho,c,n,d=0,marginal=0.5,total_years=0,closing_costs=0):
        cash_flows = self.cash_flows(home_price,down_percent,coho,c,n,d,marginal,closing_costs)
        total_months = total_years * 12
        if len(cash_flows) < total_months:
            remaining_months = range(len(cash_flows), total_months + 1)
            for month in remaining_months:
                cash_flows += [coho * self.infl((month // 12) + 1)]
        return cash_flows

    '''
     rent(self, years, monthly_rent): 
         calculates the total (nominal) amount of rent paid over the given number of years, adjusted for inflation
     payments takes arguments:
         years(int): number of years rent is being paid for
         monthly_rent(int): amount of rent paid in first year (each year this amount is updated for inflation) ie real rent
     '''
    def rent(self, years, monthly_rent):
        yearly_payments = [monthly_rent * 12 * self.infl(ele) for ele in range(1, years+1)]
        monthly_payments = [y for x in [[ele/12] * 12 for ele in yearly_payments] for y in x]
        return monthly_payments

class Investment(object):
    '''
    Investment: takes the cash flows associated with home ownership or rental income, in NOMINAL dollars (ie literal amount taken out every period, unadjusted), accounting for taxes,
                and invests them in the S&P500 at vangaurds fees, returning the end value in base year dollars
    '''
    def __init__(self):
        H = plugin.Handler()
        self.data1 = H.generate(all=True, base='S and P 500')

    # takes a list of size > grouping, and splits it into grouping size sup lists
    def condense(self,lst, grouping):
        split_payments = zip_longest(*[iter(lst)] * grouping, fillvalue=0)
        return [sum(ele) for ele in split_payments]

    def invest(self, nominal_cash_flows, metric='mean', quartile=50, state='ontario', income=53000, fee=0.0005, filing='single', real=True):
        nominal_cash_flows = self.condense(nominal_cash_flows, 12)
        H = plugin.Handler()
        mdata, all_tax, all_fees, all_contributions = H.MultiplierPeriod(data=self.data1, state=state, income=income,
                                                                         contributions=nominal_cash_flows, fee=fee,
                                                                         filing=filing, taxdef=False, span=len(nominal_cash_flows) - 1,
                                                                         real=real)
        if metric == 'mean':
            return statistics.mean([ele[1] for ele in mdata])
        elif metric == 'median':
            return statistics.median([ele[1] for ele in mdata])
        elif metric == 'quartile':
            return np.percentile(np.array([ele[1] for ele in mdata]), quartile)

    # this function re-calculates cash flows.  It assumes you
    # lend youself all the negative returns, including the down payment, at 0% interest, and then pay back that loan with immediate future returns.
    # this function takes the cash flow returned by cash_flows_pad or rent and returns the new cash flow of positive returns
    def re_invested_returns(self, cash_flow):
        new_cash_flow = [-1 * ele for ele in cash_flow]
        if sum(new_cash_flow) < 0:
            return new_cash_flow
        negative_returns = (-1) * sum(filter(lambda x: x < 0, new_cash_flow))
        new_cash_flow = [max(ele, 0) for ele in new_cash_flow]
        return new_cash_flow
        i = 0
        while i < len(cash_flow):
            if new_cash_flow[i] == 0:
                i += 1
                continue
            if negative_returns > 0:
                if negative_returns < new_cash_flow[i]:
                    new_cash_flow[i] -= negative_returns
                    negative_returns = 0
                else:
                    negative_returns -= new_cash_flow[i]
                    new_cash_flow[i] = 0
            i += 1
        return new_cash_flow

    # returns the real value of the investment if property is sold in each year.
    def asset_value(self, cash_flows, selling_price_current_year_dollars, remainint_balances, income_tax_rate_individual):
        cash_flow_months = len(cash_flows)
        real_reinvested_profits = []
        for i in range(cash_flow_months):
            if sum(cash_flows[:i+1]) > 0:
                rer = -sum(cash_flows[:i+1])
            else:
                rer = round(self.invest(self.re_invested_returns(cash_flows[:i + 1])))
            real_reinvested_profits += [round((rer + selling_price_current_year_dollars * .95 - remainint_balances[i]) * (1 - income_tax_rate_individual))]
        c = 0
        for j in range(len(real_reinvested_profits)):
            c += 1
            if real_reinvested_profits[j] > 0:
                break
        print(real_reinvested_profits)
        return real_reinvested_profits

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


