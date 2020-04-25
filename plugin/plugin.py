import os
import re
import time
import random
from datetime import datetime
from datetime import timedelta
import math
import json
from functools import reduce
import operator
from dateutil.relativedelta import relativedelta

'''
compunds interest rate.  Returns list of compounded interest rate for all n periods
product from i to n of IR(i) for all i from 1 to n.  O(n) time
'''
def IRcompunder(alpha, fee, n):
    i = n - 1
    IRs = []
    running = 1
    while i >= 0:
        running *= alpha(i) * fee(i)
        IRs.append(running)
        i -= 1
    return list(reversed(IRs))

'''
compund(A, alpha, infl, CGtaxes, dividends, divtaxes, fees, n,comma = True) -> <int>
    A:  A function that takes one argument, time, and gives back how much is entering the fund
        at the given time
    alpha: A function that takes one argument, time, and returns the interest rate for that
        time
    dividends:  A function that takes time, and returns the dividend yield percentage
    n:  The amount of time compounding (number of periods)
    infl:  A function that takes one argument, time, and gives back how much inflation is that period
    CGtaxes: the nominal tax rate on each contribution when removed
    divtaxes: tax rate on dividends earned in each period. function of period (n), optional argument t:
              total dividends being paid on, and optional argument inn: amount of other income in this period
    inflMultiplier: inflation multiplier for calculating taxes:  list that contains, for each compounding period,
                    how much money in that period is worth in todays terms (today being the last entry of inflation
                    in the inflation csv)

    All rates are to be given in the form of 1.06, for a rate of 6%.
    In the last year, it will not add money.
    Compounds from beggining of given year through end of last year given. A will be indexed one level higher then
    the rest of the functions, everything is compounded between money inputs into the fund.
    Money (A) is put in as if it were in todays CPI, and the inflation and interest rates from whatever time period are applied
    to it, accounting for inflation that occurs over the time period.
'''
def compund(A, alpha, infl, CGtaxes, dividends, divtaxes, fees, n, comma=True, real=True):

    # product of interest rates(calculate in memory to keep runtime O(n))
    int_rep = int(n)
    poi = IRcompunder(alpha, fees, n)
    s = A(0)
    all_taxes,all_fees, div_acc, infl_so_far, contributions = 0,0,[0],1,0
    # contribution-interest accumulation
    m,taxable_gains = 0,0
    while m < int_rep:
        # this is so we can actively regress our true tax payment brackets back to the base year
        # we are not accounting for inflaion here per period, we are only useing this to account for tax brackets adjusting to inflation
        infl_so_far *= infl(m)
        # we aren't adding any money in at the end of the last period.
        # dividend taxes are paid as they are recieved
        if m == int_rep-1:
            div = dividends(m) * float(s)
            divtax = div * (divtaxes(m, t=div, multiplier=1/infl_so_far) - 1)
            s = (s * alpha(m) + div - divtax) * fees(m)
            all_taxes += divtax / infl_so_far
            all_fees += s * alpha(m) * (1 - fees(m)) / infl_so_far
        else:
            div = dividends(m) * s
            divtax = div * (divtaxes(m, t=div, multiplier=1/infl_so_far) - 1)
            s = (s * alpha(m) + div - divtax) * fees(m) + float(A(m+1))*infl_so_far  # fees applied after div tax (assumption)
            all_taxes += divtax / infl_so_far
            all_fees += (s * alpha(m) + div - divtax) * (1 - fees(m)) / infl_so_far
            div_acc.append(div - divtax) # we'll pay CG taxes on div reinvestement
        # we won't tax dividends again.
        contributions += float(A(m + 1)) # we're adding the same amount in base year dollars every year
        taxable_gains += (float(A(m+1))*infl_so_far + div_acc[m]) * (poi[m] - 1)
        m += 1
    # tax calculations (CG tax, div tax already accounted for)
    CGtax = taxable_gains * (CGtaxes(taxable_gains, multiplier=1/infl_so_far)-1)
    CGtax = CGtax if CGtax > 0 else 0
    # print("Paid {} total in capital gains taxes".format(CGtax))
    all_taxes += CGtax/infl_so_far
    # print('paid {:,} in Capital Gains'.format(round(CGtax,2)))
    no_infl_total = round(s - CGtax, 2)
    if real:
        total = round(no_infl_total / infl_so_far, 2)
    else:
        total = no_infl_total
    contributions = round(contributions, 2)
    if comma == True:
        return "{:,}".format(total)
    return total,all_taxes,all_fees, contributions

'''
buildFund takes average yearly compounded rates, and fills in missing years, returning a "best guess" as
to what the returns look like.
Fundreturns: <dict> {1987:.059, 2017:.07, ...} keys are the year-to-present average compound returns
         if the last year returns were 7%, it would be key:value of 2017:.07
returns: list of dict: [{"Date":1970-07-20, "Relevent Returns":.05},...]
'''
def buildFund(Fundreturns):
    dates = list(reversed(sorted(Fundreturns.keys())))
    leng = int(dates[0]) - int(dates[-1]) + 1
    keys = [str(ele) for ele in range(int(dates[-1]), int(dates[0]) + 1)]
    returns = dict(zip(keys,[1 for _ in range(leng)]))
    returns[dates[0]] = Fundreturns[dates[0]]
    i = 0
    while i < len(dates):
        i += 1
        try:
            dates[i]
        except:
            break
        compounding = list(range(int(dates[i]), int(dates[0]) + 1))
        ret =  {k: v for k, v in returns.items() if int(k) in compounding} # dict of our compounding dates
        phi =  {k: v for k, v in ret.items() if v != 1} # dict of dates already processed by earlier compounding averages
        unass_dates = [k for k, v in ret.items() if v == 1]
        num = len(compounding) * (Fundreturns[dates[i]] - 1) + 1
        denom = reduce(operator.mul, phi.values())
        m = num/denom
        rate = round(m**(1/(len(unass_dates))),7)
        for date in unass_dates:
            returns[date] = rate
    retFormat = []
    for k,v in returns.items():
        retFormat.append({"Date":k + '-12-01', "Return Percent":v-1, "Dividend Yield": 0})
    return retFormat

'''
annuity(A, alpha, infl, CGtaxes, dividends, divtaxes, fees, n,comma = True) -> <int>
    P:  An int, the amount (in base year dollars) to be withdrawn each year.
    alpha: A function that takes one argument, time, and returns the interest rate for that
        time
    dividends:  A function that takes time, and returns the dividend yield percentage
    n:  The amount of time compounding (number of periods)
    infl:  A function that takes one argument, time, and gives back how much inflation is that period
    CGtaxes: the nominal tax rate on each contribution (to be given in base year dollars) when removed
    divtaxes: function of a: amount of money in base year dollars.  Returns taxes in base year dollars
    fees: function that takes time, and returns fee percent in that period.
    inflMultiplier: (list of int) product of inflations up to the length of the list for each point in the list.
                    first will be I1 2nd with be I1*I2, and last will be I1*I2*...*In.
    alphaMultiplier: (list of int) product of returns up to the length of the list for each point in the list.
                first will be a1 2nd with be a1*a2, and last will be a1*a2*...*an.

    - All rates are to be given in the form of 1.06, for a rate of 6%.
    - Starts removing amount yearly, starting after first appreciation and dividend payment.
    - Money removed in each period is adjusted for inflation.  That is, the calculator will assume that
      in the last period, your taking out what you took out in the first period, adjusted for n years of inflation.
    - Anuity is a class instead of a function becuase of the number of moving parts and helpers.  The init, however,
      acts as a function, executing appropriate functions internally and setting the result
'''
class Annuity():
    def __init__(self, P, alpha, dividends, n, infl, CGtaxes, divtaxes, fees):
        # create class variables
        self.alpha = alpha
        self.dividends = dividends
        self.n = n
        self.infl = infl
        self.CGtaxes = CGtaxes
        self.divtaxes = divtaxes
        self.fees = fees
        if n <= 10:
            self.acc = 1
        elif n <= 20:
            self.acc = 10
        else:
            self.acc = 100
        # generate psi/phi
        self.phi = [infl(0)]
        for i in range(1,n):
            self.phi.append(self.phi[i-1]*infl(i))
        # generate A, the amount to take out every time before inflation
        self.A = P
        for i in range(5):
            # 20 is arbitrary, simply a measure of accuracy
            self.A = P + CGtaxes(self.A,1)
        self.total_cg_paid = P - self.A

    # finds good solution in log time, returns that solution
    # we'll take advantage of the strictly increaseing nature of the LHS function
    # our guess's will take O(nlogm) for m "level of percision"
    def gen_annuity(self):
        lowInitial = self.A/2  # a reasonable lowest guess of the anuitys value
        highInitial = self.A * self.n * 10  # 10 times how much we're taking out.  Very high.
        lowGuess,_,_ = self.checkAnnuityValue(lowInitial)
        highGuess,_,_ = self.checkAnnuityValue(highInitial)
        count = 0
        while 1:
            count += 1
            newInitial = (lowInitial+highInitial)/2
            newGuess,this_tax,this_fee = self.checkAnnuityValue(newInitial)
            # print(newInitial, newGuess)
            if newGuess <= 0 <= highGuess:
                lowInitial = newInitial
            else:
                highInitial = newInitial
            # precision down to 1/1000 of a cent.  We can change this precision to improve performance
            if abs(newGuess) < self.acc:
                return newInitial,this_tax,this_fee

    # uses clas sprovided methods to check that the value of the lump sum annuity is truely 0 after the appropriate period
    def checkAnnuityValue(self, ANR):
        balance = ANR
        total_tax = 0
        total_fee = 0
        for period in range(self.n):
            balance *= self.alpha(period) # first apply growth
            div = self.dividends(period) * balance
            div_tax = self.divtaxes(div,self.phi[period])
            fee = (self.fees(balance) - 1) * balance
            total_fee += fee
            A = self.A * self.phi[period]
            total_tax += div_tax
            total_tax += self.total_cg_paid * self.phi[period]
            balance = balance - fee - A - div_tax + div
        return balance, total_tax, total_fee

# handle requests.  Spit out requested values
class Handler():
    def __init__(self):
        pass
        self.scriptdir = os.path.dirname(os.path.abspath(__file__))
        self.sandp = self.loadSandP()
        self.Inflation = self.loadInflation()
        self.federal = None
        self.state = None

    # loads taxes data from given file (in script dir)
    def loadTaxes(self, filename='state.txt'):
        with open(os.path.join(self.scriptdir, filename), 'r') as file:
            line = file.readline()
            return (json.loads(line))

    '''
    compunds inflation rates.  Returns list of compounded inflation rates rate for all n periods
    returns list of compounded rates from year frm to present to year to to present
    O(n) time
    frm,to are intigers and infl is a list of inflation rates
    '''
    def INFLcompounder(self,frm, to):
        infl_index = []
        infl = sorted(
            list(filter(lambda x: frm <= int(x['Year']), self.Inflation)),
            key=lambda x: x['Year'])
        infl = [float(ele['Inflation'].replace('%',''))/100 for ele in infl]
        gap, mult, infl_len = (to - frm), 1, len(infl)  # multiplier here is the smallest multiplier (to - present)
        while gap < infl_len:
            mult *= (1 + infl[gap])
            gap += 1
        infl_index.append(mult)
        gap = to - frm - 1
        while gap > 0:
            mult *= (1 + infl[gap])
            infl_index.append(mult)
            gap -= 1
        return list(reversed(infl_index))

    '''
    Takes income (int), taxable (capitol gains that are taxable),
    taxes (tax brackets): {"0":1.0, "5000":3.0,...}; lower range of braket is key, value is percent taxed
    brackets (list): ["0","5000", ...] list of keys for taxes, MUST BE ORDERED
    '''
    def _braket(self, income, taxable, brackets, taxes):
        i, tax, val = 0, 0, brackets[0]
        while val < income + taxable:
            try:
                val = brackets[i + 1]
            except:
                bottom = max(val, income)
                top = income + taxable
                multiplier = taxes[str(int(brackets[i]))] / 100
                tax += (top - bottom) * multiplier
                break
            i += 1
            if (val <= income):
                # none of our taxable is in this bracket
                continue
            else:
                if val < income + taxable:
                    top = val
                else:
                    top = income + taxable
                if (brackets[i - 1] < income):
                    bottom = income
                else:
                    bottom = brackets[i - 1]
                multiplier = taxes[str(int(brackets[i - 1]))] / 100
                tax += (top - bottom) * multiplier
        return tax

    '''
    Takes state (string), income (number), and taxable capital gains (intiger)
    Returns the tax on this
    '''
    def taxApplicable(self, state, income, taxable, filing="single", candiv=False):
        if not self.federal:
            self.federal = self.loadTaxes('federal.txt')
        if not self.state:
            self.state = self.loadTaxes('state.txt')
        if state == "ontario":
            pass
            states_taxes = self.state['ontario_single']
            federal_taxes = self.state['canada_single']
            if not candiv:
                taxable = taxable/2
        else:
            getname = state + '_' + filing
            federal_taxes = self.federal[filing]
            states_taxes = self.state[getname]
        state_brackets = sorted([float(ele) for ele in states_taxes.keys()])
        federal_brackets = sorted([float(ele) for ele in federal_taxes.keys()])
        state_tax = self._braket(income, taxable, state_brackets, states_taxes)
        federal_tax = self._braket(income, taxable, federal_brackets, federal_taxes)
        return state_tax + federal_tax

    # laod in the S and P 500 data csv as a dictionary
    def loadSandP(self):
        with open(os.path.join(self.scriptdir, 'SandP.csv'), 'r') as csvFile:
            lines = [ele.replace('\n', '').split(',') for ele in csvFile.readlines()]
            labels = lines[0]
            stockValues = [dict(zip(labels, ele)) for ele in lines[1:]]
        return stockValues

    # load in the inflation data csv as a dictionary
    def loadInflation(self):
        scriptDir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(scriptDir, 'inflation.csv'), 'r') as csvFile:
            lines = [ele.replace('\n', '').split(',') for ele in csvFile.readlines()]
            labels = lines[0]
            inflation = [dict(zip(labels, ele)) for ele in lines[1:]]
        return inflation

    '''
    get auxillary values takes a list of relevent returns, and produces a list of relevent inflation
    corresponding 1-1 with the relevent returns dates.  assumes there are no missing data points
    works in nlogn time (sorting time eff)
    '''
    def getAuxVals(self, releventReturns):
        n = len(releventReturns)
        RRS = sorted(releventReturns, key=lambda x: datetime.strptime(x['Date'], '%Y-%m-%d'))
        RRSyears = [datetime.strptime(ele['Date'], '%Y-%m-%d').year for ele in RRS]
        start = RRSyears[0]
        end = RRSyears[-1]
        infl = sorted(
            list(filter(lambda x: end >= int(x['Year']) >= start, self.Inflation)),
            key=lambda x: x['Year'])
        mini = int(infl[0]['Year'])
        maxi = int(infl[-1]['Year'])
        infloffset = 0
        allinfl = {}
        for ret in range(n):
            if RRSyears[ret] < mini:
                allinfl[RRSyears[ret]] = None
                infloffset += 1
            elif RRSyears[ret] > maxi:
                # no offset here.  If we are beyond the range of our infl, we wont be in range of them at any futuree point
                allinfl[RRSyears[ret]] = None
            else:
                allinfl[RRSyears[ret]] = 1 + float(infl[ret - infloffset]['Inflation'].replace('%', '')) / 100
        return allinfl

    # given years a and b, and year span span, returns every year range of length span between a and b
    def ranges(self, data, span):
        rngs, start, end, leng = [], 0, span, len(data)
        while end <= leng:
            rngs.append(data[start:end])
            start += 1
            end += 1
        return rngs

    # takes a fund name, returns fund returns
    def _getfund(self,fund):
        if fund == 'S and P 500':
            return self.sandp
        if fund == 'CIBC Balanced Fund':
            return buildFund({'2015':1.0355, '2016':1.0529, '2017':1.0584, '2014':1.0457, '2013':1.0573, '2008':1.0303,
                              '1988':1.059, '2003':1.0495, '1998':1.0383})
        if fund == 'CIBC Canadian Index Fund':
            return buildFund({'2017':1.1026, '2016':1.1082, '2015':1.0505, '2014':1.0658, '2013':1.0723, '2008':1.0287,
                              '2003':1.0827, '1998':1.0581, '1996':1.0717})
        if fund == 'CIBC U.S Broad Market Index Fund':
            return buildFund({'2017':1.1744, '2016':1.1131, '2015':1.1308, '2014':1.16, '2013':1.1928, '2008':1.0969,
                              '2003':1.0734, '1998':1.0583, '1991':1.0802})

        if fund == 'CIBC Canadian Small-Cap Fund':
            return buildFund({'2017':.985, '2016':1.051, '2015':1.0182, '2014':1.0249, '2013':1.0339, '2008':1.0229,
                              '2003':1.0678, '1998':1.05, '1991':1.0734})

    '''
    picks a n year span, returns inflation, s and p growth, and dividends for each year in the given span
    [ { 'year':year, 'inflation':inflation', 'interest':interest, 'dividend':dividend}, ...]
    O(nlogn).
    '''
    def generate(self, all=False, n=40, to=None, frm=None, base=None):
        if not base:
            stockValues = self.sandp
        else:
            stockValues = self._getfund(base)
        if not all:
            year = random.randint(a=1940, b=2015 - n)
            to = to if to else datetime.strptime('{}-01-01'.format(year + n), '%Y-%m-%d')
            frm = frm if frm else datetime.strptime('{}-01-01'.format(year), '%Y-%m-%d')
            to = datetime(year=to.year+1, month=to.month, day=to.day)
            releventReturns = list(filter(lambda x: to > datetime.strptime(x['Date'], '%Y-%m-%d') > frm and datetime.strptime(x['Date'], '%Y-%m-%d').month == 12, stockValues))
        else:
            releventReturns = list(filter(lambda x: datetime.strptime(x['Date'], '%Y-%m-%d').month == 12, stockValues))
        obs = []
        infl = self.getAuxVals(releventReturns)
        rng = range(len(releventReturns))
        for index in rng:
            releventReturn = releventReturns[index]
            inflation = infl[datetime.strptime(releventReturn['Date'], '%Y-%m-%d').year]
            obs.append({
                'year': datetime.strptime(releventReturn['Date'], '%Y-%m-%d').year,
                'inflation': inflation,
                'interest': 1 + float(releventReturn['Return Percent']),
                'dividend': float(releventReturn['Dividend Yield'])
            })
        return obs

    '''
    given the data (format of genmerate above), state (string, valid, lower case), an optional
    income: float/int the yesarly income, to be used for tax purposes
    filing: string, single or marries , to be used for tax purposes
    fee: float, marginal equity ratio
    contributions: float/int, how much is invested each year
    taxdef: bool, is this fund tax deffered (401k, no taxes applied), or not (regulaar CG taxes applied)?
    returns 3 lists:- Money made, taxes paid, and fees paid.  Each element of each list is a list of 2: year, number applied if all is removed in that year:
                    - [[1970,12000],[1971, 13400],...]<money>, [[1970,1200],[1971, 1340],...]<taxes>, [[1970,120],[1971, 134],...]<fees> for example.
                    - Goes from the first date in the data provided to the each date in data (each list has len equal to length of data)
                    - each element of each list is the appropriate value starting at the beggining of the first date, and ending at the end of the given date.

    '''
    def Multiplier(self, data, state, income=None, filing=None, fee=None, contributions = None, taxdef=False):
        data = sorted(data, key=lambda x: datetime(year=x['year'], month=1, day=1))
        frm = data[0]
        # not quite a decorator.  we want to run this on functions, changeing the data we give to them.
        def sudodec(function, data):
            def wrap(n):
                return function(n, data)

            return wrap

        def A(n):
            # print(n)
            return contributions[n]

        def alpha(n, data):
            return data[n]['interest']

        def infl(n, data):
            return data[n]['inflation']

        def CGtaxes(taxable_gains, multiplier):
            if taxable_gains == 0:
                return 0
            if not taxdef:
                inflated_tg = taxable_gains * multiplier
                tax = self.taxApplicable(state=state, income=income if income else 0, taxable=inflated_tg, filing=filing)
                return 1 + (tax / inflated_tg)
            else:
                return 1

        def dividends(n, data):
            return data[n]['dividend']

        def fees(n):
            if fee:
                return 1 - fee
            else:
                return 1 - .0005  # typical vangaurd fee

        def divtaxes(n, t, multiplier):
            if t == 0.0:
                return 0
            if not taxdef:
                inflated_tg = t * multiplier
                tax = self.taxApplicable(state=state, income=income if income else 0, taxable=inflated_tg, filing=filing, candiv=True)
                if state == 'ontario':
                    tax_credit = 0.207*(t*multiplier)
                    tax -= tax_credit
                return 1 + (tax / inflated_tg)
            else:
                return 1


        all_moneys,all_taxes,all_fees, all_contributions = [],[],[],[]
        for to in data:
            yearfrm = datetime(year=frm['year'], month=1, day=1)
            yearto = datetime(year=to['year']+1, month=1, day=1)
            if yearfrm > yearto:
                continue
            else:
                indexfrm = data.index(frm)
                indexto = data.index(to)
                newdata = data[indexfrm:indexto + 1]
                multiplier, this_tax, this_fee, this_contributions = compund(A,
                                                         sudodec(alpha, newdata),
                                                         sudodec(infl, newdata),
                                                         CGtaxes, sudodec(dividends, newdata),
                                                         divtaxes, fees, len(newdata), comma=False)

                all_moneys.append([str(to['year']) + "/01/01",multiplier])
                all_taxes.append([str(to['year']) + "/01/01", this_tax])
                all_fees.append([str(to['year']) + "/01/01", this_fee])
                all_contributions.append([str(to['year']) + "/01/01", this_contributions])
        return all_moneys,all_taxes,all_fees,all_contributions

    '''
    given the data (format of genmerate above), state (string, valid, lower case), an optional
    income: float/int the yesarly income, to be used for tax purposes
    filing: string, single or marries , to be used for tax purposes
    fee: float, marginal equity ratio
    contributions: float/int, how much is invested each year
    taxdef: bool, is this fund tax deffered (401k, no taxes applied), or not (regulaar CG taxes applied)?
    returns 3 lists:- Money made, taxes paid, and fees paid.  Each element of each list is a list of 2: year, number applied if all is removed in that year:
                    - [[1970,12000],[1971, 13400],...]<money>, [[1970,1200],[1971, 1340],...]<taxes>, [[1970,120],[1971, 134],...]<fees> for example.
                    - Returns every <span> year return in the data (length of returned data is length of given data minus span)
                    - each element of each list is the appropriate value starting at the beggining of the first date, and ending at the end of the appropriate date.

    '''
    def MultiplierPeriod(self, data, state, span=40, income=None, filing=None, fee=None, contributions = None, taxdef=False, real=True):
        data = sorted(data, key=lambda x: datetime(year=x['year'], month=1, day=1))
        # not quite a decorator.  we want to run this on functions, changeing the data we give to them.
        def sudodec(function, data):
            def wrap(n):
                return function(n, data)
            return wrap

        def A(n):
            return contributions[n]

        def alpha(n, data):
            return data[n]['interest']

        def infl(n, data):
            return data[n]['inflation']

        def CGtaxes(taxable_gains, multiplier):
            if taxable_gains == 0:
                return 0
            if not taxdef:
                inflated_tg = taxable_gains * multiplier
                tax = self.taxApplicable(state=state, income=income * (1/multiplier) if income else 0, taxable=inflated_tg, filing=filing)
                return 1 + (tax / inflated_tg)
            else:
                return 1

        def dividends(n, data):
            return data[n]['dividend']

        def fees(n):
            if fee:
                return 1 - fee
            else:
                return 1 - .0005  # typical vangaurd fee

        def divtaxes(n, t, multiplier):
            if t == 0.0:
                return 0
            if not taxdef:
                inflated_tg = t * multiplier
                tax = self.taxApplicable(state=state, income=income * (1/multiplier) if income else 0, taxable=inflated_tg, filing=filing)
                return 1 + (tax / inflated_tg)
            else:
                return 1

        all_moneys,all_taxes,all_fees, all_contributions = [],[],[],[]
        datarange = self.ranges(data, span)
        for rng in datarange:
            multiplier,this_tax,this_fee, this_contributions = compund(A,
                                 sudodec(alpha, rng),
                                 sudodec(infl, rng),
                                 CGtaxes, sudodec(dividends, rng),
                                 divtaxes, fees, len(rng), comma=False, real=real)

            all_moneys.append([str(rng[0]['year']) + "/01/01",multiplier])
            all_taxes.append([str(rng[0]['year']) + "/01/01", this_tax])
            all_fees.append([str(rng[0]['year']) + "/01/01", this_fee])
            all_contributions.append([str(rng[0]['year']) + "/01/01", this_contributions])
        return all_moneys,all_taxes,all_fees,all_contributions


    '''
    given the data (format of genmerate above), state (string, valid, lower case),
    income: float/int the yearly income, to be used for tax purposes
    filing: string, single or marries , to be used for tax purposes
    fee: float, marginal equity ratio
    wd: withdrawels made each year
    span: number of years annuity will be paid over
    returns 3 lists:- Money made, taxes paid, and fees paid.  Each element of each list is a list of 2: year, number applied if all is removed in that year:
                    - [[1970,12000],[1971, 13400],...]<money>, [[1970,1200],[1971, 1340],...]<taxes>, [[1970,120],[1971, 134],...]<fees> for example.
                    - Returns every <span> year return in the data (length of returned data is length of given data minus span)
                    - each element of each list is the appropriate value starting at the beggining of the first date, and ending at the end of the appropriate date.
    '''
    def MultiplierAnnuityPeriod(self, data, state, wd, span=40, income=None, filing=None, fee=None):
        data = sorted(data, key=lambda x: datetime(year=x['year'], month=1, day=1))
        # not quite a decorator.  we want to run this on functions, changeing the data we give to them.
        def sudodec(function, data):
            def wrap(n):
                return function(n, data)

            return wrap

        def alpha(n, data):
            return data[n]['interest']

        def infl(n, data):
            return data[n]['inflation']

        def CGtaxes(taxable_gains, multiplier):
            if taxable_gains == 0:
                return 0
            taxable_gains = taxable_gains / multiplier
            tax = self.taxApplicable(state=state, income=income / multiplier if income else 0,
                                     taxable=taxable_gains / multiplier, filing=filing)
            return tax * multiplier

        def dividends(n, data):
            return data[n]['dividend']
        # fees are calculated differently, with 1.05 being a fee of 5%
        # will still take the .05 for the 5% fee
        def fees(n):
            if fee:
                return 1 + fee
            else:
                return 1 + .0005  # typical vangaurd fee

        def divtaxes(taxable_gains, multiplier):
            if taxable_gains == 0:
                return 0
            taxable_gains = taxable_gains / multiplier
            tax = self.taxApplicable(state=state, income=income / multiplier if income else 0,
                                     taxable=taxable_gains / multiplier, filing=filing)
            return tax * multiplier

        all_wd, all_taxes, all_fees = [], [], []
        datarange = self.ranges(data, span)
        if len(datarange) > 50:
            random.shuffle(datarange)
            datarange = sorted(datarange[:50], key = lambda x: x[0]['year'])
        for rng in datarange:
            A = Annuity(P=wd,alpha=sudodec(alpha, rng),dividends=sudodec(dividends, rng),
                        n=span, infl=sudodec(infl, rng),CGtaxes=CGtaxes, divtaxes=divtaxes,
                        fees=fees)
            money, this_tax, this_fee = A.gen_annuity()
            all_wd.append([str(rng[0]['year']) + "/01/01", money])
            all_taxes.append([str(rng[0]['year']) + "/01/01", this_tax])
            all_fees.append([str(rng[0]['year']) + "/01/01", this_fee])
        return all_wd, all_taxes, all_fees


def jsonp(function):
    def wraper(event,context):
        print(event)
        event = event['queryStringParameters']
        callback = event['callback']
        r = function(event,context)
        r['body'] = '{}{});'.format(callback,r['body'])
        return r
    return wraper

@jsonp
def lambda_handler(event, context):
    H = Handler()
    # Validate Arguments
    try:
        version = event["v"]
    except:
        return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'error': 'non-specified version'})}
    if version == "1":
        try:
            frm = event['frm']
            to = event['to']
            try:
                frm = datetime.strptime(frm, '%Y-%m-%d')
                to = datetime.strptime(to, '%Y-%m-%d')
            except:
                return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps(
                    {'error': 'improperly configured dates: should be of the format "1975-01-01" '})}
            if frm > to or frm.year < 1880 or to.year > 2017:
                return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'error': 'improperly configured dates: frm should be greater then 1880 and to should be less then 2017 and frm should be less then to'})}
        except:
            return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'error': 'version 1 identifed, but no dates provided'})}
        try:
            contributions = round(float(event['contributions']), 5)
        except:
            return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'error': 'version 1 identifed, but no contributions provided'})}
    elif version == "2":
        try:
            span = int(event['span'])
        except:
            return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'error': 'version 2 identifed, but no span provided'})}
        try:
            contributions = round(float(event['contributions']), 5)
        except:
            return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'error': 'version 1 identifed, but no contributions provided'})}
    elif version == "annuity":
        try:
            span = int(event['span'])
        except:
            return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'error': 'version 2 identifed, but no span provided'})}
        try:
            wd = int(event['wd'])
        except:
            return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"},
                    'body': json.dumps({'error': 'version annuity identifed, but no wd provided'})}
    else:
        return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'error': 'inncorect version identified: {}'.format(version)})}

    try:
        contributions_explicit = json.loads(event['contributions_explicit'])
        contributions_explicit = [float(ele) for ele in contributions_explicit]
        # return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"},
        #         'body': json.dumps({'error': 'Contribution NON error, {} with arguments {}'.format(contributions_explicit, event)})}
    except Exception as e:
        contributions_explicit = None
    try:
        state = event['state'].lower()
        income = round(float(event['income']),5)
        filing = event['filing']
        fund = event['fund']
    except:
        return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'error':'invalid arguments {}'.format(event)})}
    try:
        getname = state + '_' + filing
        states_taxes = H.loadTaxes('state.txt')[getname]
    except:
        return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'error': 'Invalid State/filing status.  Please input full state name and either single or married'})}
    try:
        if float(income) < 0 or float(income) > 1000000:
            return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'error': 'invalid income: {}, please input a number greater then 0 and less the 1,000,000'.format(income)})}
    except:
        return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'error': 'invalid income: {}, please input a number greater then 0 and less the 1,000,000 and remove all commas or punctuation'.format(income)})}
    # try:
    #     if float(contributions) < 0 or float(contributions) > 1000000:
    #         return json.dumps({'status': 'error',
    #                 'error': 'invalid contribution: {}, please input a number greater then 0 and less the 1,000,000'.format(contributions),
    #                 'data': [[], [], []]})
    # except:
    #     return json.dumps({'status': 'error',
    #             'error': 'invalid contribution: {}, please input a number greater then 0 and less the 1,000,000 and remove all commas or punctuation'.format(contributions),
    #             'data': [[], [], []]})
    if not filing.lower() in ['single', 'married']:
        return json.dumps({'status': 'error',
                'error': '[+] invalid filing status {}: please input either single or married'.format(filing),
                'data': [[], [], []]})
    if not fund in ['S and P 500', 'CIBC Balanced Fund', 'CIBC Canadian Index Fund',
                    'CIBC U.S Broad Market Index Fund', 'CIBC Canadian Small-Cap Fund']:
        return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'error': 'invalid fund: {}'.format(fund)})}
    try:
        taxdef = event['taxdef']
        if taxdef == 'true':
            taxdef = True
        elif taxdef=='false':
            taxdef = False
    except:
        taxdef = False
    try:
        fee = float(event['fee'])
        if fee >= 0.0 and fee <= 1.0:
            fee = fee
        else:
            fee = .0005
    except:
        fee = .0005
    # set up contributions, if they have been explicity (each year) defined
    if contributions_explicit:
        contributions = [float(ele) for ele in contributions_explicit]
    elif version == "1":
        yearspan = relativedelta(to, frm).years
        print(yearspan)
        contributions = [contributions for _ in range(yearspan + 2)]
        print('V1: {}'.format(contributions))
    elif version == "2":
        contributions = [contributions for _ in range(span + 2)]
        print('V2: {}'.format(contributions))
    else:
        pass
    if version == "1":
        print('V1 Contribution: {}'.format(contributions))
        data1 = H.generate(frm=frm,to=to, base=fund)
        mdata,all_tax,all_fees, all_contributions = H.Multiplier(data=data1, state=state, income=income, contributions=contributions, fee=fee, filing=filing, taxdef=taxdef)
        return {'statusCode': 200, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'data':[mdata, all_tax, all_fees, all_contributions]})}
    elif version == "2":
        data1 = H.generate(all=True, base=fund)
        mdata,all_tax,all_fees, all_contributions = H.MultiplierPeriod(data=data1, state=state, income=income, contributions=contributions, fee=fee, filing=filing, taxdef=taxdef, span=span)
        return {'statusCode': 200, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'data':[mdata, all_tax, all_fees, all_contributions]})}
    elif version == "annuity":
        data1 = H.generate(all=True, base=fund)
        money,all_tax,all_fee = H.MultiplierAnnuityPeriod(data=data1, state=state, wd=wd, span=span, income=income, filing=filing, fee=fee)
        return {'statusCode': 200, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'data': [money, all_tax, all_fee]})}


# tests
if __name__ == '__main__':
    example_v1 = {
    "queryStringParameters": {
        "v": "1",
        "frm": "1910-01-01",
        "to": "1940-01-01",
        "state": "Wyoming",
        "income": "0",
        "contributions": "0",
        "callback": "localJsonpCallback",
        "taxdef": "false",
        "filing": "single",
        "fee": "0.0",
        "_": "1512401590094",
        "callback": 'localJsonFunction(v1,',
        "fund":"S and P 500"
        }
    }
    example_v2 = {
    "queryStringParameters": {
        "v": "2",
        "span": "40",
        "state": "Wyoming",
        "income": "0",
        "contributions": "0",
        "callback": "localJsonpCallback",
        "taxdef": "false",
        "filing": "single",
        "fee": "0.0",
        "_": "1512401590094",
        "callback":'localJsonFunction(v1,',
        "fund": "S and P 500"
        }
    }
    t7 = {
        "queryStringParameters": {
            "v": "2",
            "span": "10",
            "state": "Wyoming",
            "income": "60000",
            "contributions": "1000",
            "callback": "localJsonpCallback",
            "taxdef": "false",
            "filing": "single",
            "fee": "0",
            "_": "1512401590094",
            "fund":"CIBC Balanced Fund"
        }
    }
    t3 = {
        "queryStringParameters": {
            "v": "1",
            "frm": "1990-01-01",
            "to": "2000-01-01",
            "state": "Wyoming",
            "income": "0",
            "contributions": "0",
            "callback": "localJsonpCallback",
            "taxdef": "false",
            "filing": "single",
            "fee": "0",
            "_": "1512401590094",
            "fund": "CIBC Balanced Fund"
        }
    }
    test_1_v1 = {
        "queryStringParameters": {
            "v": "1",
            "frm": "2005-01-01",
            "to": "2015-01-01",
            "state": "ohio",
            "income": "60000",
            "contributions": "7500",
            "callback": "localJsonpCallback",
            "taxdef": "false",
            "filing": "single",
            "fee": "0",
            "_": "1512401590094",
            "fund": "CIBC Balanced Fund"
        }
    }
    test_1_v2 = {
        "queryStringParameters": {
            "v": "2",
            "span":11,
            "state": "ohio",
            "income": "60000",
            "contributions": "7500",
            "callback": "localJsonpCallback",
            "taxdef": "false",
            "filing": "single",
            "fee": "0",
            "_": "1512401590094",
            "fund": "CIBC Balanced Fund"
        }
    }
    test_2_v1 = {
        "queryStringParameters": {
            "v": "1",
            "frm": "2007-01-01",
            "to": "2017-01-01",
            "state": "ohio",
            "income": "60000",
            "contributions": "15000",
            "callback": "localJsonpCallback",
            "taxdef": "false",
            "filing": "single",
            "fee": "0.025",
            "_": "1512401590094",
            "fund": "CIBC Canadian Small-Cap Fund"
        }
    }
    test_4_v1 = {
        "queryStringParameters": {
            "v": "1",
            "frm": "1991-01-01",
            "to": "1991-01-01",
            "state": "ohio",
            "income": "60000",
            "contributions": "7500",
            "callback": "localJsonpCallback",
            "taxdef": "false",
            "filing": "single",
            "fee": "0.0118",
            "_": "1512401590094",
            "fund": "CIBC U.S Broad Market Index Fund"
        }
    }
    test_5_annuity = {
        "queryStringParameters": {
            "v": "annuity",
            "span": 20,
            "state": "ohio",
            "wd": "60000",
            "income": "60000",
            "callback": "localJsonpCallback",
            "filing": "single",
            "fee": "0.0118",
            "_": "1512401590094",
            "fund": "S and P 500"
        }
    }
    test6 = {
        "queryStringParameters": {
            "v": "1",
            "frm": "2007-01-01",
            "to": "2017-01-01",
            "state": "ohio",
            "income": "0",
            "contributions": "0",
            "contributions_explicit": ["30000", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
            "callback": "localJsonpCallback",
            "taxdef": "true",
            "filing": "single",
            "fee": "0.025",
            "_": "1512401590094",
            "fund": "CIBC Canadian Small-Cap Fund"
        }
    }
    test7 ={
            "queryStringParameters": {
                "v": "1",
                "frm": "1910-01-01",
                "to": "1949-01-01",
                "state": "ohio",
                "income": "0",
                "contributions": "0",
                "callback": "localJsonpCallback",
                "taxdef": "true",
                "filing": "single",
                "fee": "0.0005",
                "_": "1512401590094",
                "fund": "S and P 500",
                "contributions_explicit": [
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    30000,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0
                ]
            }
        }

    # rt1 = lambda_handler(example_v1, None)
    # rt2 = lambda_handler(example_v2, None)
    # rt3 = lambda_handler(test_1_v1,None)
    # rt4 = lambda_handler(test_1_v2, None)
    # rt5 = lambda_handler(test_4_v1, None)
    # rt6 = lambda_handler(t3, None)
    # rt8 = lambda_handler(test6, None)
    rt9 = lambda_handler(test7, None)
    # start = time.time()
    # rt7 = lambda_handler(test_5_annuity, None)
    # end = time.time()
    # print("Ran In {} seconds".format(end-start))
    # print(rt1)
    # print(rt2)
    # print(rt3)
    # print(rt7)
    # print('\n')
    print(rt9)