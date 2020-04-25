import home_ownership
import json

'''
written and copywrited by MILLETTE,LOUIS 2019

metric='mean', quartile=50, state='ontario', income=53000, fee=0.0005, filing='single', real=True

Usage:
    home ownership takes the following arguments and returns the interest, principle, and total cash flows, as well as the
    equivelent money earned inthe S&P 500.  That is, if you took each years nominal cash flows and invested in the S&P 500,
    how much money in todays (REAL) dollars would you have at the end of the mortgage duration after taxes, fees, and inflation.

Arguments:
     home_price(int): price of the home
     down_percent(float): down payment percent (20% -> 0.20)
     coho(float): cost of home ownership, per month
     c(float): interest rate monthly (APR), 5%(yearly) -> 0.00417
     n(int): number of months in mortgage
     d(float): additional monthly contributiond to go againt the principle
     marginal(float): marginal tax rate used for mortgage interest deduction. (30% -> 0.30)
     metric(string): takes 3 values: 'mean', 'median', or 'quartile'
        - mean: Take the mean money of every (n/12) year span of the S&P 500 over the last 100 years for the investment
        - median: Take the median money of every (n/12) year span of the S&P 500 over the last 100 years for the investment
        - quartile: Take the (given quartile) th quartile money of every (n/12) year span of the S&P 500 over the last 100 years for the investment
     quartile (int): if quartile above, which one? (ie 50 here would be the median)
     state (string): what state is this home in, for tax purposes on the investment (ontario also accepted)
     income (int): how much money are you making (for tax purposes for investment)
     fee (float): what is the fee (MER) for the investment? 0.05% annually for instance would be 0.0005
     filing (string): 'single' or 'married'.  For tax purposes
     real (bool): should the number be returned in real or nominal dollars?
 '''

def validate(event):
    status, error = True, ''
    if not event.get('home_price'):
        status, error = False, 'home_price is not defined'
    if not isinstance(event.get('home_price'), int):
        status, error = False, 'home_price is not an integer'
    if not event.get('down_percent'):
        status, error = False, 'down_percent is not defined'
    if not isinstance(event.get('down_percent'), float):
        status, error = False, 'down_percent is not a float'
    if not event.get('coho'):
        status, error = False, 'coho is not defined'
    if not (isinstance(event.get('coho'), float) or isinstance(event.get('coho'), int)):
        status, error = False, 'coho is not a float'
    if not event.get('c'):
        status, error = False, 'c is not defined'
    if not isinstance(event.get('c'), float):
        status, error = False, 'c is not a float'
    if not event.get('n'):
        status, error = False, 'n is not defined'
    if not isinstance(event.get('n'), int):
        status, error = False, 'c is not a int'
    if not event.get('d'):
        status, error = False, 'd is not defined'
    if not (isinstance(event.get('d'), float) or isinstance(event.get('d'), int)):
        status, error = False, 'd is not a float or int'
    if not event.get('down_percent'):
        status, error = False, 'down_percent is not defined'
    if not isinstance(event.get('down_percent'), float):
        status, error = False, 'down_percent is not a float'
    if not event.get('marginal'):
        event['marginal'] = 1.0
    if not isinstance(event.get('marginal'), float) or isinstance(event.get('marginal'), int):
        status, error = False, 'marginal is not a float or int'
    if not event.get('metric'):
        event['metric'] = 'median'
    if not event.get('quantile'):
        event['quantile'] = 50
    if not event.get('state'):
        event['state'] = 'Ontario'
    if not event.get('income'):
        event['income'] = 0
    if not event.get('fee'):
        status, error = False, 'fee is not defined'
    if not isinstance(event.get('fee'), float) or isinstance(event.get('fee'), int):
        status, error = False, 'fee is not a float or integer'
    if not event.get('filing'):
        event['filing'] = 'single'
    if not (event.get('filing') == 'single' or event.get('filing') == 'married'):
        status, error = False, 'filing is not single or married'
    if not isinstance(event.get('down_percent'), float):
        return False, 'down_percent is not a float'
    if not event.get('down_percent'):
        return False, 'down_percent is not defined'
    if not isinstance(event.get('down_percent'), float):
        return False, 'down_percent is not a float'
    if not event.get('down_percent'):
        return False, 'down_percent is not defined'
    if not isinstance(event.get('down_percent'), float):
        return False, 'down_percent is not a float'
    if not event.get('down_percent'):
        return False, 'down_percent is not defined'
    if not isinstance(event.get('down_percent'), float):
        return False, 'down_percent is not a float'
    if not event.get('real'):
        event['real'] = True
    return event, status, error

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
    event, status, error = validate(event)
    if not status:
        return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'error': error})}
    else:
        M = home_ownership.Mortgage()
        I = home_ownership.Investment()
        cash_flows = M.cash_flows_pad(event['home_price'], event['down_percent'], event['coho'], event['c'], event['n'], event['d'], event['marginal'], event['total_years'])
        total = I.invest(cash_flows, metric=event['metric'], quartile=event['quartile'], state=event['state'], income=event['income'], fee=event['fee'], filing=event['filing'], real=event['real'])

        return {'statusCode': 200, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'cash_flows': cash_flows, 'total': total})}
