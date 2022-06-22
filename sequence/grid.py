from landlab import RasterModelGrid


class SequenceModelGrid(RasterModelGrid):
    def __init__(self, n_cols, spacing=100.0):
        super().__init__((3, n_cols), xy_spacing=spacing)

        self.status_at_node[self.nodes_at_top_edge] = self.BC_NODE_IS_CLOSED
        self.status_at_node[self.nodes_at_bottom_edge] = self.BC_NODE_IS_CLOSED

        self.at_node["sediment_deposit__thickness"] = self.zeros(at="node")
        self.at_grid["sea_level__elevation"] = 0.0
