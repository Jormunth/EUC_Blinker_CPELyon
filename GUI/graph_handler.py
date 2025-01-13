import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class GraphHandler:
    def __init__(self, root, data_buffer):
        self.data_buffer = data_buffer
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(5, 4))
        self.ax_plot, = self.ax1.plot([], [], label="Ax")
        self.ay_plot, = self.ax1.plot([], [], label="Ay")
        self.az_plot, = self.ax1.plot([], [], label="Az")
        self.gx_plot, = self.ax2.plot([], [], label="Gx")
        self.gy_plot, = self.ax2.plot([], [], label="Gy")
        self.gz_plot, = self.ax2.plot([], [], label="Gz")
        self.ax1.legend()
        self.ax2.legend()
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack()

    def update_graph(self):
        if not self.data_buffer:
            return

        x_vals = range(len(self.data_buffer))
        ax_vals = [data[0] for data in self.data_buffer]
        ay_vals = [data[1] for data in self.data_buffer]
        az_vals = [data[2] for data in self.data_buffer]
        gx_vals = [data[3] for data in self.data_buffer]
        gy_vals = [data[4] for data in self.data_buffer]
        gz_vals = [data[5] for data in self.data_buffer]

        self.ax_plot.set_data(x_vals, ax_vals)
        self.ay_plot.set_data(x_vals, ay_vals)
        self.az_plot.set_data(x_vals, az_vals)
        self.gx_plot.set_data(x_vals, gx_vals)
        self.gy_plot.set_data(x_vals, gy_vals)
        self.gz_plot.set_data(x_vals, gz_vals)

        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()
        self.canvas.draw()
