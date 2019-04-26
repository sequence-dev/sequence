from landlab.components.flexure import Flexure1D
import numpy as np

class SedimentFlexure(Flexure1D):

    _name = "Sediment-loading flexure"

    _input_var_names = ("sediment_deposit__thickness", "bedrock_surface__elevation")

    _output_var_names = (
        "bedrock_surface__increment_of_elevation",
        "bedrock_surface__elevation",
    )

    _var_units = {
        "sediment_deposit__thickness": "m",
        "bedrock_surface__increment_of_elevation": "m",
        "bedrock_surface__elevation": "m",
    }

    _var_mapping = {
        "sediment_deposit__thickness": "node",
        "bedrock_surface__increment_of_elevation": "node",
        "bedrock_surface__elevation": "node",
    }

    _var_doc = {
        "sediment_deposit__thickness": "Thickness of deposited or eroded sediment",
        "bedrock_surface__increment_of_elevation": "Amount of subsidence due to sediment loading",
        "bedrock_surface__elevation": "New bedrock elevation following subsidence",
    }

    def __init__(self, grid, rho_sediment=1600.0, isostasytime=7000.0, **kwds):
        self._rho_sediment = rho_sediment
        self._isostasytime = isostasytime
        self._dt = 100.  #default timestep = 100 y
      
        Flexure1D.__init__(self, grid, **kwds)

        self.grid.add_zeros("lithosphere__increment_of_overlying_pressure", at="node")
        self.grid.add_zeros("lithosphere_surface__increment_of_elevation", at="node")
        self.subs_pool = self.grid.add_zeros('node','subsidence_pool')


    @property
    def rho_sediment(self):
        return self._rho_sediment

    def update(self):

        if self._isostasytime > 0.:
            isostasyfrac = (1 - np.exp(-1.* self._dt/self._isostasytime))
        else:
            isostasyfrac = 1.

        self.grid.at_node["lithosphere_surface__increment_of_elevation"][:] = 0.0

        dz = self.grid.at_node["sediment_deposit__thickness"]
        self.grid.at_node["lithosphere__increment_of_overlying_pressure"][:] = (
            dz * self.rho_sediment * self.gravity * self.grid.dx
        )

        Flexure1D.update(self)

        dz = self.grid.at_node["lithosphere_surface__increment_of_elevation"]
        self.subs_pool[:] += dz
        dz = self.subs_pool[:] * isostasyfrac
        self.subs_pool[:] = self.subs_pool[:] - dz
        
	
        self.grid.at_node["bedrock_surface__increment_of_elevation"][:] = dz

        self.grid.at_node["bedrock_surface__elevation"] -= dz
        self.grid.at_node["topographic__elevation"] -= dz

    def run_one_step(self, dt=100.):
        self._dt = dt
        self.update()
