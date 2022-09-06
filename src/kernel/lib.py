import sqlite3
import json
import os

def read_json(path):
    f = open(path)
    data = json.load(f)
    f.close()
    return data

def repair_path(path1, path2):
    if os.path.isabs(path2):
        return path2
    else:
        abs_path1 = os.path.abspath(os.path.dirname(path1))
        return os.path.join(abs_path1, path2)

def processDB(path):
    con = sqlite3.connect(path)
    cur = con.cursor()
    res = cur.execute("SELECT * FROM ROUTES")
    result = {}
    for row in res:
        s, d, w = row
        result[(s, d)] = w
    con.close()
    return result
        
def printRoutes(routes):
    for (s, d) in routes:
        print("{} <-> {} : {}".format(s, d, routes[(s, d)]))

def extract_outgoing_of(routes, src):
    return [(d, routes[(s, d)]) for (s, d) in routes if s == src] + [(s, routes[(s, d)]) for (s, d) in routes if d == src]
            
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

    def __repr__(self):
        return self.data
        
    def compare_insert(self, data, comparator):
        comp = comparator(self.data, data)
        if comp < 0:
            if self.next is None:
                self.next = Node(data)
            else:
                self.next.compare_insert(data, comparator)
        elif comp > 0:
            newNext = Node(self.data)
            newNext.next = self.next
            self.data = data
            self.next = newNext

class LinkedList:
    def __init__(self):
        self.head = None
        
    def __init__(self, nodes=None):
        self.head = None
        if nodes is not None:
            node = Node(data=nodes.pop(0))
            self.head = node
            for elem in nodes:
                node.next = Node(data=elem)
                node = node.next

    def __repr__(self):
        node = self.head
        nodes = []
        while node is not None:
            nodes.append(str(node.data))
            node = node.next
        nodes.append("None")
        return " -> ".join(nodes)
    
    def __iter__(self):
        node = self.head
        while node is not None:
            yield node
            node = node.next
    
    def is_empty(self):
        return self.head == None
    
    def pop(self):
        if self.head == None:
            return None
        else:
            data = self.head.data
            self.head = self.head.next
            return data
        
    def compare_insert(self, data, comparator):
        if self.head is None:
            self.head = Node(data=data)
        else:
            self.head.compare_insert(data, comparator)

def processEmpire_bis(empire):
    hunters_planning = {}
    for plan in empire["bounty_hunters"]:
        l = hunters_planning.get(plan["day"], [])
        l.append(plan["planet"])
        hunters_planning[plan["day"]] = l
    return (empire["countdown"], hunters_planning)

def processEmpire(path):
    empire = read_json(path)
    return processEmpire_bis(empire)

def compare(data1, data2): #Used for a_star algorithm
    (current_k, current_fuel, current_day, current_path) = data1
    (current_k2, current_fuel2, current_day2, current_path2) = data2
    if current_k < current_k2:
        return -1
    elif current_k > current_k2:
        return 1
    if current_day < current_day2:
        return -1
    elif current_day > current_day2:
        return 1
    if current_fuel > current_fuel2:
        return -1
    elif current_fuel < current_fuel2:
        return 1
    if current_path[-1] == current_path2[-1]:
        return 0
    else:
        return -1

def process_a_star(routes, src, dst, autonomy, countdown, hunters_planning): #applying a_star algorithm
    tasks = LinkedList(nodes = [((1 if src in hunters_planning.get(0, []) else 0, autonomy, 0, [src]))])
    while not tasks.is_empty():
        (current_k, current_fuel, current_day, current_path) = tasks.pop()
        if current_path[-1] == dst:
            return (current_k, current_fuel, current_day, current_path)
               
        #Refuel solution
        if current_day < countdown:
            tasks.compare_insert((current_k + 1 if current_path[-1] in hunters_planning.get(current_day, []) else current_k, autonomy, current_day + 1, current_path + [current_path[-1]]), compare)
        
        #other possibilities
        possible_next_steps = extract_outgoing_of(routes, current_path[-1])
        for (dst2, cost) in possible_next_steps:
            if cost <= current_fuel and current_day + cost <= countdown: #Acceptable solution
                tasks.compare_insert(( (current_k + 1) if dst2 in hunters_planning.get(current_day + cost, []) else current_k, current_fuel - cost, current_day + cost, current_path + [dst2]), compare)
    return None
        
def compute_proba(k): #Computes the failure probability
    if k == 0:
        return 0
    res = 1/10
    for i in range(2, k+1):
        res += 9/(10**i)
    return res

if __name__ == "__main__":
    falcon_path = "../../examples/example4/millennium-falcon.json"
    falcon = read_json(falcon_path)
    falcon["routes_db"] = repair_path(falcon_path, falcon["routes_db"])
    #print(falcon["routes_db"])
    routes = processDB(falcon["routes_db"])
    printRoutes(routes)
    print (extract_outgoing_of(routes, "Dagobah"))
    list_test = LinkedList(nodes = [1, 2, 3, 4, 5])
    print(list_test)
    list_test.compare_insert(2.5, lambda x, y: x - y)
    print(list_test)
    (countdown, hunters_planning) = processEmpire("../../examples/example4/empire.json")
    print (process_a_star(routes, falcon["departure"], falcon["arrival"], falcon["autonomy"], countdown, hunters_planning))
    
    
    