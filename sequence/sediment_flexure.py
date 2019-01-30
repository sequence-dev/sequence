from landlab.components.flexure import Flexure


class SedimentFlexure(Flexure):

    _name = "Sediment-loading flexure"

    _input_var_names = ("sediment_deposit__thickness", "bedrock_surface__elevation")

    _output_var_names = (
        "bedrock_surface__elevation_increment",
        "bedrock_surface__elevation",
    )

    _var_units = {
        "sediment_deposit__thickness": "m",
        "bedrock_surface__elevation_increment": "m",
        "bedrock_surface__elevation": "m",
    }

    _var_mapping = {
        "sediment_deposit__thickness": "node",
        "bedrock_surface__elevation_increment": "node",
        "bedrock_surface__elevation": "node",
    }

    _var_doc = {
        "sediment_deposit__thickness": "Thickness of deposited or eroded sediment",
        "bedrock_surface__elevation_increment": "Amount of subsidence due to sediment loading",
        "bedrock_surface__elevation": "New bedrock elevation following subsidence",
    }

    # @use_file_name_or_kwds
    def __init__(self, grid, rho_sediment=1600., **kwds):
        self._rho_sediment = rho_sediment

        Flexure.__init__(self, grid, **kwds)

        self.grid.add_zeros("lithosphere__overlying_pressure_increment", at="node")
        self.grid.add_zeros("lithosphere_surface__elevation_increment", at="node")

    @property
    def rho_sediment(self):
        return self._rho_sediment

    def update(self):
        dz = self.grid.at_node["sediment_deposit__thickness"]
        self.grid.at_node["lithosphere__overlying_pressure_increment"][:] = (
            dz * self.rho_sediment * self.gravity
        )

        Flexure.update(self)

        dz = self.grid.at_node["lithosphere_surface__elevation_increment"]
        self.grid.at_node["bedrock_surface__elevation_increment"][:] = dz

        self.grid.at_node["bedrock_surface__elevation"] -= dz
        self.grid.at_node["topographic__elevation"] -= dz

    def run_one_step(self, dt=None):
        self.update()
