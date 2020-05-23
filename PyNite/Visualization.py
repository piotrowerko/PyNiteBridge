# Import the Visualization Toolkit if it's not alread imported
# You must be running a 64 bit version of Python for this to work
import vtk
from numpy import array, empty, append
from math import isclose, sqrt

#%%
def RenderModel(model, text_height=5, deformed_shape=False, deformed_scale=30, render_loads=True, combo_name='Combo 1', case=None):

  # Input validation
  if deformed_shape == True and case != None:
    print('Error: Deformed shape is only available for load combinations, not load cases.')
    return

  visNodes = []
  for node in model.Nodes:
    visNodes.append(VisNode(node, text_height))

  visAuxNodes = []
  for auxnode in model.auxNodes:
    visAuxNodes.append(VisNode(auxnode, text_height, color='red'))

  visMembers = []
  for member in model.Members:
    visMembers.append(VisMember(member, model.Nodes, text_height))

  visPlates = []
  for plate in model.Plates:
    visPlates.append(VisPlate(plate, model.Nodes, text_height))
  
  # Create a window
  window = vtk.vtkRenderWindow()

  # Set the pixel width and length of the window
  window.SetSize(500, 500)

  # Set up the interactor
  # The interactor style determines how user interactions affect the view
  interactor = vtk.vtkRenderWindowInteractor()
  style = vtk.vtkInteractorStyleTrackballCamera() # The trackball camera style behaves a lot like most CAD programs
  interactor.SetInteractorStyle(style)
  interactor.SetRenderWindow(window)

  # Create a renderer
  renderer = vtk.vtkRenderer()
  window.AddRenderer(renderer)
  
  # Add actors for each member
  for visMember in visMembers:

    # Add the actor for the member
    renderer.AddActor(visMember.actor)

    # Add the actor for the member label
    renderer.AddActor(visMember.lblActor)

    # Set the text to follow the camera as the user interacts
    # This next line will require us to reset the camera when we're done (below)
    visMember.lblActor.SetCamera(renderer.GetActiveCamera())

  # Add actors for each node
  for visNode in visNodes:

    # Add the actor for the node
    renderer.AddActor(visNode.actor)

    # Add the actor for the node label
    renderer.AddActor(visNode.lblActor)

    # Set the text to follow the camera as the user interacts
    # This next line will require us to reset the camera when we're done (below)
    visNode.lblActor.SetCamera(renderer.GetActiveCamera())

  # Add actors for each plate
  for visPlate in visPlates:

    # Add the actors for the plate
    renderer.AddActor(visPlate.actor)

    # Add the actor for the plate label
    renderer.AddActor(visPlate.lblActor)

    # Set the text to follow the camera as the user interacts
    # This next line will require us to reset the camera when we're done (below)
    visPlate.lblActor.SetCamera(renderer.GetActiveCamera())

  # Add actors for each auxnode
  for visAuxNode in visAuxNodes:

    # Add the actor for the node
    renderer.AddActor(visAuxNode.actor)

    # Add the actor for the node label
    renderer.AddActor(visAuxNode.lblActor)

    # Set the text to follow the camera as the user interacts
    # This next line will require us to reset the camera when we're done (below)
    visAuxNode.lblActor.SetCamera(renderer.GetActiveCamera())

  # Render the deformed shape if requested
  if deformed_shape == True:
    __DeformedShape(model, renderer, deformed_scale, text_height, combo_name)

  # Render the loads if requested
  if combo_name != None or case !=None:
    __RenderLoads(model, renderer, text_height, combo_name, case)

  # Setting the background to blue.
  renderer.SetBackground(0.1, 0.1, 0.4)

  # Reset the camera
  renderer.ResetCamera()

  window.Render()
  interactor.Start()

#%%
def __DeformedShape(model, renderer, scale_factor, text_height, combo_name):

  visDeformedNodes = []
  for node in model.Nodes:
    visDeformedNodes.append(VisDeformedNode(node, scale_factor, text_height, combo_name))
  
  visDeformedMembers = []
  for member in model.Members:
    visDeformedMembers.append(VisDeformedMember(member, model.Nodes, scale_factor, text_height, combo_name))

  # Add actors for each deformed member
  for visDeformedMember in visDeformedMembers:

    # Add the actor for the deformed member
    renderer.AddActor(visDeformedMember.polylineActor)

  # Add actors for each deformed node
  for visDeformedNode in visDeformedNodes:

    # Add the actor for the node
    renderer.AddActor(visDeformedNode.actor)

    # Add the actor for the node label
    renderer.AddActor(visDeformedNode.lblActor)

    # Set the text to follow the camera as the user interacts
    # This next line will require us to reset the camera when we're done (below)
    visDeformedNode.lblActor.SetCamera(renderer.GetActiveCamera())

#%%
def __RenderLoads(model, renderer, text_height, combo_name, case):

  # Get the maximum load magnitudes that will be used to normalize the display scale
  maxPtLoad, maxMoment, maxDistLoad = __MaxLoads(model, combo_name, case)

  # Display the requested load combination, or 'Combo 1' if no load combo or case has been specified
  if case == None:

    # Ensure a load combination name has been specified. If not the default of 'Combo 1' will be used.
    if combo_name == None:
      combo = 'Combo 1'
    else:
      combo = combo_name

    # Step through each node
    for node in model.Nodes:

      # Step through and display each nodal load
      for load in node.NodeLoads:
        
        # Determine if this load is part of the requested load combination
        if load[2] in model.LoadCombos[combo].factors:
          
          # Calculate the factored value for this load and it's sign (positive or negative)
          load_value = load[1]*model.LoadCombos[combo].factors[load[2]]
          sign = load_value/abs(load_value)
          
          # Display the load
          if load[0] == 'FX':
            ptLoad = VisPtLoad((node.X - 0.6*text_height*sign, node.Y, node.Z), [1, 0, 0], load_value/maxPtLoad*5*text_height, str(load_value), text_height)
            renderer.AddActor(ptLoad.actor)
            renderer.AddActor(ptLoad.lblActor)
            ptLoad.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'FY':
            ptLoad = VisPtLoad((node.X, node.Y - 0.6*text_height*sign, node.Z), [0, 1, 0], load_value/maxPtLoad*5*text_height, str(load_value), text_height)
            renderer.AddActor(ptLoad.actor)
            renderer.AddActor(ptLoad.lblActor)
            ptLoad.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'FZ':
            ptLoad = VisPtLoad((node.X, node.Y, node.Z - 0.6*text_height*sign), [0, 0, 1], load_value/maxPtLoad*5*text_height, str(load_value), text_height)
            renderer.AddActor(ptLoad.actor)
            renderer.AddActor(ptLoad.lblActor)
            ptLoad.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'MX':
            moment = VisMoment((node.X, node.Y, node.Z), (1*sign, 0, 0), abs(load_value)/maxMoment*2.5*text_height, str(load_value), text_height)
            renderer.AddActor(moment.actor)
            renderer.AddActor(moment.lblActor)
            moment.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'MY':
            moment = VisMoment((node.X, node.Y, node.Z), (0, 1*sign, 0), abs(load_value)/maxMoment*2.5*text_height, str(load_value), text_height)
            renderer.AddActor(moment.actor)
            renderer.AddActor(moment.lblActor)
            moment.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'MZ':
            moment = VisMoment((node.X, node.Y, node.Z), (0, 0, 1*sign), abs(load_value)/maxMoment*2.5*text_height, str(load_value), text_height)
            renderer.AddActor(moment.actor)
            renderer.AddActor(moment.lblActor)
            moment.lblActor.SetCamera(renderer.GetActiveCamera())

    # Step through each member
    for member in model.Members:

      # Get the direction cosines for the member's local axes
      dir_cos = member.T()[0:3, 0:3]

      # Get the starting point for the member
      x_start, y_start, z_start = member.iNode.X, member.iNode.Y, member.iNode.Z

      # Step through each member point load
      for load in member.PtLoads:

        # Determine if this load is part of the requested load combination
        if load[3] in model.LoadCombos[combo].factors:

          # Calculate the factored value for this load and it's sign (positive or negative)
          load_value = load[1]*model.LoadCombos[combo].factors[load[3]]
          sign = load_value/abs(load_value)

          # Calculate the loads location in 3D space
          x = load[2]
          position = [x_start + dir_cos[0, 0]*x, y_start + dir_cos[0, 1]*x, z_start + dir_cos[0, 2]*x]

          # Display the load
          if load[0] == 'Fx':
            ptLoad = VisPtLoad(position, dir_cos[0, :], load_value/maxPtLoad*5*text_height, str(load_value), text_height)
            renderer.AddActor(ptLoad.actor)
            renderer.AddActor(ptLoad.lblActor)
            ptLoad.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'Fy':
            ptLoad = VisPtLoad(position, dir_cos[1, :], load_value/maxPtLoad*5*text_height, str(load_value), text_height)
            renderer.AddActor(ptLoad.actor)
            renderer.AddActor(ptLoad.lblActor)
            ptLoad.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'Fz':
            ptLoad = VisPtLoad(position, dir_cos[2, :], load_value/maxPtLoad*5*text_height, str(load_value), text_height)
            renderer.AddActor(ptLoad.actor)
            renderer.AddActor(ptLoad.lblActor)
            ptLoad.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'Mx':
            moment = VisMoment(position, dir_cos[0, :]*sign, abs(load_value)/maxMoment*2.5*text_height, str(load_value), text_height)
            renderer.AddActor(moment.actor)
            renderer.AddActor(moment.lblActor)
            moment.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'My':
            moment = VisMoment(position, dir_cos[1, :]*sign, abs(load_value)/maxMoment*2.5*text_height, str(load_value), text_height)
            renderer.AddActor(moment.actor)
            renderer.AddActor(moment.lblActor)
            moment.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'Mz':
            moment = VisMoment(position, dir_cos[2, :]*sign, abs(load_value)/maxMoment*2.5*text_height, str(load_value), text_height)
            renderer.AddActor(moment.actor)
            renderer.AddActor(moment.lblActor)
            moment.lblActor.SetCamera(renderer.GetActiveCamera())
      
      # Step through each member distributed load
      for load in member.DistLoads:

        # Determine if this load is part of the requested load combination
        if load[5] in model.LoadCombos[combo].factors:

          # Calculate the factored value for this load and it's sign (positive or negative)
          w1 = load[1]*model.LoadCombos[combo].factors[load[5]]
          w2 = load[2]*model.LoadCombos[combo].factors[load[5]]
          sign1 = w1/abs(w1)
          sign2 = w2/abs(w2)

          # Calculate the loads location in 3D space
          x1 = load[3]
          x2 = load[4]
          position1 = [x_start + dir_cos[0, 0]*x1, y_start + dir_cos[0, 1]*x1, z_start + dir_cos[0, 2]*x1]
          position2 = [x_start + dir_cos[0, 0]*x2, y_start + dir_cos[0, 1]*x2, z_start + dir_cos[0, 2]*x2]
          
          # Display the load
          if load[0] == 'Fx':
            distLoad = VisDistLoad(position1, position2, dir_cos[0, :], w1/maxDistLoad*5*text_height, w2/maxDistLoad*5*text_height, str(w1), str(w2), text_height)
            renderer.AddActor(distLoad.actor)
            renderer.AddActor(distLoad.lblActors[0])
            renderer.AddActor(distLoad.lblActors[1])
            distLoad.lblActors[0].SetCamera(renderer.GetActiveCamera())
            distLoad.lblActors[1].SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'Fy':
            distLoad = VisDistLoad(position1, position2, dir_cos[1, :], w1/maxDistLoad*5*text_height, w2/maxDistLoad*5*text_height, str(w1), str(w2), text_height)
            renderer.AddActor(distLoad.actor)
            renderer.AddActor(distLoad.lblActors[0])
            renderer.AddActor(distLoad.lblActors[1])
            distLoad.lblActors[0].SetCamera(renderer.GetActiveCamera())
            distLoad.lblActors[1].SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'Fz':
            distLoad = VisDistLoad(position1, position2, dir_cos[2, :], w1/maxDistLoad*5*text_height, w2/maxDistLoad*5*text_height, str(w1), str(w2), text_height)
            renderer.AddActor(distLoad.actor)
            renderer.AddActor(distLoad.lblActors[0])
            renderer.AddActor(distLoad.lblActors[1])
            distLoad.lblActors[0].SetCamera(renderer.GetActiveCamera())
            distLoad.lblActors[1].SetCamera(renderer.GetActiveCamera())

  # Display the requested load case
  else:

    # Step through each node
    for node in model.Nodes:

      # Step through and display each nodal load
      for load in node.NodeLoads:
        
        # Determine if this load is part of the requested load case
        if load[2] == case:
          
          # Calculate the factored value for this load and it's sign (positive or negative)
          load_value = load[1]
          sign = load_value/abs(load_value)
          
          # Display the load
          if load[0] == 'FX':
            ptLoad = VisPtLoad((node.X - 0.6*text_height*sign, node.Y, node.Z), [1, 0, 0], load_value/maxPtLoad*5*text_height, str(load_value), text_height)
            renderer.AddActor(ptLoad.actor)
            renderer.AddActor(ptLoad.lblActor)
            ptLoad.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'FY':
            ptLoad = VisPtLoad((node.X, node.Y - 0.6*text_height*sign, node.Z), [0, 1, 0], load_value/maxPtLoad*5*text_height, str(load_value), text_height)
            renderer.AddActor(ptLoad.actor)
            renderer.AddActor(ptLoad.lblActor)
            ptLoad.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'FZ':
            ptLoad = VisPtLoad((node.X, node.Y, node.Z - 0.6*text_height*sign), [0, 0, 1], load_value/maxPtLoad*5*text_height, str(load_value), text_height)
            renderer.AddActor(ptLoad.actor)
            renderer.AddActor(ptLoad.lblActor)
            ptLoad.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'MX':
            moment = VisMoment((node.X, node.Y, node.Z), (1*sign, 0, 0), abs(load_value)/maxMoment*2.5*text_height, str(load_value), text_height)
            renderer.AddActor(moment.actor)
            renderer.AddActor(moment.lblActor)
            moment.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'MY':
            moment = VisMoment((node.X, node.Y, node.Z), (0, 1*sign, 0), abs(load_value)/maxMoment*2.5*text_height, str(load_value), text_height)
            renderer.AddActor(moment.actor)
            renderer.AddActor(moment.lblActor)
            moment.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'MZ':
            moment = VisMoment((node.X, node.Y, node.Z), (0, 0, 1*sign), abs(load_value)/maxMoment*2.5*text_height, str(load_value), text_height)
            renderer.AddActor(moment.actor)
            renderer.AddActor(moment.lblActor)
            moment.lblActor.SetCamera(renderer.GetActiveCamera())

    # Step through each member
    for member in model.Members:

      # Get the direction cosines for the member's local axes
      dir_cos = member.T()[0:3, 0:3]

      # Get the starting point for the member
      x_start, y_start, z_start = member.iNode.X, member.iNode.Y, member.iNode.Z

      # Step through each member point load
      for load in member.PtLoads:

        # Determine if this load is part of the requested load combination
        if load[3] == case:

          # Calculate the factored value for this load and it's sign (positive or negative)
          load_value = load[1]
          sign = load_value/abs(load_value)

          # Calculate the loads location in 3D space
          x = load[2]
          position = [x_start + dir_cos[0, 0]*x, y_start + dir_cos[0, 1]*x, z_start + dir_cos[0, 2]*x]

          # Display the load
          if load[0] == 'Fx':
            ptLoad = VisPtLoad(position, dir_cos[0, :], load_value/maxPtLoad*5*text_height, str(load_value), text_height)
            renderer.AddActor(ptLoad.actor)
            renderer.AddActor(ptLoad.lblActor)
            ptLoad.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'Fy':
            ptLoad = VisPtLoad(position, dir_cos[1, :], load_value/maxPtLoad*5*text_height, str(load_value), text_height)
            renderer.AddActor(ptLoad.actor)
            renderer.AddActor(ptLoad.lblActor)
            ptLoad.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'Fz':
            ptLoad = VisPtLoad(position, dir_cos[2, :], load_value/maxPtLoad*5*text_height, str(load_value), text_height)
            renderer.AddActor(ptLoad.actor)
            renderer.AddActor(ptLoad.lblActor)
            ptLoad.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'Mx':
            moment = VisMoment(position, dir_cos[0, :]*sign, abs(load_value)/maxMoment*2.5*text_height, str(load_value), text_height)
            renderer.AddActor(moment.actor)
            renderer.AddActor(moment.lblActor)
            moment.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'My':
            moment = VisMoment(position, dir_cos[1, :]*sign, abs(load_value)/maxMoment*2.5*text_height, str(load_value), text_height)
            renderer.AddActor(moment.actor)
            renderer.AddActor(moment.lblActor)
            moment.lblActor.SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'Mz':
            moment = VisMoment(position, dir_cos[2, :]*sign, abs(load_value)/maxMoment*2.5*text_height, str(load_value), text_height)
            renderer.AddActor(moment.actor)
            renderer.AddActor(moment.lblActor)
            moment.lblActor.SetCamera(renderer.GetActiveCamera())
      
      # Step through each member distributed load
      for load in member.DistLoads:

        # Determine if this load is part of the requested load combination
        if load[5] == case:

          # Calculate the factored value for this load and it's sign (positive or negative)
          w1 = load[1]
          w2 = load[2]
          sign1 = w1/abs(w1)
          sign2 = w2/abs(w2)

          # Calculate the loads location in 3D space
          x1 = load[3]
          x2 = load[4]
          position1 = [x_start + dir_cos[0, 0]*x1, y_start + dir_cos[0, 1]*x1, z_start + dir_cos[0, 2]*x1]
          position2 = [x_start + dir_cos[0, 0]*x2, y_start + dir_cos[0, 1]*x2, z_start + dir_cos[0, 2]*x2]
          
          # Display the load
          if load[0] == 'Fx':
            distLoad = VisDistLoad(position1, position2, dir_cos[0, :], w1/maxDistLoad*5*text_height, w2/maxDistLoad*5*text_height, str(w1), str(w2), text_height)
            renderer.AddActor(distLoad.actor)
            renderer.AddActor(distLoad.lblActors[0])
            renderer.AddActor(distLoad.lblActors[1])
            distLoad.lblActors[0].SetCamera(renderer.GetActiveCamera())
            distLoad.lblActors[1].SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'Fy':
            distLoad = VisDistLoad(position1, position2, dir_cos[1, :], w1/maxDistLoad*5*text_height, w2/maxDistLoad*5*text_height, str(w1), str(w2), text_height)
            renderer.AddActor(distLoad.actor)
            renderer.AddActor(distLoad.lblActors[0])
            renderer.AddActor(distLoad.lblActors[1])
            distLoad.lblActors[0].SetCamera(renderer.GetActiveCamera())
            distLoad.lblActors[1].SetCamera(renderer.GetActiveCamera())
          elif load[0] == 'Fz':
            distLoad = VisDistLoad(position1, position2, dir_cos[2, :], w1/maxDistLoad*5*text_height, w2/maxDistLoad*5*text_height, str(w1), str(w2), text_height)
            renderer.AddActor(distLoad.actor)
            renderer.AddActor(distLoad.lblActors[0])
            renderer.AddActor(distLoad.lblActors[1])
            distLoad.lblActors[0].SetCamera(renderer.GetActiveCamera())
            distLoad.lblActors[1].SetCamera(renderer.GetActiveCamera())


#%%
def __MaxLoads(model, combo_name=None, case=None):

  maxPtLoad = 0
  maxMoment = 0
  maxDistLoad = 0

  # Find the requested load combination, or use 'Combo 1' if no load combo or case has been specified
  if (combo_name == None and case == None) or combo_name != None:

    if combo_name == None:
      combo = 'Combo 1'
    else:
      combo = combo_name

    # Step through each node
    for node in model.Nodes:

      # Step through each nodal load to find the largest one
      for load in node.NodeLoads:
        
        # Find the largest loads in the load combination
        if load[2] in model.LoadCombos[combo].factors:
          if load[0] == 'FX' or load[0] == 'FY' or load[0] == 'FZ':
            if abs(load[1]*model.LoadCombos[combo].factors[load[2]]) > maxPtLoad:
              maxPtLoad = abs(load[1]*model.LoadCombos[combo].factors[load[2]])
          else:
            if abs(load[1]*model.LoadCombos[combo].factors[load[2]]) > maxMoment:
              maxMoment = abs(load[1]*model.LoadCombos[combo].factors[load[2]])

    # Step through each member
    for member in model.Members:

      # Step through each member point load
      for load in member.PtLoads:
        
        # Find and store the largest point load and moment in the load combination
        if load[3] in model.LoadCombos[combo].factors:

          if load[0] == 'Fx' or load[0] == 'Fy' or load[0] == 'Fz':
            if abs(load[1]*model.LoadCombos[combo].factors[load[3]]) > maxPtLoad:
              maxPtLoad = abs(load[1]*model.LoadCombos[combo].factors[load[3]])
          else:
            if abs(load[1]*model.LoadCombos[combo].factors[load[3]]) > maxMoment:
              maxMoment = abs(load[1]*model.LoadCombos[combo].factors[load[3]])

      # Step through each member distributed load
      for load in member.DistLoads:

        #Find and store the largest distributed load in the load combination
        if load[5] in model.LoadCombos[combo].factors:

          if abs(load[1]*model.LoadCombos[combo].factors[load[5]]) > maxDistLoad:
            maxDistLoad = abs(load[1]*model.LoadCombos[combo].factors[load[5]])
          if abs(load[2]*model.LoadCombos[combo].factors[load[5]]) > maxDistLoad:
            maxDistLoad = abs(load[2]*model.LoadCombos[combo].factors[load[5]])

  # Behavior if case has been specified and combo has not been specified
  else:
    
    # Step through each node
    for node in model.Nodes:

      # Step through each nodal load to find the largest one
      for load in node.NodeLoads:
        
        # Find the largest loads in the load combination
        if load[2] == case:
          if load[0] == 'FX' or load[0] == 'FY' or load[0] == 'FZ':
            if abs(load[1]) > maxPtLoad:
              maxPtLoad = abs(load[1])
          else:
            if abs(load[1]) > maxMoment:
              maxMoment = abs(load[1])

    # Step through each member
    for member in model.Members:

      # Step through each member point load
      for load in member.PtLoads:
        
        # Find and store the largest point load and moment in the load combination
        if load[3] == case:

          if load[0] == 'FX' or load[0] == 'FY' or load[0] == 'FZ':
            if abs(load[1]) > maxPtLoad:
              maxPtLoad = abs(load[1])
          else:
            if abs(load[1]) > maxMoment:
              maxMoment = abs(load[1])

      # Step through each member distributed load
      for load in member.DistLoads:

        #Find and store the largest distributed load in the load combination
        if load[5] == case:

          if abs(load[1]) > maxDistLoad:
            maxDistLoad = abs(load[1])
          if abs(load[2]) > maxDistLoad:
            maxDistLoad = abs(load[2])

  # Return the maximum loads in the load combination or load case
  return maxPtLoad, maxMoment, maxDistLoad

#%%
# Converts a node object into a node for the viewer
class VisNode():

  # Constructor
  def __init__(self, node, text_height=5, color=None):

    # Create an append filter to append all the sources related to the node into a single 'PolyData' object
    append_filter = vtk.vtkAppendPolyData()

    # Get the node's position
    X = node.X # Global X coordinate
    Y = node.Y # Global Y coordinate
    Z = node.Z # Global Z coordinate

    # Generate a sphere source for the node
    sphere = vtk.vtkSphereSource()
    sphere.SetCenter(X, Y, Z)
    sphere.SetRadius(0.6*text_height)
    sphere.Update()

    # Append the sphere to the append filter
    poly_data = vtk.vtkPolyData()
    poly_data.ShallowCopy(sphere.GetOutput())
    append_filter.AddInputData(poly_data)

    # Create the text for the node label
    label = vtk.vtkVectorText()
    label.SetText(node.Name)
    
    # Set up a mapper for the node label
    lblMapper = vtk.vtkPolyDataMapper()
    lblMapper.SetInputConnection(label.GetOutputPort())

    # Set up an actor for the node label
    self.lblActor = vtk.vtkFollower()
    self.lblActor.SetMapper(lblMapper)
    self.lblActor.SetScale(text_height, text_height, text_height)
    self.lblActor.SetPosition(X + 0.6*text_height, Y + 0.6*text_height, Z)

    # Generate any supports that occur at the node
    # Check for a fixed suppport
    if node.SupportDX == True and node.SupportDY == True and node.SupportDZ == True \
    and node.SupportRX == True and node.SupportRY == True and node.SupportRZ == True:

      # Create the fixed support
      support = vtk.vtkCubeSource()
      support.SetCenter(node.X, node.Y, node.Z)
      support.SetXLength(text_height*1.2)
      support.SetYLength(text_height*1.2)
      support.SetZLength(text_height*1.2)

      # Copy and append the support data to the append filter
      support.Update()
      poly_data = vtk.vtkPolyData()
      poly_data.ShallowCopy(support.GetOutput())
      append_filter.AddInputData(poly_data)
    
    # Check for a pinned support
    elif node.SupportDX == True and node.SupportDY == True and node.SupportDZ == True \
    and node.SupportRX == True and node.SupportRY == True and node.SupportRZ == True:
      
      # Create the pinned support
      support = vtk.vtkConeSource()
      support.SetCenter(node.X, node.Y-0.6*text_height, node.Z)
      support.SetDirection((0, 1, 0))
      support.SetHeight(text_height*1.2)
      support.SetRadius(text_height*1.2)

      # Copy and append the support data to the append filter
      support.Update()
      poly_data = vtk.vtkPolyData()
      poly_data.ShallowCopy(support.GetOutput())
      append_filter.AddInputData(poly_data)
    
    # Other support conditions
    else:

      # Restrained against X translation
      if node.SupportDX == True:
        
        # Create the support
        support1 = vtk.vtkLineSource()  # The line showing the support direction
        support1.SetPoint1(node.X-text_height, node.Y, node.Z)
        support1.SetPoint2(node.X+text_height, node.Y, node.Z)

        # Copy and append the support data to the append filter
        support1.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support1.GetOutput())
        append_filter.AddInputData(poly_data)

        support2 = vtk.vtkConeSource()
        support2.SetCenter(node.X-text_height, node.Y, node.Z)
        support2.SetDirection((1, 0, 0))
        support2.SetHeight(text_height*0.6)
        support2.SetRadius(text_height*0.3)

        # Copy and append the support data to the append filter
        support2.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support2.GetOutput())
        append_filter.AddInputData(poly_data)

        support3 = vtk.vtkConeSource()
        support3.SetCenter(node.X+text_height, node.Y, node.Z)
        support3.SetDirection((-1, 0, 0))
        support3.SetHeight(text_height*0.6)
        support3.SetRadius(text_height*0.3)

        # Copy and append the support data to the append filter
        support3.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support3.GetOutput())
        append_filter.AddInputData(poly_data)
      
      # Restrained against Y translation
      if node.SupportDY == True:
        
        # Create the support
        support1 = vtk.vtkLineSource()  # The line showing the support direction
        support1.SetPoint1(node.X, node.Y-text_height, node.Z)
        support1.SetPoint2(node.X, node.Y+text_height, node.Z)

        # Copy and append the support data to the append filter
        support1.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support1.GetOutput())
        append_filter.AddInputData(poly_data)

        support2 = vtk.vtkConeSource()
        support2.SetCenter(node.X, node.Y-text_height, node.Z)
        support2.SetDirection((0, 1, 0))
        support2.SetHeight(text_height*0.6)
        support2.SetRadius(text_height*0.3)

        # Copy and append the support data to the append filter
        support2.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support2.GetOutput())
        append_filter.AddInputData(poly_data)

        support3 = vtk.vtkConeSource()
        support3.SetCenter(node.X, node.Y+text_height, node.Z)
        support3.SetDirection((0, -1, 0))
        support3.SetHeight(text_height*0.6)
        support3.SetRadius(text_height*0.3)

        # Copy and append the support data to the append filter
        support3.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support3.GetOutput())
        append_filter.AddInputData(poly_data)
      
      # Restrained against Z translation
      if node.SupportDZ == True:
        
        # Create the support
        support1 = vtk.vtkLineSource()  # The line showing the support direction
        support1.SetPoint1(node.X, node.Y, node.Z-text_height)
        support1.SetPoint2(node.X, node.Y, node.Z+text_height)

        # Copy and append the support data to the append filter
        support1.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support1.GetOutput())
        append_filter.AddInputData(poly_data)

        support2 = vtk.vtkConeSource()
        support2.SetCenter(node.X, node.Y, node.Z-text_height)
        support2.SetDirection((0, 0, 1))
        support2.SetHeight(text_height*0.6)
        support2.SetRadius(text_height*0.3)

        # Copy and append the support data to the append filter
        support2.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support2.GetOutput())
        append_filter.AddInputData(poly_data)

        support3 = vtk.vtkConeSource()
        support3.SetCenter(node.X, node.Y, node.Z+text_height)
        support3.SetDirection((0, 0, -1))
        support3.SetHeight(text_height*0.6)
        support3.SetRadius(text_height*0.3)

        # Copy and append the support data to the append filter
        support3.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support3.GetOutput())
        append_filter.AddInputData(poly_data)

      # Restrained against rotation about the X-axis
      if node.SupportRX == True:
        
        # Create the support
        support1 = vtk.vtkLineSource()  # The line showing the support direction
        support1.SetPoint1(node.X-1.6*text_height, node.Y, node.Z)
        support1.SetPoint2(node.X+1.6*text_height, node.Y, node.Z)

        # Copy and append the support data to the append filter
        support1.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support1.GetOutput())
        append_filter.AddInputData(poly_data)

        support2 = vtk.vtkCubeSource()
        support2.SetCenter(node.X-1.9*text_height, node.Y, node.Z)
        support2.SetXLength(text_height*0.6)
        support2.SetYLength(text_height*0.6)
        support2.SetZLength(text_height*0.6)

        # Copy and append the support data to the append filter
        support2.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support2.GetOutput())
        append_filter.AddInputData(poly_data)

        support3 = vtk.vtkCubeSource()
        support3.SetCenter(node.X+1.9*text_height, node.Y, node.Z)
        support3.SetXLength(text_height*0.6)
        support3.SetYLength(text_height*0.6)
        support3.SetZLength(text_height*0.6)

        # Copy and append the support data to the append filter
        support3.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support3.GetOutput())
        append_filter.AddInputData(poly_data)
      
      # Restrained against rotation about the Y-axis
      if node.SupportRY == True:
        
        # Create the support
        support1 = vtk.vtkLineSource()  # The line showing the support direction
        support1.SetPoint1(node.X, node.Y-1.6*text_height, node.Z)
        support1.SetPoint2(node.X, node.Y+1.6*text_height, node.Z)

        # Copy and append the support data to the append filter
        support1.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support1.GetOutput())
        append_filter.AddInputData(poly_data)

        support2 = vtk.vtkCubeSource()
        support2.SetCenter(node.X, node.Y-1.9*text_height, node.Z)
        support2.SetXLength(text_height*0.6)
        support2.SetYLength(text_height*0.6)
        support2.SetZLength(text_height*0.6)

        # Copy and append the support data to the append filter
        support2.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support2.GetOutput())
        append_filter.AddInputData(poly_data)

        support3 = vtk.vtkCubeSource()
        support3.SetCenter(node.X, node.Y+1.9*text_height, node.Z)
        support3.SetXLength(text_height*0.6)
        support3.SetYLength(text_height*0.6)
        support3.SetZLength(text_height*0.6)

        # Copy and append the support data to the append filter
        support3.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support3.GetOutput())
        append_filter.AddInputData(poly_data)
      
      # Restrained against rotation about the Z-axis
      if node.SupportRZ == True:
        
        # Create the support
        support1 = vtk.vtkLineSource()  # The line showing the support direction
        support1.SetPoint1(node.X, node.Y, node.Z-1.6*text_height)
        support1.SetPoint2(node.X, node.Y, node.Z+1.6*text_height)

        # Copy and append the support data to the append filter
        support1.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support1.GetOutput())
        append_filter.AddInputData(poly_data)

        support2 = vtk.vtkCubeSource()
        support2.SetCenter(node.X, node.Y, node.Z-1.9*text_height)
        support2.SetXLength(text_height*0.6)
        support2.SetYLength(text_height*0.6)
        support2.SetZLength(text_height*0.6)

        # Copy and append the support data to the append filter
        support2.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support2.GetOutput())
        append_filter.AddInputData(poly_data)

        support3 = vtk.vtkCubeSource()
        support3.SetCenter(node.X, node.Y, node.Z+1.9*text_height)
        support3.SetXLength(text_height*0.6)
        support3.SetYLength(text_height*0.6)
        support3.SetZLength(text_height*0.6)

        # Copy and append the support data to the append filter
        support3.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(support3.GetOutput())
        append_filter.AddInputData(poly_data)
    
    # Update the append filter
    append_filter.Update()

    # Create a mapper and actor
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(append_filter.GetOutputPort())
    self.actor = vtk.vtkActor()

    # Add color to the actors
    if color == 'red':
      self.actor.GetProperty().SetColor(255, 0, 0) # Red
      self.lblActor.GetProperty().SetColor(255, 0, 0) # Red
    elif color == 'yellow':
      self.actor.GetProperty().SetColor(255, 255, 0) # Yellow
      self.lblActor.GetProperty().SetColor(255, 255, 0) # Yellow
    
    # Set the mapper for the node's actor
    self.actor.SetMapper(mapper)

#%%        
# Converts a member object into a member for the viewer
class VisMember():

  # Constructor
  def __init__(self, member, nodes, text_height=5):

    # Generate a line for the member
    line = vtk.vtkLineSource()

    # Step through each node in the model and find the position of the i-node and j-node
    for node in nodes:

      # Check to see if the current node is the i-node
      if node.Name == member.iNode.Name:
        Xi = node.X
        Yi = node.Y
        Zi = node.Z
        line.SetPoint1(Xi, Yi, Zi)

      # Check to see if the current node is the j-node
      elif node.Name == member.jNode.Name:
        Xj = node.X
        Yj = node.Y
        Zj = node.Z
        line.SetPoint2(Xj, Yj, Zj)
    
    # Set up a mapper for the member
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(line.GetOutputPort())

    # Set up an actor for the member
    self.actor = vtk.vtkActor()
    self.actor.SetMapper(mapper)

    # Create the text for the member label
    label = vtk.vtkVectorText()
    label.SetText(member.Name)

    # Set up a mapper for the member label
    lblMapper = vtk.vtkPolyDataMapper()
    lblMapper.SetInputConnection(label.GetOutputPort())

    # Set up an actor for the member label
    self.lblActor = vtk.vtkFollower()
    self.lblActor.SetMapper(lblMapper)
    self.lblActor.SetScale(text_height, text_height, text_height)
    self.lblActor.SetPosition((Xi+Xj)/2, (Yi+Yj)/2, (Zi+Zj)/2)

#%%
# Converts a plate object into a plate for the viewer
class VisPlate():

  # Constructor
  def __init__(self, plate, nodes, text_height=5):

    # Generate lines for the plate
    line1 = vtk.vtkLineSource()
    line2 = vtk.vtkLineSource()
    line3 = vtk.vtkLineSource()
    line4 = vtk.vtkLineSource()

    # Step through each node in the model and find the position of the i-node and j-node
    for node in nodes:

      # Check to see if the current node is the i-node
      if node.Name == plate.iNode.Name:
        Xi = node.X
        Yi = node.Y
        Zi = node.Z
        line1.SetPoint1(Xi, Yi, Zi)
        line4.SetPoint2(Xi, Yi, Zi)

      # Check to see if the current node is the j-node
      elif node.Name == plate.jNode.Name:
        Xj = node.X
        Yj = node.Y
        Zj = node.Z
        line1.SetPoint2(Xj, Yj, Zj)
        line2.SetPoint1(Xj, Yj, Zj)

      # Check to see if the current node is the m-node
      elif node.Name == plate.mNode.Name:
        Xm = node.X
        Ym = node.Y
        Zm = node.Z
        line2.SetPoint2(Xm, Ym, Zm)
        line3.SetPoint1(Xm, Ym, Zm)
      
      # Check to see if the current node is the n-node
      elif node.Name == plate.nNode.Name:
        Xn = node.X
        Yn = node.Y
        Zn = node.Z
        line3.SetPoint2(Xn, Yn, Zn)
        line4.SetPoint1(Xn, Yn, Zn)

    # Create a 'vtkAppendPolyData' filter to add all the lines to
    append_filter = vtk.vtkAppendPolyData()

    line1.Update()
    poly_data1 = vtk.vtkPolyData()
    poly_data1.ShallowCopy(line1.GetOutput())
    append_filter.AddInputData(poly_data1)

    line2.Update()
    poly_data2 = vtk.vtkPolyData()
    poly_data2.ShallowCopy(line2.GetOutput())
    append_filter.AddInputData(poly_data2)

    line3.Update()
    poly_data3 = vtk.vtkPolyData()
    poly_data3.ShallowCopy(line3.GetOutput())
    append_filter.AddInputData(poly_data3)

    line4.Update()
    poly_data4 = vtk.vtkPolyData()
    poly_data4.ShallowCopy(line4.GetOutput())
    append_filter.AddInputData(poly_data4)
    
    # Set up a mapper
    mapper = vtk.vtkPolyDataMapper()
    append_filter.Update()
    mapper.SetInputConnection(append_filter.GetOutputPort())

    # Set up an actor
    self.actor = vtk.vtkActor()
    self.actor.SetMapper(mapper)

    # Create the text for the plate label
    label = vtk.vtkVectorText()
    label.SetText(plate.Name)

    # Set up a mapper for the plate label
    lblMapper = vtk.vtkPolyDataMapper()
    lblMapper.SetInputConnection(label.GetOutputPort())

    # Set up an actor for the plate label
    self.lblActor = vtk.vtkFollower()
    self.lblActor.SetMapper(lblMapper)
    self.lblActor.SetScale(text_height, text_height, text_height)
    self.lblActor.SetPosition((Xi+Xj+Xm+Xn)/4, (Yi+Yj+Ym+Yn)/4, (Zi+Zj+Zm+Zn)/4)

#%%
# Converts a node object into a node in its deformed position for the viewer
class VisDeformedNode():
  
  def __init__(self, node, scale_factor, text_height=5, combo_name='Combo 1'):
  
    # Calculate the node's deformed position
    newX = node.X + scale_factor*(node.DX[combo_name])
    newY = node.Y + scale_factor*(node.DY[combo_name])
    newZ = node.Z + scale_factor*(node.DZ[combo_name])

    # Generate a sphere for the node
    sphere = vtk.vtkSphereSource()
    sphere.SetCenter(newX, newY, newZ)
    sphere.SetRadius(0.6*text_height)

    # Set up a mapper for the node
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(sphere.GetOutputPort())

    # Set up an actor for the node
    self.actor = vtk.vtkActor()
    self.actor.GetProperty().SetColor(255, 255, 0) # Yellow
    self.actor.SetMapper(mapper)
        
    # Create the text for the node label
    label = vtk.vtkVectorText()
    label.SetText(node.Name)

    # Set up a mapper for the node label
    lblMapper = vtk.vtkPolyDataMapper()
    lblMapper.SetInputConnection(label.GetOutputPort())

    # Set up an actor for the node label
    self.lblActor = vtk.vtkFollower()
    self.lblActor.SetMapper(lblMapper)
    self.lblActor.SetScale(text_height, text_height, text_height)
    self.lblActor.SetPosition(newX + 0.6*text_height, newY + 0.6*text_height, newZ)
    self.lblActor.GetProperty().SetColor(255, 255, 0) # Yellow

#%%
# Converts a member object into a member in its deformed position for the viewer
class VisDeformedMember():

  def __init__(self, member, nodes, scale_factor, text_height=5, combo_name='Combo 1'):

    L = member.L() # Member length
    T = member.T() # Member local transformation matrix

    cos_x = array([T[0,0:3]]) # Direction cosines of local x-axis
    cos_y = array([T[1,0:3]]) # Direction cosines of local y-axis
    cos_z = array([T[2,0:3]]) # Direction cosines of local z-axis

    # Find the initial position of the local i-node
    # Step through each node
    for node in nodes:
      
      # Check to see if the current node is the i-node
      if node.Name == member.iNode.Name:
        Xi = node.X
        Yi = node.Y
        Zi = node.Z

    # Calculate the local y-axis displacements at 20 points along the member's length
    DY_plot = empty((0,3))
    for i in range(20):

      # Displacements in local coordinates
      dy_tot = member.Deflection('dy', L/19*i, combo_name)

      # Magnified displacements in global coordinates
      DY_plot = append(DY_plot, dy_tot*cos_y*scale_factor, axis=0)

    # Calculate the local z-axis displacements at 20 points along the member's length
    DZ_plot = empty((0,3)) 
    for i in range(20):

      # Displacements in local coordinates
      dz_tot = member.Deflection('dz', L/19*i, combo_name)

      # Magnified displacements in global coordinates
      DZ_plot = append(DZ_plot, dz_tot*cos_z*scale_factor, axis=0)

    # Calculate the local x-axis displacements at 20 points along the member's length
    DX_plot = empty((0,3)) 
    for i in range(20):

      # Displacements in local coordinates
      dx_tot = [[Xi, Yi, Zi]] + (L/19*i + member.Deflection('dx', L/19*i, combo_name)*scale_factor)*cos_x
      
      # Magnified displacements in global coordinates
      DX_plot = append(DX_plot, dx_tot, axis=0)
    
    # Sum the component displacements to obtain overall displacement
    D_plot = (DY_plot + DZ_plot + DX_plot)

    # Generate vtk points
    points = vtk.vtkPoints()
    points.SetNumberOfPoints(len(D_plot))

    for i in range(len(D_plot)):
      points.SetPoint(i, D_plot[i, 0], D_plot[i, 1], D_plot[i, 2])

    # Generate vtk lines
    lines = vtk.vtkCellArray()
    lines.InsertNextCell(len(D_plot))

    for i in range(len(D_plot)):
      lines.InsertCellPoint(i)

    # Create a polyline from the defined points and lines
    polyline = vtk.vtkPolyData()
    polyline.SetPoints(points)
    polyline.SetLines(lines)

    # Set up a mapper
    polylineMapper = vtk.vtkPolyDataMapper()
    polylineMapper.SetInputData(polyline)
    polylineMapper.Update()

    # Set up an actor for the polyline
    self.polylineActor = vtk.vtkActor()
    self.polylineActor.SetMapper(polylineMapper)
    self.polylineActor.GetProperty().SetColor(255,255,0) # Yellow
    
#%%
class VisPtLoad():
  '''
  Creates a point load for the viewer
  '''

  def __init__(self, position, direction, length, label_text=None, text_height=5):
    '''
    Constructor.

    Parameters
    ----------
    position : tuple
      A tuple of X, Y and Z coordinates for the point of the load arrow: (X, Y, Z).
    direction : tuple
      A tuple indicating the direction vector for the load arrow: (i, j, k).
    length : number
      The length of the load arrow.
    tip_length : number
      The height of the arrow head.
    label_text : string
      Text that will show up at the tail of the arrow. If set to 'None' no text will be displayed.
    '''

    # Create a unit vector in the direction of the 'direction' vector
    unitVector = UnitVector(direction)

    # Create a 'vtkAppendPolyData' filter to append the tip and shaft together into a single dataset
    self.append_filter = vtk.vtkAppendPolyData()

    # Determine if the load is positive or negative
    sign = abs(length)/length

    # Generate the tip of the load arrow
    tip_length = abs(length)/4
    radius = abs(length)/16
    tip = vtk.vtkConeSource()
    tip.SetCenter(position[0] - tip_length*sign*0.5*unitVector[0], \
                  position[1] - tip_length*sign*0.5*unitVector[1], \
                  position[2] - tip_length*sign*0.5*unitVector[2])
    tip.SetDirection([direction[0]*sign, direction[1]*sign, direction[2]*sign])
    tip.SetHeight(tip_length)
    tip.SetRadius(radius)
    tip.Update()

    # Add the arrow tip to the append filter
    poly_data = vtk.vtkPolyData()
    poly_data.ShallowCopy(tip.GetOutput())
    self.append_filter.AddInputData(poly_data)
    
    # Create the shaft
    shaft = vtk.vtkLineSource()
    shaft.SetPoint1(position)
    shaft.SetPoint2((position[0]-length*unitVector[0], position[1]-length*unitVector[1], position[2]-length*unitVector[2]))
    shaft.Update()

    # Copy and append the shaft data to the append filter
    poly_data = vtk.vtkPolyData()
    poly_data.ShallowCopy(shaft.GetOutput())
    self.append_filter.AddInputData(poly_data)

    # Create a mapper and actor
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(self.append_filter.GetOutputPort())
    self.actor = vtk.vtkActor()
    self.actor.GetProperty().SetColor(0, 255, 0) # Green
    self.actor.SetMapper(mapper)

    # Create the label if needed
    if label_text != None:

      # Create the label and set its text
      self.label = vtk.vtkVectorText()
      self.label.SetText(label_text)

      # Set up a mapper for the label
      lblMapper = vtk.vtkPolyDataMapper()
      lblMapper.SetInputConnection(self.label.GetOutputPort())

      # Set up an actor for the label
      self.lblActor = vtk.vtkFollower()
      self.lblActor.SetMapper(lblMapper)
      self.lblActor.SetScale(text_height, text_height, text_height)
      self.lblActor.SetPosition(position[0] - (length - 0.6*text_height)*unitVector[0], \
                                position[1] - (length - 0.6*text_height)*unitVector[1], \
                                position[2] - (length - 0.6*text_height)*unitVector[2])
      self.lblActor.GetProperty().SetColor(0, 255, 0) # Green
    
class VisDistLoad():
  '''
  Creates a distributed load for the viewer
  '''

  def __init__(self, position1, position2, direction, length1, length2, label_text1, label_text2, text_height=5):
    '''
    Constructor.
    '''

    # Calculate the length of the distributed load
    loadLength = ((position2[0]-position1[0])**2 + (position2[1]-position1[1])**2 + (position2[2]-position1[2])**2)**0.5

    # Find the direction cosines for the line the load acts on
    lineDirCos = [(position2[0]-position1[0])/loadLength, (position2[1]-position1[1])/loadLength, (position2[2]-position1[2])/loadLength]

    # Find the direction cosines for the direction the load acts in
    magnitude = (direction[0]**2 + direction[1]**2 + direction[2]**2)**0.5
    dirDirCos = [direction[0]/magnitude, direction[1]/magnitude, direction[2]/magnitude]

    # Create point loads at intervals roughly equal to 75% of the load's largest length (magnitude)
    # Add text labels to the first and last load arrow
    num_steps = int(round(0.75*loadLength/max(abs(length1), abs(length2)), 0))
    step = loadLength/num_steps
    ptLoads = []

    for i in range(num_steps + 1):

      # Calculate the position (X, Y, Z) of this load arrow's point
      position = (position1[0] + i*step*lineDirCos[0], position1[1] + i*step*lineDirCos[1], position1[2] + i*step*lineDirCos[2])

      # Determine the length of this load arrow
      length = length1 + (length2 - length1)/loadLength*i*step

      # Determine the label's text
      if i == 0:
        label_text = label_text1
      elif i == num_steps:
        label_text = label_text2

      # Create the load arrow
      ptLoads.append(VisPtLoad(position, direction, length, label_text, text_height=text_height))
    
    # Draw a line between the first and last load arrow's tails
    tail_line = vtk.vtkLineSource()
    tail_line.SetPoint1((position1[0] - length1*dirDirCos[0], position1[1] - length1*dirDirCos[1], position1[2] - length1*dirDirCos[2]))
    tail_line.SetPoint2((position2[0] - length2*dirDirCos[0], position2[1] - length2*dirDirCos[1], position2[2] - length2*dirDirCos[2]))

    # Combine all the geometry into one 'vtkPolyData' object
    append_filter = vtk.vtkAppendPolyData()
    for arrow in ptLoads:
      arrow.append_filter.Update()
      poly_data = vtk.vtkPolyData()
      poly_data.ShallowCopy(arrow.append_filter.GetOutput())
      append_filter.AddInputData(poly_data)
    
    tail_line.Update()
    poly_data = vtk.vtkPolyData()
    poly_data.ShallowCopy(tail_line.GetOutput())
    append_filter.AddInputData(poly_data)

    # Create a mapper and actor for the geometry
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(append_filter.GetOutputPort())
    self.actor = vtk.vtkActor()
    self.actor.GetProperty().SetColor(0, 255, 0) # Green
    self.actor.SetMapper(mapper)

    # Get the actors for the labels
    self.lblActors = [ptLoads[0].lblActor, ptLoads[len(ptLoads) - 1].lblActor]

class VisMoment():
  '''
  Creates a concentrated moment for the viewer
  '''

  def __init__(self, position, direction, radius, label_text=None, text_height=5):
    '''
    Constructor.

    Parameters
    ----------
    position : tuple
      A tuple of X, Y and Z coordinates for center of the moment: (X, Y, Z).
    direction : tuple
      A tuple indicating the direction vector for the moment: (i, j, k).
    radius : number
      The radius of the moment.
    tip_length : number
      The height of the arrow head.
    label_text : string
      Text that will show up at the tail of the moment. If set to 'None' no text will be displayed.
    '''

    # Find a vector perpendicular to the directional unit vector
    v1 = UnitVector(direction) # The direction of the moment
    v2 = PerpVector(v1) # A vector perpendicular to the direction
    v3 = UnitVector(CrossProduct(v1, v2))

    # Create a 'vtkAppendPolyData' filter to append the tip and shaft together into a single dataset
    self.append_filter = vtk.vtkAppendPolyData()

    # Generate an arc for the moment
    arc = vtk.vtkArcSource()
    arc.SetCenter(position[0], position[1], position[2])
    arc.SetPoint1(position[0] + v2[0]*radius, position[1] + v2[1]*radius, position[2] + v2[2]*radius)
    arc.SetPoint2(position[0] + v3[0]*radius, position[1] + v3[1]*radius, position[2] + v3[2]*radius)
    arc.SetNegative(True)
    arc.SetResolution(20)

    # Copy and append the shaft data to the append filter
    arc.Update()
    poly_data = vtk.vtkPolyData()
    poly_data.ShallowCopy(arc.GetOutput())
    self.append_filter.AddInputData(poly_data)

    # Generate the arrow head
    tip_length = radius/2
    cone_radius = radius/8
    tip = vtk.vtkConeSource()
    tip.SetCenter(arc.GetPoint1()[0], arc.GetPoint1()[1], arc.GetPoint1()[2])
    tip.SetDirection(CrossProduct(v1, v2))
    tip.SetHeight(tip_length)
    tip.SetRadius(cone_radius)

    # Copy and append the tip data to the append filter
    tip.Update()
    poly_data = vtk.vtkPolyData()
    poly_data.ShallowCopy(tip.GetOutput())
    self.append_filter.AddInputData(poly_data)

    # Create a mapper and actor
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(self.append_filter.GetOutputPort())
    self.actor = vtk.vtkActor()
    self.actor.GetProperty().SetColor(0, 255, 0) # Green
    self.actor.SetMapper(mapper)

    # Create the label if needed
    self.label = vtk.vtkVectorText()
    self.label.SetText(label_text)

    # Set up a mapper for the label
    lblMapper = vtk.vtkPolyDataMapper()
    lblMapper.SetInputConnection(self.label.GetOutputPort())

    # Set up an actor for the label
    self.lblActor = vtk.vtkFollower()
    self.lblActor.SetMapper(lblMapper)
    self.lblActor.SetScale(text_height, text_height, text_height)
    self.lblActor.SetPosition(arc.GetPoint2()[0] + 0.6*text_height, \
                              arc.GetPoint2()[1] + 0.6*text_height, \
                              arc.GetPoint2()[2] + 0.6*text_height)
    self.lblActor.GetProperty().SetColor(0, 255, 0) # Green

def UnitVector(v):
  '''
  Returns a unit vector in the direction of v=[i, j, k]
  '''

  i = v[0]
  j = v[1]
  k = v[2]

  # Calculate the magnitude of the vector
  mag = (i**2 + j**2 + k**2)**0.5

  # Divide the vector by its magnitude to get a unit vector
  return [i/mag, j/mag, k/mag]

def CrossProduct(v1, v2):

  i1, j1, k1 = v1[0], v1[1], v1[2]
  i2, j2, k2 = v2[0], v2[1], v2[2]

  return [j1*k2 - j2*k1, -i1*k2 + i2*k1, i1*j2 - i2*j1]

def PerpVector(v):
  '''
  Returns a unit vector perpendicular to v=[i, j, k]
  '''

  i = v[0]
  j = v[1]
  k = v[2]

  # Find a vector in a direction perpendicular to <i, j, k>
  if i == 0:
    i2 = 1
    j2 = 0
    k2 = 0
  elif j == 0:
    i2 = 0
    j2 = 1
    k2 = 0
  elif k == 0:
    i2 = 0
    j2 = 0
    k2 = 1
  else:
    i2 = 1
    j2 = 1
    k2 = -(i*i2+j*j2)/k
  
  # Return the unit vector
  return UnitVector([i2, j2, k2])



  