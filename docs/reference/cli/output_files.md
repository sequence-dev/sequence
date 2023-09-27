# Output File

The output file of *Sequence* is a netcdf-formatted file that records the
generated stratigraphy. Output parameters are controlled through the
[output section](the-output-section) of the [parameter file](the-parameter-file).


```bash
ncdump -h sequence.nc
```

```ncl
dimensions:
	time = UNLIMITED ; // (48 currently)
	node = 100 ;
	link = 497 ;
	face = 295 ;
	cell = 98 ;
	grid = 1 ;
	layer = UNLIMITED ; // (4710 currently)
variables:
	double time(time) ;
	double x_of_node(node) ;
	double y_of_node(node) ;
	double x_of_link(link) ;
	double y_of_link(link) ;
	double x_of_face(face) ;
	double y_of_face(face) ;
	double x_of_cell(cell) ;
	double y_of_cell(cell) ;
	double at_node\:topographic__elevation(time, node) ;
	double at_node\:bedrock_surface__elevation(time, node) ;
	double at_node\:sediment_deposit__thickness(time, node) ;
	double at_link\:hillslope_sediment__unit_volume_flux(time, link) ;
	double at_link\:topographic__gradient(time, link) ;
	double at_grid\:x_of_shelf_edge(time, grid) ;
	double at_grid\:sea_level__increment_of_elevation(time, grid) ;
	double at_grid\:x_of_shore(time, grid) ;
	double at_grid\:sediment_load(time, grid) ;
	double at_grid\:sea_level__elevation(time, grid) ;
	double at_layer\:age(layer, cell) ;
	double at_layer\:water_depth(layer, cell) ;
	double at_layer\:t0(layer, cell) ;
	double at_layer\:percent_sand(layer, cell) ;
	double at_layer\:porosity(layer, cell) ;
	double at_layer\:thickness(layer, cell) ;
}
```
