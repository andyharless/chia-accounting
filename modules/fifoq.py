from collections import deque
from math import isclose


class FifoQ(deque):
    """FIFO Queue of (quantity, cost) tuples allowing for quantity withdrawals"""

    def __init__(self, safe_bounce=False):
        super().__init__([])
        self.safe_bounce = safe_bounce
        self.liq_val = 0
        self.total_quantity = 0

    def liquidate(self):
        basis = self.liq_val
        total = self.total_quantity
        self.__init__(safe_bounce=self.safe_bounce)
        return basis, total

    def add_to_totals(self, element):
        quantity, cost = element
        self.liq_val += cost
        self.total_quantity += quantity
        return None

    def remove_from_totals(self, element):
        quantity, cost = element
        self.liq_val -= cost
        self.total_quantity -= quantity
        return None

    def enq(self, addition):
        """Add an element to the queue"""
        self.append(addition)
        self.add_to_totals(addition)
        return None

    def popleft(self):
        """Remove and return the first-in element"""
        result = super().popleft()
        self.remove_from_totals(result)
        return result
    
    def pop(self):
        """Remove and return the last-in element"""
        result = super().pop()
        self.remove_from_totals(result)
        return result

    def putback(self, element):
        """Put an element back as the first-in element"""
        self.appendleft(element)
        self.add_to_totals(element)
        return None
    
    def deq(self, wd, verbose=False):
        """Withdraw a specified quantity from the queue"""
        totq = self.total_quantity
        totv = self.liq_val
        deficit = wd - totq
        if deficit > 0:
            if self.safe_bounce:
                totq += deficit
                self.enq((deficit, 0))
            else:
                raise Exception("Quantity {total_quantity} insufficient")
        tempq = FifoQ()
        while tempq.total_quantity < wd:
            tempq.enq(self.popleft())
        surplus = tempq.total_quantity - wd
        if verbose:
            print(f'available={tempq.total_quantity}, w/d={wd}, surplus={surplus}')
        assert(surplus >= 0)
        if surplus:
            quantity, cost = tempq.pop()
            needed = wd - tempq.total_quantity
            price = cost / quantity if quantity else cost
            surplus_cost = price * surplus
            needed_cost = price * needed
            self.putback((surplus, surplus_cost))
            tempq.enq((needed, needed_cost))
        if verbose:
            print(f'available after putback={tempq.total_quantity}')
        totcost, totwd = tempq.liquidate()
        if verbose:
            print(f'calculated basis={totcost}')
        assert(totwd == wd)
        assert(isclose(totwd + self.total_quantity, totq))
        assert(isclose(totcost + self.liq_val, totv))
        basis = totcost
        return basis
        
        
class Asset(FifoQ):
    """Inventory of an asset stored as a FIFO Queue"""

    def __init__(self, fair_value=None, safe_bounce=False, name='Anonymous', 
                 start=None, track_balance=False):
        super().__init__(safe_bounce)
        self.fair_value = fair_value
        self.name = name
        self.track_balance = track_balance
        if start is not None:
            self.enq(start)
        if self.track_balance:
            self.balances = []

    def sell(self, amount, date=None, verbose=False):
        basis = self.deq(amount, verbose=verbose)
        profit = 0
        if self.fair_value is not None:
            profit = amount * self.fair_value(date) - basis
        if self.track_balance and date is not None:
            self.balances.append((date, self.total_quantity))
        return basis, profit

    def buy(self, amount, cost=0, date=None):
        self.enq((amount, cost))
        if self.track_balance and date is not None:
            self.balances.append((date, self.total_quantity))
            
    def __repr__(self):
        return f'Asset({self.name}, amount={self.total_quantity})'


class Account:
    def __init__(self):
        self.profit = 0

    def transact(self, date, a_sold, q_sold, a_bought, q_bought, verbose=False):
        if a_sold is not None:
            basis, profit = a_sold.sell(q_sold, date, verbose=verbose)
        else:
            basis = 0
            profit = q_bought * a_bought.fair_value(date)
        self.profit += profit
        new_basis = basis + profit
        a_bought.buy(q_bought, new_basis, date=date)
        if verbose:
            print(f'basis={basis}, new_basis={new_basis}')
            return date, self.profit, basis, new_basis, profit
        return date, self.profit

    def receive(self, date, asset, quantity):
        return self.transact(self, date, None, None, asset, quantity)
    
    
    
