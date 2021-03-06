import easytrader
import easyquotation

g_investment = 1000000
#g_stocks = ['000715','002728','600243','300374','600883','002549','000759','603889','002034','601116','300280','000736','600505','600444','600792']
g_stocks = ['300029','600099','300268','002193','002205','002627','600213','300344','300120','300330','000785','600448','600985','300405','600444']

g_entrusts = []

g_percent = 0.33 # sell percent for total amount

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

	print('collect the stocks needed be sold')
	stockbook = prepare(trader, g_stocks)

	# process the orders
	process(trader, quota, stockbook)

#get the stock positions
def prepare(trader, ids):
	stockdata = trader.position

	stockbook = {}
	for stock in stockdata:
		if stock['stock_code'] in ids:
			target = {}
			target['total_amount'] = stock['enable_amount'] * g_percent // 100 * 100
			target['business_amount'] = 0
			stockbook[ stock['stock_code'] ] = target
	return stockbook

def sell(trader, quota, stockid, stocknum):
	hq = quota.stocks(stockid)
	estimate_price = hq[stockid]['buy']

	result = input('Sell '+stockid+', amount '+str(stocknum)+', price '+str(estimate_price)+'(y/n)?    ')
	if result == 'y' : 
		hq = quota.stocks(stockid)
		num = hq[stockid]['bid1_volume'] # default to bid1 volume
		if stocknum < num:
			num = stocknum
		actual_price = hq[stockid]['buy']
		if(actual_price/estimate_price < 0.997) :
			print('actual sell price is down more than 0.3%, skip selling!')
			return

		entrust = trader.sell(stockid, hq[stockid]['buy'], num)
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
			
			#skip the buy order
			if order['entrust_bs'] == '1' : ### 1 for buy, 2 for sell
				continue

			ba += order['business_amount']

			## 撤销“已报”和“部成”和“未报”的订单
			## 0 -- 未报; 3--已报待撤 6 -- 已撤； 8 -- 已成； 需要检查部成的代号(可能是7) 和 已报（可能是2） 的代号
			status = order['entrust_status']
			
			#cancel all the orders except succeeded or cancelled.
			if( status!='6') and (status!='8') :
				print('entrust status: '+ order['entrust_status']+'; status name: '+order['status_name'])
				result = input('Cancel order for '+ k + ', entrust amount is ' + str(order['entrust_amount']) + ', business amount is ' + str(order['business_amount']) +' (y/n)?')
				if result == 'y':
					trader.cancel_entrust(order['entrust_no'])	

			
		stockbook[str(k)]['business_amount'] = ba

	return stockbook
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

		#sell the stocks
		for k in stockbook.keys():
			num = stockbook[k]['total_amount'] - stockbook[k]['business_amount']
			if num > 0:
				sell(trader, quota, k, num)



	
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


	