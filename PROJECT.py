import numpy as np
import random
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import threading



class SetupDialog:
    def _init_(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Setup Parameters")
        ttk.Label(self.top, text="Number of Delivery Points:").pack(pady=5)
        self.num_points_entry = ttk.Entry(self.top)
        self.num_points_entry.pack(pady=5)
        ttk.Label(self.top, text="Number of Trucks:").pack(pady=5)
        self.num_trucks_entry = ttk.Entry(self.top)
        self.num_trucks_entry.pack(pady=5)
        ttk.Label(self.top, text="Enter demands for each delivery point (comma-separated):").pack(pady=5)
        self.demands_entry = ttk.Entry(self.top)
        self.demands_entry.pack(pady=5)
        ttk.Button(self.top, text="OK", command=self.submit).pack(pady=10)


    def submit(self):
        try:
            self.num_points = int(self.num_points_entry.get())
            self.num_trucks = int(self.num_trucks_entry.get())
            self.demands = list(map(int, self.demands_entry.get().split(',')))
            if len(self.demands) != self.num_points:
                raise ValueError("Number of demands must match the number of delivery points.")
            self.top.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e))



class VRPApp:
    def _init_(self, master):
        self.master = master
        master.title("Vehicle Routing Problem Solver")
        self.setup_params()
        self.best_cost = float('inf')
        self.best_route = None

    def setup_params(self):
        self.dialog = SetupDialog(self.master)
        self.master.wait_window(self.dialog.top)
        self.num_delivery_points = self.dialog.num_points
        self.num_trucks = self.dialog.num_trucks
        self.truck_capacity = 100    # Assuming a fixed truck capacity
        self.demands = self.dialog.demands
        self.depot_position = (0, 0)
        self.delivery_points = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(self.num_delivery_points)]
        self.init_ui()

    def init_ui(self):
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, self.master)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.frame_controls = ttk.Frame(self.master)
        self.frame_controls.pack(fill=tk.X)
        self.button_start = ttk.Button(self.frame_controls, text="Start Optimization", command=self.start_optimization)
        self.button_start.pack(side=tk.LEFT)
        self.status_label = ttk.Label(self.master, text="Best Distance: N/A", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X)

    def start_optimization(self):
        self.thread = threading.Thread(target=self.run_optimization)
        self.thread.start()

    def run_optimization(self):
        initial_temp = 100
        final_temp = 1
        cooling_rate = 0.99
        current_solution = self.generate_initial_solution()
        current_cost = self.total_route_distance(current_solution)

        while initial_temp > final_temp:
            new_solution = self.get_neighbour(current_solution)
            new_cost = self.total_route_distance(new_solution)
            cost_difference = new_cost - current_cost

            if cost_difference < 0 or random.uniform(0, 1) < np.exp(-cost_difference / initial_temp):
                current_solution = new_solution
                current_cost = new_cost

            if current_cost < self.best_cost:
                self.best_cost = current_cost
                self.best_route = current_solution
                self.master.after(0, self.plot_routes, self.best_route, self.best_cost)

            initial_temp *= cooling_rate

    def plot_routes(self, routes, cost):
        self.ax.clear()
        self.ax.set_xlabel('X-coordinate')
        self.ax.set_ylabel('Y-coordinate')
        self.ax.set_title(f"Best Total Distance: {cost:.2f}")
        colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']

        self.ax.plot(self.depot_position[0], self.depot_position[1], 'ks')  # Depot

        for i, point in enumerate(self.delivery_points):
            self.ax.plot(point[0], point[1], 'o', color='blue')
            label = f"{self.demands[i]} ({point[0]:.2f}, {point[1]:.2f})"
            self.ax.text(point[0], point[1], label, color='black', fontsize=9, verticalalignment='bottom')

        for idx, route in enumerate(routes):
            if route:
                route_points = [self.depot_position] + [self.delivery_points[i] for i in route] + [self.depot_position]
                x, y = zip(*route_points)
                self.ax.plot(x, y, f'-{colors[idx % len(colors)]}')
                for i in range(len(route_points) - 1):
                    mid_x = (route_points[i][0] + route_points[i + 1][0]) / 2
                    mid_y = (route_points[i][1] + route_points[i + 1][1]) / 2
                    distance = self.calculate_distance(route_points[i], route_points[i + 1])
                    self.ax.text(mid_x, mid_y, f"{distance:.2f} (Step {i+1})", color='black', fontsize=8, backgroundcolor='white')

        self.canvas.draw()
        self.status_label.config(text=f"Best Distance: {cost:.2f}")

    def calculate_distance(self, point1, point2):
        return np.sqrt((point1[0] - point2[0])*2 + (point1[1] - point2[1])*2)

    def total_route_distance(self, routes):
        total_distance = 0
        for route in routes:
            if route:
                route_distance = self.calculate_distance(self.depot_position, self.delivery_points[route[0]])
                for i in range(len(route) - 1):
                    route_distance += self.calculate_distance(self.delivery_points[route[i]], self.delivery_points[route[i+1]])
                route_distance += self.calculate_distance(self.delivery_points[route[-1]], self.depot_position)
                total_distance += route_distance
        return total_distance

    def generate_initial_solution(self):
        routes = [[] for _ in range(self.num_trucks)]
        delivery_indices = list(range(self.num_delivery_points))
        random.shuffle(delivery_indices)
        for delivery_index in delivery_indices:
            assigned = False
            for route in routes:
                if sum(self.demands[i] for i in route) + self.demands[delivery_index] <= self.truck_capacity:
                    route.append(delivery_index)
                    assigned = True
                    break
            if not assigned:
                random.choice(routes).append(delivery_index)
        return routes

    def get_neighbour(self, routes):
        new_routes = [route.copy() for route in routes]
        truck_from = random.randint(0, len(routes) - 1)
        truck_to = random.randint(0, len(routes) - 1)
        if new_routes[truck_from]:
            delivery = new_routes[truck_from].pop(random.randint(0, len(new_routes[truck_from]) - 1))
            if sum(self.demands[i] for i in new_routes[truck_to]) + self.demands[delivery] <= self.truck_capacity:
                new_routes[truck_to].append(delivery)
            else:
                new_routes[truck_from].append(delivery)
        return new_routes

root = tk.Tk()
app = VRPApp(root)
root.mainloop()