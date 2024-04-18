from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
import collections
from collections import defaultdict
import random
import math
import copy
import numpy as np

empty_dict = {'CHOCOLATE' : 0, 'STRAWBERRY': 0, 'ROSE' : 0, 'GIFT_BASKET' : 0}


def def_value():
    return copy.deepcopy(empty_dict)

INF = int(1e9)

class Trader:

    position = copy.deepcopy(empty_dict)
    POSITION_LIMIT = {'CHOCOLATE' : 250, 'STRAWBERRY': 350, 'ROSE' : 60, 'GIFT_BASKET' : 60}
    volume_traded = copy.deepcopy(empty_dict)

    person_position = defaultdict(def_value)
    person_actvalof_position = defaultdict(def_value)















    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {'CHOCOLATE' : [], 'STRAWBERRY' : [], 'ROSE' : [], 'GIFT_BASKET' : []}

        # Iterate over all the keys (the available products) contained in the order dephts
        for key, val in state.position.items():
            self.position[key] = val
        print()
        for key, val in self.position.items():
            print(f'{key} position: {val}')

        assert abs(self.position.get('UKULELE', 0)) <= self.POSITION_LIMIT['UKULELE']

        timestamp = state.timestamp

        if len(self.bananas_cache) == self.bananas_dim:
            self.bananas_cache.pop(0)
        if len(self.coconuts_cache) == self.coconuts_dim:
            self.coconuts_cache.pop(0)

        _, bs_bananas = self.values_extract(collections.OrderedDict(sorted(state.order_depths['BANANAS'].sell_orders.items())))
        _, bb_bananas = self.values_extract(collections.OrderedDict(sorted(state.order_depths['BANANAS'].buy_orders.items(), reverse=True)), 1)

        self.bananas_cache.append((bs_bananas+bb_bananas)/2)

        INF = 1e9
    
        bananas_lb = -INF
        bananas_ub = INF

        if len(self.bananas_cache) == self.bananas_dim:
            bananas_lb = self.calc_next_price_bananas()-1
            bananas_ub = self.calc_next_price_bananas()+1

        pearls_lb = 10000
        pearls_ub = 10000

        # CHANGE FROM HERE

        acc_bid = {'PEARLS' : pearls_lb, 'BANANAS' : bananas_lb} # we want to buy at slightly below
        acc_ask = {'PEARLS' : pearls_ub, 'BANANAS' : bananas_ub} # we want to sell at slightly above

        self.steps += 1

        for product in state.market_trades.keys():
            for trade in state.market_trades[product]:
                if trade.buyer == trade.seller:
                    continue
                self.person_position[trade.buyer][product] = 1.5
                self.person_position[trade.seller][product] = -1.5
                self.person_actvalof_position[trade.buyer][product] += trade.quantity
                self.person_actvalof_position[trade.seller][product] += -trade.quantity

        orders = self.compute_orders_c_and_pc(state.order_depths)
        result['PINA_COLADAS'] += orders['PINA_COLADAS']
        result['COCONUTS'] += orders['COCONUTS']
        orders = self.compute_orders_dg(state.order_depths, state.observations)
        result['DIVING_GEAR'] += orders['DIVING_GEAR']
        orders = self.compute_orders_br(state.order_depths, state.timestamp)
        result['BERRIES'] += orders['BERRIES']

        orders = self.compute_orders_basket(state.order_depths)
        result['PICNIC_BASKET'] += orders['PICNIC_BASKET']
        result['DIP'] += orders['DIP']
        result['BAGUETTE'] += orders['BAGUETTE']
        result['UKULELE'] += orders['UKULELE']

        for product in ['PEARLS', 'BANANAS']:
            order_depth: OrderDepth = state.order_depths[product]
            orders = self.compute_orders(product, order_depth, acc_bid[product], acc_ask[product])
            result[product] += orders

        for product in state.own_trades.keys():
            for trade in state.own_trades[product]:
                if trade.timestamp != state.timestamp-100:
                    continue
                # print(f'We are trading {product}, {trade.buyer}, {trade.seller}, {trade.quantity}, {trade.price}')
                self.volume_traded[product] += abs(trade.quantity)
                if trade.buyer == "SUBMISSION":
                    self.cpnl[product] -= trade.quantity * trade.price
                else:
                    self.cpnl[product] += trade.quantity * trade.price

        totpnl = 0

        for product in state.order_depths.keys():
            settled_pnl = 0
            best_sell = min(state.order_depths[product].sell_orders.keys())
            best_buy = max(state.order_depths[product].buy_orders.keys())

            if self.position[product] < 0:
                settled_pnl += self.position[product] * best_buy
            else:
                settled_pnl += self.position[product] * best_sell
            totpnl += settled_pnl + self.cpnl[product]
            print(f"For product {product}, {settled_pnl + self.cpnl[product]}, {(settled_pnl+self.cpnl[product])/(self.volume_traded[product]+1e-20)}")

        for person in self.person_position.keys():
            for val in self.person_position[person].keys():
                
                if person == 'Olivia':
                    self.person_position[person][val] *= 0.995
                if person == 'Pablo':
                    self.person_position[person][val] *= 0.8
                if person == 'Camilla':
                    self.person_position[person][val] *= 0

        print(f"Timestamp {timestamp}, Total PNL ended up being {totpnl}")
        # print(f'Will trade {result}')
        print("End transmission")
                
        return result