import numpy as np #for computing
import random #for randomize
import tkinter as tk #GUI Library
from tkinter import ttk, messagebox #GUI Library
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg #for complex plots
import matplotlib.pyplot as plt #for plotting
import threading

class SetupDialog: #to setup a new class for the first frame
    def __init__(self, parent):
        self.top = tk.Toplevel(parent) #it will appaer on the top
        self.top.title("Setup Parameters") # the title of the frame
        ttk.Label(self.top, text="Number of Delivery Points:").pack(pady=5) #delivery point label with padding 5
        self.num_points_entry = ttk.Entry(self.top) #the number of delivry points the user enters will be stored in num_points_entry
        self.num_points_entry.pack(pady=5)#padding 5
        ttk.Label(self.top, text="Number of Trucks:").pack(pady=5) #number of trucks label with padding 5
        self.num_trucks_entry = ttk.Entry(self.top) #the number of trucks the user enters will be stored in num_trucks_entry
        self.num_trucks_entry.pack(pady=5) #padding 5
        ttk.Label(self.top, text="Enter demands for each delivery point (comma-separated):").pack(pady=5)  #demands label with padding 5
        self.demands_entry = ttk.Entry(self.top) #the number of demand of each node the user enters will be stored in demands_entry
        self.demands_entry.pack(pady=5)#padding 5
        ttk.Button(self.top, text="OK", command=self.submit).pack(pady=10) #OK button

    def submit(self): # when the button OK is pressed
        try:
            self.num_points = int(self.num_points_entry.get()) #string to int
            self.num_trucks = int(self.num_trucks_entry.get())  #string to int
            self.demands = list(map(int, self.demands_entry.get().split(',')))  #string to list
            if len(self.demands) != self.num_points:
                raise ValueError("Number of demands must match the number of delivery points.") #if the number of demands and number of nodes is not equal
            self.top.destroy() #close frame if all things are correct
        except ValueError as e:
            messagebox.showerror("Error", str(e)) #if there is error but it in message box

class VRPApp: #class for second frame
    def __init__(self, master):#main frame
        self.master = master #to access the parent
        master.title("Vehicle Routing Problem Solver") #frame title
        self.setup_params() #to get the intializaton variables
        self.best_cost = float('inf') #best_route = infinity
        self.best_route = None #no best_route until now

    def setup_params(self):
        self.dialog = SetupDialog(self.master) #call the class and the master now is the parent to gather the input
        self.master.wait_window(self.dialog.top) #wait until first frame is closed
        self.num_delivery_points = self.dialog.num_points # number of delivry points
        self.num_trucks = self.dialog.num_trucks # number of trucks
        self.truck_capacity = 100  #truck capacity is 100
        self.demands = self.dialog.demands  #list of demands
        self.depot_position = (0, 0) #initial postion of the trucks
        self.delivery_points = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(self.num_delivery_points)] #random (x,y) coordinates for the delivry points
        self.init_ui() # calls the init_ui method

    def init_ui(self):
        self.figure, self.ax = plt.subplots() #initialize to plot graphical representation
        self.canvas = FigureCanvasTkAgg(self.figure, self.master) #to enable the plot to be displayed in the GUI
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True) #The frame is placed on the top
        self.frame_controls = ttk.Frame(self.master) #intilaize a new frame to the buttons
        self.frame_controls.pack(fill=tk.X) #expand horizantally
        self.button_start = ttk.Button(self.frame_controls, text="Start Optimization", command=self.start_optimization) #creates start optimaizong button, the method will run when clicking the button
        self.button_start.pack(side=tk.LEFT) #the button will be on the left side
        self.button_reset = ttk.Button(self.frame_controls, text="Reset Nodes", command=self.reset_nodes) #creates reset button, the method will run when clicking the button
        self.button_reset.pack(side=tk.LEFT) #the button will be on the left side
        self.status_label = ttk.Label(self.master, text="Best Distance: N/A", relief=tk.SUNKEN, anchor=tk.W) #create a label and aligns it to the left
        self.status_label.pack(fill=tk.X) #expand horizantally

    def reset_nodes(self):
        self.delivery_points = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(self.num_delivery_points)]  #regenerate the position of the nodes
        self.best_cost = float('inf') #initialize the best cost as infinity
        self.best_route = None  #initialize the best route as none
        self.plot_routes([], 0)  #clear all routes and best costs
        messagebox.showinfo("Reset Successful", "The nodes have been reset successfully.") #message box to show that all nodes have been reset

    def start_optimization(self):
        self.thread = threading.Thread(target=self.run_optimization) #to allow the optimization process to run and prevent the main GUI thread
        self.thread.start()

    def run_optimization(self):
        initial_temp = 100 #initial tempreture (simulated annealing big moves first)
        final_temp = 1 #the algorithim will run until temp decrease to this value
        cooling_rate = 0.99 #each iteration will decrease 1%
        current_solution = self.generate_initial_solution() #generate a solution
        current_cost = self.total_route_distance(current_solution) #calculate the distance to calculate the cost

        while initial_temp > final_temp:  #while the temp>1
            new_solution = self.get_neighbour(current_solution) #check if it can enhance the route by calling get neighbour func
            new_cost = self.total_route_distance(new_solution) #calculate the new route cost
            cost_difference = new_cost - current_cost #decide whuch route is better

            if cost_difference < 0 or random.uniform(0, 1) < np.exp(-cost_difference / initial_temp): #decide to accept the new solution or not
                current_solution = new_solution #accept the new route
                current_cost = new_cost

            if current_cost < self.best_cost: #check if solution is the best
                self.best_cost = current_cost #upadate cost and route
                self.best_route = current_solution
                self.master.after(0, self.plot_routes, self.best_route, self.best_cost) #plot the route

            initial_temp *= cooling_rate #update the initial temp

    def plot_routes(self, routes, cost):
        self.ax.clear() #clear the plot
        self.ax.set_xlabel('X-coordinate') #X label
        self.ax.set_ylabel('Y-coordinate') # y label
        self.ax.set_title(f"Best Total Distance: {cost:.2f}") # title
        colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k'] #color for each truck red, greeb, blue, ...etc

        self.ax.plot(self.depot_position[0], self.depot_position[1], 'ks')  #plot the initial node (0,0) as black square (KS) start and end

        for i, point in enumerate(self.delivery_points): #each Point
            self.ax.plot(point[0], point[1], 'o', color='blue') #plot each point as blue circle
            label = f"{self.demands[i]} ({point[0]:.2f}, {point[1]:.2f})"#label for demand of the point and the (x,y)
            self.ax.text(point[0], point[1], label, color='black', fontsize=9, verticalalignment='bottom') #set the text under the point

        for idx, route in enumerate(routes): #for each route the has delivry points
            if route:
                route_points = [self.depot_position] + [self.delivery_points[i] for i in route] + [self.depot_position] #list of points starting and enidng at (0,0) with point inbetween
                x, y = zip(*route_points)
                self.ax.plot(x, y, f'-{colors[idx % len(colors)]}') #each route in one color
                for i in range(len(route_points) - 1):
                    mid_x = (route_points[i][0] + route_points[i + 1][0]) / 2 #calculate the mid point of each line to put label in it
                    mid_y = (route_points[i][1] + route_points[i + 1][1]) / 2 #calculate the mid point of each line to put label in it
                    distance = self.calculate_distance(route_points[i], route_points[i + 1])# calculate the distance
                    self.ax.text(mid_x, mid_y, f"{distance:.2f} (Step {i+1})", color='black', fontsize=8, backgroundcolor='white')#label the number of step and the distance of the line

        self.canvas.draw() #redraw the canvas to plot all commands
        self.status_label.config(text=f"Best Distance: {cost:.2f}") #label for best distance

    def calculate_distance(self, point1, point2):
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2) #calculate the ditance equation

    def total_route_distance(self, routes):
        total_distance = 0 #initialaize to 0
        for route in routes:
            if route: #if the route not empty
                route_distance = self.calculate_distance(self.depot_position, self.delivery_points[route[0]])#caculate from the initail postion to the first point
                for i in range(len(route) - 1):
                    route_distance += self.calculate_distance(self.delivery_points[route[i]], self.delivery_points[route[i+1]]) #add to the distance the route distance
                route_distance += self.calculate_distance(self.delivery_points[route[-1]], self.depot_position) #add to the distanse from last point to (0,0)
                total_distance += route_distance #total distance
        return total_distance

    def generate_initial_solution(self):
        routes = [[] for _ in range(self.num_trucks)] #creates a list for each truck (empty)
        delivery_indices = list(range(self.num_delivery_points)) #create a list for each delivry points from 0 to number of points
        random.shuffle(delivery_indices) #randomise the list
        for delivery_index in delivery_indices:
            assigned = False
            for route in routes:
                if sum(self.demands[i] for i in route) + self.demands[delivery_index] <= self.truck_capacity: #Calculate the demand of the route+the demand of the point if < truck capacity the point will be added to the truck route
                    route.append(delivery_index)
                    assigned = True
                    break
            if not assigned: #if not been added
                random.choice(routes).append(delivery_index) #add to a random truck route
        return routes

    def get_neighbour(self, routes):
        new_routes = [route.copy() for route in routes] #create a copy of the current route
        truck_from = random.randint(0, len(routes) - 1) #select a random truck to start moving from
        truck_to = random.randint(0, len(routes) - 1) #select a random truck to go to
        if new_routes[truck_from]: #if the truck has at least one delivery point
            delivery = new_routes[truck_from].pop(random.randint(0, len(new_routes[truck_from]) - 1)) #remove a random delivry point
            if sum(self.demands[i] for i in new_routes[truck_to]) + self.demands[delivery] <= self.truck_capacity:
                new_routes[truck_to].append(delivery) #if the truck can accept the removed delivery point and add it to the route
            else:
                new_routes[truck_from].append(delivery) #if not the point will returned to its original route beacuse demand>truck capacity
        return new_routes # return the route solution

root = tk.Tk() #intilaize the main window
app = VRPApp(root) #to call the class with parameter root
root.mainloop()
