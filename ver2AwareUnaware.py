import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import random
import tkinter as tk
import xml.etree.ElementTree as ET


class CellularAutomata:
    def __init__(self, num_cells, min_connections, max_connections, aware_chance, spread_chance):
        self.num_cells = num_cells
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.aware_chance = aware_chance
        self.spread_chance = spread_chance
        # Adjacency matrix for connections between cells
        self.adj_matrix = np.zeros((num_cells, num_cells))
        self.states = [{'state': 'unaware', 'spread': False}
                       for _ in range(num_cells)]  # Initial state of all cells
        self.graph = nx.Graph()  # Graph for visualization
        self.node_positions = None  # Store positions of nodes for static visualization

        # Initialize graph with nodes representing cells
        for i in range(num_cells):
            self.graph.add_node(i)

        # Connect cells randomly
        for i in range(num_cells):
            num_connections = random.randint(min_connections, min(
                max_connections, num_cells-1))  # Prevent self-connections
            connected_cells = random.sample(
                [c for c in range(num_cells) if c != i], num_connections)
            for cell in connected_cells:
                self.adj_matrix[i][cell] = 1
                self.graph.add_edge(i, cell)

        # Generate initial positions randomly
        # Decrease k for wider spread on y-axis
        self.node_positions = nx.spring_layout(self.graph, k=0.3)

        # Statistics for each iteration
        self.iteration_stats = []
        self.log_data = ET.Element('log')  # XML log data

    def adjust_positions(self):
        # Use force-directed layout to adjust positions
        # Decrease k for wider spread on y-axis
        self.node_positions = nx.spring_layout(
            self.graph, pos=self.node_positions, k=0.3)

    def initialize_information(self, num_initial_aware):
        # Randomly select cells to be initially aware
        aware_cells = random.sample(range(self.num_cells), num_initial_aware)
        for cell in aware_cells:
            self.states[cell]['state'] = 'aware'

    def visualize(self, iteration, last_iteration=False):
        plt.title(f"Iteration: {iteration}")  # Add iteration number to title

        node_colors = []
        for state in self.states:
            if state['state'] == 'aware':
                if state['spread']:
                    node_colors.append('red')  # Aware and spread information
                else:
                    # Aware but haven't spread information yet
                    node_colors.append('purple')
            else:
                node_colors.append('blue')  # Unaware
        nx.draw(self.graph, pos=self.node_positions,
                with_labels=True, node_color=node_colors)

        # Display the number of aware cells and aware cells that haven't spread information yet
        num_aware = sum(state['state'] == 'aware' for state in self.states)
        num_unspread_aware = sum(
            1 for state in self.states if state['state'] == 'aware' and not state['spread'])
        plt.text(
            0.1, 0.9, f"Aware Cells: {num_aware}", transform=plt.gca().transAxes)
        plt.text(
            0.1, 0.85, f"Aware Cells (Not Spread): {num_unspread_aware}", transform=plt.gca().transAxes)

        # Display legend with acronyms
        aware_patch = plt.Line2D(
            [0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label='Aware (Spread)')
        aware_unspread_patch = plt.Line2D(
            [0], [0], marker='o', color='w', markerfacecolor='purple', markersize=10, label='Aware (Not Spread)')
        unaware_patch = plt.Line2D(
            [0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='Unaware')
        plt.legend(handles=[aware_patch, aware_unspread_patch, unaware_patch])

        # Save the plot as an image file
        plt.savefig(f'iteration_{iteration}.png')

        if last_iteration:
            plt.show()  # Show the plot indefinitely
        else:
            plt.clf()  # Clear the plot for the next iteration

    def spread_information(self):
        num_aware = sum(state['state'] == 'aware' for state in self.states)
        num_unaware = sum(state['state'] == 'unaware' for state in self.states)
        num_unspread_aware = sum(
            1 for state in self.states if state['state'] == 'aware' and not state['spread'])

        # Track cells that have already spread information in this iteration
        spread_cells = set()

        iteration_data = ET.SubElement(self.log_data, 'iteration')
        iteration_data.set('number', str(len(self.iteration_stats) + 1))

        # Log initial states of all nodes in this iteration
        initial_states = ET.SubElement(iteration_data, 'initial_states')
        for i, state in enumerate(self.states):
            node_state = ET.SubElement(initial_states, 'node_state')
            node_state.set('node', str(i))
            node_state.set('state', state['state'])

        aware_nodes = ET.SubElement(iteration_data, 'aware_nodes')

        for i in range(self.num_cells):
            if self.states[i]['state'] == 'aware' and not self.states[i]['spread']:
                aware_node = ET.SubElement(aware_nodes, 'node')
                aware_node.set('id', str(i))

                # Check if the cell spreads information to its neighbors
                for j in range(self.num_cells):
                    if self.adj_matrix[i][j] == 1 and self.states[j]['state'] == 'unaware':
                        if random.random() < self.spread_chance:
                            self.states[j]['state'] = 'aware'
                            self.states[i]['spread'] = True
                            # Change color of edge
                            self.graph[i][j]['color'] = 'red'
                            spread_cells.add(i)
                            # Log spread information for this iteration
                            spread_data = ET.SubElement(
                                iteration_data, 'spread')
                            spread_data.set('from', str(i))
                            spread_data.set('to', str(j))

        # Log final states of all nodes in this iteration
        final_states = ET.SubElement(iteration_data, 'final_states')
        for i, state in enumerate(self.states):
            node_state = ET.SubElement(final_states, 'node_state')
            node_state.set('node', str(i))
            node_state.set('state', state['state'])

        num_aware_after = sum(
            state['state'] == 'aware' for state in self.states)
        num_unaware_after = sum(
            state['state'] == 'unaware' for state in self.states)

        # Store iteration statistics
        self.iteration_stats.append({
            'iteration': len(self.iteration_stats) + 1,
            'num_aware': num_aware_after,
            'num_unspread_aware': num_unspread_aware,
            'num_unaware': num_unaware_after,
            'spread_from': list(spread_cells)
        })

    def generate_html_report(self):
        html_content = "<html><head><title>Cellular Automata Simulation Report</title></head><body>"

        # Simulation parameters
        html_content += "<h2>Simulation Parameters</h2>"
        html_content += f"<p>Number of cells: {self.num_cells}</p>"
        html_content += f"<p>Min connections: {self.min_connections}</p>"
        html_content += f"<p>Max connections: {self.max_connections}</p>"
        html_content += f"<p>Aware chance: {self.aware_chance}</p>"
        html_content += f"<p>Spread chance: {self.spread_chance}</p>"

        # Iteration statistics
        html_content += "<h2>Iteration Statistics</h2>"
        html_content += "<table border='1'><tr><th>Iteration</th><th>Num Aware</th><th>Num Aware (Not Spread)</th><th>Num Unaware</th><th>Spread From</th></tr>"
        for stats in self.iteration_stats:
            html_content += f"<tr><td>{stats['iteration']}</td><td>{stats['num_aware']}</td><td>{stats['num_unspread_aware']}</td><td>{stats['num_unaware']}</td><td>{', '.join(str(cell) for cell in stats['spread_from'])}</td></tr>"
        html_content += "</table>"

        # Plot of each iteration
        html_content += "<h2>Plots</h2>"
        for stats in self.iteration_stats:
            html_content += f"<h3>Iteration {stats['iteration']}</h3>"
            html_content += f"<img src='iteration_{stats['iteration']}.png'>"

        # Link to log path
        html_content += "<h2>Logs</h2>"
        html_content += "<p><a href='simulation_log.xml'>Link to log file</a></p>"

        html_content += "</body></html>"

        with open("simulation_report.html", "w") as file:
            file.write(html_content)

    def generate_xml_log(self, log_file):
        tree = ET.ElementTree(self.log_data)
        tree.write(log_file)


def run_simulation(parameters):
    # Extract parameters and run the simulation
    num_cells = parameters['Number of cells']
    min_connections = parameters['Min connections']
    max_connections = parameters['Max connections']
    aware_chance = parameters['Aware chance']
    spread_chance = parameters['Spread chance']
    num_initial_aware = parameters['Initial aware cells']
    num_iterations = parameters['Number of iterations']

    automata = CellularAutomata(
        num_cells, min_connections, max_connections, aware_chance, spread_chance)
    automata.initialize_information(num_initial_aware)

    # Run the automata for the specified number of iterations
    for iteration in range(num_iterations):
        automata.spread_information()
        automata.adjust_positions()  # Adjust positions between iterations

    # Generate HTML report
    automata.generate_html_report()
    # Generate XML log file
    automata.generate_xml_log('simulation_log.xml')


class ParameterWindow:
    def __init__(self, parent):
        self.parent = parent
        self.parent.title("Cellular Automata Parameters")

        # Create labels and entry fields for each parameter
        self.labels = ['Number of cells:', 'Min connections:', 'Max connections:',
                       'Aware chance:', 'Spread chance:', 'Initial aware cells:', 'Number of iterations:']
        self.entries = []

        # Default values for parameters
        default_values = [100, 2, 4, 0.2, 0.5, 3, 5]
        explanations = [
            "The total number of cells in the cellular automata grid.",
            "The minimum number of connections each cell has.",
            "The maximum number of connections each cell can have.",
            "The probability of a cell becoming aware in the initial state.",
            "The probability of spreading information to neighboring cells.",
            "The number of cells initially aware of the information.",
            "The number of iterations the simulation will run for."
        ]

        for i, label_text in enumerate(self.labels):
            label = tk.Label(parent, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)
            entry = tk.Entry(parent)
            entry.insert(0, str(default_values[i]))  # Set default value
            entry.grid(row=i, column=1, padx=10, pady=5)
            self.entries.append(entry)

            explanation_label = tk.Label(
                parent, text=explanations[i], wraplength=300, justify=tk.LEFT)
            explanation_label.grid(
                row=i, column=2, padx=10, pady=5, sticky=tk.W)

        # Add a button to submit the parameters
        submit_button = tk.Button(
            parent, text="Submit", command=self.submit_parameters)
        submit_button.grid(row=len(self.labels), columnspan=3, pady=10)

    def submit_parameters(self):
        parameters = {}
        for label, entry in zip(self.labels, self.entries):
            parameter_name = label.strip(':')
            parameter_value = entry.get()
            parameters[parameter_name] = float(
                parameter_value) if '.' in parameter_value else int(parameter_value)
        self.parent.destroy()  # Close the window
        run_simulation(parameters)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("600x400")  # Set initial window size
    parameter_window = ParameterWindow(root)
    root.mainloop()
