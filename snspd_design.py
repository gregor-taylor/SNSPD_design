import gdspy
import numpy as np

nw_cell=gdspy.Cell('Nanowire')

def generate_nw(line, gap, area, prox_buffer=0.5, end=0.5, start_point=(0,0), round_ends=True):
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

    poly=gdspy.Polygon(points)
    if round_ends==True:
    	poly.fillet((gap/2))

    #copy and rotate the nanowire and slot it in
    poly2 = gdspy.Polygon(points)
    if round_ends==True:
    	poly2.fillet((gap/2))
    poly2.rotate(np.pi)
    poly2.translate((area+(2*prox_buffer)),(area+(2*prox_buffer)+line)) 

    nw=gdspy.PolygonSet([poly, poly2])

    return poly, poly2

def generate_cross(size,thickness, start_point=(0,0)):
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
    cross=gdspy.Polygon(points)
    return cross

def generate_grill(size, thickness, spacing=None,start_point=(0,0)):
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

    grill=gdspy.PolygonSet(set_of_poly)
    return grill
  

def generate_taper(start_width, end_width, length, footprint, thickness=0.5, start_point=(0,0), orientation='r', corner_correction=3, rec_flag=False): 
    #footprint in form (x,y) 
    taper=gdspy.Path(thickness, start_point, number_of_paths=2, distance=(start_width+thickness))
    taper.turn((start_width),'l') #first turn to go out of the nanowire
    #calculate the length of each straight section
    number_lines=length/footprint[0]-corner_correction #corner_correction tunes the length to account for the lengths in the corners.
    taper_per_line=(end_width-start_width)/number_lines #how much to taper on each straight
    current_width=start_width 
    line_length=footprint[0]
    #First and last straight only goes half way.
    #First straight
    current_width+=(taper_per_line/2)
    taper.segment((line_length/2), '+y', final_distance=(current_width))
    taper.turn((current_width),'rr')
    neg=True #Keeps track of which end is the corner
    #Main body of lines
    for i in range(int(round(number_lines-1))):
        current_width+=taper_per_line
        if neg==True:
            taper.segment((line_length), '-y', final_distance=(current_width))
            taper.turn((current_width),'ll')
            neg=False
        else:
            taper.segment((line_length), '+y', final_distance=(current_width))
            taper.turn((current_width),'rr')
            neg=True
    #Last straight
    current_width+=(taper_per_line/2)
    #Sets the end of the taper to be exactly as requested.
    if round(current_width)!=end_width:
        print(f'End width is {current_width}, setting last line taper to end in {end_width} instead')
        current_width=end_width
    if neg==True:
        taper.segment((line_length/2), '-y', final_distance=(current_width))
        taper.turn((current_width),'l')
    else:
        taper.segment((line_length/2), '+y', final_distance=(current_width))
        taper.turn((current_width),'r')
    #Allows to rotate the taper so it can go in any direction
    if orientation!='r':
        if orientation=='d':
            taper.rotate((3*np.pi)/2)
        if orientation=='u':
            taper.rotate((np.pi)/2)
        if orientation=='l':
            taper.rotate((np.pi))
    #Next section to remove lines to account for the lengths of the corners. Works by tuning the corner correction parameter until the line.length is within
    #acceptable limits.
    #rec_flag parameter set to True ensures it only runs this section once and will not infinitely loop. If length is still wrong manually adjust the 
    #corner_correction parameter. probably a better way to do this - will return to it.
    if rec_flag==False:
        if taper.length > (length+1000): #accept within 1um either way.
            corner_correction+=1
            taper = generate_taper(start_width, end_width, length, footprint,corner_correction=corner_correction, rec_flag=True)
        elif taper.length < (length-1000):
            corner_correction-=1
            taper = generate_taper(start_width, end_width, length, footprint,corner_correction=corner_correction, rec_flag=True)

    print(f'Taper length:{taper.length}')
    return taper

def generate_cpw(start_width, end_width, gap, length, orientation='u',start_point=(0,0), contact_pad=True):
    cpw=gdspy.Path(gap, start_point, number_of_paths=2, distance=(start_width+gap))
    #square section to start#
    cpw.segment((start_width), '+y')
    #taper it up
    cpw.segment(length, '+y', final_distance=end_width)
    if contact_pad==True:
        cpw.segment((end_width+(2*gap)), '+y')
    if orientation!='u':
        if orientation=='r':
            cpw.rotate((3*np.pi)/2)
        if orientation=='l':
            cpw.rotate((np.pi)/2)
        if orientation=='d':
            cpw.rotate((np.pi))
    return cpw

    

#nw1_1, nw1_2=generate_nw(0.05,0.1, 10.2)

#nw_cell.add([nw1_1,nw1_2])
#taper=generate_taper(0.5, 135, 77900, (2300,1100))
#cpw=generate_cpw(0.5, 200, 1,500)
#cross=generate_cross(100,10)
grill=generate_grill(10, 1)
nw_cell.add(grill)
gdspy.LayoutViewer()