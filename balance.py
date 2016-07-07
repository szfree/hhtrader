import easytrader
import easyquotation

g_investment = 450000

#illiq
#g_stocks = ['000715','002728','600243','300374','600883','002549','000759','603889','002034','601116','300280','000736','600505','600444','600792']
# '002333','603606','300260','002578','002687'

#lowmc
g_stocks = ['300029','600099','300268','002193','002205','002627','600213','300344','300120','300330','000785','600448','600985','300405','600444']
# '600561','600853','600593','600605','300321'

g_entrusts = []

def main():

	#stock account
	trader = easytrader.use('ht', debug=False)
	trader.config['entrust']['cssweb_type'] = 'GET_TODAY_ENTRUST'
	#quotation
	quota = easyquotation.use('sina')

	print('login huatai system......')
	trader.prepare('ht.json')
	print('login successfully')

	show_balance(trader.balance[0])

	# if cash less than investment, quit and check
	if (trader.balance[0]['enable_balance'] < g_investment):
		print('**WARNING: total cash is less than the investment you want to use, please check!')
		return

	print('calculate the allocation for each stock...')
	stockbook = prepare(quota, g_stocks)

	print(stockbook)

	# process the orders
	process(trader, quota, stockbook)

#calculate the stock num for each stocks based on the allocation
def prepare(quota, stocks):
	stockdata = quota.stocks(stocks)
	allocation = g_investment / len(stocks)
	stockbook = {}
	for (k,v) in stockdata.items():
		if v['sell'] == 0:
			print('skip stock '+k+', it may not tradable today!')
			continue

		num = allocation // v['sell']
		if num % 100 > 50:
			num = (num // 100 + 1)*100
		else:
			num = (num // 100) * 100
		target = {}
		target['total_amount'] = num # total stock num
		target['business_amount'] = 0 # deal made number
		stockbook[k] = target
	return stockbook

def buy(trader, quota, stockid, stocknum):
	hq = quota.stocks(stockid)
	estimate_price = hq[stockid]['sell']

	result = input('Buy '+stockid+', amount '+str(stocknum)+', price '+str(estimate_price)+'(y/n)?    ')
	if result == 'y' : 
		hq = quota.stocks(stockid)
		num = hq[stockid]['ask1_volume'] # default to ask1 volume
		if stocknum < num:
			num = stocknum
		actual_price = hq[stockid]['sell']
		if(actual_price/estimate_price > 1.003) :
			print('actual sell price increased more than 0.3%, skip purchase!')
			return

		entrust = trader.buy(stockid, hq[stockid]['sell'], num)
		g_entrusts.append(entrust[0]['entrust_no'])

def cancel(trader, order_id):
	trader.cancel_entrust(order_id)

def update(trader, stockbook):
	orders = trader.entrust
	
	
	## test , no orders, jump out
	if 'cssweb_type' in orders:
		return stockbook

	for k in stockbook.keys():
		ba = 0 # business amount

		for order in orders:
			if order['entrust_no'] not in g_entrusts:
				continue
				
			if order['stock_code'] != str(k):
				continue
			
			#skip the sell order
			if order['entrust_bs'] == '2' : ### 1 for buy, 2 for sell
				continue

			ba += order['business_amount']

			
			## 0 -- not submit;3--submitted and waiting for cancel;6 -- canclled;8 -- successful;2--submitted;7--partially successful
			status = order['entrust_status']

			#except success and cancelled order, cancel all the other orders
			if (status != '6') and (status != '8') :
				print('entrust status: '+ order['entrust_status']+'; status name: '+order['status_name'])
				result = input('Cancel order for '+ k + ', entrust amount is ' + str(order['entrust_amount']) + ', business amount is ' + str(order['business_amount']) +' (y/n)?')
				if result == 'y':
					trader.cancel_entrust(order['entrust_no'])	

			
		stockbook[k]['business_amount'] = ba

	return stockbook

#finish process the orders
def finished(stockbook):
	for v in stockbook.values():
		if v['total_amount'] > v['business_amount']:
			return False
	return True



def process(trader, quota, stockbook):
	while not finished(stockbook):
		s = input("Do you want to continue process(y/n)?   ")
		if s != 'y':
			break
		# update the stockbook based on the order
		sb = update(trader, stockbook)

		stockbook = sb

		#buy the stocks
		for k in stockbook.keys():
			num = stockbook[k]['total_amount'] - stockbook[k]['business_amount']
			if num > 0:
				buy(trader, quota, k, num)



	
#show stock account briefing
def show_balance(balance):
	print('-----------------------------')
	print('current stock account briefing')
	print('total asset: '+str(balance['asset_balance']))
	print('total cash: '+str(balance['current_balance']))
	print('available cash: ' + str(balance['enable_balance']))
	print('total stock: ' + str(balance['market_value']))
	print('------------------------------')


main()


	