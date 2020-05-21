import statistics
import copy
import os
import itertools
import numpy as np

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
        return [-1 * ele for ele in cash_flows]

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