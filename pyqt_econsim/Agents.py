import random
import numpy as np
import math
import pandas as pd

class Agent:
    def __init__(self, unique_id, model):
        self.unique_id = unique_id
        self.model = model
        
    class SimultaneousActivation:
        def __init__(self, model):
            self.model = model
            self.agents = []
            
        def add(self, agent):
            self.agents.append(agent)
            
        def step(self):
            for agent in self.agents:
                agent.step()
            for agent in self.agents:
                agent.advance()

class MarketAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.trade = False
        self.selected = None
        self.tempSurplus = 0 # represents the surplus collected in a round
        self.round = 1 
        self.index = self.unique_id
        self.move = 0
        self.averagePrice = None
        self.NValue = 0
        self.NValLagged = 1
        self.successes = 0
        self.failures = 0
        self.pastTraders = []
        self.indicator = 0
        
    def select_partner(self, connection_list, attraction_list):
        """This method determines how an agent selects a partner. Initially, 
        will do a check to see if this is the first trade an agent has made."""
        if self.move == 0 or len(connection_list[self.unique_id] == 0): # if not connected to anyone
            return random.choice(connection_list[self.unique_id]) if connection_list[self.unique_id] else None
    
    def update_offer_price(self, tradeResult, role):
        """Method updates offer price dependent on the result of the trade with another agent."""
        gamma = self.model.gammaValue
        fixed_cost = self.model.fixedCost
        
        if role == "buyer":
            if tradeResult:
                self.offerPrice = (1 - gamma) * self.offerPrice + gamma * self.upperBound
            else:
                self.offerPrice = (1 - gamma) * self.offerPrice + gamma * self.initialValue
        elif role == "seller":
            if tradeResult:
                self.offerPrice = (1-gamma) * self.offerPrice + gamma * self.lowerBound
            else:
                self.offerPrice = (1 - gamma) * self.offerPrice + gamma * self.cost
                            
class MarketSeller(MarketAgent):
    """A seller with a fixed price for a product."""
    
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.trade = False
        self.selected = None
        self.tempSurplus = 0
        self.round = 1
    
    def step(self):
        self.tempSurplus = 0
        
class MarketBuyer(MarketAgent):
    def __init__(self, unique_id, model):
        self.trade = False
        
class HumanPlayer(MarketAgent):
    """A human player which acts as a buyer or a seller"""
    
    def __init__(self, unique_id, model=None, role='buyer', initial_value=None, offer_price=None, cost=None):
        super().__init__(unique_id, model)
        self.role = role  # 'buyer' or 'seller'
        if self.role == 'buyer':
            lb = model.buyer_lower_bound if model else 5
            ub = model.buyer_upper_bound if model else 10
            self.initial_price = float(initial_value) if initial_value else lb
            self.surplus = 0
            self.offerPrice = float(offer_price) if offer_price else lb
            self.lowerBound = lb
        else:
            lb = model.seller_lower_bound if model else 0
            ub = model.seller_upper_bound if model else 15
            self.cost = float(cost) if cost else ub
            self.surplus = 0
            self.offerPrice = float(offer_price) if offer_price else ub
            self.upperBound = ub
            self.initial_price = self.cost
        self.selected_partner_id = None
        self.trade_result_message = ""
        self.trade_history = {}

    def step(self):
        self.tempSurplus = 0
        self.trade = False
        self.trade_result_message = ""
