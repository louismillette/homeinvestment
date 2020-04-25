from plugin import plugin
import statistics
import numpy as np
from itertools import zip_longest

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
