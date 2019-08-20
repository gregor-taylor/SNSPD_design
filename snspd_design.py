import gdspy
import numpy as np


def generate_nw(line, gap, area, layer_def, prox_buffer=0.5, end=0.5, start_point=(0,0), round_ends=True):
    points=[start_point]
    number_of_lines = (area/((2*gap)+(2*line)))
    current_x, current_y = start_point[0],start_point[1]
    #draw buffer side first
    current_y+=(area+(2*prox_buffer)+line)
    points.append((current_x, current_y))
    current_x+=(area+prox_buffer-end)
    points.append((current_x, current_y))
    current_y-=prox_buffer
    points.append((current_x, current_y))
    current_x-=(area-end)
    points.append((current_x, current_y))
    for i in range(int(round(number_of_lines))):
        current_y-=((2*line)+gap)
        points.append((current_x, current_y))
        current_x+=(area-end-prox_buffer)
        points.append((current_x, current_y))
        current_y-=gap
        points.append((current_x, current_y))
        current_x-=(area-end-prox_buffer)
        points.append((current_x, current_y))
    current_y-=(prox_buffer+line)
    points.append((current_x, current_y))

    poly=gdspy.Polygon(points,**layer_def)
    if round_ends==True:
    	poly.fillet((gap/2))

    #copy and rotate the nanowire and slot it in
    poly2 = gdspy.Polygon(points,**layer_def)
    if round_ends==True:
    	poly2.fillet((gap/2))
    poly2.rotate(np.pi, center=start_point)
    poly2.translate((area+(2*prox_buffer)),(area+(2*prox_buffer)+line)) 

    return [poly, poly2]

def generate_cross(size,thickness,layer_def, start_point=(0,0)):
    points=[(start_point[0]+(size/2)-(thickness/2), start_point[1])]
    current_x, current_y=points[0][0], points[0][1]
    long_side=(size/2)-(thickness/2)
    current_y+=long_side
    points.append((current_x, current_y))
    current_x-=long_side
    points.append((current_x, current_y))
    current_y+=thickness
    points.append((current_x, current_y))
    current_x+=long_side
    points.append((current_x, current_y))
    current_y+=long_side
    points.append((current_x, current_y))
    current_x+=thickness
    points.append((current_x, current_y))
    current_y-=long_side
    points.append((current_x, current_y))
    current_x+=long_side
    points.append((current_x, current_y))
    current_y-=thickness
    points.append((current_x, current_y))
    current_x-=long_side
    points.append((current_x, current_y))
    current_y-=long_side
    points.append((current_x, current_y))
    current_x-=thickness
    points.append((current_x, current_y))
    cross=gdspy.Polygon(points, **layer_def)
    return cross

def generate_grill(size, thickness, layer_def, spacing=None,start_point=(0,0)):
    set_of_poly=[]
    points=[start_point]
    #If spacing not equal to thickness then change from None
    if spacing==None:
        spacing=thickness
    #first one
    current_x, current_y=points[0][0], points[0][1]
    current_y+=size
    points.append((current_x, current_y))
    current_x+=thickness
    points.append((current_x, current_y))
    current_y-=size
    points.append((current_x, current_y))
    set_of_poly.append(points)
    for i in range(int(size/(thickness+spacing))):
        points=[]
        current_x+=spacing
        points.append((current_x, current_y))
        current_y+=size
        points.append((current_x, current_y))
        current_x+=thickness
        points.append((current_x, current_y))
        current_y-=size
        points.append((current_x, current_y))
        set_of_poly.append(points)

    grill=gdspy.PolygonSet(set_of_poly, **layer_def)
    return grill
  

def generate_taper(start_width, end_width, length, footprint, layer_def, thickness=0.5, start_point=(0,0), orientation='r', corner_correction=3, rec_flag=False): 
    #footprint in form (x,y) 
    taper=gdspy.Path(thickness, start_point, number_of_paths=2, distance=(start_width+thickness))
    taper.turn((start_width),'l',**layer_def) #first turn to go out of the nanowire
    #calculate the length of each straight section
    number_lines=length/footprint[0]-corner_correction #corner_correction tunes the length to account for the lengths in the corners.
    taper_per_line=(end_width-start_width)/number_lines #how much to taper on each straight
    current_width=start_width 
    line_length=footprint[0]
    #First and last straight only goes half way.
    #First straight
    current_width+=(taper_per_line/2)
    taper.segment((line_length/2), '+y', final_distance=(current_width),**layer_def)
    taper.turn((current_width),'rr',**layer_def)
    neg=True #Keeps track of which end is the corner
    #Main body of lines
    for i in range(int(round(number_lines-1))):
        current_width+=taper_per_line
        if neg==True:
            taper.segment((line_length), '-y', final_distance=(current_width),**layer_def)
            taper.turn((current_width),'ll',**layer_def)
            neg=False
        else:
            taper.segment((line_length), '+y', final_distance=(current_width),**layer_def)
            taper.turn((current_width),'rr',**layer_def)
            neg=True
    #Last straight
    current_width+=(taper_per_line/2)
    #Sets the end of the taper to be exactly as requested.
    if round(current_width)!=end_width:
        print(f'End width is {current_width}, setting last line taper to end in {end_width} instead')
        current_width=end_width
    if neg==True:
        taper.segment((line_length/2), '-y', final_distance=(current_width),**layer_def)
        taper.turn((current_width),'l',**layer_def)
    else:
        taper.segment((line_length/2), '+y', final_distance=(current_width),**layer_def)
        taper.turn((current_width),'r',**layer_def)
    #Allows to rotate the taper so it can go in any direction
    if orientation!='r':
        if orientation=='d':
            taper.rotate((3*np.pi)/2, center=start_point)
        if orientation=='u':
            taper.rotate((np.pi)/2, center=start_point)
        if orientation=='l':
            taper.rotate((np.pi), center=start_point)
    #Next section to remove lines to account for the lengths of the corners. Works by tuning the corner correction parameter until the line.length is within
    #acceptable limits.
    #rec_flag parameter set to True ensures it only runs this section once and will not infinitely loop. If length is still wrong manually adjust the 
    #corner_correction parameter. probably a better way to do this - will return to it.
    if rec_flag==False:
        if taper.length > (length+1000): #accept within 1um either way.
            corner_correction+=1
            taper = generate_taper(start_width, end_width, length, layer_def, footprint,corner_correction=corner_correction, rec_flag=True)
        elif taper.length < (length-1000):
            corner_correction-=1
            taper = generate_taper(start_width, end_width, length, layer_def, footprint,corner_correction=corner_correction, rec_flag=True)

    print(f'Taper length:{taper.length}')
    return taper
def generate_taper_advanced(start_width, end_width, length, footprint, layer_def, thickness=0.5, start_point=(0,0), orientation='r', section_length=10000):
    #Will work by:
    #work out impedance versus position over the length
    #take steps of impedance and work out the width for each step
    #create the taper in sections of section_length

    pass

def generate_straight_taper(start_width, end_width, length, layer_def, thickness=3, start_point=(0,0), orientation='u'):
    taper=gdspy.Path(thickness, start_point, number_of_paths=2, distance=(start_width+thickness))
    taper.segment(length, '+y', final_distance=(end_width), **layer_def)
    return taper

def generate_cpw(start_width, end_width, gap_start, gap_final, length, layer_def, orientation='u',start_point=(0,0), contact_pad=True):
    cpw=gdspy.Path(gap_start, start_point, number_of_paths=2, distance=(start_width+gap_start))
    #square section to start#
    cpw.segment((start_width), '+y', **layer_def)
    #taper it up
    cpw.segment(length, '+y', final_distance=end_width+gap_final, final_width=gap_final, **layer_def)
    if contact_pad==True:
        cpw.segment(end_width, '+y', **layer_def)
        close_off=gdspy.Rectangle(((start_point[0]-end_width),(start_point[1]+length+end_width)), ((start_point[0]+end_width), (start_point[1]+length+end_width+gap_final)))
    if orientation!='u':
        if orientation=='r':
            cpw.rotate((3*np.pi)/2, center=start_point)
            if contact_pad==True:
                close_off.rotate((3*np.pi)/2, center=start_point)
        if orientation=='l':
            cpw.rotate((np.pi)/2, center=start_point)
            if contact_pad==True:
                close_off.rotate((np.pi)/2, center=start_point)
        if orientation=='d':
            cpw.rotate((np.pi), center=start_point)
            if contact_pad==True:
                close_off.rotate((np.pi), center=start_point)
    if contact_pad==True:
        return [cpw, close_off]
    else:
        return [cpw]

def generate_cpw_contacts(start_point, length, thickness, layer_def, cpw1, cpw2): #if odd angles required better to geneate CPW and contacts then rotate cell
    short_length=length-(2*thickness)
    points=[start_point]
    current_x=start_point[0]
    current_y=start_point[1]
    current_x+=(length/2)
    points.append((current_x, current_y))
    current_y-=length
    points.append((current_x, current_y))
    current_x-=(length)
    points.append((current_x, current_y))
    current_y+=length
    points.append((current_x, current_y))
    current_x+=(length/2)
    points.append((current_x, current_y))
    #For whatever reason doesn't seem to want to create a hole of the second polygon so will create two and subtract
    outer_poly=gdspy.Polygon(points, **layer_def)
    #reset points
    current_y-=thickness
    points=[(current_x, current_y)]
    current_x+=((short_length/2)+(thickness/2))
    points.append((current_x, current_y))
    current_y-=(short_length)
    points.append((current_x, current_y))
    current_x-=((short_length+(thickness/2)*(2/3)))
    points.append((current_x, current_y))
    current_x-=((short_length-(thickness/2))*(1/3))
    current_y+=(short_length*(1/3))
    points.append((current_x, current_y))
    current_y+=(short_length*(2/3))
    points.append((current_x, current_y))
    inner_poly=gdspy.Polygon(points, **layer_def)

    cutout=gdspy.boolean(outer_poly, inner_poly, 'not', **layer_def)

    #Take away the CPW lines to form the contacts. Set cpw2==None if only one
    if cpw2!=None:
        contacts=gdspy.boolean(cutout, [*cpw,*cpw2], 'not',**layer_def)
    else:
        contacts=gdspy.boolean(cutout, [*cpw], 'not', **layer_def)


    return contacts


#Def types
wafer_def={'layer':12, 'datatype':12}
chip_def={'layer':11, 'datatype':11}
superconductor_def={'layer':0, 'datatype':0}
contact_def={'layer':1,'datatype':1}

############################
#
#
####Twin CPW SNSPD####
#
#
############################
#Some common definitions:
chip_edge = 5000
wafer_edge=10000
#Def cell
nw_cell=gdspy.Cell('Nanowire')
#Def wafer

#Def chip size
chip_size=gdspy.Rectangle((0,0),(chip_edge,chip_edge), **chip_def)
nw_cell.add(chip_size)

#Def SC layer
nw1=generate_nw(0.05,0.1, 10.2, superconductor_def, start_point=(2500,2500))
#nw_cell.add([nw1_1,nw1_2])
#taper=generate_taper(0.5, 135, 77900, (2300,1100))
#str_taper=generate_straight_taper(0.5,135,77900)
cpw=generate_cpw(0.5, 600, 3.5,300,1115, superconductor_def, start_point=(2510.45,2511.2))
cpw2=generate_cpw(0.5,600,3.5,300,1115,superconductor_def,start_point=(2500.75,2500.05),orientation='d')
nw_cell.add([*nw1,*cpw,*cpw2])

#Edges of the contact pads
y_cord_list=[]
x_cord_list=[]
for i in cpw[1].get_bounding_box():
    y_cord_list.append(i[1])
    x_cord_list.append(i[0])
for i in cpw2[1].get_bounding_box():
    y_cord_list.append(i[1])

sq_size=max(y_cord_list)-min(y_cord_list)
strt_point_x=(max(x_cord_list)+min(x_cord_list))/2
strt_point_y=max(y_cord_list)
strt_point=(strt_point_x,strt_point_y)

contacts=generate_cpw_contacts(strt_point, sq_size, 900, contact_def, cpw, cpw2)
nw_cell.add(contacts)

##########################################################################################



###############################
#
#
#Wafer and layer 4xcells on it
#
#
################################
wafer_cell=gdspy.Cell('Wafer')
wafer_size=gdspy.Rectangle((0,0),(wafer_edge,wafer_edge), **wafer_def)
wafer_cell.add(wafer_size)

wafer_cell.add(gdspy.CellArray(nw_cell,2,2,(chip_edge-250,chip_edge-250)))

#some alignment markers
cross=generate_cross(400,20, contact_def, start_point=(wafer_edge-9000, wafer_edge-500))
grill=generate_grill(400, 20, contact_def, start_point=(wafer_edge-9600,wafer_edge-500))
wafer_cell.add([cross, grill])

top_plate=gdspy.Rectangle((2000,wafer_edge-500), (wafer_edge-1000,wafer_edge-100), **contact_def)
side_plate=gdspy.Rectangle((wafer_edge-500, 1000), (wafer_edge-100,wafer_edge-1000), **contact_def)
wafer_cell.add([top_plate,side_plate])

gdspy.LayoutViewer()









#For inverting the shape for simulations
'''
bounds=cpw.get_bounding_box()
point_1=(bounds[0][0]-1000, bounds[0][1])
point_2=(bounds[1][0]+1000, bounds[1][1])
box=gdspy.Rectangle(point_1, point_2)
comb=gdspy.boolean(box, cpw, 'not')
'''

#cross=generate_cross(100,10)
#grill=generate_grill(10, 1)



#gdspy.write_gds('Output_gds.gds')