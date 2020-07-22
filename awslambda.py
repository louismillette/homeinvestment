import home_ownership
import json
import numpy
'''
written and copywrited by MILLETTE,LOUIS 2020
All rights reserved
'''


'''
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
    for argument in ['total_years', 'mortgageable_months', 'list_price', 'taxable_price', 'selling_price_current_year_dollars',
                     'sales_tax', 'monthly_interest_rate', 'property_tax_rate_yearly', 'new', 'down_payment', 'fixed_closeing_costs',
                     'rental_income', 'percent_time_unit_occupied', 'maintainance_monthly', 'condo_fees_monthly', 'income_tax_rate_company',
                     'income_tax_rate_individual', 'home_insurance_monthly']:
        if not event.get(argument):
            svtatus, error = False, f'{argument} is not defined'
    print([event])
    event["total_years"] = int(event["total_years"])
    event["mortgageable_months"] = int(event["mortgageable_months"])
    event["list_price"] = int(event["list_price"])
    event["taxable_price"] = int(event["taxable_price"])
    event["selling_price_current_year_dollars"] = int(event["selling_price_current_year_dollars"])
    event["sales_tax"] = float(event["sales_tax"])
    event["monthly_interest_rate"] = float(event["monthly_interest_rate"])
    event["property_tax_rate_yearly"] = float(event["property_tax_rate_yearly"])
    event["new"] = bool(event["new"])
    event["down_payment"] = float(event["down_payment"])
    event["fixed_closeing_costs"] = int(event["fixed_closeing_costs"])
    event["rental_income"] = int(event["rental_income"])
    event["percent_time_unit_occupied"] = float(event["percent_time_unit_occupied"])
    event["maintainance_monthly"] = float(event["maintainance_monthly"])
    event["home_insurance_monthly"] = float(event["home_insurance_monthly"])
    event["condo_fees_monthly"] = int(event["condo_fees_monthly"])
    event["income_tax_rate_company"] = float(event["income_tax_rate_company"])
    event["income_tax_rate_individual"] = float(event["income_tax_rate_individual"])
    # {'statusCode': 200, 'headers': {'Content-Type': 'jsonp'}, 'body': 'localJsonpCallback({"cash_flow": [-169096, -2347, -2348, -2348, -2349, -2349, -2350, -2351, -2351, -2352, -2352, -2353, -2311, -2312, -2312, -2313, -2313, -2314, -2315, -2315, -2316, -2316, -2317, -2318, -2274, -2274, -2275, -2276, -2276, -2277, -2277, -2278, -2279, -2279, -2280, -2281, -2234, -2235, -2236, -2236, -2237, -2238, -2238, -2239, -2240, -2240, -2241, -2241, -2193, -2194, -2194, -2195, -2196, -2196, -2197, -2198, -2198, -2199, -2200, -2200, -2149, -2149, -2150, -2151, -2151, -2152, -2153, -2154, -2154, -2155, -2156, -2156, -2102, -2102, -2103, -2104, -2104, -2105, -2106, -2107, -2107, -2108, -2109, -2109, -2052, -2052, -2053, -2054, -2055, -2055, -2056, -2057, -2057, -2058, -2059, -2060, -1999, -2000, -2000, -2001, -2002, -2003, -2003, -2004, -2005, -2006, -2006, -2007, -1945, -1946, -1947, -1947, -1948, -1949, -1950, -1951, -1951, -1952, -1953, -1954, -1889, -1890, -1891, -1892, -1893, -1893, -1894, -1895, -1896, -1897, -1898, -1898, -1831, -1832, -1832, -1833, -1834, -1835, -1836, -1837, -1837, -1838, -1839, -1840, -1769, -1770, -1771, -1772, -1773, -1773, -1774, -1775, -1776, -1777, -1778, -1779, -1706, -1707, -1707, -1708, -1709, -1710, -1711, -1712, -1713, -1714, -1715, -1715, -1642, -1643, -1644, -1645, -1646, -1646, -1647, -1648, -1649, -1650, -1651, -1652, -1576, -1577, -1578, -1579, -1580, -1581, -1582, -1583, -1584, -1585, -1585, -1586, -1506, -1507, -1508, -1509, -1510, -1511, -1512, -1513, -1514, -1515, -1515, -1516, -1432, -1433, -1434, -1435, -1436, -1437, -1438, -1439, -1440, -1441, -1442, -1443, -1355, -1356, -1357, -1358, -1359, -1360, -1361, -1362, -1363, -1364, -1365, -1366, -1274, -1275, -1276, -1277, -1278, -1279, -1280, -1281, -1282, -1283, -1284, -1285, -1187, -1189, -1190, -1191, -1192, -1193, -1194, -1195, -1196, -1197, -1198, -1199, -1095, -1096, -1098, -1099, -1100, -1101, -1102, -1103, -1104, -1105, -1106, -1108, -997, -998, -999, -1000, -1001, -1002, -1004, -1005, -1006, -1007, -1008, -1009, -892, -893, -894, -895, -896, -897, -899, -900, -901, -902, -903, -905, -781, -782, -783, -784, -785, -787, -788, -789, -790, -792, -793, -794, -663, -664, -665, -667, -668, -669, -670, -672, -673, -674, -676, -677, -538, -539, -540, -542, -543, -544, -546, -547, -548, -550, -551, -552, -406, -407, -408, -410, -411, -412, -414, -415, -416, -418, -419, -420, -265, -267, -268, -269, -271, -272, -273, -275, -276, -278, -279, -280, -115, -117, -118, -120, -121, -122, -124, -125, -127, -128, -130, -131], "number_of_months_to_pay_back_initial": 359, "nominal_profit": 45681, "real_profit": [-135052, -1871, -1869, -1866, -1863, -1861, -1858, -1856, -1853, -1850, -1848, -1845, -1809, -1807, -1804, -1802, -1799, -1797, -1794, -1792, -1789, -1787, -1784, -1782, -1745, -1742, -1740, -1738, -1735, -1733, -1730, -1728, -1726, -1723, -1721, -1718, -1681, -1678, -1676, -1674, -1671, -1669, -1667, -1665, -1662, -1660, -1658, -1655, -1617, -1615, -1613, -1610, -1608, -1606, -1604, -1602, -1599, -1597, -1595, -1593, -1553, -1551, -1549, -1547, -1545, -1543, -1540, -1538, -1536, -1534, -1532, -1530, -1489, -1487, -1485, -1483, -1481, -1479, -1477, -1475, -1473, -1471, -1469, -1467, -1425, -1423, -1421, -1419, -1417, -1415, -1413, -1412, -1410, -1408, -1406, -1404, -1361, -1359, -1357, -1355, -1354, -1352, -1350, -1348, -1347, -1345, -1343, -1341, -1298, -1296, -1295, -1293, -1291, -1290, -1288, -1286, -1285, -1283, -1281, -1280, -1236, -1234, -1233, -1231, -1230, -1228, -1227, -1225, -1224, -1222, -1220, -1219, -1174, -1172, -1171, -1169, -1168, -1167, -1165, -1164, -1162, -1161, -1160, -1158, -1112, -1110, -1109, -1108, -1106, -1105, -1104, -1103, -1101, -1100, -1099, -1097, -1051, -1049, -1048, -1047, -1046, -1045, -1043, -1042, -1041, -1040, -1039, -1037, -991, -990, -989, -988, -987, -986, -985, -984, -983, -981, -980, -979, -933, -932, -931, -930, -929, -928, -927, -926, -925, -924, -923, -922, -874, -873, -872, -871, -870, -869, -868, -867, -866, -866, -865, -864, -814, -813, -812, -812, -811, -810, -809, -809, -808, -807, -806, -805, -755, -755, -754, -753, -752, -752, -751, -750, -750, -749, -748, -748, -696, -695, -695, -694, -694, -693, -692, -692, -691, -691, -690, -690, -636, -635, -635, -634, -634, -634, -633, -633, -632, -632, -631, -631, -575, -575, -574, -574, -573, -573, -573, -572, -572, -572, -571, -571, -513, -513, -512, -512, -512, -512, -511, -511, -511, -510, -510, -510, -450, -450, -449, -449, -449, -449, -449, -449, -448, -448, -448, -448, -386, -386, -386, -386, -386, -386, -386, -386, -386, -386, -385, -385, -321, -321, -321, -321, -322, -322, -322, -322, -322, -322, -322, -322, -256, -256, -256, -256, -256, -256, -257, -257, -257, -257, -257, -258, -189, -189, -189, -190, -190, -190, -191, -191, -191, -192, -192, -192, -121, -121, -122, -122, -123, -123, -124, -124, -124, -125, -125, -126, -52, -52, -53, -53, -54, -54, -55, -55, -56, -57, -57, 607942], "eac": 1781122, "real_reinvested_profits": 608000});'}
    return event, status, error

def jsonp(function):
    def wraper(event,context):
        callback = event.get('callback')
        event = event['queryStringParameters'] if event.get('queryStringParameters') else event
        if not callback:
            callback = event.get('callback')
        print([event])
        r = function(event,context)
        if callback and callback != '':
            # if callback is empty, send back json as is
            r['body'] = '{}{});'.format(callback,r['body'])
        return r
    return wraper

@jsonp
def lambda_handler(event, context):
    event, status, error = validate(event)
    if not status:
        return {'statusCode': 400, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({'error': error})}
    else:
        cash_flow, number_of_months_to_pay_back_initial, nominal_profit, real_profit, eac, real_reinvested_profits = \
            home_ownership.rental_property(total_years=event['total_years'], mortgageable_months=event['mortgageable_months'],
            list_price=event['list_price'], taxable_price=event['taxable_price'], selling_price_current_year_dollars=event['selling_price_current_year_dollars'],
            sales_tax=event['sales_tax'], monthly_interest_rate=event['monthly_interest_rate'], property_tax_rate_yearly=event['property_tax_rate_yearly'],
            new=event['new'], down_payment=event['down_payment'], fixed_closeing_costs= event['fixed_closeing_costs'], rental_income=event['rental_income'],
            percent_time_unit_occupied=event['percent_time_unit_occupied'], maintainance_monthly=event['maintainance_monthly'],
            condo_fees_monthly=event['condo_fees_monthly'], income_tax_rate_company=event['income_tax_rate_company'], income_tax_rate_individual=event['income_tax_rate_individual'],
            home_insurance_monthly=event['home_insurance_monthly'])
        return {'statusCode': 200, 'headers': {"Content-Type": "jsonp"}, 'body': json.dumps({
            'cash_flow': cash_flow,
            'number_of_months_to_pay_back_initial': number_of_months_to_pay_back_initial,
            'nominal_profit': nominal_profit,
            'real_profit': real_profit,
            'eac': eac,
            'real_reinvested_profits':real_reinvested_profits
        })}
